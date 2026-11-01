from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequirePcell, RequireStudent, get_current_user
from app.models.content import InterviewQuestion, QuestionSubmission, QuestionTopic
from app.models.enums import Difficulty, QuestionSubmissionStatus, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.services.audit_service import write_audit
from app.services.question_service import create_submission
from app.utils.text_normalize import normalize_question_text

router = APIRouter(prefix="/api/questions", tags=["questions"])
submissions_router = APIRouter(prefix="/api/question-submissions", tags=["question-submissions"])


class QuestionPublicOut(BaseModel):
    id: int
    question_text: str
    round_label: str | None
    difficulty: Difficulty
    frequency: int
    company_id: int | None
    company_year_id: int | None
    role_id: int | None
    topic_id: int | None

    model_config = {"from_attributes": True}


class QuestionSubmitIn(BaseModel):
    submitted_text: str = Field(min_length=5)
    company_id: int | None = None
    company_year_id: int | None = None
    role_id: int | None = None
    round_label: str | None = None
    topic_id: int | None = None
    difficulty: Difficulty = Difficulty.UNKNOWN


class SubmissionOut(BaseModel):
    id: int
    submitted_text: str
    status: QuestionSubmissionStatus
    student_id: int | None = None
    student_name: str | None = None
    student_email: str | None = None
    canonical_question_id: int | None

    model_config = {"from_attributes": True}


@router.get("", response_model=PaginatedResponse[QuestionPublicOut])
async def list_questions(
    company_id: int | None = None,
    company_year_id: int | None = None,
    role_id: int | None = None,
    topic_id: int | None = None,
    difficulty: Difficulty | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = RequireStudent,
):
    stmt = select(InterviewQuestion).where(InterviewQuestion.is_public.is_(True))
    if company_id:
        stmt = stmt.where(InterviewQuestion.company_id == company_id)
    if company_year_id:
        stmt = stmt.where(InterviewQuestion.company_year_id == company_year_id)
    if role_id:
        stmt = stmt.where(InterviewQuestion.role_id == role_id)
    if topic_id:
        stmt = stmt.where(InterviewQuestion.topic_id == topic_id)
    if difficulty:
        stmt = stmt.where(InterviewQuestion.difficulty == difficulty)
    if q:
        stmt = stmt.where(InterviewQuestion.question_text.ilike(f"%{q}%"))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.order_by(InterviewQuestion.frequency.desc()).offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(items=result.scalars().all(), total=total or 0, page=page, page_size=page_size)


@router.get("/{question_id}", response_model=QuestionPublicOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    qobj = await db.get(InterviewQuestion, question_id)
    if not qobj or not qobj.is_public:
        raise HTTPException(status_code=404, detail="Question not found")
    return qobj


@router.post("/submit")
async def submit_question(body: QuestionSubmitIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students submit questions via this endpoint")
    sub = await create_submission(
        db,
        student_id=user.id,
        text=body.submitted_text,
        company_id=body.company_id,
        company_year_id=body.company_year_id,
        role_id=body.role_id,
        round_label=body.round_label,
        topic_id=body.topic_id,
        difficulty=body.difficulty,
    )
    return {"id": sub.id, "status": sub.status}


@submissions_router.get("", response_model=PaginatedResponse[SubmissionOut])
async def list_submissions(
    status: QuestionSubmissionStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = RequirePcell,
):
    stmt = select(QuestionSubmission)
    if status:
        stmt = stmt.where(QuestionSubmission.status == status)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.order_by(QuestionSubmission.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    items: list[SubmissionOut] = []
    for sub in result.scalars():
        student = await db.get(User, sub.student_id)
        items.append(
            SubmissionOut(
                id=sub.id,
                submitted_text=sub.submitted_text,
                status=sub.status,
                student_id=student.id if student else None,
                student_name=student.full_name if student else None,
                student_email=student.email if student else None,
                canonical_question_id=sub.canonical_question_id,
            )
        )
    return PaginatedResponse(items=items, total=total or 0, page=page, page_size=page_size)


class ReviewNote(BaseModel):
    note: str | None = None
    merge_into_question_id: int | None = None


async def _approve_submission(db: AsyncSession, sub: QuestionSubmission, reviewer: User, merge_id: int | None = None):
    if merge_id:
        canonical = await db.get(InterviewQuestion, merge_id)
        if not canonical:
            raise HTTPException(status_code=404, detail="Canonical question not found")
    elif sub.canonical_question_id:
        canonical = await db.get(InterviewQuestion, sub.canonical_question_id)
    else:
        canonical = InterviewQuestion(
            company_id=sub.company_id,
            company_year_id=sub.company_year_id,
            role_id=sub.role_id,
            round_label=sub.round_label,
            question_text=sub.submitted_text.strip(),
            normalized_text=sub.normalized_text,
            topic_id=sub.topic_id,
            difficulty=sub.difficulty,
            is_public=True,
        )
        db.add(canonical)
        await db.flush()
        if sub.topic_id:
            db.add(QuestionTopic(question_id=canonical.id, topic_id=sub.topic_id))
    canonical.frequency = (canonical.frequency or 0) + 1
    sub.status = QuestionSubmissionStatus.APPROVED
    sub.canonical_question_id = canonical.id
    sub.reviewer_id = reviewer.id
    await write_audit(db, reviewer, "APPROVE_QUESTION_SUBMISSION", "question_submission", sub.id)


@submissions_router.post("/{submission_id}/approve")
async def approve_submission(
    submission_id: int,
    body: ReviewNote | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = RequirePcell,
):
    sub = await db.get(QuestionSubmission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    merge_id = body.merge_into_question_id if body else None
    await _approve_submission(db, sub, user, merge_id)
    if body and body.note:
        sub.review_note = body.note
    return {"message": "Approved"}


@submissions_router.post("/{submission_id}/reject")
async def reject_submission(
    submission_id: int, body: ReviewNote | None = None, db: AsyncSession = Depends(get_db), user: User = RequirePcell
):
    sub = await db.get(QuestionSubmission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.status = QuestionSubmissionStatus.REJECTED
    sub.reviewer_id = user.id
    if body and body.note:
        sub.review_note = body.note
    await write_audit(db, user, "REJECT_QUESTION_SUBMISSION", "question_submission", sub.id)
    return {"message": "Rejected"}


@submissions_router.post("/{submission_id}/merge")
async def merge_submission(
    submission_id: int, body: ReviewNote, db: AsyncSession = Depends(get_db), user: User = RequirePcell
):
    if not body.merge_into_question_id:
        raise HTTPException(status_code=400, detail="merge_into_question_id required")
    sub = await db.get(QuestionSubmission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.status = QuestionSubmissionStatus.DUPLICATE
    await _approve_submission(db, sub, user, body.merge_into_question_id)
    return {"message": "Merged"}
