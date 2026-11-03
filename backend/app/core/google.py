import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


async def verify_google_credential(credential: str) -> dict:
    """Validate a Google ID token and return its claims (sub, email, name, picture).

    Google checks the signature and expiry; we check audience (our client ID), issuer and verified email.
    """
    client_id = get_settings().google_client_id
    if not client_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google sign-in is not configured on the server")
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(TOKENINFO_URL, params={"id_token": credential})
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Could not reach Google to verify sign-in") from exc
    if resp.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google sign-in")
    claims = resp.json()
    if claims.get("aud") != client_id or claims.get("iss") not in ISSUERS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google sign-in")
    if str(claims.get("email_verified")).lower() != "true" or not claims.get("email"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Google email is not verified")
    return claims
