from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hiring_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    years: Mapped[list["CompanyYear"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class CompanyYear(Base):
    __tablename__ = "company_years"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    visit_year: Mapped[int] = mapped_column(index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped[Company] = relationship(back_populates="years")
    roles: Mapped[list["CompanyRole"]] = relationship(back_populates="company_year", cascade="all, delete-orphan")


class CompanyRole(Base):
    __tablename__ = "company_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_year_id: Mapped[int] = mapped_column(ForeignKey("company_years.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    selection_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company_year: Mapped[CompanyYear] = relationship(back_populates="roles")
    role_skills: Mapped[list["RoleSkill"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class RoleSkill(Base):
    __tablename__ = "role_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("company_roles.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)

    role: Mapped[CompanyRole] = relationship(back_populates="role_skills")
