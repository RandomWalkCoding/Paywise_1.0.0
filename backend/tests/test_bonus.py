from datetime import date
from decimal import Decimal

from app.models.calculation import CalculationRequest
from app.models.policy import PolicyVersion
from app.services import calculator
from app.services.calculator import annual_bonus_tax, calculate_salary


def _policy(*, separate_allowed: bool = True) -> PolicyVersion:
    return PolicyVersion(
        version="test-policy",
        region_code="SH",
        region_name="上海",
        effective_from=date(2026, 1, 1),
        social_security_min_base=Decimal("1"),
        social_security_max_base=Decimal("1000000"),
        social_security_employee_rate=Decimal("0"),
        social_security_employer_rate=Decimal("0"),
        housing_fund_min_base=Decimal("1"),
        housing_fund_max_base=Decimal("1000000"),
        housing_fund_employee_rate=Decimal("0"),
        housing_fund_employer_rate=Decimal("0"),
        annual_bonus_separate_allowed=separate_allowed,
        source_name="test policy",
        source_url="https://example.test/policy",
    )


def _request(**overrides: object) -> CalculationRequest:
    values: dict[str, object] = {
        "calculation_month": "2026-12",
        "work_city": "上海",
        "social_security_city": "上海",
        "housing_fund_city": "上海",
        "monthly_salary": "5000",
        "annual_bonus": "120000",
        "bonus_payout_month": "2026-12",
    }
    values.update(overrides)
    return CalculationRequest(**values)


def test_bonus_separate_tax_uses_monthly_bracket_and_monthly_quick_deduction() -> None:
    separate, combined, recommended = annual_bonus_tax(Decimal("120000"), Decimal("0"))

    assert separate == Decimal("11790.00")
    assert combined == Decimal("9480.00")
    assert recommended == "combined"


def test_bonus_separate_tax_monthly_bracket_boundaries() -> None:
    cases = (
        ("36000", "1080.00"),
        ("36000.01", "3390.00"),
        ("144000", "14190.00"),
        ("144000.01", "27390.00"),
        ("300000", "58590.00"),
        ("300000.01", "72340.00"),
        ("420000", "102340.00"),
        ("420000.01", "121590.00"),
        ("660000", "193590.00"),
        ("660000.01", "223840.00"),
        ("960000", "328840.00"),
        ("960000.01", "416840.00"),
    )

    for bonus, expected_tax in cases:
        separate, _, _ = annual_bonus_tax(Decimal(bonus), Decimal("0"))
        assert separate == Decimal(expected_tax), f"bonus={bonus}"


def test_bonus_disallowed_by_policy_forces_combined_method(monkeypatch) -> None:
    disallowed_policy = _policy(separate_allowed=False)
    monkeypatch.setattr(calculator, "find_policy", lambda region, month: disallowed_policy)

    result = calculate_salary(_request(monthly_salary="105000"))

    assert result.bonus_recommended == "combined"
    assert result.bonus_separate_tax == Decimal("11790.00")
    assert result.estimated_tax == result.monthly_tax + result.bonus_combined_tax


def test_bonus_allowed_by_policy_selects_cheaper_separate_method(monkeypatch) -> None:
    allowed_policy = _policy(separate_allowed=True)
    monkeypatch.setattr(calculator, "find_policy", lambda region, month: allowed_policy)

    result = calculate_salary(_request(monthly_salary="105000"))

    assert result.bonus_recommended == "separate"
    assert result.estimated_tax == result.monthly_tax + result.bonus_separate_tax


def test_bonus_tax_compares_separate_and_combined_results() -> None:
    separate, combined, recommended = annual_bonus_tax(Decimal("120000"), Decimal("100000"))

    assert separate == Decimal("11790.00")
    assert combined == Decimal("19600.00")
    assert recommended == "separate"


def test_bonus_payout_month_controls_current_cash_and_tax(monkeypatch) -> None:
    policy = _policy(separate_allowed=True)
    monkeypatch.setattr(calculator, "find_policy", lambda region, month: policy)

    paid_now = calculate_salary(_request(monthly_salary="105000", bonus_payout_month="2026-12"))
    paid_later = calculate_salary(_request(monthly_salary="105000", bonus_payout_month="2027-01"))

    assert paid_now.bonus_paid_this_month == Decimal("120000.00")
    assert paid_now.estimated_tax == paid_now.monthly_tax + paid_now.bonus_separate_tax
    assert paid_later.bonus_paid_this_month == Decimal("0.00")
    assert paid_later.estimated_tax == paid_later.monthly_tax
    assert paid_later.annual_total_compensation == paid_now.annual_total_compensation


def test_zero_bonus_has_no_bonus_tax_or_recommendation() -> None:
    separate, combined, recommended = annual_bonus_tax(Decimal("0"), Decimal("100000"))

    assert separate == Decimal("0.00")
    assert combined == Decimal("0.00")
    assert recommended == "none"


def test_missing_policy_does_not_recommend_separate_bonus_tax(monkeypatch) -> None:
    monkeypatch.setattr(calculator, "find_policy", lambda region, month: None)

    result = calculate_salary(_request(monthly_salary="105000"))

    assert result.bonus_recommended == "combined"
