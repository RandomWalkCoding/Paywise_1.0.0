from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    calculation_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    work_city: str = Field(min_length=1, max_length=80)
    social_security_city: str = Field(min_length=1, max_length=80)
    housing_fund_city: str = Field(min_length=1, max_length=80)
    monthly_salary: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2)
    allowance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    performance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    annual_bonus: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    other_taxable_income: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    special_deduction: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    special_additional_deduction: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    social_security_base: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    housing_fund_base: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    cumulative_months: int = Field(default=1, ge=1, le=12)
    prior_cumulative_income: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    prior_cumulative_taxable_income: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    prior_cumulative_tax: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    other_after_tax_deduction: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    bonus_payout_month: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class CalculationResult(BaseModel):
    calculation_month: str
    policy_version: str
    confidence: Literal["policy_matched", "partially_estimated", "user_customized"]
    total_income: Decimal
    annual_total_compensation: Decimal
    bonus_paid_this_month: Decimal
    estimated_tax: Decimal
    estimated_social_security: Decimal
    estimated_housing_fund: Decimal
    social_security_base: Decimal
    housing_fund_base: Decimal
    employer_social_security: Decimal
    employer_housing_fund: Decimal
    monthly_tax: Decimal
    cumulative_tax: Decimal
    cumulative_taxable_income: Decimal
    tax_rate: Decimal
    quick_deduction: Decimal
    bonus_separate_tax: Decimal
    bonus_combined_tax: Decimal
    bonus_separate_allowed: bool
    bonus_recommended: Literal["separate", "combined", "none"]
    take_home_cash: Decimal
    personal_asset_increase: Decimal
    assumptions: list[str]
    needs_confirmation: list[str]
    breakdown: list[str]
    policy_source: str
    is_mock: bool = False
