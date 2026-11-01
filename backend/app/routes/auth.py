import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
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
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserPublic,
)
from app.schemas.common import MessageResponse as Msg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.role == UserRole.PCELL_MEMBER and user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="PCELL account pending approval or suspended")
    if user.status in {UserStatus.SUSPENDED, UserStatus.REJECTED, UserStatus.INACTIVE}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    token = create_access_token(str(user.id), {"role": user.role.value})
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/register", response_model=Msg)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    email = body.email.lower()

    if body.role == UserRole.STUDENT and not settings.allow_student_registration:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Student registration with college email is not enabled yet. Use demo accounts from README.",
        )

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    status_value = UserStatus.ACTIVE
    if body.role == UserRole.PCELL_MEMBER:
        status_value = UserStatus.PENDING
    elif body.role == UserRole.TPO:
        raise HTTPException(status_code=403, detail="TPO accounts cannot self-register")

    user = User(
        email=email,
        full_name=body.full_name,
        hashed_password=get_password_hash(body.password),
        role=body.role,
        status=status_value,
    )
    db.add(user)
    await db.flush()

    if body.role == UserRole.STUDENT:
        db.add(StudentProfile(user_id=user.id))
    if body.role == UserRole.PCELL_MEMBER:
        db.add(ApprovalRequest(user_id=user.id, requested_role=UserRole.PCELL_MEMBER, status=UserStatus.PENDING))

    return Msg(message="Registration successful")


@router.post("/logout", response_model=Msg)
async def logout(_: User = Depends(get_current_user)):
    return Msg(message="Logged out")


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password", response_model=Msg)
async def change_password(body: ChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(body.current_password, user.hashed_password):
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
