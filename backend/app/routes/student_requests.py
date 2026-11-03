from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequirePcell
from app.models.enums import UserRole, UserStatus
from app.models.user import ApprovalRequest, StudentProfile, User
from app.schemas.common import PaginatedResponse
from app.services.audit_service import write_audit

router = APIRouter(prefix="/api/admin/student-requests", tags=["student-requests"])


class StudentRequestOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    roll_number: str | None
    course: str | None
    batch: str | None
    phone: str | None
    status: UserStatus
    review_note: str | None
    created_at: datetime


class ReviewIn(BaseModel):
    note: str | None = None


def _out(req: ApprovalRequest, user: User, profile: StudentProfile | None) -> StudentRequestOut:
    return StudentRequestOut(
        id=req.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        roll_number=profile.roll_number if profile else None,
        course=profile.course if profile else None,
        batch=profile.batch if profile else None,
        phone=profile.phone if profile else None,
        status=req.status,
        review_note=req.review_note,
        created_at=req.created_at,
    )


@router.get("", response_model=PaginatedResponse[StudentRequestOut])
async def list_requests(
    status: UserStatus = UserStatus.PENDING,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = RequirePcell,
):
    base = (
        select(ApprovalRequest, User, StudentProfile)
        .join(User, User.id == ApprovalRequest.user_id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(ApprovalRequest.requested_role == UserRole.STUDENT, ApprovalRequest.status == status)
    )
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    rows = await db.execute(base.order_by(ApprovalRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [_out(r, u, p) for r, u, p in rows.all()]
    return PaginatedResponse(items=items, total=total or 0, page=page, page_size=page_size)


async def _review(request_id: int, new_status: UserStatus, note: str | None, action: str, db: AsyncSession, actor: User):
    req = await db.get(ApprovalRequest, request_id)
    if not req or req.requested_role != UserRole.STUDENT:
        raise HTTPException(status_code=404, detail="Request not found")
    user = await db.get(User, req.user_id)
    req.status = new_status
    req.reviewed_by_id = actor.id
    req.review_note = note
    user.status = new_status
    await write_audit(db, actor, action, "user", user.id, details=note)
    return {"message": "Updated"}


@router.post("/{request_id}/approve")
async def approve(request_id: int, body: ReviewIn | None = None, db: AsyncSession = Depends(get_db), actor: User = RequirePcell):
    return await _review(request_id, UserStatus.ACTIVE, body.note if body else None, "APPROVE_STUDENT", db, actor)


@router.post("/{request_id}/reject")
async def reject(request_id: int, body: ReviewIn | None = None, db: AsyncSession = Depends(get_db), actor: User = RequirePcell):
    return await _review(request_id, UserStatus.REJECTED, body.note if body else None, "REJECT_STUDENT", db, actor)
