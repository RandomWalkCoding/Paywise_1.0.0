from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def calculation_payload() -> dict[str, str]:
    return {
        "calculation_month": "2026-10",
        "work_city": "上海",
        "social_security_city": "上海",
        "housing_fund_city": "上海",
        "monthly_salary": "20000",
        "annual_bonus": "12000",
    }


def test_scenario_saves_input_policy_engine_and_result_snapshot() -> None:
    response = client.post("/api/v1/scenarios", json={"name": "上海 offer", "input": calculation_payload()})
    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "上海 offer"
    assert payload["input_snapshot"]["monthly_salary"] == "20000"
    assert payload["result_snapshot"]["policy_version"] == "example-sh-2026-01"
    assert payload["engine_version"].startswith("calculator-")
    assert payload["result_summary"]["take_home_cash"] == payload["result_snapshot"]["take_home_cash"]

    detail = client.get(f"/api/v1/scenarios/{payload['id']}")
    assert detail.status_code == 200
    assert detail.json()["result_snapshot"] == payload["result_snapshot"]


def test_scenario_list_returns_summaries_and_missing_is_404() -> None:
    response = client.post("/api/v1/scenarios", json={"name": "list case", "calculation": calculation_payload()})
    assert response.status_code == 201
    listed = client.get("/api/v1/scenarios")
    assert listed.status_code == 200
    assert any(item["id"] == response.json()["id"] for item in listed.json())

    missing = client.get("/api/v1/scenarios/not-a-real-id")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "SCENARIO_NOT_FOUND"


def test_scenario_requires_input() -> None:
    response = client.post("/api/v1/scenarios", json={"name": "incomplete"})
    assert response.status_code == 422


def test_scenario_can_be_renamed_soft_deleted_and_restored() -> None:
    created = client.post("/api/v1/scenarios", json={"name": "lifecycle", "input": calculation_payload()})
    scenario_id = created.json()["id"]
    renamed = client.patch(f"/api/v1/scenarios/{scenario_id}", json={"name": "renamed"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "renamed"

    deleted = client.delete(f"/api/v1/scenarios/{scenario_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted_at"] is not None
    assert all(item["id"] != scenario_id for item in client.get("/api/v1/scenarios").json())

    restored = client.post(f"/api/v1/scenarios/{scenario_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["deleted_at"] is None
