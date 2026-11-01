from datetime import datetime

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequirePcell, RequireStudent, get_current_user
from app.models.company import Company, CompanyRole, CompanyYear
from app.models.content import Event, InterviewExperience, InterviewQuestion, Notification, RegistrationForm, Topic
from app.models.enums import UserRole
from app.models.resume import Resume
from app.models.skill import Skill
from app.models.user import StudentProfile, User
from app.schemas.common import PaginatedResponse

router = APIRouter(tags=["misc"])


class SkillOut(BaseModel):
    id: int
    name: str
    category: str | None

    model_config = {"from_attributes": True}


class TopicOut(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = {"from_attributes": True}


@router.get("/api/skills", response_model=list[SkillOut])
async def list_skills(db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    result = await db.execute(select(Skill).order_by(Skill.name))
    return result.scalars().all()


class SkillCreate(BaseModel):
    name: str
    category: str | None = None


@router.post("/api/skills")
async def create_skill(body: SkillCreate, db: AsyncSession = Depends(get_db), _: User = RequirePcell):
    from app.utils.text_normalize import normalize_skill_name

    skill = Skill(name=body.name, normalized_name=normalize_skill_name(body.name), category=body.category)
    db.add(skill)
    await db.flush()
    return skill


@router.get("/api/topics", response_model=list[TopicOut])
async def list_topics(db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    result = await db.execute(select(Topic).order_by(Topic.name))
    return result.scalars().all()


@router.post("/api/topics", response_model=TopicOut)
async def create_topic(body: TopicOut, db: AsyncSession = Depends(get_db), _: User = RequirePcell):
    topic = Topic(name=body.name, description=body.description)
    db.add(topic)
    await db.flush()
    return topic


@router.get("/api/search")
async def global_search(q: str = Query(min_length=1), db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    pattern = f"%{q}%"
    companies = (await db.execute(select(Company).where(Company.name.ilike(pattern)).limit(10))).scalars().all()
    questions = (
        await db.execute(select(InterviewQuestion).where(InterviewQuestion.question_text.ilike(pattern)).limit(10))
    ).scalars().all()
    experiences = (
        await db.execute(select(InterviewExperience).where(InterviewExperience.overall_experience.ilike(pattern)).limit(5))
    ).scalars().all()
    topics = (await db.execute(select(Topic).where(Topic.name.ilike(pattern)).limit(10))).scalars().all()
    skills = (await db.execute(select(Skill).where(Skill.name.ilike(pattern)).limit(10))).scalars().all()
    events = (await db.execute(select(Event).where(Event.title.ilike(pattern)).limit(10))).scalars().all()
    return {
        "companies": [{"id": c.id, "name": c.name} for c in companies],
        "questions": [{"id": qn.id, "text": qn.question_text} for qn in questions],
        "experiences": [{"id": e.id, "company_id": e.company_id} for e in experiences],
        "topics": [{"id": t.id, "name": t.name} for t in topics],
        "skills": [{"id": s.id, "name": s.name} for s in skills],
        "events": [{"id": ev.id, "title": ev.title} for ev in events],
    }


@router.get("/api/dashboard/feed")
async def dashboard_feed(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Priority feed: open registrations by deadline, then events, then recent content."""
    from app.routes.events_registrations import _effective_form_status
    from app.models.enums import EventStatus, FormStatus

    forms_result = await db.execute(
        select(RegistrationForm).where(RegistrationForm.status.in_([FormStatus.OPEN, FormStatus.CLOSED])).limit(20)
    )
    forms = forms_result.scalars().all()
    registration_cards = []
    for f in sorted(forms, key=lambda x: x.registration_deadline):
        status = _effective_form_status(f)
        registration_cards.append(
            {
                "type": "registration",
                "id": f.id,
                "title": f.title,
                "deadline": f.registration_deadline,
                "status": status.value,
            }
        )

    events = (
        await db.execute(
            select(Event).where(Event.status == EventStatus.PUBLISHED).order_by(Event.created_at.desc()).limit(10)
        )
    ).scalars().all()

    recent_questions = (
        await db.execute(select(InterviewQuestion).order_by(InterviewQuestion.created_at.desc()).limit(5))
    ).scalars().all()

    return {
        "registrations": registration_cards[:8],
        "events": [{"id": e.id, "title": e.title, "deadline": e.registration_deadline} for e in events],
        "recent_questions": [{"id": q.id, "text": q.question_text} for q in recent_questions],
        "role": user.role.value,
    }


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/api/notifications", response_model=list[NotificationOut])
async def notifications(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50)
    )
    return result.scalars().all()


@router.get("/api/notifications/unread-count")
async def unread_notification_count(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    count = await db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )
    return {"count": count or 0}


@router.post("/api/notifications/read-all")
async def mark_all_notifications_read(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await db.execute(
        update(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False)).values(is_read=True)
    )
    return {"message": "All notifications marked as read"}


@router.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    return {"message": "Marked as read"}


@router.get("/api/students")
async def list_students(
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = RequirePcell,
):
    stmt = (
        select(User, StudentProfile)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.role == UserRole.STUDENT)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(User.full_name.ilike(pattern), User.email.ilike(pattern), StudentProfile.roll_number.ilike(pattern))
        )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.order_by(User.full_name).offset((page - 1) * page_size).limit(page_size))
    rows = result.all()
    with_resume = set(
        (await db.execute(select(Resume.student_id).where(Resume.student_id.in_([u.id for u, _ in rows])))).scalars()
    )
    items = [
        {
            "has_resume": u.id in with_resume,
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "roll_number": p.roll_number if p else None,
            "branch": p.branch if p else None,
            "graduation_year": p.graduation_year if p else None,
        }
        for u, p in rows
    ]
    return PaginatedResponse(items=items, total=total or 0, page=page, page_size=page_size)
