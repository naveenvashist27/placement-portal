from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequireTpo
from app.models.audit import AuditLog
from app.models.enums import UserRole, UserStatus
from app.models.user import ApprovalRequest, User
from app.schemas.common import PaginatedResponse
from app.services.audit_service import write_audit

router = APIRouter(prefix="/api/tpo", tags=["tpo"])


class PcellMemberOut(BaseModel):
    id: int
    email: str
    full_name: str
    status: UserStatus

    model_config = {"from_attributes": True}


@router.get("/pcell-members", response_model=PaginatedResponse[PcellMemberOut])
async def list_pcell_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = RequireTpo,
):
    stmt = select(User).where(User.role == UserRole.PCELL_MEMBER)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(items=result.scalars().all(), total=total or 0, page=page, page_size=page_size)


@router.post("/pcell-members/{user_id}/approve")
async def approve_pcell(user_id: int, db: AsyncSession = Depends(get_db), actor: User = RequireTpo):
    user = await db.get(User, user_id)
    if not user or user.role != UserRole.PCELL_MEMBER:
        raise HTTPException(status_code=404, detail="PCELL member not found")
    user.status = UserStatus.ACTIVE
    req = await db.execute(select(ApprovalRequest).where(ApprovalRequest.user_id == user_id))
    for r in req.scalars():
        r.status = UserStatus.ACTIVE
        r.reviewed_by_id = actor.id
    await write_audit(db, actor, "APPROVE_PCELL_MEMBER", "user", user.id)
    return {"message": "Approved"}


@router.post("/pcell-members/{user_id}/reject")
async def reject_pcell(user_id: int, db: AsyncSession = Depends(get_db), actor: User = RequireTpo):
    user = await db.get(User, user_id)
    if not user or user.role != UserRole.PCELL_MEMBER:
        raise HTTPException(status_code=404, detail="PCELL member not found")
    user.status = UserStatus.REJECTED
    await write_audit(db, actor, "REJECT_PCELL_MEMBER", "user", user.id)
    return {"message": "Rejected"}


@router.post("/pcell-members/{user_id}/suspend")
async def suspend_pcell(user_id: int, db: AsyncSession = Depends(get_db), actor: User = RequireTpo):
    user = await db.get(User, user_id)
    if not user or user.role != UserRole.PCELL_MEMBER:
        raise HTTPException(status_code=404, detail="PCELL member not found")
    user.status = UserStatus.SUSPENDED
    await write_audit(db, actor, "SUSPEND_PCELL_MEMBER", "user", user.id)
    return {"message": "Suspended"}


@router.post("/pcell-members/{user_id}/reactivate")
async def reactivate_pcell(user_id: int, db: AsyncSession = Depends(get_db), actor: User = RequireTpo):
    user = await db.get(User, user_id)
    if not user or user.role != UserRole.PCELL_MEMBER:
        raise HTTPException(status_code=404, detail="PCELL member not found")
    user.status = UserStatus.ACTIVE
    await write_audit(db, actor, "REACTIVATE_PCELL_MEMBER", "user", user.id)
    return {"message": "Reactivated"}


@router.get("/audit-logs")
async def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = RequireTpo,
):
    stmt = select(AuditLog)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    logs = [
        {
            "id": l.id,
            "actor_id": l.actor_id,
            "actor_role": l.actor_role.value,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "details": l.details,
            "created_at": l.created_at,
        }
        for l in result.scalars().all()
    ]
    return PaginatedResponse(items=logs, total=total or 0, page=page, page_size=page_size)
