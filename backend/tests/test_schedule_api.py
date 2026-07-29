from fastapi.testclient import TestClient

from app.main import app, seed_demo_data


seed_demo_data()
client = TestClient(app)


def _token(account: str = "E001") -> str:
    response = client.post("/api/auth/login", json={"account": account, "password": "1234"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_calculate_leave_uses_employee_rotation_group():
    token = _token("E001")
    response = client.post(
        "/api/leaves/calculate",
        headers={"Authorization": f"Bearer {token}"},
        json={"start_date": "2026-01-09", "end_date": "2026-01-12"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rotation_group"] == "A"
    assert data["calendar_days"] == 4
    assert data["workdays"] == 2


def test_chatbot_can_answer_saturday_schedule():
    token = _token("E001")
    response = client.post(
        "/api/rag/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "我這個星期六要上班嗎？", "history": [], "language": "zh-TW"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "schedule-tool"
    assert data["schedule"]["rotation_group"] == "A"


def test_chatbot_can_answer_current_time_without_rag_fallback():
    token = _token("E001")
    response = client.post(
        "/api/rag/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "現在幾點？", "history": [], "language": "zh-TW"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "time-tool"
    assert data["timezone"] == "Asia/Bangkok"
    assert "泰國時間" in data["answer"]


def test_chatbot_auto_detects_english_question_language():
    token = _token("E001")
    response = client.post(
        "/api/rag/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "What time is it?", "history": [], "language": "zh-TW"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "time-tool"
    assert data["answer"].startswith("The current time")


def test_chatbot_auto_detects_thai_greeting_language():
    token = _token("E001")
    response = client.post(
        "/api/rag/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "สวัสดี", "history": [], "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "greeting-tool"
    assert data["answer"].startswith("สวัสดี")


def test_chatbot_chinese_greeting_does_not_return_leave_balance():
    token = _token("E001")
    response = client.post(
        "/api/rag/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "你好", "history": [], "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "greeting-tool"
    assert "12 天特休" not in data["answer"]
    assert data["answer"].startswith("你好")
