from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from app.models.calculation import CalculationRequest, CalculationResult
from app.models.scenario import ScenarioResponse, ScenarioSummary
from app.services.calculator import calculate_salary

ENGINE_VERSION = "calculator-0.2.0"


@dataclass(frozen=True)
class ScenarioRecord:
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    engine_version: str
    input_snapshot: CalculationRequest
    result_snapshot: CalculationResult
    deleted_at: datetime | None = None

    @property
    def summary(self) -> dict[str, object]:
        result = self.result_snapshot
        return {
            "total_income": result.total_income,
            "take_home_cash": result.take_home_cash,
            "annual_total_compensation": result.annual_total_compensation,
            "estimated_tax": result.estimated_tax,
            "estimated_social_security": result.estimated_social_security,
            "estimated_housing_fund": result.estimated_housing_fund,
        }

    def to_response(self) -> ScenarioResponse:
        result = self.result_snapshot
        return ScenarioResponse(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            updated_at=self.updated_at,
            engine_version=self.engine_version,
            policy_version=result.policy_version,
            calculation_month=result.calculation_month,
            total_income=result.total_income,
            take_home_cash=result.take_home_cash,
            annual_total_compensation=result.annual_total_compensation,
            deleted_at=self.deleted_at,
            input_snapshot=self.input_snapshot,
            result_snapshot=result,
            result_summary=self.summary,
        )

    def to_summary(self) -> ScenarioSummary:
        result = self.result_snapshot
        return ScenarioSummary(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            updated_at=self.updated_at,
            engine_version=self.engine_version,
            policy_version=result.policy_version,
            calculation_month=result.calculation_month,
            total_income=result.total_income,
            take_home_cash=result.take_home_cash,
            annual_total_compensation=result.annual_total_compensation,
            deleted_at=self.deleted_at,
        )


class ScenarioStore:
    """Process-local scenario repository used until the database layer lands.

    The complete input and result are kept together, so reading a saved scenario
    never recalculates it against a newer policy.
    """

    def __init__(self) -> None:
        self._records: dict[str, ScenarioRecord] = {}
        self._lock = RLock()

    def create(self, name: str, request: CalculationRequest) -> ScenarioRecord:
        now = datetime.now(timezone.utc)
        record = ScenarioRecord(
            id=str(uuid4()),
            name=name.strip(),
            created_at=now,
            updated_at=now,
            engine_version=ENGINE_VERSION,
            input_snapshot=request.model_copy(deep=True),
            result_snapshot=calculate_salary(request),
        )
        with self._lock:
            self._records[record.id] = record
        return record

    def list(self, include_deleted: bool = False) -> list[ScenarioRecord]:
        with self._lock:
            records = self._records.values() if include_deleted else (
                record for record in self._records.values() if record.deleted_at is None
            )
            return sorted(records, key=lambda item: item.created_at, reverse=True)

    def get(self, scenario_id: str) -> ScenarioRecord | None:
        with self._lock:
            return self._records.get(scenario_id)

    def rename(self, scenario_id: str, name: str) -> ScenarioRecord | None:
        with self._lock:
            record = self._records.get(scenario_id)
            if record is None:
                return None
            updated = replace(record, name=name.strip(), updated_at=datetime.now(timezone.utc))
            self._records[scenario_id] = updated
            return updated

    def soft_delete(self, scenario_id: str) -> ScenarioRecord | None:
        with self._lock:
            record = self._records.get(scenario_id)
            if record is None:
                return None
            updated = replace(record, deleted_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            self._records[scenario_id] = updated
            return updated

    def restore(self, scenario_id: str) -> ScenarioRecord | None:
        with self._lock:
            record = self._records.get(scenario_id)
            if record is None:
                return None
            updated = replace(record, deleted_at=None, updated_at=datetime.now(timezone.utc))
            self._records[scenario_id] = updated
            return updated


scenario_store = ScenarioStore()
