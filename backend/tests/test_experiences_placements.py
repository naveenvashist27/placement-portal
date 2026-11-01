import pytest


@pytest.fixture
def experience(client, student, company):
    r = client.post(
        "/api/experiences",
        headers=student,
        json={
            "company_id": company["id"],
            "company_year_id": company["year_id"],
            "overall_experience": "Three rounds: aptitude, technical and HR.",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def ids(response):
    return [i["id"] for i in response.json()["items"]]


def test_pending_experience_is_hidden_from_other_students_but_visible_to_author(client, student, student2, experience):
    assert experience["id"] not in ids(client.get("/api/experiences", headers=student2))
    assert experience["id"] in ids(client.get("/api/experiences", headers=student, params={"mine": True}))


def test_pcell_sees_who_submitted_and_students_do_not(client, pcell, student, student2, experience):
    staff_item = next(i for i in client.get("/api/experiences", headers=pcell).json()["items"] if i["id"] == experience["id"])
    assert staff_item["submitter"]["email"] == "student@test.dev"
    assert staff_item["submitter"]["course"] == "MBA Tech"

    mine = client.get("/api/experiences", headers=student, params={"mine": True}).json()["items"]
    assert all(i["submitter"] is None for i in mine)


def test_reject_needs_a_reason_and_student_can_read_it(client, pcell, student, student2, experience):
    assert client.post(f"/api/experiences/{experience['id']}/reject", headers=pcell, json={}).status_code == 422
    assert client.post(f"/api/experiences/{experience['id']}/reject", headers=pcell, json={"note": "ab"}).status_code == 422

    r = client.post(f"/api/experiences/{experience['id']}/reject", headers=pcell, json={"note": "Add technical details"})
    assert r.status_code == 200

    mine = client.get("/api/experiences", headers=student, params={"mine": True}).json()["items"]
    item = next(i for i in mine if i["id"] == experience["id"])
    assert item["status"] == "REJECTED" and item["review_note"] == "Add technical details"

    notes = client.get("/api/notifications", headers=student).json()
    assert any("Add technical details" in n["message"] for n in notes)


def test_approved_experience_is_public_without_review_note_or_submitter(client, pcell, student, student2, experience):
    client.post(f"/api/experiences/{experience['id']}/approve", headers=pcell, json={"note": "internal"})
    seen = next(i for i in client.get("/api/experiences", headers=student2).json()["items"] if i["id"] == experience["id"])
    assert seen["review_note"] is None and seen["submitter"] is None and seen["visit_year"] == 2026


def test_students_cannot_review(client, student, experience):
    assert client.post(f"/api/experiences/{experience['id']}/approve", headers=student).status_code == 403


# ---- placements

def _student_id(client, pcell, email):
    return next(s["id"] for s in client.get("/api/students", headers=pcell, params={"q": email}).json()["items"])


def placement_body(student_id, company, **extra):
    return {"student_id": student_id, "company_id": company["id"], "company_year_id": company["year_id"], **extra}


def test_placement_lifecycle_and_stats(client, pcell, company):
    sid = _student_id(client, pcell, "student@test.dev")
    before = client.get("/api/stats/overview", headers=pcell).json()["students_placed_auto"]

    r = client.post("/api/placements", headers=pcell, json=placement_body(sid, company, package_lpa=6.5, role_id=company["role_id"]))
    assert r.status_code == 200, r.text
    pid = r.json()["id"]

    assert client.get("/api/stats/overview", headers=pcell).json()["students_placed_auto"] == before + 1

    # same student, same company year and role again
    dup = client.post("/api/placements", headers=pcell, json=placement_body(sid, company, role_id=company["role_id"]))
    assert dup.status_code == 400

    # declining takes them out of the "placed" count
    client.put(f"/api/placements/{pid}/status", headers=pcell, json={"placement_status": "DECLINED"})
    assert client.get("/api/stats/overview", headers=pcell).json()["students_placed_auto"] == before

    row = next(p for p in client.get("/api/placements", headers=pcell).json()["items"] if p["id"] == pid)
    assert row["company"] == "TestCorp" and row["role"] == "Engineer" and row["package_lpa"] == 6.5

    assert client.delete(f"/api/placements/{pid}", headers=pcell).status_code == 200


def test_placement_validation(client, pcell, student, company):
    sid = _student_id(client, pcell, "student@test.dev")
    assert client.post("/api/placements", headers=student, json=placement_body(sid, company)).status_code == 403
    assert client.post("/api/placements", headers=pcell, json=placement_body(999999, company)).status_code == 400

    other = client.post("/api/companies", headers=pcell, json={"name": "OtherCorp"}).json()
    mismatched = {"student_id": sid, "company_id": other["id"], "company_year_id": company["year_id"]}
    assert client.post("/api/placements", headers=pcell, json=mismatched).status_code == 400
