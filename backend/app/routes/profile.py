from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.enums import UserRole
from app.models.user import StudentProfile, User

router = APIRouter(prefix="/api/profile", tags=["profile"])


# Student-only columns on StudentProfile; also the keys a registration form field can pull from.
STUDENT_FIELDS = (
    "course", "batch", "branch", "graduation_year", "roll_number", "phone", "bio", "cgpa", "tenth_percentage", "twelfth_percentage",
    "has_atkt", "atkt_count", "current_semester", "gender", "date_of_birth", "personal_email", "city",
    "linkedin_url", "github_url",
)


class ProfileOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    course: str | None = None
    batch: str | None = None
    branch: str | None = None
    graduation_year: int | None = None
    roll_number: str | None = None
    phone: str | None = None
    bio: str | None = None
    cgpa: float | None = None
    tenth_percentage: float | None = None
    twelfth_percentage: float | None = None
    has_atkt: bool | None = None
    atkt_count: int | None = None
    current_semester: int | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    personal_email: str | None = None
    city: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    course: str | None = Field(default=None, max_length=128)
    batch: str | None = Field(default=None, max_length=32)
    branch: str | None = Field(default=None, max_length=128)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    roll_number: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32)
    bio: str | None = None
    cgpa: float | None = Field(default=None, ge=0, le=10)
    tenth_percentage: float | None = Field(default=None, ge=0, le=100)
    twelfth_percentage: float | None = Field(default=None, ge=0, le=100)
    has_atkt: bool | None = None
    atkt_count: int | None = Field(default=None, ge=0, le=50)
    current_semester: int | None = Field(default=None, ge=1, le=12)
    gender: str | None = Field(default=None, max_length=32)
    date_of_birth: date | None = None
    personal_email: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    linkedin_url: str | None = Field(default=None, max_length=512)
    github_url: str | None = Field(default=None, max_length=512)


async def _student_profile(db: AsyncSession, user: User) -> StudentProfile | None:
    if user.role != UserRole.STUDENT:
        return None
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    return result.scalar_one_or_none()


def _to_out(user: User, profile: StudentProfile | None) -> ProfileOut:
    extra = {f: getattr(profile, f) for f in STUDENT_FIELDS} if profile else {}
    return ProfileOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role, **extra)


@router.get("", response_model=ProfileOut)
async def get_profile(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return _to_out(user, await _student_profile(db, user))


@router.put("", response_model=ProfileOut)
async def update_profile(body: ProfileUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    data = body.model_dump(exclude_unset=True)
    if data.get("full_name"):
        user.full_name = data.pop("full_name")
    else:
        data.pop("full_name", None)

    profile = await _student_profile(db, user)
    if user.role == UserRole.STUDENT:
        if profile is None:
            profile = StudentProfile(user_id=user.id)
            db.add(profile)
        for key, value in data.items():
            setattr(profile, key, value)
        await db.flush()
    return _to_out(user, profile)
