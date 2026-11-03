from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine
from app.core.geofence import PASS_HEADER, pass_is_valid
from app.exceptions.handlers import register_exception_handlers
from app.routes.analytics import router as analytics_router
from app.routes.campus import router as campus_router
from app.routes.auth import router as auth_router
from app.routes.companies import roles_router, router as companies_router, years_router
from app.routes.events_registrations import events_router, forms_router
from app.routes.experiences import router as experiences_router
from app.routes.misc import router as misc_router
from app.routes.placements import router as placements_router
from app.routes.profile import router as profile_router
from app.routes.questions import router as questions_router, submissions_router
from app.routes.resume import router as resume_router
from app.routes.stats import router as stats_router
from app.routes.student_requests import router as student_requests_router
from app.routes.tpo import router as tpo_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.use_local_storage:
        Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(title="Placement Intelligence Portal API", version="1.0.0", lifespan=lifespan)
settings = get_settings()

@app.middleware("http")
async def require_campus_pass(request: Request, call_next):
    path = request.url.path
    guarded = path.startswith("/api/") and not path.startswith("/api/campus/") and request.method != "OPTIONS"
    if guarded and settings.geofence_enabled and not pass_is_valid(request.headers.get(PASS_HEADER)):
        return JSONResponse(
            status_code=403,
            content={"detail": "This portal is only available on the IIPS campus.", "code": "CAMPUS_REQUIRED"},
        )
    return await call_next(request)


# Added after the geofence middleware so CORS wraps it and the 403 above still carries CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Uploads are deliberately NOT mounted as public static files; they are served by authenticated endpoints.
if settings.use_local_storage:
    Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)

app.include_router(campus_router)
app.include_router(auth_router)
app.include_router(companies_router)
app.include_router(years_router)
app.include_router(roles_router)
app.include_router(questions_router)
app.include_router(submissions_router)
app.include_router(experiences_router)
app.include_router(events_router)
app.include_router(forms_router)
app.include_router(resume_router)
app.include_router(analytics_router)
app.include_router(placements_router)
app.include_router(stats_router)
app.include_router(tpo_router)
app.include_router(student_requests_router)
app.include_router(profile_router)
app.include_router(misc_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
