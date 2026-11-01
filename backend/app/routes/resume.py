from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.dependencies.auth import RequirePcell, get_current_user
from app.models.enums import UserRole
from app.models.resume import Resume, ResumeSkill
from app.models.skill import Skill
from app.models.user import User
from app.utils.resume_extractor import extract_skills_from_text, extract_text_from_pdf_bytes
from app.utils.storage import StorageService
from app.utils.text_normalize import normalize_skill_name

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


class ResumeOut(BaseModel):
    id: int
    skills: list[str]

    model_config = {"from_attributes": True}


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Students only")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF only")
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    storage = StorageService()
    path = await storage.upload("resumes", file.filename or "resume.pdf", data, "application/pdf")
    text = extract_text_from_pdf_bytes(data)

    existing = await db.execute(select(Resume).where(Resume.student_id == user.id))
    resume = existing.scalar_one_or_none()
    if resume:
        resume.file_path = path
        resume.extracted_text = text
        await db.execute(delete(ResumeSkill).where(ResumeSkill.resume_id == resume.id))
    else:
        resume = Resume(student_id=user.id, file_path=path, extracted_text=text)
        db.add(resume)
        await db.flush()

    skill_names = extract_skills_from_text(text or "")
    for name in skill_names:
        norm = normalize_skill_name(name)
        result = await db.execute(select(Skill).where(Skill.normalized_name == norm))
        skill = result.scalar_one_or_none()
        if not skill:
            skill = Skill(name=name, normalized_name=norm)
            db.add(skill)
            await db.flush()
        db.add(ResumeSkill(resume_id=resume.id, skill_id=skill.id))

    return {"message": "Resume uploaded", "resume_id": resume.id}


@router.get("/me")
async def my_resume(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Resume).where(Resume.student_id == user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume")
    skills_result = await db.execute(
        select(Skill.name).join(ResumeSkill, ResumeSkill.skill_id == Skill.id).where(ResumeSkill.resume_id == resume.id)
    )
    skills = [r[0] for r in skills_result.all()]
    return ResumeOut(id=resume.id, skills=skills)


def _serve(resume: Resume):
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_role_key:
        from supabase import create_client

        client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        signed = client.storage.from_(settings.supabase_storage_bucket).create_signed_url(resume.file_path, 120)
        return RedirectResponse(signed["signedURL"])

    root = Path(settings.local_storage_path).resolve()
    path = Path(resume.file_path).resolve()
    if root not in path.parents or not path.is_file():  # never serve anything outside the uploads folder
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="application/pdf", filename="resume.pdf", content_disposition_type="inline")


@router.get("/{resume_id}/file")
async def download_resume(resume_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """The owner and PCELL / TPO can open a resume. Everyone else gets a 404, like a missing file."""
    resume = await db.get(Resume, resume_id)
    if not resume or (user.role == UserRole.STUDENT and resume.student_id != user.id):
        raise HTTPException(status_code=404, detail="Not found")
    return _serve(resume)


@router.get("/by-student/{student_id}/file")
async def download_student_resume(student_id: int, db: AsyncSession = Depends(get_db), _: User = RequirePcell):
    """PCELL / TPO open a student's resume from the Students list or an experience submission."""
    resume = (await db.execute(select(Resume).where(Resume.student_id == student_id))).scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="This student has not uploaded a resume")
    return _serve(resume)


@router.delete("/{resume_id}")
async def delete_resume(resume_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    resume = await db.get(Resume, resume_id)
    if not resume or resume.student_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(resume)
    return {"message": "Deleted"}


@router.post("/{resume_id}/extract-skills")
async def reextract(resume_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    resume = await db.get(Resume, resume_id)
    if not resume or resume.student_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    if not resume.extracted_text:
        raise HTTPException(status_code=400, detail="No extracted text")
    await db.execute(delete(ResumeSkill).where(ResumeSkill.resume_id == resume.id))
    for name in extract_skills_from_text(resume.extracted_text):
        norm = normalize_skill_name(name)
        result = await db.execute(select(Skill).where(Skill.normalized_name == norm))
        skill = result.scalar_one_or_none()
        if not skill:
            skill = Skill(name=name, normalized_name=norm)
            db.add(skill)
            await db.flush()
        db.add(ResumeSkill(resume_id=resume.id, skill_id=skill.id))
    return {"message": "Skills re-extracted"}
