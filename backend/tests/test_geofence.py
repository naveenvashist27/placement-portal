import pytest

from app.core.config import get_settings
from app.core.geofence import create_pass, distance_m, is_on_campus, pass_is_valid

CAMPUS = (22.6884251, 75.876705)
INDORE_CENTRE = (22.7196, 75.8577)  # roughly 4 km away


def test_distance_is_zero_at_same_point_and_sane_across_town():
    assert distance_m(*CAMPUS, *CAMPUS) == pytest.approx(0, abs=0.1)
    assert 3500 < distance_m(*CAMPUS, *INDORE_CENTRE) < 4500


def test_inside_and_outside_radius():
    assert is_on_campus(22.6886, 75.8770, 10)[0] is True
    allowed, distance = is_on_campus(*INDORE_CENTRE, 10)
    assert allowed is False and distance > 3000


def test_accuracy_allowance_is_capped():
    # ~700 m east of the centre: outside 500 m + the 100 m cap, so a huge accuracy figure must not rescue it.
    lng_700m = CAMPUS[1] + 700 / (111_320 * 0.9227)
    assert is_on_campus(CAMPUS[0], lng_700m, 5000)[0] is False
    # ~550 m: only the (capped) accuracy allowance makes this pass.
    lng_550m = CAMPUS[1] + 550 / (111_320 * 0.9227)
    assert is_on_campus(CAMPUS[0], lng_550m, 0)[0] is False
    assert is_on_campus(CAMPUS[0], lng_550m, 60)[0] is True


def test_pass_roundtrip_and_tampering():
    token, ttl = create_pass()
    assert ttl > 0 and pass_is_valid(token)
    assert not pass_is_valid(None)
    assert not pass_is_valid("garbage")
    assert not pass_is_valid(token[:-3] + "abc")


@pytest.fixture
def geofence_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "geofence_enabled", True)


def test_api_blocked_without_pass(client, geofence_on):
    r = client.post("/api/auth/login", json={"email": "student@test.dev", "password": "Test@12345"})
    assert r.status_code == 403
    assert r.json()["code"] == "CAMPUS_REQUIRED"


def test_campus_endpoints_stay_open(client, geofence_on):
    assert client.get("/api/campus/status").json()["enabled"] is True
    assert client.get("/health").status_code == 200


def test_check_rejects_off_campus_and_issues_pass_on_campus(client, geofence_on):
    far = client.post("/api/campus/check", json={"latitude": INDORE_CENTRE[0], "longitude": INDORE_CENTRE[1]}).json()
    assert far["allowed"] is False and far["pass_token"] is None

    near = client.post("/api/campus/check", json={"latitude": 22.6886, "longitude": 75.8770, "accuracy": 15}).json()
    assert near["allowed"] is True

    r = client.post(
        "/api/auth/login",
        headers={"X-Campus-Pass": near["pass_token"]},
        json={"email": "student@test.dev", "password": "Test@12345"},
    )
    assert r.status_code == 200


def test_check_validates_coordinates(client, geofence_on):
    assert client.post("/api/campus/check", json={"latitude": 999, "longitude": 0}).status_code == 422
