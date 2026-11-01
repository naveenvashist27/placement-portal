import json
from datetime import datetime, timedelta, timezone

import pytest

FIELDS = [
    {"key": "cgpa", "label": "CGPA", "type": "number", "required": True, "profile_key": "cgpa", "options": []},
    {"key": "has_atkt", "label": "ATKT", "type": "yesno", "required": True, "profile_key": "has_atkt", "options": []},
    {"key": "why", "label": "Why us?", "type": "text", "required": False, "profile_key": None, "options": []},
    {"key": "pref", "label": "Preference", "type": "select", "required": False, "profile_key": None, "options": ["A", "B"]},
]


def _deadline(days=3):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


@pytest.fixture
def form(client, pcell):
    r = client.post(
        "/api/registrations/forms",
        headers=pcell,
        json={
            "title": "Drive =cmd",
            "description": "d",
            "registration_deadline": _deadline(),
            "status": "OPEN",
            "form_fields_json": json.dumps(FIELDS),
        },
    )
    assert r.status_code == 200, r.text
    yield r.json()
    client.delete(f"/api/registrations/forms/{r.json()['id']}", headers=pcell)


def register(client, headers, form_id, responses):
    return client.post(f"/api/registrations/forms/{form_id}/register", headers=headers, json={"responses": responses})


def test_required_answers_are_enforced(client, student, form):
    r = register(client, student, form["id"], {"cgpa": "8.2"})
    assert r.status_code == 400 and "ATKT" in r.json()["detail"]


def test_invalid_value_for_profile_field_is_rejected(client, student, form):
    r = register(client, student, form["id"], {"cgpa": "99", "has_atkt": "No"})
    assert r.status_code == 400 and "cgpa" in r.json()["detail"]


def test_invalid_dropdown_choice_is_rejected(client, student, form):
    r = register(client, student, form["id"], {"cgpa": "8", "has_atkt": "No", "pref": "Z"})
    assert r.status_code == 400


def test_register_saves_answers_and_updates_profile(client, student, form):
    r = register(client, student, form["id"], {"cgpa": "8.4", "has_atkt": "Yes", "why": "Good fit"})
    assert r.status_code == 200, r.text

    profile = client.get("/api/profile", headers=student).json()
    assert profile["cgpa"] == 8.4 and profile["has_atkt"] is True

    assert form["id"] in client.get("/api/registrations/forms/mine", headers=student).json()["form_ids"]
    assert register(client, student, form["id"], {"cgpa": "8", "has_atkt": "No"}).status_code == 400  # duplicate


def test_closed_form_rejects_registration(client, pcell, student2):
    r = client.post(
        "/api/registrations/forms",
        headers=pcell,
        json={"title": "Old", "description": "d", "registration_deadline": _deadline(-1), "status": "OPEN"},
    )
    assert register(client, student2, r.json()["id"], {}).status_code == 400
    client.delete(f"/api/registrations/forms/{r.json()['id']}", headers=pcell)


def test_malformed_field_definitions_are_rejected(client, pcell):
    bad = [{"key": "x", "label": "X", "type": "select", "options": []}]
    r = client.post(
        "/api/registrations/forms",
        headers=pcell,
        json={"title": "t", "description": "d", "registration_deadline": _deadline(), "form_fields_json": json.dumps(bad)},
    )
    assert r.status_code == 422


def test_editing_keeps_questions_when_only_status_changes(client, pcell, form):
    r = client.put(
        f"/api/registrations/forms/{form['id']}",
        headers=pcell,
        json={"title": form["title"], "description": "d", "registration_deadline": form["registration_deadline"], "status": "CLOSED"},
    )
    assert r.status_code == 200
    forms = client.get("/api/registrations/forms", headers=pcell).json()["items"]
    assert json.loads(next(f for f in forms if f["id"] == form["id"])["form_fields_json"])[0]["key"] == "cgpa"


def test_csv_export_has_answers_and_neutralises_formulas(client, pcell, student2, form):
    register(client, student2, form["id"], {"cgpa": "7.5", "has_atkt": "No", "why": "=HYPERLINK(1)"})
    r = client.get(f"/api/registrations/forms/{form['id']}/export.csv", headers=pcell)
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    text = r.content.decode("utf-8-sig")
    assert "Other Student" in text and "MBA Tech" in text and "7.5" in text
    assert "'=HYPERLINK(1)" in text and ",=HYPERLINK" not in text


def test_students_cannot_export(client, student, form):
    assert client.get(f"/api/registrations/forms/{form['id']}/export.csv", headers=student).status_code == 403


# ---- eligibility rules

def _rules_form(client, pcell, rules, fields=None):
    r = client.post(
        "/api/registrations/forms",
        headers=pcell,
        json={
            "title": "Rules",
            "description": "d",
            "registration_deadline": _deadline(),
            "status": "OPEN",
            "form_fields_json": json.dumps(fields if fields is not None else FIELDS[:2]),
            "eligibility_json": json.dumps(rules),
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_eligibility_blocks_low_cgpa_and_atkt_and_keeps_profile_untouched(client, pcell, student2):
    f = _rules_form(client, pcell, {"min_cgpa": 8, "no_atkt": True})
    before = client.get("/api/profile", headers=student2).json()["cgpa"]

    low = register(client, student2, f["id"], {"cgpa": "7", "has_atkt": "No"})
    assert low.status_code == 400 and "CGPA must be at least 8" in low.json()["detail"]

    atkt = register(client, student2, f["id"], {"cgpa": "9", "has_atkt": "Yes"})
    assert atkt.status_code == 400 and "ATKT" in atkt.json()["detail"]
    assert client.get("/api/profile", headers=student2).json()["cgpa"] == before  # nothing saved on a rejected attempt

    assert register(client, student2, f["id"], {"cgpa": "9", "has_atkt": "No"}).status_code == 200
    client.delete(f"/api/registrations/forms/{f['id']}", headers=pcell)


def test_eligibility_course_rule_and_listing_reasons(client, pcell, student):
    f = _rules_form(client, pcell, {"courses": ["B.Tech"], "min_tenth_percentage": 60}, fields=[])
    listed = next(x for x in client.get("/api/registrations/forms", headers=student).json()["items"] if x["id"] == f["id"])
    assert "Course: B.Tech" in listed["eligibility_summary"]
    assert any("10th %" in r for r in listed["ineligible_reasons"])
    assert any("course" in r for r in listed["ineligible_reasons"])
    assert register(client, student, f["id"], {}).status_code == 400
    client.delete(f"/api/registrations/forms/{f['id']}", headers=pcell)


def test_eligible_student_has_no_reasons(client, pcell, student):
    f = _rules_form(client, pcell, {"courses": ["mba tech"], "passing_years": [2027]}, fields=[])
    listed = next(x for x in client.get("/api/registrations/forms", headers=student).json()["items"] if x["id"] == f["id"])
    assert listed["ineligible_reasons"] == []  # course match ignores case
    client.delete(f"/api/registrations/forms/{f['id']}", headers=pcell)


def test_invalid_rules_are_rejected(client, pcell):
    r = client.post(
        "/api/registrations/forms",
        headers=pcell,
        json={"title": "t", "description": "d", "registration_deadline": _deadline(), "eligibility_json": json.dumps({"min_cgpa": 15})},
    )
    assert r.status_code == 422
