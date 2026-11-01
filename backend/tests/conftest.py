"""Test setup. Runs against a separate `placement_portal_test` database, never the dev one.

Run from backend/:  python -m pytest
"""

import os

TEST_DB = "placement_portal_test"
os.environ["DATABASE_URL"] = f"postgresql+asyncpg://postgres:postgres@localhost:5432/{TEST_DB}"
os.environ["DATABASE_URL_SYNC"] = f"postgresql://postgres:postgres@localhost:5432/{TEST_DB}"
os.environ["GEOFENCE_ENABLED"] = "false"  # individual tests turn it on when they need it
os.environ["USE_LOCAL_STORAGE"] = "true"

import psycopg2  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import models  # noqa: E402,F401
from app.core.database import Base  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole, UserStatus  # noqa: E402
from app.models.user import StudentProfile, User  # noqa: E402

PASSWORD = "Test@12345"


def _ensure_database() -> None:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/postgres")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{TEST_DB}"')
    conn.close()


@pytest.fixture(scope="session")
def client():
    _ensure_database()
    sync_engine = create_engine(os.environ["DATABASE_URL_SYNC"])
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)

    with Session(sync_engine) as db:
        for email, name, role in [
            ("tpo@test.dev", "Test TPO", UserRole.TPO),
            ("pcell@test.dev", "Test PCELL", UserRole.PCELL_MEMBER),
            ("student@test.dev", "Test Student", UserRole.STUDENT),
            ("student2@test.dev", "Other Student", UserRole.STUDENT),
        ]:
            user = User(
                email=email,
                full_name=name,
                hashed_password=get_password_hash(PASSWORD),
                role=role,
                status=UserStatus.ACTIVE,
            )
            db.add(user)
            db.flush()
            if role == UserRole.STUDENT:
                db.add(StudentProfile(user_id=user.id, course="MBA Tech", batch="2022-2027", graduation_year=2027))
        db.commit()
    sync_engine.dispose()

    # One client for the whole run: the async DB pool must stay on a single event loop.
    with TestClient(app) as c:
        yield c


def _login(client: TestClient, email: str) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def pcell(client):
    return _login(client, "pcell@test.dev")


@pytest.fixture(scope="session")
def student(client):
    return _login(client, "student@test.dev")


@pytest.fixture(scope="session")
def student2(client):
    return _login(client, "student2@test.dev")


@pytest.fixture(scope="session")
def company(client, pcell):
    """A company with one visit year and one role, shared by the experience and placement tests."""
    c = client.post("/api/companies", headers=pcell, json={"name": "TestCorp", "industry": "IT"}).json()
    year = client.post(f"/api/companies/{c['id']}/years", headers=pcell, json={"visit_year": 2026}).json()
    role = client.post(f"/api/company-years/{year['id']}/roles", headers=pcell, json={"title": "Engineer"}).json()
    return {"id": c["id"], "year_id": year["id"], "role_id": role["id"]}
