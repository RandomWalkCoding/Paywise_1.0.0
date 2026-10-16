from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.policies import policy_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_imports() -> None:
    policy_store.clear_imports()
    yield
    policy_store.clear_imports()


def policy_payload(version: str) -> dict[str, object]:
    return {
        "version": version,
        "region_code": "SH",
        "region_name": "上海",
        "effective_from": "2026-01-01",
        "social_security_min_base": "7380",
        "social_security_max_base": "36921",
        "social_security_employee_rate": "0.105",
        "social_security_employer_rate": "0.265",
        "housing_fund_min_base": "2690",
        "housing_fund_max_base": "36921",
        "housing_fund_employee_rate": "0.07",
        "housing_fund_employer_rate": "0.07",
        "source_name": "上海市人力资源和社会保障局",
        "source_url": "https://example.gov.cn/policy/2026",
        "source_published_at": "2026-01-01",
    }


def test_import_starts_pending_and_cannot_replace_formal_policy() -> None:
    version = "import-pending-2026-01"
    response = client.post("/api/v1/policies/imports", json={"policy": policy_payload(version), "imported_by": "importer"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["review_status"] == "pending"
    assert payload["formal_policy"] is False
    assert payload["reviewed"] is False
    assert payload["imported_at"] is not None

    # A pending import must not replace the currently selected example fallback.
    selected = client.get("/api/v1/policies", params={"region_code": "SH", "month": "2026-10"})
    assert selected.status_code == 200
    assert selected.json()["version"] == "example-sh-2026-01"


def test_approved_import_becomes_the_policy_selected_for_its_region() -> None:
    version = "import-approved-2026-02"
    create = client.post("/api/v1/policies/imports", json={"policy": policy_payload(version), "imported_by": "importer"})
    assert create.status_code == 201

    review = client.patch(
        f"/api/v1/policies/imports/{version}/review",
        json={"review_status": "approved", "reviewed_by": "reviewer", "review_note": "来源与字段已核验"},
    )
    assert review.status_code == 200
    assert review.json()["formal_policy"] is True
    assert review.json()["reviewed"] is True
    assert review.json()["reviewed_at"] is not None

    selected = client.get("/api/v1/policies", params={"region_code": "SH", "month": "2026-10"})
    assert selected.json()["version"] == version


def test_policy_import_validates_dates_bases_and_source_url() -> None:
    invalid = policy_payload("import-invalid-2026-01")
    invalid["effective_to"] = date(2025, 12, 31).isoformat()
    invalid["social_security_min_base"] = "40000"
    invalid["source_url"] = "not-a-url"

    response = client.post("/api/v1/policies/imports", json={"policy": invalid, "imported_by": "importer"})
    assert response.status_code == 422


def test_import_versions_must_be_unique() -> None:
    version = "import-duplicate-2026-01"
    payload = {"policy": policy_payload(version), "imported_by": "importer"}
    assert client.post("/api/v1/policies/imports", json=payload).status_code == 201
    duplicate = client.post("/api/v1/policies/imports", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "POLICY_VERSION_EXISTS"
