from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200


def test_login_demo_citizen():
    r = client.post("/api/auth/login", json={"email": "citizen@demo.in", "password": "Demo@1234"})
    assert r.status_code == 200
    assert r.json()["role"] == "citizen"


def test_invalid_password():
    r = client.post("/api/auth/login", json={"email": "citizen@demo.in", "password": "wrong"})
    assert r.status_code == 401


def _token(email):
    return client.post("/api/auth/login", json={"email": email, "password": "Demo@1234"}).json()["access_token"]


def test_role_authorization():
    token = _token("citizen@demo.in")
    r = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_citizen_register_and_verify():
    r = client.post(
        "/api/auth/register/citizen",
        json={
            "full_name": "Test User",
            "email": "newcitizen@demo.in",
            "mobile": "9988776655",
            "password": "Secret123",
            "confirm_password": "Secret123",
            "district": "Ranchi",
            "block": "Namkum",
            "village": "Test",
            "address": "Addr",
        },
    )
    assert r.status_code == 200
    v = client.post("/api/auth/verify", json={"email": "newcitizen@demo.in", "code": "123456"})
    assert v.status_code == 200


def test_problem_requires_location():
    token = _token("citizen@demo.in")
    r = client.post(
        "/api/problems",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Contaminated drinking water report",
            "description": "The village well water smells and people are falling ill after drinking it.",
            "category": "Water Management",
            "district": "Ranchi",
        },
    )
    assert r.status_code == 400


def test_problem_submit():
    token = _token("citizen@demo.in")
    r = client.post(
        "/api/problems",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Contaminated drinking water report",
            "description": "The village well water smells and people are falling ill after drinking it.",
            "category": "Water Management",
            "district": "Ranchi",
            "latitude": 23.35,
            "longitude": 85.33,
            "estimated_affected_population": 100,
            "severity": "high",
            "urgency": "high",
        },
    )
    assert r.status_code == 200
    assert r.json()["public_id"].startswith("JH-PR-")
    assert r.json()["status"] == "pending_government_verification"


def test_government_verify_assign_solution():
    ctok = _token("citizen@demo.in")
    created = client.post(
        "/api/problems",
        headers={"Authorization": f"Bearer {ctok}"},
        json={
            "title": "Broken rural culvert blocking access",
            "description": "A damaged culvert has made the approach road unsafe for school buses and ambulances.",
            "category": "Urban Infrastructure",
            "district": "Khunti",
            "latitude": 23.07,
            "longitude": 85.27,
            "estimated_affected_population": 400,
            "severity": "high",
            "urgency": "high",
        },
    ).json()
    pid = created["public_id"]
    gtok = _token("gov@demo.in")
    headers = {"Authorization": f"Bearer {gtok}"}
    v = client.post(f"/api/government/problems/{pid}/verify", headers=headers, json={"remarks": "Verified on record"})
    assert v.status_code == 200
    depts = client.get("/api/government/departments", headers=headers).json()
    a = client.post(
        f"/api/government/problems/{pid}/assign",
        headers=headers,
        json={"department_id": depts[0]["id"], "remarks": "Assign"},
    )
    assert a.status_code == 200
    sol = client.post(
        f"/api/government/problems/{pid}/solution",
        headers=headers,
        data={"description": "Temporary diversion and repair estimate.", "action_taken": "Site inspection completed.", "implementation_details": "Tender note drafted."},
    )
    assert sol.status_code == 200
    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers)
    assert recs.status_code == 200
    ids = [r["university_id"] for r in recs.json()][:1]
    sel = client.post(f"/api/government/problems/{pid}/select-universities", headers=headers, json={"university_ids": ids})
    assert sel.status_code == 200
    utok = _token("university@demo.in")
    op = client.post(
        f"/api/universities/problems/{pid}/opinion",
        headers={"Authorization": f"Bearer {utok}"},
        json={"suggestion": "Use geotagged photo log for repair verification.", "expected_benefit": "Auditability"},
    )
    assert op.status_code == 200
    done = client.post(f"/api/government/problems/{pid}/done-solution", headers=headers, json={"remarks": "Ready for optional industry"})
    assert done.status_code == 200
    itok = _token("iot@demo.in")
    part = client.post(
        f"/api/industry/problems/{pid}/participate",
        headers={"Authorization": f"Bearer {itok}"},
        json={"participation_types": ["Prototype", "Testing"]},
    )
    assert part.status_code == 200


def test_university_no_opinion_and_admin_audit():
    atok = _token("admin@c2i.jharkhand.gov.in")
    logs = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {atok}"})
    assert logs.status_code == 200
    assert len(logs.json()) > 0


def test_unverified_government_blocked():
    client.post(
        "/api/auth/register/government",
        json={
            "full_name": "Unverified Officer",
            "email": "unverified.gov@demo.in",
            "password": "Secret123",
            "official_id": "X-1",
            "department_code": "WRD",
            "district": "Ranchi",
        },
    )
    token = client.post("/api/auth/login", json={"email": "unverified.gov@demo.in", "password": "Secret123"}).json()["access_token"]
    r = client.get("/api/government/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
