import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.google import verify_google_credential
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.dependencies.auth import get_current_user
from app.models.enums import UserRole, UserStatus
from app.models.user import ApprovalRequest, PasswordResetToken, StudentProfile, User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    GoogleLoginResponse,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserPublic,
)
from app.schemas.common import MessageResponse as Msg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Email + password sign-in. Used by the TPO and PCELL staff; students sign in with Google."""
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status == UserStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is pending approval")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    token = create_access_token(str(user.id), {"role": user.role.value})
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/google", response_model=GoogleLoginResponse)
async def google_login(body: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    """Sign in with Google. A first-time student creates a PENDING account and an approval request for PCELL/TPO."""
    claims = await verify_google_credential(body.credential)
    email = claims["email"].lower()
    sub = claims["sub"]
    name = claims.get("name") or email.split("@")[0]

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        if body.details is None:
            return GoogleLoginResponse(status="DETAILS_REQUIRED", email=email, full_name=name)
        user = User(
            email=email,
            full_name=name,
            hashed_password=None,
            google_sub=sub,
            avatar_url=claims.get("picture"),
            role=UserRole.STUDENT,
            status=UserStatus.PENDING,
        )
        db.add(user)
        await db.flush()
        d = body.details
        db.add(
            StudentProfile(
                user_id=user.id, roll_number=d.roll_number.strip(), course=d.course.strip(), batch=d.batch.strip(), phone=d.phone
            )
        )
        db.add(ApprovalRequest(user_id=user.id, requested_role=UserRole.STUDENT, status=UserStatus.PENDING))
        return GoogleLoginResponse(
            status="PENDING", email=email, full_name=name, message="Request sent. You can sign in once PCELL approves it."
        )

    if user.google_sub and user.google_sub != sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This email is linked to a different Google account")
    if user.status == UserStatus.PENDING:
        return GoogleLoginResponse(
            status="PENDING", email=email, full_name=user.full_name, message="Your request is still waiting for approval."
        )
    if user.status == UserStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your request was rejected. Contact the placement cell.")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    user.google_sub = sub
    user.avatar_url = claims.get("picture") or user.avatar_url
    token = create_access_token(str(user.id), {"role": user.role.value})
    return GoogleLoginResponse(status="OK", access_token=token, role=user.role, full_name=user.full_name, email=email)


@router.post("/logout", response_model=Msg)
async def logout(_: User = Depends(get_current_user)):
    return Msg(message="Logged out")


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password", response_model=Msg)
async def change_password(body: ChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not user.hashed_password or not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = get_password_hash(body.new_password)
    return Msg(message="Password updated")


@router.post("/forgot-password", response_model=Msg)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if user:
        token = create_password_reset_token(user.email)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        from datetime import timedelta

        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )
        )
        # No mail provider is wired up yet: the reset link is logged server-side only, never returned to the client.
        logger.warning("Password reset link for %s: %s/reset-password?token=%s", user.email, get_settings().frontend_url, token)
    return Msg(message="If the account exists, password reset instructions were sent.")


@router.post("/reset-password", response_model=Msg)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.token)
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token")
        email = payload.get("sub")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid or expired token") from exc

    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    record = result.scalar_one_or_none()
    if not record or record.used_at:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(body.new_password)
    record.used_at = datetime.now(timezone.utc)
    return Msg(message="Password reset successful")
