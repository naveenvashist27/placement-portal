"""Create (or reset the password of) the TPO account. Run from backend/:

    python -m scripts.create_tpo                       # uses TPO_EMAIL / TPO_PASSWORD from .env
    python -m scripts.create_tpo you@iips.edu.in 'S3cret!pass' "Full Name"
"""

import asyncio
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.enums import UserRole, UserStatus
from app.models.user import User


async def main(email: str, password: str, name: str) -> None:
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
        if user is None:
            user = User(email=email.lower(), full_name=name, role=UserRole.TPO, status=UserStatus.ACTIVE)
            db.add(user)
        user.role = UserRole.TPO
        user.status = UserStatus.ACTIVE
        user.hashed_password = get_password_hash(password)
        await db.commit()
    print(f"TPO ready. Email: {email.lower()}  (password as given)")


if __name__ == "__main__":
    s = get_settings()
    args = sys.argv[1:]
    asyncio.run(main(args[0] if args else s.tpo_email, args[1] if len(args) > 1 else s.tpo_password, args[2] if len(args) > 2 else "TPO"))
