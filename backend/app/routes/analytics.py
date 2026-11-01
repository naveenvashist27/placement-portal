from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequirePcell
from app.models.company import Company, CompanyYear
from app.models.placement import PlacementRecord
from app.models.user import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/placements")
async def placement_analytics(db: AsyncSession = Depends(get_db), _: User = RequirePcell):
    total = await db.scalar(select(func.count()).select_from(PlacementRecord)) or 0
    avg_pkg = await db.scalar(select(func.avg(PlacementRecord.package_lpa)))
    max_pkg = await db.scalar(select(func.max(PlacementRecord.package_lpa)))
    by_company = await db.execute(
        select(Company.name, func.count(PlacementRecord.id))
        .join(Company, Company.id == PlacementRecord.company_id)
        .group_by(Company.name)
    )
    by_year = await db.execute(
        select(CompanyYear.visit_year, func.count(PlacementRecord.id))
        .join(CompanyYear, CompanyYear.id == PlacementRecord.company_year_id)
        .group_by(CompanyYear.visit_year)
        .order_by(CompanyYear.visit_year)
    )
    return {
        "total_placed": total,
        "average_package_lpa": float(avg_pkg or 0),
        "highest_package_lpa": float(max_pkg or 0),
        "company_wise": [{"company": r[0], "count": r[1]} for r in by_company.all()],
        "year_wise": [{"year": r[0], "count": r[1]} for r in by_year.all()],
    }


@router.get("/companies")
async def company_analytics(db: AsyncSession = Depends(get_db), _: User = RequirePcell):
    total_companies = await db.scalar(select(func.count()).select_from(Company).where(Company.is_active.is_(True))) or 0
    by_year = await db.execute(
        select(CompanyYear.visit_year, func.count(CompanyYear.id)).group_by(CompanyYear.visit_year).order_by(CompanyYear.visit_year)
    )
    return {
        "total_companies": total_companies,
        "companies_by_year": [{"year": r[0], "count": r[1]} for r in by_year.all()],
    }


@router.get("/years")
async def year_analytics(db: AsyncSession = Depends(get_db), _: User = RequirePcell):
    result = await db.execute(select(CompanyYear.visit_year, func.count(CompanyYear.id)).group_by(CompanyYear.visit_year))
    return {"years": [{"year": r[0], "visits": r[1]} for r in result.all()]}
