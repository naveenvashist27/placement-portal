from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import InterviewQuestion, QuestionSubmission
from app.models.enums import QuestionSubmissionStatus
from app.utils.text_normalize import normalize_question_text

SIMILARITY_THRESHOLD = 88


async def find_similar_canonical(
    db: AsyncSession,
    normalized: str,
    company_id: int | None,
    company_year_id: int | None,
    role_id: int | None,
) -> InterviewQuestion | None:
    stmt = select(InterviewQuestion).where(InterviewQuestion.is_public.is_(True))
    if company_id:
        stmt = stmt.where(InterviewQuestion.company_id == company_id)
    if company_year_id:
        stmt = stmt.where(InterviewQuestion.company_year_id == company_year_id)
    if role_id:
        stmt = stmt.where(InterviewQuestion.role_id == role_id)
    result = await db.execute(stmt)
    for q in result.scalars().all():
        score = fuzz.token_sort_ratio(normalized, q.normalized_text)
        if score >= SIMILARITY_THRESHOLD:
            return q
    return None


async def create_submission(
    db: AsyncSession,
    *,
    student_id: int,
    text: str,
    company_id: int | None,
    company_year_id: int | None,
    role_id: int | None,
    round_label: str | None,
    topic_id: int | None,
    difficulty,
) -> QuestionSubmission:
    normalized = normalize_question_text(text)
    duplicate = await find_similar_canonical(db, normalized, company_id, company_year_id, role_id)

    submission = QuestionSubmission(
        student_id=student_id,
        submitted_text=text.strip(),
        normalized_text=normalized,
        company_id=company_id,
        company_year_id=company_year_id,
        role_id=role_id,
        round_label=round_label,
        topic_id=topic_id,
        difficulty=difficulty,
        status=QuestionSubmissionStatus.DUPLICATE if duplicate else QuestionSubmissionStatus.PENDING,
        canonical_question_id=duplicate.id if duplicate else None,
    )
    db.add(submission)
    await db.flush()
    return submission
