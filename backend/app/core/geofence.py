"""Campus geofence: a browser-reported location is checked here, and a short-lived signed pass is issued.

The pass (not the raw coordinates) is what every API request must carry, so the check can't be skipped from the frontend.
"""

import math
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings

PASS_HEADER = "X-Campus-Pass"
EARTH_RADIUS_M = 6_371_000
# GPS/Wi-Fi location is approximate, so we forgive the reported accuracy, but never more than this.
MAX_ACCURACY_ALLOWANCE_M = 100


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def is_on_campus(lat: float, lng: float, accuracy_m: float | None) -> tuple[bool, float]:
    s = get_settings()
    d = distance_m(lat, lng, s.campus_latitude, s.campus_longitude)
    allowance = min(max(accuracy_m or 0, 0), MAX_ACCURACY_ALLOWANCE_M)
    return d <= s.campus_radius_m + allowance, d


def create_pass() -> tuple[str, int]:
    s = get_settings()
    ttl = s.campus_pass_minutes * 60
    exp = datetime.now(timezone.utc) + timedelta(seconds=ttl)
    return jwt.encode({"typ": "campus", "exp": exp}, s.secret_key, algorithm=s.jwt_algorithm), ttl


def pass_is_valid(token: str | None) -> bool:
    if not token:
        return False
    s = get_settings()
    try:
        return jwt.decode(token, s.secret_key, algorithms=[s.jwt_algorithm]).get("typ") == "campus"
    except JWTError:
        return False
