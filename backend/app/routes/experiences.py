from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies.auth import RequirePcell, RequireStudent, get_current_user
from app.models.content import InterviewExperience, InterviewRound
from app.models.enums import Difficulty, ExperienceStatus, UserRole
from app.models.company import CompanyRole, CompanyYear
from app.models.content import Notification
from app.models.resume import Resume
from app.models.user import StudentProfile, User
from app.schemas.common import PaginatedResponse
from app.services.audit_service import write_audit

router = APIRouter(prefix="/api/experiences", tags=["experiences"])


class RoundIn(BaseModel):
    round_number: int
    round_type: str
    description: str | None = None
    difficulty: Difficulty = Difficulty.UNKNOWN


class ExperienceIn(BaseModel):
    company_id: int
    company_year_id: int
    role_id: int | None = None
    overall_experience: str = Field(min_length=20)
    preparation_advice: str | None = None
    difficulty: Difficulty = Difficulty.UNKNOWN
    selection_outcome: str | None = None
    rounds: list[RoundIn] = []


class Submitter(BaseModel):
    id: int
    full_name: str
    email: str
    roll_number: str | None = None
    course: str | None = None
    batch: str | None = None
    branch: str | None = None
    passing_year: int | None = None
    phone: str | None = None
    has_resume: bool = False


class ExperienceOut(BaseModel):
    id: int
    company_id: int
    company_year_id: int
    role_id: int | None
    overall_experience: str
    preparation_advice: str | None
    difficulty: Difficulty
    selection_outcome: str | None
    status: ExperienceStatus
    visit_year: int | None = None
    role_title: str | None = None
    review_note: str | None = None  # shown only to the author and to PCELL / TPO
    submitter: Submitter | None = None  # only filled in for PCELL / TPO; students stay anonymous

    model_config = {"from_attributes": True}


@router.get("", response_model=PaginatedResponse[ExperienceOut])
async def list_experiences(
    company_id: int | None = None,
    company_year_id: int | None = None,
    role_id: int | None = None,
    difficulty: Difficulty | None = None,
    mine: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = RequireStudent,
):
    stmt = select(InterviewExperience)
    if mine:
        stmt = stmt.where(InterviewExperience.student_id == user.id)
    elif user.role == UserRole.STUDENT:
        stmt = stmt.where(InterviewExperience.status == ExperienceStatus.APPROVED)
    if company_id:
        stmt = stmt.where(InterviewExperience.company_id == company_id)
    if company_year_id:
        stmt = stmt.where(InterviewExperience.company_year_id == company_year_id)
    if role_id:
        stmt = stmt.where(InterviewExperience.role_id == role_id)
    if difficulty:
        stmt = stmt.where(InterviewExperience.difficulty == difficulty)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (
        await db.execute(
            stmt.add_columns(CompanyYear.visit_year, CompanyRole.title, User, StudentProfile)
            .join(CompanyYear, CompanyYear.id == InterviewExperience.company_year_id)
            .outerjoin(CompanyRole, CompanyRole.id == InterviewExperience.role_id)
            .join(User, User.id == InterviewExperience.student_id)
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .order_by(InterviewExperience.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    is_staff = user.role != UserRole.STUDENT
    with_resume = set()
    if is_staff and rows:
        with_resume = set(
            (await db.execute(select(Resume.student_id).where(Resume.student_id.in_([r[3].id for r in rows])))).scalars()
        )
    items = []
    for exp, visit_year, role_title, student, profile in rows:
        item = ExperienceOut.model_validate(exp)
        item.visit_year = visit_year
        item.role_title = role_title
        if not (is_staff or exp.student_id == user.id):
            item.review_note = None
        if is_staff and not mine:
            item.submitter = Submitter(
                id=student.id,
                full_name=student.full_name,
                email=student.email,
                roll_number=profile.roll_number if profile else None,
                course=profile.course if profile else None,
                batch=profile.batch if profile else None,
                branch=profile.branch if profile else None,
                passing_year=profile.graduation_year if profile else None,
                phone=profile.phone if profile else None,
                has_resume=student.id in with_resume,
            )
        items.append(item)
    return PaginatedResponse(items=items, total=total or 0, page=page, page_size=page_size)


@router.post("", response_model=ExperienceOut)
async def create_experience(body: ExperienceIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Students submit experiences")
    exp = InterviewExperience(
        student_id=user.id,
        company_id=body.company_id,
        company_year_id=body.company_year_id,
        role_id=body.role_id,
        overall_experience=body.overall_experience,
        preparation_advice=body.preparation_advice,
        difficulty=body.difficulty,
        selection_outcome=body.selection_outcome,
        status=ExperienceStatus.PENDING,
    )
    db.add(exp)
    await db.flush()
    for r in body.rounds:
        db.add(InterviewRound(experience_id=exp.id, **r.model_dump()))
    return exp


@router.get("/{experience_id}")
async def get_experience(experience_id: int, db: AsyncSession = Depends(get_db), user: User = RequireStudent):
    result = await db.execute(
        select(InterviewExperience)
        .where(InterviewExperience.id == experience_id)
        .options(selectinload(InterviewExperience.rounds))
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role == UserRole.STUDENT and exp.status != ExperienceStatus.APPROVED and exp.student_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    return exp


@router.post("/{experience_id}/rounds")
async def add_round(experience_id: int, body: RoundIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    exp = await db.get(InterviewExperience, experience_id)
    if not exp or exp.student_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    db.add(InterviewRound(experience_id=experience_id, **body.model_dump()))
    return {"message": "Round added"}


class ReviewIn(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class RejectIn(BaseModel):
    note: str = Field(min_length=3, max_length=1000)


async def _review(db: AsyncSession, user: User, experience_id: int, status: ExperienceStatus, note: str | None):
    exp = await db.get(InterviewExperience, experience_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Not found")
    exp.status = status
    exp.reviewer_id = user.id
    exp.review_note = note
    approved = status == ExperienceStatus.APPROVED
    db.add(
        Notification(
            user_id=exp.student_id,
            title="Experience approved" if approved else "Experience needs changes",
            message=(
                "Your interview experience is now visible to other students."
                if approved
                else f"Your interview experience was not approved. Reason: {note}"
            ),
            notification_type="VERIFICATION",
        )
    )
    await write_audit(db, user, f"{status.value}_EXPERIENCE", "interview_experience", exp.id, note)


@router.post("/{experience_id}/approve")
async def approve_experience(
    experience_id: int, body: ReviewIn | None = None, db: AsyncSession = Depends(get_db), user: User = RequirePcell
):
    await _review(db, user, experience_id, ExperienceStatus.APPROVED, body.note if body else None)
    return {"message": "Approved"}


@router.post("/{experience_id}/reject")
async def reject_experience(
    experience_id: int, body: RejectIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell
):
    await _review(db, user, experience_id, ExperienceStatus.REJECTED, body.note)
    return {"message": "Rejected"}
