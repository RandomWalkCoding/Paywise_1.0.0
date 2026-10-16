from datetime import date, datetime, timezone
from decimal import Decimal
from threading import RLock

from app.models.policy import PolicyImportRequest, PolicyReviewRequest, PolicyVersion

EXAMPLE_POLICIES = [
    PolicyVersion(
        version="example-sh-2026-01", region_code="SH", region_name="上海", effective_from=date(2026, 1, 1),
        social_security_min_base=Decimal("7380"), social_security_max_base=Decimal("36921"),
        social_security_employee_rate=Decimal("0.105"), social_security_employer_rate=Decimal("0.265"),
        housing_fund_min_base=Decimal("2690"), housing_fund_max_base=Decimal("36921"),
        housing_fund_employee_rate=Decimal("0.07"), housing_fund_employer_rate=Decimal("0.07"),
        source_name="示例政策数据（待官方审核）", source_url="https://www.gov.cn/",
    ),
    PolicyVersion(
        version="example-bj-2026-01", region_code="BJ", region_name="北京", effective_from=date(2026, 1, 1),
        social_security_min_base=Decimal("6821"), social_security_max_base=Decimal("35283"),
        social_security_employee_rate=Decimal("0.105"), social_security_employer_rate=Decimal("0.265"),
        housing_fund_min_base=Decimal("2420"), housing_fund_max_base=Decimal("35283"),
        housing_fund_employee_rate=Decimal("0.07"), housing_fund_employer_rate=Decimal("0.07"),
        source_name="示例政策数据（待官方审核）", source_url="https://www.gov.cn/",
    ),
]


def _matching_policy(
    policies: list[PolicyVersion], region_code: str, month: str
) -> PolicyVersion | None:
    try:
        month_date = date.fromisoformat(f"{month.strip()}-01")
    except ValueError:
        return None

    candidates = [
        policy
        for policy in policies
        if policy.region_code.strip().upper() == region_code.strip().upper()
        and policy.effective_from <= month_date
        and (policy.effective_to is None or month_date <= policy.effective_to)
    ]
    return max(candidates, key=lambda policy: policy.effective_from, default=None)


class PolicyStore:
    """Process-local policy intake store pending a persistent repository.

    Imported records begin in ``pending`` status and are deliberately excluded
    from formal policy matching until a reviewer approves them.
    """

    def __init__(self) -> None:
        self._records: dict[str, PolicyVersion] = {}
        self._lock = RLock()

    def import_policy(self, request: PolicyImportRequest) -> PolicyVersion:
        with self._lock:
            example_versions = {policy.version for policy in EXAMPLE_POLICIES}
            if request.policy.version in self._records or request.policy.version in example_versions:
                raise ValueError("POLICY_VERSION_EXISTS")
            record = PolicyVersion.model_validate(
                request.policy.model_dump()
                | {
                    "review_status": "pending",
                    "reviewed": False,
                    "reviewed_at": None,
                    "reviewed_by": None,
                    "review_note": None,
                    "formal_policy": False,
                    "is_example": False,
                    "imported_at": datetime.now(timezone.utc),
                    "imported_by": request.imported_by,
                }
            )
            self._records[record.version] = record
            return record

    def review(self, version: str, request: PolicyReviewRequest) -> PolicyVersion | None:
        with self._lock:
            record = self._records.get(version)
            if record is None:
                return None
            reviewed_at = datetime.now(timezone.utc)
            updated = PolicyVersion.model_validate(
                record.model_dump()
                | {
                    "review_status": request.review_status,
                    "reviewed": request.review_status == "approved",
                    "reviewed_at": reviewed_at,
                    "reviewed_by": request.reviewed_by,
                    "review_note": request.review_note,
                    "formal_policy": request.review_status == "approved",
                }
            )
            self._records[version] = updated
            return updated

    def list_imports(self) -> list[PolicyVersion]:
        with self._lock:
            return sorted(
                self._records.values(),
                key=lambda policy: policy.imported_at
                or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )

    def clear_imports(self) -> None:
        """Clear process-local imports for test setup and controlled resets."""
        with self._lock:
            self._records.clear()

    def find_formal_policy(self, region_code: str, month: str) -> PolicyVersion | None:
        with self._lock:
            formal = [
                policy
                for policy in self._records.values()
                if policy.formal_policy and policy.review_status == "approved"
            ]
        return _matching_policy(formal, region_code, month)


policy_store = PolicyStore()


def find_policy(region_code: str, month: str) -> PolicyVersion | None:
    """Find an approved import, or use clearly labelled example data for estimates."""
    formal_policy = policy_store.find_formal_policy(region_code, month)
    return formal_policy or _matching_policy(EXAMPLE_POLICIES, region_code, month)
