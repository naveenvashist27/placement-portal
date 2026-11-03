from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # None for accounts that only sign in with Google.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    profile_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    student_profile: Mapped["StudentProfile | None"] = relationship(back_populates="user", uselist=False)
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        back_populates="user", foreign_keys="ApprovalRequest.user_id"
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    course: Mapped[str | None] = mapped_column(String(128), nullable=True)
    batch: Mapped[str | None] = mapped_column(String(32), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(128), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(nullable=True)
    roll_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    tenth_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    twelfth_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    has_atkt: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    atkt_count: Mapped[int | None] = mapped_column(nullable=True)
    current_semester: Mapped[int | None] = mapped_column(nullable=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    personal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[User] = relationship(back_populates="student_profile")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    requested_role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.PENDING)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="approval_requests", foreign_keys=[user_id])


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
