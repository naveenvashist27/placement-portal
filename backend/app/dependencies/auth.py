from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.enums import UserRole, UserStatus
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.status not in {UserStatus.ACTIVE, UserStatus.PENDING}:
        raise credentials_exception
    return user


def require_roles(*roles: UserRole):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        if user.role == UserRole.PCELL_MEMBER and user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="PCELL account not active")
        return user

    return checker


RequireStudent = Depends(require_roles(UserRole.STUDENT, UserRole.PCELL_MEMBER, UserRole.TPO))
RequirePcell = Depends(require_roles(UserRole.PCELL_MEMBER, UserRole.TPO))
RequireTpo = Depends(require_roles(UserRole.TPO))
