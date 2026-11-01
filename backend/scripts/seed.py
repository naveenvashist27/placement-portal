"""Development seed data. Run: python -m scripts.seed"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.company import Company, CompanyRole, CompanyYear, RoleSkill
from app.models.content import (
    Event,
    InterviewQuestion,
    RegistrationForm,
    Topic,
)
from app.models.enums import EventStatus, FormStatus, UserRole, UserStatus
from app.models.skill import Skill
from app.models.user import StudentProfile, User
from app.utils.text_normalize import normalize_question_text, normalize_skill_name


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == "tpo@college.demo"))
        if existing.scalar_one_or_none():
            print("Seed already applied")
            return

        tpo = User(
            email="tpo@college.demo",
            full_name="Demo TPO",
            hashed_password=get_password_hash("Demo@12345"),
            role=UserRole.TPO,
            status=UserStatus.ACTIVE,
        )
        pcell = User(
            email="pcell@college.demo",
            full_name="Demo PCELL Member",
            hashed_password=get_password_hash("Demo@12345"),
            role=UserRole.PCELL_MEMBER,
            status=UserStatus.ACTIVE,
        )
        student = User(
            email="student@college.demo",
            full_name="Demo Student",
            hashed_password=get_password_hash("Demo@12345"),
            role=UserRole.STUDENT,
            status=UserStatus.ACTIVE,
        )
        db.add_all([tpo, pcell, student])
        await db.flush()
        db.add(StudentProfile(user_id=student.id, branch="CSE", graduation_year=2026, roll_number="CS2026001"))

        skill_names = ["C++", "Python", "SQL", "DSA", "OOP", "DBMS", "JavaScript", "React", "Git"]
        skills: dict[str, Skill] = {}
        for name in skill_names:
            s = Skill(name=name, normalized_name=normalize_skill_name(name))
            db.add(s)
            skills[name] = s
        await db.flush()

        for topic_name in ["DSA", "DBMS", "OS", "Computer Networks", "OOP", "SQL", "Python", "Aptitude", "HR"]:
            db.add(Topic(name=topic_name))

        tcs = Company(
            name="TCS",
            industry="IT Services",
            website="https://www.tcs.com",
            description="Tata Consultancy Services placement history and interview insights.",
        )
        db.add(tcs)
        await db.flush()

        cy2025 = CompanyYear(company_id=tcs.id, visit_year=2025, notes="Campus placement cycle")
        cy2024 = CompanyYear(company_id=tcs.id, visit_year=2024)
        db.add_all([cy2025, cy2024])
        await db.flush()

        se2025 = CompanyRole(company_year_id=cy2025.id, title="Software Engineer", eligibility="CGPA >= 7.0")
        de2025 = CompanyRole(company_year_id=cy2025.id, title="Digital Engineer")
        se2024 = CompanyRole(company_year_id=cy2024.id, title="Software Engineer")
        db.add_all([se2025, de2025, se2024])
        await db.flush()

        for role, names in [(se2025, ["C++", "DSA", "OOP", "DBMS", "SQL"]), (de2025, ["JavaScript", "React", "SQL"])]:
            for n in names:
                db.add(RoleSkill(role_id=role.id, skill_id=skills[n].id))

        q_text = "What is normalization in DBMS?"
        db.add(
            InterviewQuestion(
                company_id=tcs.id,
                company_year_id=cy2025.id,
                role_id=se2025.id,
                round_label="Technical Interview",
                question_text=q_text,
                normalized_text=normalize_question_text(q_text),
                is_public=True,
                frequency=3,
            )
        )

        deadline = datetime.now(timezone.utc) + timedelta(days=7)
        db.add(
            RegistrationForm(
                title="TCS Placement Registration",
                description="Register for the TCS campus placement process.",
                company_id=tcs.id,
                role_id=se2025.id,
                registration_deadline=deadline,
                status=FormStatus.OPEN,
                created_by_id=pcell.id,
            )
        )
        db.add(
            Event(
                title="Placement Cell Announcement",
                description="Review updated TCS placement registration deadline.",
                company_id=tcs.id,
                registration_deadline=deadline,
                status=EventStatus.PUBLISHED,
                created_by_id=pcell.id,
            )
        )

        await db.commit()
        print("Seed complete. Demo logins (password Demo@12345):")
        print("  TPO: tpo@college.demo")
        print("  PCELL: pcell@college.demo")
        print("  Student: student@college.demo")


if __name__ == "__main__":
    asyncio.run(seed())
