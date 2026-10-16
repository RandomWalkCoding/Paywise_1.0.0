import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { apiClient, CalculationResult, Scenario, ScenarioSummary } from "../api/client";

const MAX_COMPARE = 4;

type ComparisonMetric = {
  label: string;
  hint: string;
  value: (scenario: Scenario) => number;
};

const money = (value: number) => `¥${Number(value).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const annualTotalPackage = (result: CalculationResult) => Number(result.annual_total_compensation) + (Number(result.employer_social_security) + Number(result.employer_housing_fund)) * 12;

const metrics: ComparisonMetric[] = [
  { label: "月到手收入", hint: "本月实际可支配现金", value: (scenario) => scenario.result_snapshot.take_home_cash },
  { label: "年收入", hint: "税前收入含年终奖", value: (scenario) => scenario.result_snapshot.annual_total_compensation },
  { label: "本月个税", hint: "本月预估个人所得税", value: (scenario) => scenario.result_snapshot.estimated_tax },
  { label: "个人公积金", hint: "本月个人缴存", value: (scenario) => scenario.result_snapshot.estimated_housing_fund },
  { label: "年度总包", hint: "含雇主全年社保和公积金", value: (scenario) => annualTotalPackage(scenario.result_snapshot) },
];

export function ComparisonPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [details, setDetails] = useState<Record<string, Scenario>>({});
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function loadScenarios() {
      setLoading(true);
      setError("");
      try {
        const result = await apiClient.listScenarios();
        if (!active) return;
        setScenarios(result.filter((scenario) => !scenario.deleted_at));
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "方案暂时无法加载，请稍后重试。");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadScenarios();
    return () => { active = false; };
  }, []);

  const selectedSummaries = useMemo(() => selectedIds.map((id) => scenarios.find((scenario) => scenario.id === id)).filter((scenario): scenario is ScenarioSummary => Boolean(scenario)), [scenarios, selectedIds]);

  async function toggleScenario(id: string) {
    setError("");
    if (selectedIds.includes(id)) {
      setSelectedIds((current) => current.filter((item) => item !== id));
      return;
    }
    if (selectedIds.length >= MAX_COMPARE) {
      setError(`最多选择 ${MAX_COMPARE} 个方案进行对比。`);
      return;
    }
    setSelectedIds((current) => [...current, id]);
    if (details[id]) return;
    setLoadingDetails(true);
    try {
      const detail = await apiClient.getScenario(id);
      setDetails((current) => ({ ...current, [id]: detail }));
    } catch (err) {
      setSelectedIds((current) => current.filter((item) => item !== id));
      setError(err instanceof Error ? err.message : "方案详情暂时无法加载，请稍后重试。");
    } finally {
      setLoadingDetails(false);
    }
  }

  function selectAll() {
    const nextIds = scenarios.slice(0, MAX_COMPARE).map((scenario) => scenario.id);
    setSelectedIds(nextIds);
    setError("");
    const missing = nextIds.filter((id) => !details[id]);
    if (missing.length === 0) return;
    setLoadingDetails(true);
    void Promise.all(missing.map((id) => apiClient.getScenario(id)))
      .then((loaded) => setDetails((current) => loaded.reduce((next, detail) => ({ ...next, [detail.id]: detail }), current)))
      .catch((err) => {
        setSelectedIds((current) => current.filter((id) => !missing.includes(id)));
        setError(err instanceof Error ? err.message : "方案详情暂时无法加载，请稍后重试。");
      })
      .finally(() => setLoadingDetails(false));
  }

  if (loading) return <ComparisonShell><div className="comparison-state" role="status"><span className="state-mark">…</span><h2>正在读取方案</h2><p className="muted">马上就能开始比较。</p></div></ComparisonShell>;
  if (error && scenarios.length === 0) return <ComparisonShell><div className="comparison-state" role="alert"><span className="state-mark state-mark-error">!</span><h2>方案加载失败</h2><p className="muted">{error}</p><Link className="button" to="/calculator">回到计算器</Link></div></ComparisonShell>;
  if (scenarios.length === 0) return <ComparisonShell><div className="comparison-state"><span className="state-mark">＋</span><h2>还没有可比较的方案</h2><p className="muted">先在计算器里完成一次计算并保存，回来就能把不同 Offer 放在一起看。</p><Link className="button" to="/calculator">创建第一个方案</Link></div></ComparisonShell>;

  return <ComparisonShell>
    <div className="comparison-header">
      <div><p className="eyebrow">OFFER / COMPARE</p><h1>把 Offer 放在同一张表里。</h1><p className="muted">选中最多 4 个方案，快速看清到手现金、税费、公积金和年度总包。</p></div>
      <div className="comparison-summary"><strong>{selectedIds.length}<span>/ {MAX_COMPARE}</span></strong><small>已选方案</small></div>
    </div>
    <div className="comparison-workspace"><section className="comparison-picker" aria-labelledby="picker-heading">
      <div className="section-heading"><div><p className="eyebrow">SAVED OFFERS</p><h2 id="picker-heading">选择要比较的方案</h2></div><button className="text-button" type="button" onClick={selectAll} disabled={scenarios.length === 0}>选择前 {Math.min(MAX_COMPARE, scenarios.length)} 个</button></div>
      <div className="offer-picker-list">{scenarios.map((scenario) => <label className={`offer-picker-row${selectedIds.includes(scenario.id) ? " is-selected" : ""}`} key={scenario.id}><input type="checkbox" checked={selectedIds.includes(scenario.id)} onChange={() => void toggleScenario(scenario.id)} /><span className="offer-check" aria-hidden="true">✓</span><span className="offer-picker-copy"><strong>{scenario.name}</strong><small>{scenario.calculation_month} · 月到手 {money(scenario.take_home_cash)}</small></span><span className="offer-picker-total">{money(scenario.annual_total_compensation)}<small>年收入</small></span></label>)}</div>
      {error && <p className="error" role="alert">{error}</p>}
    </section>
    {selectedIds.length === 0 ? <div className="comparison-state comparison-state-inline"><span className="state-mark">↔</span><h2>选择方案开始比较</h2><p className="muted">可以先选 2 个方案，也可以一次选择最多 4 个。</p></div> : <section className="comparison-table-wrap" aria-labelledby="table-heading"><div className="comparison-table-heading"><div><p className="eyebrow">DECISION TABLE</p><h2 id="table-heading">方案差异</h2></div>{loadingDetails && <span className="loading-note" role="status">正在读取详情…</span>}</div><div className="comparison-table-scroll"><table className="comparison-table"><thead><tr><th scope="col">指标</th>{selectedSummaries.map((scenario) => <th scope="col" key={scenario.id}><span className="table-scenario-name">{scenario.name}</span><small>{scenario.calculation_month} · {scenario.policy_version}</small></th>)}</tr></thead><tbody>{metrics.map((metric) => <tr key={metric.label}><th scope="row"><span>{metric.label}</span><small>{metric.hint}</small></th>{selectedSummaries.map((summary) => { const detail = details[summary.id]; return <td key={summary.id}>{detail ? money(metric.value(detail)) : <span className="value-skeleton">加载中</span>}</td>; })}</tr>)}</tbody></table></div><p className="comparison-footnote">总包按税前年度收入加雇主全年社保、公积金估算；结果沿用各方案保存时的政策版本。</p></section>}
    </div>
  </ComparisonShell>;
}

function ComparisonShell({ children }: { children: ReactNode }) { return <section className="page comparison-page">{children}</section>; }
