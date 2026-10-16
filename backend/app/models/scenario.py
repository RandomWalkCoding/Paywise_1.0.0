from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.models.calculation import CalculationRequest, CalculationResult


class ScenarioCreateRequest(BaseModel):
    """Payload for saving a calculation as a named scenario.

    ``input`` is accepted as an alias for clients that use the terminology from
    the product spec; ``calculation`` keeps the calculation API vocabulary.
    """

    name: str = Field(min_length=1, max_length=120)
    calculation: CalculationRequest | None = None
    input: CalculationRequest | None = None

    @model_validator(mode="after")
    def require_calculation(self) -> "ScenarioCreateRequest":
        if self.calculation is None and self.input is None:
            raise ValueError("calculation or input is required")
        if self.calculation is None:
            self.calculation = self.input
        return self


class ScenarioRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ScenarioSummary(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    engine_version: str
    policy_version: str
    calculation_month: str
    total_income: Decimal
    take_home_cash: Decimal
    annual_total_compensation: Decimal
    deleted_at: datetime | None = None


class ScenarioResponse(ScenarioSummary):
    input_snapshot: CalculationRequest
    result_snapshot: CalculationResult
    result_summary: dict[str, Any]
