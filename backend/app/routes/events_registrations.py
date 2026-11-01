import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import RequirePcell, RequireStudent, get_current_user
from app.models.content import Event, Registration, RegistrationForm
from app.models.enums import EventStatus, FormStatus, UserRole
from app.models.user import StudentProfile, User
from app.routes.profile import STUDENT_FIELDS, ProfileUpdate
from app.schemas.common import PaginatedResponse
from app.services import eligibility
from app.services.audit_service import write_audit

events_router = APIRouter(prefix="/api/events", tags=["events"])
forms_router = APIRouter(prefix="/api/registrations/forms", tags=["registrations"])


class EventIn(BaseModel):
    title: str
    description: str
    company_id: int | None = None
    registration_deadline: datetime | None = None
    event_info: str | None = None
    registration_form_id: int | None = None
    status: EventStatus = EventStatus.DRAFT


class EventOut(BaseModel):
    id: int
    title: str
    description: str
    company_id: int | None
    registration_deadline: datetime | None
    status: EventStatus

    model_config = {"from_attributes": True}


FIELD_TYPES = {"text", "textarea", "number", "select", "yesno", "url", "date"}
# Profile keys a form field may be linked to (email is shown but never written back).
LINKABLE_PROFILE_KEYS = set(STUDENT_FIELDS) - {"bio"} | {"full_name", "email"}


def _validate_form_fields(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        fields = json.loads(raw)
    except ValueError:
        raise ValueError("form_fields_json must be valid JSON")
    if not isinstance(fields, list):
        raise ValueError("form_fields_json must be a list of fields")
    seen = set()
    for f in fields:
        if not isinstance(f, dict) or not str(f.get("key", "")).strip() or not str(f.get("label", "")).strip():
            raise ValueError("Every field needs a key and a label")
        if f["key"] in seen:
            raise ValueError(f"Duplicate field: {f['key']}")
        seen.add(f["key"])
        if f.get("type") not in FIELD_TYPES:
            raise ValueError(f"Unknown field type: {f.get('type')}")
        if f["type"] == "select" and not f.get("options"):
            raise ValueError(f"'{f['label']}' needs at least one option")
        if f.get("profile_key") and f["profile_key"] not in LINKABLE_PROFILE_KEYS:
            raise ValueError(f"Unknown profile field: {f['profile_key']}")
    return json.dumps(fields)


class FormIn(BaseModel):
    title: str
    description: str
    company_id: int | None = None
    role_id: int | None = None
    registration_start: datetime | None = None
    registration_deadline: datetime
    form_fields_json: str | None = None
    eligibility_json: str | None = None
    external_link: str | None = None
    status: FormStatus = FormStatus.DRAFT

    @field_validator("form_fields_json")
    @classmethod
    def _check_fields(cls, v):
        return _validate_form_fields(v)

    @field_validator("eligibility_json")
    @classmethod
    def _check_eligibility(cls, v):
        return eligibility.validate_rules(v)


class FormOut(BaseModel):
    id: int
    title: str
    description: str
    company_id: int | None
    role_id: int | None
    registration_deadline: datetime
    status: FormStatus
    external_link: str | None
    form_fields_json: str | None = None
    eligibility_json: str | None = None
    eligibility_summary: list[str] = []
    ineligible_reasons: list[str] = []  # why the logged-in student can't register (students only)

    model_config = {"from_attributes": True}


ELIGIBILITY_KEYS = ("cgpa", "tenth_percentage", "twelfth_percentage", "has_atkt", "course", "batch", "graduation_year")


def _eligibility_values(profile: StudentProfile | None) -> dict:
    return {k: getattr(profile, k, None) for k in ELIGIBILITY_KEYS}


def _effective_form_status(form: RegistrationForm) -> FormStatus:
    now = datetime.now(timezone.utc)
    deadline = form.registration_deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if form.status == FormStatus.OPEN and now > deadline:
        return FormStatus.CLOSED
    return form.status


@events_router.get("", response_model=PaginatedResponse[EventOut])
async def list_events(
    status: EventStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = RequireStudent,
):
    stmt = select(Event)
    if user.role == UserRole.STUDENT:
        stmt = stmt.where(Event.status == EventStatus.PUBLISHED)
    elif status:
        stmt = stmt.where(Event.status == status)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(
        stmt.order_by(Event.registration_deadline.asc().nulls_last(), Event.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return PaginatedResponse(items=result.scalars().all(), total=total or 0, page=page, page_size=page_size)


@events_router.post("", response_model=EventOut)
async def create_event(body: EventIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    ev = Event(created_by_id=user.id, **body.model_dump())
    db.add(ev)
    await db.flush()
    await write_audit(db, user, "CREATE_EVENT", "event", ev.id)
    return ev


@events_router.put("/{event_id}", response_model=EventOut)
async def update_event(event_id: int, body: EventIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    for k, v in body.model_dump().items():
        setattr(ev, k, v)
    return ev


@events_router.delete("/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(ev)
    return {"message": "Deleted"}


@forms_router.get("", response_model=PaginatedResponse[FormOut])
async def list_forms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = RequireStudent,
):
    stmt = select(RegistrationForm)
    if user.role == UserRole.STUDENT:
        stmt = stmt.where(RegistrationForm.status.in_([FormStatus.OPEN, FormStatus.CLOSED]))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(
        stmt.order_by(RegistrationForm.registration_deadline.asc()).offset((page - 1) * page_size).limit(page_size)
    )
    forms = result.scalars().all()
    profile = None
    if user.role == UserRole.STUDENT:
        profile = (await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))).scalar_one_or_none()
    for f in forms:
        f.status = _effective_form_status(f)
        f.eligibility_summary = eligibility.describe(json.loads(f.eligibility_json)) if f.eligibility_json else []
        f.ineligible_reasons = eligibility.check(f.eligibility_json, _eligibility_values(profile)) if user.role == UserRole.STUDENT else []
    return PaginatedResponse(items=forms, total=total or 0, page=page, page_size=page_size)


@forms_router.post("", response_model=FormOut)
async def create_form(body: FormIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    form = RegistrationForm(created_by_id=user.id, **body.model_dump())
    db.add(form)
    await db.flush()
    return form


@forms_router.put("/{form_id}", response_model=FormOut)
async def update_form(form_id: int, body: FormIn, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    form = await db.get(RegistrationForm, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(form, k, v)
    return form


@forms_router.delete("/{form_id}")
async def delete_form(form_id: int, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    form = await db.get(RegistrationForm, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    await db.delete(form)
    return {"message": "Deleted"}


class RegisterIn(BaseModel):
    responses: dict[str, Any] = {}


def _blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


@forms_router.get("/mine")
async def my_registered_form_ids(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Registration.form_id).where(Registration.student_id == user.id))
    return {"form_ids": list(result.scalars().all())}


@forms_router.post("/{form_id}/register")
async def register_form(form_id: int, body: RegisterIn | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students register")
    form = await db.get(RegistrationForm, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    status = _effective_form_status(form)
    if status != FormStatus.OPEN:
        raise HTTPException(status_code=400, detail="Registration is closed")
    existing = await db.execute(
        select(Registration).where(Registration.form_id == form_id, Registration.student_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already registered")

    submitted = body.responses if body else {}
    fields = json.loads(form.form_fields_json) if form.form_fields_json else []
    answers: dict[str, Any] = {}
    to_profile: dict[str, Any] = {}
    for f in fields:
        value = submitted.get(f["key"])
        if _blank(value):
            if f.get("required"):
                raise HTTPException(status_code=400, detail=f"'{f['label']}' is required")
            continue
        if f["type"] == "select" and value not in f.get("options", []):
            raise HTTPException(status_code=400, detail=f"Invalid choice for '{f['label']}'")
        answers[f["key"]] = value
        if f.get("profile_key") and f["profile_key"] != "email":
            to_profile[f["profile_key"]] = value

    profile = (await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))).scalar_one_or_none()
    corrected: dict = {}
    if to_profile:
        try:
            corrected = ProfileUpdate(**to_profile).model_dump(exclude_unset=True)
        except ValidationError as e:
            err = e.errors()[0]
            raise HTTPException(status_code=400, detail=f"Invalid value for {err['loc'][0]}: {err['msg']}")
    # Judge eligibility on what the student confirmed in this form, falling back to their saved profile.
    reasons = eligibility.check(form.eligibility_json, {**_eligibility_values(profile), **corrected})
    if reasons:
        raise HTTPException(status_code=400, detail="You are not eligible: " + "; ".join(reasons))

    # Values the student confirmed or corrected here also update their profile, so they never retype them.
    if corrected:
        if "full_name" in corrected:
            user.full_name = corrected.pop("full_name")
        if profile is None:
            profile = StudentProfile(user_id=user.id)
            db.add(profile)
        for key, value in corrected.items():
            setattr(profile, key, value)

    db.add(Registration(form_id=form_id, student_id=user.id, responses_json=json.dumps(answers)))
    return {"message": "Registered successfully"}


@forms_router.get("/{form_id}/registrations")
async def list_form_registrations(
    form_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = RequirePcell,
):
    stmt = (
        select(Registration, User)
        .join(User, User.id == Registration.student_id)
        .where(Registration.form_id == form_id)
    )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(
        stmt.order_by(Registration.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [
        {
            "id": reg.id,
            "student_id": u.id,
            "student_name": u.full_name,
            "student_email": u.email,
            "responses_json": reg.responses_json,
            "created_at": reg.created_at,
        }
        for reg, u in result.all()
    ]
    return PaginatedResponse(items=items, total=total or 0, page=page, page_size=page_size)


def _csv_safe(value: Any) -> str:
    """Stop spreadsheet apps from running a cell as a formula (=, +, -, @ at the start)."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


@forms_router.get("/{form_id}/export.csv")
async def export_form_registrations(form_id: int, db: AsyncSession = Depends(get_db), user: User = RequirePcell):
    form = await db.get(RegistrationForm, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    fields = json.loads(form.form_fields_json) if form.form_fields_json else []
    rows = (
        await db.execute(
            select(Registration, User, StudentProfile)
            .join(User, User.id == Registration.student_id)
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .where(Registration.form_id == form_id)
            .order_by(Registration.created_at)
        )
    ).all()

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        ["Name", "Email", "Roll no.", "Course", "Branch", "Batch", "Passing year", "Phone"]
        + [f["label"] for f in fields]
        + ["Registered at"]
    )
    for reg, student, profile in rows:
        answers = json.loads(reg.responses_json) if reg.responses_json and reg.responses_json.startswith("{") else {}
        base = (
            student.full_name,
            student.email,
            profile.roll_number if profile else None,
            profile.course if profile else None,
            profile.branch if profile else None,
            profile.batch if profile else None,
            profile.graduation_year if profile else None,
            profile.phone if profile else None,
        )
        writer.writerow(
            [_csv_safe(v) for v in base]
            + [_csv_safe(answers.get(f["key"])) for f in fields]
            + [reg.created_at.strftime("%Y-%m-%d %H:%M")]
        )
    await write_audit(db, user, "EXPORT_REGISTRATIONS", "registration_form", form_id)
    filename = "".join(c if c.isalnum() else "_" for c in form.title)[:40] or "registrations"
    # utf-8-sig so Excel opens Hindi / accented names correctly
    return Response(
        content=out.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
