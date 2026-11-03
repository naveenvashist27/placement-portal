import pytest

from app.routes import auth as auth_routes

DETAILS = {"roll_number": "CS2023042", "course": "MBA Tech", "batch": "2023-2028", "phone": "9999999999"}


@pytest.fixture
def google(monkeypatch):
    """Make 'Google' accept tokens of the form 'tok:<email>'."""

    async def fake_verify(credential: str) -> dict:
        email = credential.split(":", 1)[1]
        return {"sub": f"sub-{email}", "email": email, "name": "New Student", "picture": None}

    monkeypatch.setattr(auth_routes, "verify_google_credential", fake_verify)


def google_login(client, email, details=None):
    return client.post("/api/auth/google", json={"credential": f"tok:{email}", "details": details})


def test_first_login_needs_details_then_creates_pending_request(client, google):
    r = google_login(client, "fresh@gmail.com")
    assert r.json()["status"] == "DETAILS_REQUIRED"  # nothing created yet

    r = google_login(client, "fresh@gmail.com", DETAILS)
    assert r.json()["status"] == "PENDING" and r.json()["access_token"] is None

    # Still pending on the next attempt, no token.
    assert google_login(client, "fresh@gmail.com").json()["status"] == "PENDING"


def test_pcell_approves_then_student_gets_in(client, google, pcell):
    google_login(client, "approve@gmail.com", DETAILS)
    pending = client.get("/api/admin/student-requests", headers=pcell).json()["items"]
    req = next(p for p in pending if p["email"] == "approve@gmail.com")
    assert req["roll_number"] == "CS2023042"

    assert client.post(f"/api/admin/student-requests/{req['id']}/approve", headers=pcell).status_code == 200

    r = google_login(client, "approve@gmail.com").json()
    assert r["status"] == "OK" and r["role"] == "STUDENT"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {r['access_token']}"})
    assert me.json()["email"] == "approve@gmail.com"


def test_rejected_student_is_blocked(client, google, pcell):
    google_login(client, "reject@gmail.com", DETAILS)
    req = next(p for p in client.get("/api/admin/student-requests", headers=pcell).json()["items"] if p["email"] == "reject@gmail.com")
    client.post(f"/api/admin/student-requests/{req['id']}/reject", headers=pcell, json={"note": "1st year"})
    assert google_login(client, "reject@gmail.com").status_code == 403


def test_students_cannot_review_requests(client, student):
    assert client.get("/api/admin/student-requests", headers=student).status_code == 403


def test_google_only_account_cannot_use_password_login(client, google):
    google_login(client, "nopass@gmail.com", DETAILS)
    r = client.post("/api/auth/login", json={"email": "nopass@gmail.com", "password": "whatever123"})
    assert r.status_code == 401


def test_register_endpoint_is_gone(client):
    assert client.post("/api/auth/register", json={}).status_code in (404, 405)
