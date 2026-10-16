from fastapi import APIRouter, HTTPException, Query

from app.models.policy import PolicyImportRequest, PolicyReviewRequest, PolicyVersion
from app.services.policies import find_policy, policy_store

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=PolicyVersion)
def get_policy(region_code: str = Query(min_length=2, max_length=10), month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")) -> PolicyVersion:
    policy = find_policy(region_code, month)
    if policy is None:
        raise HTTPException(status_code=404, detail={"code": "POLICY_NOT_FOUND", "message": "暂无匹配政策"})
    return policy


@router.get("/imports", response_model=list[PolicyVersion])
def list_policy_imports() -> list[PolicyVersion]:
    return policy_store.list_imports()


@router.post("/imports", response_model=PolicyVersion, status_code=201)
def import_policy(request: PolicyImportRequest) -> PolicyVersion:
    try:
        return policy_store.import_policy(request)
    except ValueError as exc:
        if str(exc) == "POLICY_VERSION_EXISTS":
            raise HTTPException(status_code=409, detail={"code": "POLICY_VERSION_EXISTS", "message": "政策版本已存在"}) from exc
        raise


@router.patch("/imports/{version}/review", response_model=PolicyVersion)
def review_policy(version: str, request: PolicyReviewRequest) -> PolicyVersion:
    policy = policy_store.review(version, request)
    if policy is None:
        raise HTTPException(status_code=404, detail={"code": "POLICY_NOT_FOUND", "message": "暂无该导入政策"})
    return policy
