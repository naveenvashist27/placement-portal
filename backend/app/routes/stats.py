from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequirePcell, get_current_user
from app.models.company import Company
from app.models.enums import PlacementStatus
from app.models.placement import PlacementRecord
from app.models.stat import PortalStat
from app.models.user import User
from app.services.audit_service import write_audit

router = APIRouter(prefix="/api/stats", tags=["stats"])

COMPANIES_KEY = "companies_visited"
PLACED_KEY = "students_placed"


class StatsOverrideIn(BaseModel):
    """Send null to go back to the automatic value."""

    companies_visited: int | None = Field(default=None, ge=0, le=100000)
    students_placed: int | None = Field(default=None, ge=0, le=100000)


async def _overview(db: AsyncSession) -> dict:
    auto_companies = await db.scalar(select(func.count(Company.id)).where(Company.is_active.is_(True))) or 0
    auto_placed = (
        await db.scalar(
            select(func.count(func.distinct(PlacementRecord.student_id))).where(
                PlacementRecord.placement_status != PlacementStatus.DECLINED
            )
        )
        or 0
    )
    rows = {s.key: s.override_value for s in (await db.execute(select(PortalStat))).scalars()}
    out = {}
    for key, auto in ((COMPANIES_KEY, auto_companies), (PLACED_KEY, auto_placed)):
        override = rows.get(key)
        out[key] = override if override is not None else auto
        out[f"{key}_auto"] = auto
        out[f"{key}_override"] = override
    return out


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    data = await _overview(db)
    if user.role.value == "STUDENT":
        return {k: data[k] for k in (COMPANIES_KEY, PLACED_KEY)}
    return data


@router.put("/overview")
async def update_overview(body: StatsOverrideIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    for key, value in body.model_dump().items():
        stat = await db.get(PortalStat, key)
        if stat is None:
            stat = PortalStat(key=key)
            db.add(stat)
        stat.override_value = value
        stat.updated_by_id = user.id
    await write_audit(db, user, "UPDATE_DASHBOARD_STATS", "portal_stats", None, str(body.model_dump()))
    await db.flush()
    return await _overview(db)
