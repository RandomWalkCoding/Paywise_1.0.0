from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_policy_can_be_queried_by_region_and_month() -> None:
    response = client.get("/api/v1/policies", params={"region_code": "SH", "month": "2026-10"})
    assert response.status_code == 200
    assert response.json()["version"] == "example-sh-2026-01"
    assert response.json()["is_example"] is True


def test_calculation_contract_returns_mock_result() -> None:
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "上海", "social_security_city": "上海",
        "housing_fund_city": "上海", "monthly_salary": "20000",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_mock"] is False
    assert payload["confidence"] == "partially_estimated"
    assert "take_home_cash" in payload
    assert float(payload["monthly_tax"]) >= 0
    assert payload["bonus_recommended"] == "none"


def test_calculation_contract_validates_month() -> None:
    response = client.post("/api/v1/calculations", json={"calculation_month": "2026/10"})
    assert response.status_code == 422
