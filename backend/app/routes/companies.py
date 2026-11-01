from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies.auth import RequirePcell, RequireStudent, get_current_user, require_roles
from app.models.company import Company, CompanyRole, CompanyYear, RoleSkill
from app.models.enums import UserRole
from app.models.skill import Skill
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate, CompanyYearCreate, CompanyYearOut, RoleCreate, RoleOut
from app.services.audit_service import write_audit
from app.utils.storage import StorageService

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=PaginatedResponse[CompanyOut])
async def list_companies(
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = RequireStudent,
):
    stmt = select(Company).where(Company.is_active.is_(True))
    if q:
        stmt = stmt.where(or_(Company.name.ilike(f"%{q}%"), Company.industry.ilike(f"%{q}%")))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(stmt.order_by(Company.name).offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()
    return PaginatedResponse(items=items, total=total or 0, page=page, page_size=page_size)


@router.post("", response_model=CompanyOut)
async def create_company(body: CompanyCreate, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    company = Company(**body.model_dump())
    db.add(company)
    await db.flush()
    await write_audit(db, user, "CREATE_COMPANY", "company", company.id)
    return company


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    company = await db.get(Company, company_id)
    if not company or not company.is_active:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: int, body: CompanyUpdate, db: AsyncSession = Depends(get_db), user: User = RequirePcell
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    await write_audit(db, user, "UPDATE_COMPANY", "company", company.id)
    return company


@router.delete("/{company_id}")
async def deactivate_company(company_id: int, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.is_active = False
    await write_audit(db, user, "DEACTIVATE_COMPANY", "company", company.id)
    return {"message": "Company deactivated"}


@router.post("/{company_id}/logo", response_model=CompanyOut)
async def upload_logo(
    company_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = RequirePcell,
):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Invalid image type")
    data = await file.read()
    storage = StorageService()
    path = await storage.upload("logos", file.filename or "logo.png", data, file.content_type)
    company.logo_path = path
    return company


@router.get("/{company_id}/years", response_model=list[CompanyYearOut])
async def list_years(company_id: int, db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    result = await db.execute(
        select(CompanyYear).where(CompanyYear.company_id == company_id).order_by(CompanyYear.visit_year.desc())
    )
    return result.scalars().all()


@router.post("/{company_id}/years", response_model=CompanyYearOut)
async def add_year(
    company_id: int, body: CompanyYearCreate, db: AsyncSession = Depends(get_db), user: User = RequirePcell
):
    cy = CompanyYear(company_id=company_id, **body.model_dump())
    db.add(cy)
    await db.flush()
    await write_audit(db, user, "CREATE_COMPANY_YEAR", "company_year", cy.id)
    return cy


years_router = APIRouter(prefix="/api/company-years", tags=["company-years"])


@years_router.put("/{year_id}", response_model=CompanyYearOut)
async def update_year(year_id: int, body: CompanyYearCreate, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    cy = await db.get(CompanyYear, year_id)
    if not cy:
        raise HTTPException(status_code=404, detail="Year not found")
    cy.visit_year = body.visit_year
    cy.notes = body.notes
    return cy


@years_router.delete("/{year_id}")
async def delete_year(year_id: int, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    cy = await db.get(CompanyYear, year_id)
    if not cy:
        raise HTTPException(status_code=404, detail="Year not found")
    await db.delete(cy)
    return {"message": "Deleted"}


@years_router.get("/{year_id}/roles", response_model=list[RoleOut])
async def list_roles(year_id: int, db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    result = await db.execute(select(CompanyRole).where(CompanyRole.company_year_id == year_id))
    return result.scalars().all()


@years_router.post("/{year_id}/roles", response_model=RoleOut)
async def create_role(
    year_id: int, body: RoleCreate, db: AsyncSession = Depends(get_db), user: User = RequirePcell
):
    role = CompanyRole(company_year_id=year_id, title=body.title, eligibility=body.eligibility, selection_info=body.selection_info)
    db.add(role)
    await db.flush()
    for sid in body.skill_ids:
        db.add(RoleSkill(role_id=role.id, skill_id=sid))
    return role


roles_router = APIRouter(prefix="/api/roles", tags=["roles"])


@roles_router.put("/{role_id}", response_model=RoleOut)
async def update_role(role_id: int, body: RoleCreate, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    role = await db.get(CompanyRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role.title = body.title
    role.eligibility = body.eligibility
    role.selection_info = body.selection_info
    await db.execute(select(RoleSkill).where(RoleSkill.role_id == role_id))
    # simplistic replace
    existing = await db.execute(select(RoleSkill).where(RoleSkill.role_id == role_id))
    for rs in existing.scalars():
        await db.delete(rs)
    for sid in body.skill_ids:
        db.add(RoleSkill(role_id=role.id, skill_id=sid))
    return role


@roles_router.delete("/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    role = await db.get(CompanyRole, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    await db.delete(role)
    return {"message": "Deleted"}


@router.get("/{company_id}/detail")
async def company_detail(company_id: int, db: AsyncSession = Depends(get_db), _: User = RequireStudent):
    result = await db.execute(
        select(Company)
        .where(Company.id == company_id)
        .options(selectinload(Company.years).selectinload(CompanyYear.roles))
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
