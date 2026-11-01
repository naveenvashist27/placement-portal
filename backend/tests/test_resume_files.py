import fitz  # PyMuPDF
import pytest


def tiny_pdf() -> bytes:
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Python SQL resume")
    return doc.tobytes()


@pytest.fixture(scope="module")
def resume_id(client, student):
    r = client.post("/api/resumes/upload", headers=student, files={"file": ("cv.pdf", tiny_pdf(), "application/pdf")})
    assert r.status_code == 200, r.text
    return r.json()["resume_id"]


def test_uploads_are_not_publicly_served(client, resume_id):
    assert client.get("/static/resumes/anything.pdf").status_code == 404


def test_resume_api_does_not_leak_server_paths(client, student, resume_id):
    assert "file_path" not in client.get("/api/resumes/me", headers=student).json()


def test_owner_and_staff_can_open_but_other_students_cannot(client, student, student2, pcell, resume_id):
    for headers in (student, pcell):
        r = client.get(f"/api/resumes/{resume_id}/file", headers=headers)
        assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert client.get(f"/api/resumes/{resume_id}/file", headers=student2).status_code == 404


def test_file_needs_login(client, resume_id):
    assert client.get(f"/api/resumes/{resume_id}/file").status_code == 401


def test_pcell_can_open_a_student_resume_by_student_id_and_students_cannot(client, student, student2, pcell, resume_id):
    sid = next(s["id"] for s in client.get("/api/students", headers=pcell, params={"q": "student@test.dev"}).json()["items"])
    r = client.get(f"/api/resumes/by-student/{sid}/file", headers=pcell)
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert client.get(f"/api/resumes/by-student/{sid}/file", headers=student2).status_code == 403


def test_students_list_and_experience_submitter_flag_resume(client, student, pcell, company, resume_id):
    listing = client.get("/api/students", headers=pcell, params={"q": "student@test.dev"}).json()["items"]
    assert listing[0]["has_resume"] is True
    assert next(s for s in client.get("/api/students", headers=pcell, params={"q": "student2@test.dev"}).json()["items"])["has_resume"] is False

    client.post(
        "/api/experiences",
        headers=student,
        json={"company_id": company["id"], "company_year_id": company["year_id"], "overall_experience": "A long enough experience text."},
    )
    items = client.get("/api/experiences", headers=pcell).json()["items"]
    assert any(i["submitter"]["has_resume"] for i in items if i["submitter"]["email"] == "student@test.dev")
