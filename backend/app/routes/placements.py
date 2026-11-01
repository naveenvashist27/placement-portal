from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequirePcell
from app.models.company import Company, CompanyRole, CompanyYear
from app.models.enums import PlacementStatus, UserRole
from app.models.placement import PlacementRecord
from app.models.user import StudentProfile, User
from app.services.audit_service import write_audit

router = APIRouter(prefix="/api/placements", tags=["placements"])


class PlacementIn(BaseModel):
    student_id: int
    company_id: int
    company_year_id: int
    role_id: int | None = None
    package_lpa: Decimal | None = Field(default=None, ge=0, le=1000)
    placement_type: str | None = Field(default=None, max_length=64)
    placement_status: PlacementStatus = PlacementStatus.OFFERED


class StatusIn(BaseModel):
    placement_status: PlacementStatus


def _row(rec, student, profile, company, year, role):
    return {
        "id": rec.id,
        "student_id": student.id,
        "student_name": student.full_name,
        "roll_number": profile.roll_number if profile else None,
        "course": profile.course if profile else None,
        "batch": profile.batch if profile else None,
        "company_id": company.id,
        "company": company.name,
        "visit_year": year.visit_year,
        "role": role.title if role else None,
        "package_lpa": float(rec.package_lpa) if rec.package_lpa is not None else None,
        "placement_type": rec.placement_type,
        "placement_status": rec.placement_status.value,
    }


@router.get("")
async def list_placements(
    company_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = RequirePcell,
):
    stmt = (
        select(PlacementRecord, User, StudentProfile, Company, CompanyYear, CompanyRole)
        .join(User, User.id == PlacementRecord.student_id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .join(Company, Company.id == PlacementRecord.company_id)
        .join(CompanyYear, CompanyYear.id == PlacementRecord.company_year_id)
        .outerjoin(CompanyRole, CompanyRole.id == PlacementRecord.role_id)
    )
    if company_id:
        stmt = stmt.where(PlacementRecord.company_id == company_id)
    rows = (
        await db.execute(stmt.order_by(PlacementRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    ).all()
    return {"items": [_row(*r) for r in rows]}


@router.post("")
async def create_placement(body: PlacementIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    student = await db.get(User, body.student_id)
    if not student or student.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Pick a valid student")
    year = await db.get(CompanyYear, body.company_year_id)
    if not year or year.company_id != body.company_id:
        raise HTTPException(status_code=400, detail="That visit year does not belong to the selected company")
    if body.role_id:
        role = await db.get(CompanyRole, body.role_id)
        if not role or role.company_year_id != body.company_year_id:
            raise HTTPException(status_code=400, detail="That role does not belong to the selected visit year")
    same_role = (
        PlacementRecord.role_id.is_(None) if body.role_id is None else PlacementRecord.role_id == body.role_id
    )
    duplicate = await db.scalar(
        select(PlacementRecord.id).where(
            PlacementRecord.student_id == body.student_id,
            PlacementRecord.company_year_id == body.company_year_id,
            same_role,
        )
    )
    if duplicate:
        raise HTTPException(status_code=400, detail="This student already has a placement record for that company and year")
    rec = PlacementRecord(**body.model_dump())
    db.add(rec)
    await db.flush()
    await write_audit(db, user, "CREATE_PLACEMENT", "placement", rec.id, f"student={body.student_id} company={body.company_id}")
    return {"id": rec.id}


@router.put("/{placement_id}/status")
async def update_status(placement_id: int, body: StatusIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    rec = await db.get(PlacementRecord, placement_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    rec.placement_status = body.placement_status
    await write_audit(db, user, "UPDATE_PLACEMENT", "placement", rec.id, body.placement_status.value)
    return {"message": "Updated"}


@router.delete("/{placement_id}")
async def delete_placement(placement_id: int, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    rec = await db.get(PlacementRecord, placement_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(rec)
    await write_audit(db, user, "DELETE_PLACEMENT", "placement", placement_id)
    return {"message": "Deleted"}
