from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PolicyVersion(BaseModel):
    version: str
    region_code: str
    region_name: str
    effective_from: date
    effective_to: date | None = None
    social_security_min_base: Decimal = Field(gt=0)
    social_security_max_base: Decimal = Field(gt=0)
    social_security_employee_rate: Decimal = Field(ge=0, le=1)
    social_security_employer_rate: Decimal = Field(ge=0, le=1)
    housing_fund_min_base: Decimal = Field(gt=0)
    housing_fund_max_base: Decimal = Field(gt=0)
    housing_fund_employee_rate: Decimal = Field(ge=0, le=1)
    housing_fund_employer_rate: Decimal = Field(ge=0, le=1)
    annual_bonus_separate_allowed: bool = True
    source_name: str = Field(min_length=1, max_length=200)
    source_url: str = Field(min_length=8, max_length=2_000, pattern=r"^https?://")
    source_published_at: date | None = None
    source_retrieved_at: datetime | None = None
    imported_at: datetime | None = None
    imported_by: str | None = Field(default=None, min_length=1, max_length=120)
    review_status: Literal["pending", "approved", "rejected"] = "pending"
    reviewed: bool = False
    reviewed_at: datetime | None = None
    reviewed_by: str | None = Field(default=None, min_length=1, max_length=120)
    review_note: str | None = Field(default=None, max_length=1_000)
    formal_policy: bool = False
    is_example: bool = True

    @model_validator(mode="after")
    def validate_policy(self) -> "PolicyVersion":
        if self.social_security_min_base > self.social_security_max_base:
            raise ValueError("social_security_min_base cannot exceed social_security_max_base")
        if self.housing_fund_min_base > self.housing_fund_max_base:
            raise ValueError("housing_fund_min_base cannot exceed housing_fund_max_base")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be earlier than effective_from")
        if self.review_status == "approved":
            if not self.reviewed or not self.formal_policy:
                raise ValueError("approved policies must be reviewed and formally usable")
            if self.reviewed_at is None or self.reviewed_by is None:
                raise ValueError("approved policies require reviewer and review timestamp")
        elif self.formal_policy:
            raise ValueError("only approved policies can be formally usable")
        return self


class PolicyImportRequest(BaseModel):
    policy: PolicyVersion
    imported_by: str = Field(min_length=1, max_length=120)


class PolicyReviewRequest(BaseModel):
    review_status: Literal["approved", "rejected"]
    reviewed_by: str = Field(min_length=1, max_length=120)
    review_note: str | None = Field(default=None, max_length=1_000)
