from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str
    industry: str | None = None
    website: str | None = None
    description: str | None = None
    hiring_info: str | None = None


class CompanyUpdate(CompanyCreate):
    is_active: bool | None = None


class CompanyOut(BaseModel):
    id: int
    name: str
    industry: str | None
    website: str | None
    description: str | None
    hiring_info: str | None
    logo_path: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class CompanyYearCreate(BaseModel):
    visit_year: int = Field(ge=2000, le=2100)
    notes: str | None = None


class CompanyYearOut(BaseModel):
    id: int
    company_id: int
    visit_year: int
    notes: str | None

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    title: str
    eligibility: str | None = None
    selection_info: str | None = None
    skill_ids: list[int] = []


class RoleOut(BaseModel):
    id: int
    company_year_id: int
    title: str
    eligibility: str | None
    selection_info: str | None

    model_config = {"from_attributes": True}
