from decimal import Decimal, ROUND_HALF_UP

from app.models.calculation import CalculationRequest, CalculationResult
from app.services.policies import find_policy

TAX_BRACKETS = (
    (Decimal("36000"), Decimal("0.03"), Decimal("0")),
    (Decimal("144000"), Decimal("0.10"), Decimal("2520")),
    (Decimal("300000"), Decimal("0.20"), Decimal("16920")),
    (Decimal("420000"), Decimal("0.25"), Decimal("31920")),
    (Decimal("660000"), Decimal("0.30"), Decimal("52920")),
    (Decimal("960000"), Decimal("0.35"), Decimal("85920")),
    (None, Decimal("0.45"), Decimal("181920")),
)

# 年终奖单独计税使用月度换算金额和月度速算扣除数判断税率档位。
BONUS_TAX_BRACKETS = tuple(
    (
        ceiling / Decimal("12") if ceiling is not None else None,
        rate,
        quick / Decimal("12"),
    )
    for ceiling, rate, quick in TAX_BRACKETS
)


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def tax_for_income(income: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    taxable = max(Decimal("0"), income)
    for ceiling, rate, quick in TAX_BRACKETS:
        if ceiling is None or taxable <= ceiling:
            return money(taxable * rate - quick), rate, quick
    return Decimal("0"), Decimal("0"), Decimal("0")


def bonus_tax_bracket(monthly_equivalent: Decimal) -> tuple[Decimal, Decimal]:
    taxable = max(Decimal("0"), monthly_equivalent)
    for ceiling, rate, quick in BONUS_TAX_BRACKETS:
        if ceiling is None or taxable <= ceiling:
            return rate, quick
    return Decimal("0"), Decimal("0")


def annual_bonus_tax(
    bonus: Decimal, annual_taxable: Decimal, separate_allowed: bool = True
) -> tuple[Decimal, Decimal, str]:
    if bonus <= 0:
        return Decimal("0.00"), Decimal("0.00"), "none"
    # 单独计税按月度换算确定适用档位，再用该档税率与速算扣除数计算全额奖金税额。
    monthly_equivalent = bonus / Decimal("12")
    rate, quick = bonus_tax_bracket(monthly_equivalent)
    separate = money(max(Decimal("0"), bonus * rate - quick))
    combined = money(
        max(
            Decimal("0"),
            tax_for_income(annual_taxable + bonus)[0] - tax_for_income(annual_taxable)[0],
        )
    )
    if not separate_allowed:
        return separate, combined, "combined"
    return separate, combined, "separate" if separate <= combined else "combined"


def resolve_region_code(city: str) -> str:
    normalized = city.strip().upper()
    if normalized in {"SH", "SHANGHAI", "上海市"} or "上海" in city:
        return "SH"
    if normalized in {"BJ", "BEIJING", "北京市"} or "北京" in city:
        return "BJ"
    return ""


def calculate_salary(request: CalculationRequest) -> "CalculationResult":
    social_region = resolve_region_code(request.social_security_city)
    fund_region = resolve_region_code(request.housing_fund_city)
    social_policy = find_policy(social_region, request.calculation_month)
    fund_policy = find_policy(fund_region, request.calculation_month)
    total_income = (
        request.monthly_salary
        + request.allowance
        + request.performance
        + request.other_taxable_income
    )
    social_base = request.social_security_base if request.social_security_base is not None else total_income
    fund_base = request.housing_fund_base if request.housing_fund_base is not None else total_income
    social = fund = employer_social = employer_fund = Decimal("0")
    social_applied_base, fund_applied_base = social_base, fund_base
    if social_policy:
        social_applied_base = min(max(social_base, social_policy.social_security_min_base), social_policy.social_security_max_base)
        social = social_applied_base * social_policy.social_security_employee_rate
        employer_social = social_applied_base * social_policy.social_security_employer_rate
    if fund_policy:
        fund_applied_base = min(max(fund_base, fund_policy.housing_fund_min_base), fund_policy.housing_fund_max_base)
        fund = fund_applied_base * fund_policy.housing_fund_employee_rate
        employer_fund = fund_applied_base * fund_policy.housing_fund_employer_rate
    months = request.cumulative_months
    basic_deduction = Decimal("5000")
    monthly_deductions = social + fund + request.special_deduction + request.special_additional_deduction
    if request.prior_cumulative_taxable_income is not None:
        taxable = max(
            Decimal("0"),
            request.prior_cumulative_taxable_income + total_income - basic_deduction - monthly_deductions,
        )
        prior_taxable = request.prior_cumulative_taxable_income
    else:
        # Without a payroll snapshot, assume the current month's income and deductions were stable.
        prior_income = (
            request.prior_cumulative_income
            if request.prior_cumulative_income is not None
            else total_income * (months - 1)
        )
        cumulative_income = prior_income + total_income
        taxable = max(Decimal("0"), cumulative_income - basic_deduction * months - monthly_deductions * months)
        prior_taxable = max(
            Decimal("0"), prior_income - basic_deduction * (months - 1) - monthly_deductions * (months - 1)
        )
    tax, rate, quick = tax_for_income(taxable)
    prior_tax = request.prior_cumulative_tax
    if prior_tax is None:
        prior_tax = tax_for_income(prior_taxable)[0]
    monthly_tax = max(Decimal("0"), tax - prior_tax)
    payout_month = request.bonus_payout_month or request.calculation_month
    bonus_paid_this_month = request.annual_bonus if payout_month == request.calculation_month else Decimal("0")
    matched_policies = [policy for policy in (social_policy, fund_policy) if policy is not None]
    bonus_separate_allowed = bool(matched_policies) and all(
        policy.annual_bonus_separate_allowed for policy in matched_policies
    )
    bonus_separate, bonus_combined, bonus_recommended = annual_bonus_tax(
        request.annual_bonus,
        taxable,
        separate_allowed=bonus_separate_allowed,
    )
    bonus_tax = (
        bonus_separate if bonus_recommended == "separate" else bonus_combined
    ) if bonus_paid_this_month > 0 else Decimal("0")
    custom_base = request.social_security_base is not None or request.housing_fund_base is not None
    matched_policies = [policy for policy in (social_policy, fund_policy) if policy is not None]
    all_reviewed = bool(matched_policies) and all(policy.reviewed for policy in matched_policies)
    confidence = "user_customized" if custom_base else ("policy_matched" if all_reviewed else "partially_estimated")
    confirmations = []
    if not custom_base:
        confirmations.append("请核对社保和公积金实际缴费基数；当前使用工资收入推算")
    if request.annual_bonus > 0 and request.bonus_payout_month is None:
        confirmations.append("请确认年终奖发放月份；未填写时按计算月份处理")
    if social_policy is None:
        confirmations.insert(0, "社保缴纳地暂无匹配政策，社保缴费暂按 0 估算")
    if fund_policy is None:
        confirmations.insert(0, "公积金缴纳地暂无匹配政策，公积金缴费暂按 0 估算")
    if request.prior_cumulative_taxable_income is None and months > 1:
        confirmations.append("未提供此前累计应纳税所得额，按当前收入和扣除稳定估算")
    if social_policy and fund_policy and social_policy.version == fund_policy.version:
        policy_version = social_policy.version
    else:
        policy_versions = []
        if social_policy:
            policy_versions.append(f"社保 {social_policy.version}")
        if fund_policy:
            policy_versions.append(f"公积金 {fund_policy.version}")
        policy_version = "; ".join(policy_versions) if policy_versions else "unmatched"
    policy_source_details = list(
        dict.fromkeys(
            f"{policy.source_name}（{policy.source_url}）"
            for policy in (social_policy, fund_policy) if policy is not None
        )
    )
    policy_source = "；".join(policy_source_details) if policy_source_details else "未匹配政策"
    social_base_label = "用户提供" if request.social_security_base is not None else "系统按收入推算"
    fund_base_label = "用户提供" if request.housing_fund_base is not None else "系统按收入推算"
    social_base_explanation = (
        f"社保基数（{social_base_label}）为 {money(social_base)}，限制在 {money(social_policy.social_security_min_base)} 至 "
        f"{money(social_policy.social_security_max_base)}，实际采用 {money(social_applied_base)}"
        if social_policy else "社保无匹配政策，未计入缴费"
    )
    fund_base_explanation = (
        f"公积金基数（{fund_base_label}）为 {money(fund_base)}，限制在 {money(fund_policy.housing_fund_min_base)} 至 "
        f"{money(fund_policy.housing_fund_max_base)}，实际采用 {money(fund_applied_base)}"
        if fund_policy else "公积金无匹配政策，未计入缴费"
    )
    bonus_explanation = (
        f"年终奖单独计税 {money(bonus_separate)}，并入综合所得 {money(bonus_combined)}，"
        f"当前推荐 {bonus_recommended}"
        if request.annual_bonus > 0 else "本次未计入年终奖"
    )
    return CalculationResult(
        calculation_month=request.calculation_month,
        policy_version=policy_version,
        confidence=confidence,
        total_income=money(total_income),
        annual_total_compensation=money(total_income * Decimal("12") + request.annual_bonus),
        bonus_paid_this_month=money(bonus_paid_this_month),
        estimated_tax=money(monthly_tax + bonus_tax),
        estimated_social_security=money(social),
        estimated_housing_fund=money(fund),
        social_security_base=money(social_applied_base),
        housing_fund_base=money(fund_applied_base),
        employer_social_security=money(employer_social),
        employer_housing_fund=money(employer_fund),
        monthly_tax=money(monthly_tax),
        cumulative_tax=money(tax),
        cumulative_taxable_income=money(taxable),
        tax_rate=rate,
        quick_deduction=quick,
        bonus_separate_tax=bonus_separate,
        bonus_combined_tax=bonus_combined,
        bonus_separate_allowed=bonus_separate_allowed,
        bonus_recommended=bonus_recommended,
        take_home_cash=money(
            total_income
            + bonus_paid_this_month
            - social
            - fund
            - monthly_tax
            - bonus_tax
            - request.other_after_tax_deduction
        ),
        personal_asset_increase=money(
            total_income + bonus_paid_this_month - social - monthly_tax - bonus_tax
            - request.other_after_tax_deduction
        ),
        assumptions=[f"按居民个人累计预扣口径估算，累计第 {months} 月", "当前政策数据为示例数据，计算结果仅供参考"],
        needs_confirmation=confirmations,
        breakdown=[
            f"累计第 {months} 月：累计收入扣除基本减除费用、社保公积金和专项扣除后，"
            f"应纳税所得额 {money(taxable)} × 税率 {rate} - 速算扣除数 {quick} = 累计税额 {money(tax)}",
            f"本月预扣税 = 累计税额 {money(tax)} - 既往累计已扣税 {money(prior_tax)} = {money(monthly_tax)}",
            social_base_explanation,
            fund_base_explanation,
            f"个人社保 {money(social)}，公司社保 {money(employer_social)}，个人公积金 {money(fund)}，公司公积金 {money(employer_fund)}",
            bonus_explanation,
            f"个人资产增加 = 到手现金 + 个人公积金（{money(fund)}）",
        ],
        policy_source=policy_source,
    )
