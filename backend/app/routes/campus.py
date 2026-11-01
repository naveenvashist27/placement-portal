from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.geofence import create_pass, is_on_campus

router = APIRouter(prefix="/api/campus", tags=["campus"])


class LocationIn(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float | None = Field(default=None, ge=0)


@router.get("/status")
async def status():
    s = get_settings()
    return {"enabled": s.geofence_enabled, "radius_m": s.campus_radius_m}


@router.post("/check")
async def check(body: LocationIn):
    s = get_settings()
    if not s.geofence_enabled:
        return {"allowed": True, "pass_token": None, "expires_in": 0, "distance_m": None}
    allowed, distance = is_on_campus(body.latitude, body.longitude, body.accuracy)
    if not allowed:
        return {"allowed": False, "pass_token": None, "expires_in": 0, "distance_m": round(distance)}
    token, ttl = create_pass()
    return {"allowed": True, "pass_token": token, "expires_in": ttl, "distance_m": round(distance)}
