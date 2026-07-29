from fastapi.testclient import TestClient

from app.main import app, seed_demo_data

seed_demo_data()
client = TestClient(app)


def token(account: str) -> str:
    response = client.post("/api/auth/login", json={"account": account, "password": "1234"})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(account: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(account)}"}


def test_sop_catalog_contains_published_and_draft_documents():
    response = client.get("/api/sops", headers=auth("E001"))
    assert response.status_code == 200
    items = response.json()
    assert any(item["code"] == "LEV-001" and item["status"] == "published" for item in items)
    assert any(item["code"] == "SAF-001" and item["status"] == "draft" for item in items)


def test_published_sop_requires_passing_quiz_score():
    items = client.get("/api/sops", headers=auth("E001")).json()
    sop_id = next(item["id"] for item in items if item["code"] == "LEV-001")
    response = client.post(
        f"/api/sops/{sop_id}/acknowledge",
        headers=auth("E001"),
        json={"quiz_score": 60},
    )
    assert response.status_code == 422


def test_employee_can_acknowledge_published_sop():
    headers = auth("E001")
    items = client.get("/api/sops", headers=headers).json()
    sop_id = next(item["id"] for item in items if item["code"] == "SYS-001")
    response = client.post(
        f"/api/sops/{sop_id}/acknowledge",
        headers=headers,
        json={"quiz_score": 100},
    )
    assert response.status_code == 201
    progress = client.get("/api/sops/progress", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["completed"] >= 1


def test_draft_sop_cannot_be_acknowledged():
    headers = auth("E001")
    items = client.get("/api/sops", headers=headers).json()
    sop_id = next(item["id"] for item in items if item["code"] == "SAF-001")
    response = client.post(
        f"/api/sops/{sop_id}/acknowledge",
        headers=headers,
        json={"quiz_score": 100},
    )
    assert response.status_code == 409


def test_employee_attendance_is_scoped_to_self():
    response = client.get("/api/attendance", headers=auth("E001"))
    assert response.status_code == 200
    items = response.json()
    assert items
    assert {item["employee_id"] for item in items} == {"E001"}


def test_hr_can_import_attendance_and_employee_can_request_correction():
    import_response = client.post(
        "/api/attendance/import",
        headers=auth("HR001"),
        json={
            "records": [
                {
                    "employee_id": "E001",
                    "work_date": "2026-07-20",
                    "scheduled_start": "08:00",
                    "scheduled_end": "17:00",
                    "clock_in": None,
                    "clock_out": "17:02",
                    "status": "missing_punch",
                    "source": "pytest",
                    "note": "test",
                }
            ]
        },
    )
    assert import_response.status_code == 200

    records = client.get(
        "/api/attendance?start_date=2026-07-20&end_date=2026-07-20",
        headers=auth("E001"),
    ).json()
    assert len(records) == 1
    correction = client.post(
        f"/api/attendance/{records[0]['id']}/corrections",
        headers=auth("E001"),
        json={"requested_clock_in": "07:58", "requested_clock_out": "17:02", "reason": "Reader failed"},
    )
    assert correction.status_code == 201
    assert correction.json()["status"] == "pending"


def test_employee_cannot_import_attendance():
    response = client.post(
        "/api/attendance/import",
        headers=auth("E001"),
        json={
            "records": [
                {
                    "employee_id": "E001",
                    "work_date": "2026-07-21",
                    "status": "normal",
                }
            ]
        },
    )
    assert response.status_code == 403
