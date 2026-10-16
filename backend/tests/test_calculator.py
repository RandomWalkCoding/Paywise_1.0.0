from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.services.calculator import annual_bonus_tax, bonus_tax_bracket, tax_for_income
from app.services.policies import find_policy


def test_tax_brackets_apply_rate_and_quick_deduction() -> None:
    tax, rate, quick = tax_for_income(Decimal("100000"))
    assert tax == Decimal("7480.00")
    assert rate == Decimal("0.10")
    assert quick == Decimal("2520")


def test_negative_taxable_income_is_zero() -> None:
    tax, rate, quick = tax_for_income(Decimal("-1"))
    assert tax == Decimal("0.00")
    assert rate == Decimal("0.03")
    assert quick == Decimal("0")


def test_annual_bonus_uses_monthly_equivalent_bracket() -> None:
    separate, combined, recommended = annual_bonus_tax(Decimal("120000"), Decimal("0"))
    assert separate == Decimal("11790.00")
    assert combined == Decimal("9480.00")
    assert recommended == "combined"


def test_bonus_bracket_uses_monthly_quick_deduction() -> None:
    rate, quick = bonus_tax_bracket(Decimal("10000"))
    assert rate == Decimal("0.10")
    assert quick == Decimal("210")


def test_bonus_bracket_changes_at_monthly_income_threshold() -> None:
    assert bonus_tax_bracket(Decimal("3000"))[0] == Decimal("0.03")
    assert bonus_tax_bracket(Decimal("3000.01"))[0] == Decimal("0.10")


def test_annual_bonus_combined_is_forced_when_policy_disallows_separate() -> None:
    separate, combined, recommended = annual_bonus_tax(
        Decimal("120000"), Decimal("0"), separate_allowed=False
    )
    assert separate == Decimal("11790.00")
    assert combined == Decimal("9480.00")
    assert recommended == "combined"


def test_annual_bonus_recommends_combined_when_cheaper() -> None:
    separate, combined, recommended = annual_bonus_tax(Decimal("120000"), Decimal("0"))
    assert separate > combined
    assert recommended == "combined"


def test_annual_bonus_recommends_separate_when_cheaper() -> None:
    separate, combined, recommended = annual_bonus_tax(Decimal("120000"), Decimal("150000"))
    assert separate < combined
    assert recommended == "separate"


def test_policy_base_limits_clamp_social_and_fund() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "上海", "social_security_city": "上海",
        "housing_fund_city": "上海", "monthly_salary": "100000",
    })
    assert response.status_code == 200
    payload = response.json()
    policy = find_policy("SH", "2026-10")
    assert policy is not None
    assert Decimal(str(payload["social_security_base"])) == policy.social_security_max_base
    assert Decimal(str(payload["housing_fund_base"])) == policy.housing_fund_max_base


def test_user_base_override_marks_customized_confidence() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "上海", "social_security_city": "上海",
        "housing_fund_city": "上海", "monthly_salary": "20000",
        "social_security_base": "15000", "housing_fund_base": "15000",
    })
    assert response.status_code == 200
    assert response.json()["confidence"] == "user_customized"


def test_cumulative_withholding_across_months() -> None:
    client = TestClient(app)

    def post(prior_income: str, months: int) -> dict:
        response = client.post("/api/v1/calculations", json={
            "calculation_month": "2026-05", "work_city": "上海", "social_security_city": "上海",
            "housing_fund_city": "上海", "monthly_salary": "20000",
            "prior_cumulative_income": prior_income, "cumulative_months": months,
        })
        assert response.status_code == 200
        return response.json()

    month_2 = post("20000", 2)
    assert Decimal(str(month_2["cumulative_taxable_income"])) > 0
    # 累计第 2 月的当月预扣税应等于两个月累计税减去第 1 月累计税。
    month_1_tax = Decimal(str(post("0", 1)["cumulative_tax"]))
    expected = Decimal(str(month_2["cumulative_tax"])) - month_1_tax
    assert Decimal(str(month_2["monthly_tax"])) == expected


def test_unmatched_region_reports_missing_policy() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "广州", "social_security_city": "广州",
        "housing_fund_city": "广州", "monthly_salary": "20000",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_version"] == "unmatched"
    assert any("暂无匹配政策" in item for item in payload["needs_confirmation"])


def test_social_and_fund_regions_are_matched_independently() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "上海", "social_security_city": "上海",
        "housing_fund_city": "北京", "monthly_salary": "20000",
    })
    assert response.status_code == 200
    assert "社保 example-sh-2026-01" in response.json()["policy_version"]
    assert "公积金 example-bj-2026-01" in response.json()["policy_version"]


def test_prior_tax_snapshots_drive_current_withholding() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "上海", "social_security_city": "上海",
        "housing_fund_city": "上海", "monthly_salary": "20000", "cumulative_months": 2,
        "prior_cumulative_taxable_income": "10000", "prior_cumulative_tax": "300",
    })
    assert response.status_code == 200
    payload = response.json()
    assert Decimal(str(payload["monthly_tax"])) == Decimal(str(payload["cumulative_tax"])) - Decimal("300")


def test_bonus_paid_in_a_later_month_is_not_in_current_cash() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "上海", "social_security_city": "上海",
        "housing_fund_city": "上海", "monthly_salary": "20000", "annual_bonus": "120000",
        "bonus_payout_month": "2026-12",
    })
    assert response.status_code == 200
    payload = response.json()
    assert Decimal(str(payload["bonus_paid_this_month"])) == Decimal("0.00")
    assert Decimal(str(payload["annual_total_compensation"])) == Decimal("360000.00")


def test_bonus_with_unmatched_policy_cannot_recommend_separate_tax() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "广州", "social_security_city": "广州",
        "housing_fund_city": "广州", "monthly_salary": "20000", "annual_bonus": "120000",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["bonus_recommended"] == "combined"


def test_result_explains_policy_source_and_asset_definition() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/calculations", json={
        "calculation_month": "2026-10", "work_city": "上海市", "social_security_city": "上海市",
        "housing_fund_city": "上海市", "monthly_salary": "20000",
    })
    assert response.status_code == 200
    payload = response.json()
    assert "https://www.gov.cn/" in payload["policy_source"]
    assert any("个人资产增加 = 到手现金 + 个人公积金" in item for item in payload["breakdown"])
    assert Decimal(str(payload["personal_asset_increase"])) == (
        Decimal(str(payload["take_home_cash"])) + Decimal(str(payload["estimated_housing_fund"]))
    )


def test_reviewed_policy_can_produce_policy_matched_confidence(monkeypatch) -> None:
    from app.services import calculator

    policy = find_policy("SH", "2026-10")
    assert policy is not None
    reviewed = policy.model_copy(update={"reviewed": True})
    monkeypatch.setattr(calculator, "find_policy", lambda region, month: reviewed)
    request = {
        "calculation_month": "2026-10", "work_city": "上海", "social_security_city": "上海",
        "housing_fund_city": "上海", "monthly_salary": "20000",
    }
    response = TestClient(app).post("/api/v1/calculations", json=request)
    assert response.status_code == 200
    assert response.json()["confidence"] == "policy_matched"
