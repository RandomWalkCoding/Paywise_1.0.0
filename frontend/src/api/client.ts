export type HealthResponse = {
  status: "ok";
  service: string;
  version: string;
  timestamp: string;
};

export type CalculationRequest = {
  calculation_month: string;
  work_city: string;
  social_security_city: string;
  housing_fund_city: string;
  monthly_salary: string;
  allowance: string;
  performance: string;
  annual_bonus: string;
  other_taxable_income: string;
  special_deduction: string;
  special_additional_deduction: string;
  social_security_base?: string;
  housing_fund_base?: string;
  cumulative_months?: number;
  prior_cumulative_income?: string;
  prior_cumulative_taxable_income?: string;
  prior_cumulative_tax?: string;
  other_after_tax_deduction?: string;
  bonus_payout_month?: string;
};

export type CalculationResult = {
  calculation_month: string;
  policy_version: string;
  confidence: string;
  total_income: number;
  annual_total_compensation: number;
  bonus_paid_this_month: number;
  estimated_tax: number;
  estimated_social_security: number;
  estimated_housing_fund: number;
  social_security_base: number;
  housing_fund_base: number;
  employer_social_security: number;
  employer_housing_fund: number;
  monthly_tax: number;
  cumulative_tax: number;
  cumulative_taxable_income: number;
  tax_rate: number;
  quick_deduction: number;
  bonus_separate_tax: number;
  bonus_combined_tax: number;
  bonus_separate_allowed: boolean;
  bonus_recommended: "separate" | "combined" | "none";
  take_home_cash: number;
  personal_asset_increase: number;
  assumptions: string[];
  needs_confirmation: string[];
  breakdown: string[];
  policy_source: string;
  is_mock: boolean;
};

export type ScenarioSummary = {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  engine_version: string;
  policy_version: string;
  calculation_month: string;
  total_income: number;
  take_home_cash: number;
  annual_total_compensation: number;
  deleted_at: string | null;
};

export type Scenario = ScenarioSummary & {
  input_snapshot: CalculationRequest;
  result_snapshot: CalculationResult;
  result_summary: Record<string, number>;
};

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new ApiError(response.status, `API request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ApiError(response.status, `API request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

async function patchJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status, `API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

async function deleteJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, { method: "DELETE", headers: { Accept: "application/json" } });
  if (!response.ok) throw new ApiError(response.status, `API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const apiClient = {
  health: () => getJson<HealthResponse>("/health"),
  calculate: (request: CalculationRequest) => postJson<CalculationResult>("/calculations", request),
  saveScenario: (name: string, input: CalculationRequest) => postJson<Scenario>("/scenarios", { name, input }),
  listScenarios: (includeDeleted = false) => getJson<ScenarioSummary[]>(`/scenarios?include_deleted=${includeDeleted}`),
  getScenario: (id: string) => getJson<Scenario>(`/scenarios/${encodeURIComponent(id)}`),
  renameScenario: (id: string, name: string) => patchJson<ScenarioSummary>(`/scenarios/${encodeURIComponent(id)}`, { name }),
  deleteScenario: (id: string) => deleteJson<ScenarioSummary>(`/scenarios/${encodeURIComponent(id)}`),
  restoreScenario: (id: string) => postJson<ScenarioSummary>(`/scenarios/${encodeURIComponent(id)}/restore`, {}),
};
