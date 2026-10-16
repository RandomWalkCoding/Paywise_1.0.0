from fastapi import APIRouter, HTTPException, Query, status

from app.models.scenario import ScenarioCreateRequest, ScenarioRenameRequest, ScenarioResponse, ScenarioSummary
from app.services.scenarios import scenario_store

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(payload: ScenarioCreateRequest) -> ScenarioResponse:
    # The server calculates and stores the result; clients cannot forge a snapshot.
    assert payload.calculation is not None
    return scenario_store.create(payload.name, payload.calculation).to_response()


@router.get("", response_model=list[ScenarioSummary])
def list_scenarios(include_deleted: bool = Query(default=False)) -> list[ScenarioSummary]:
    return [record.to_summary() for record in scenario_store.list(include_deleted=include_deleted)]


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: str) -> ScenarioResponse:
    record = scenario_store.get(scenario_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SCENARIO_NOT_FOUND", "message": "方案不存在"},
        )
    return record.to_response()


def _missing(scenario_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "SCENARIO_NOT_FOUND", "message": f"方案不存在：{scenario_id}"},
    )


@router.patch("/{scenario_id}", response_model=ScenarioSummary)
def rename_scenario(scenario_id: str, payload: ScenarioRenameRequest) -> ScenarioSummary:
    record = scenario_store.rename(scenario_id, payload.name)
    if record is None:
        raise _missing(scenario_id)
    return record.to_summary()


@router.delete("/{scenario_id}", response_model=ScenarioSummary)
def delete_scenario(scenario_id: str) -> ScenarioSummary:
    record = scenario_store.soft_delete(scenario_id)
    if record is None:
        raise _missing(scenario_id)
    return record.to_summary()


@router.post("/{scenario_id}/restore", response_model=ScenarioSummary)
def restore_scenario(scenario_id: str) -> ScenarioSummary:
    record = scenario_store.restore(scenario_id)
    if record is None:
        raise _missing(scenario_id)
    return record.to_summary()
