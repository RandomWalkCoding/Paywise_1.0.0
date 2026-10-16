from fastapi import APIRouter

from app.models.calculation import CalculationRequest, CalculationResult
from app.services.calculator import calculate_salary

router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("", response_model=CalculationResult)
def calculate(request: CalculationRequest) -> CalculationResult:
    return calculate_salary(request)
