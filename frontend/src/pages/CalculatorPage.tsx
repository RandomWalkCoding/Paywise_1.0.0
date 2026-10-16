import { FormEvent, useEffect, useState } from "react";
import { apiClient, CalculationRequest, CalculationResult, Scenario, ScenarioSummary } from "../api/client";

type FormState = CalculationRequest;
const initial: FormState = { calculation_month: "2026-10", work_city: "上海", social_security_city: "上海", housing_fund_city: "上海", monthly_salary: "20000", allowance: "0", performance: "0", annual_bonus: "0", other_taxable_income: "0", special_deduction: "0", special_additional_deduction: "0", cumulative_months: 1, prior_cumulative_income: "0", other_after_tax_deduction: "0", bonus_payout_month: "2026-10" };
const fields: Array<[keyof FormState, string]> = [["monthly_salary", "月固定工资"], ["allowance", "津贴"], ["performance", "绩效"], ["annual_bonus", "年终奖"], ["other_taxable_income", "其他应税收入"], ["special_deduction", "专项扣除"], ["special_additional_deduction", "专项附加扣除"], ["social_security_base", "社保实际基数（可选）"], ["housing_fund_base", "公积金实际基数（可选）"], ["other_after_tax_deduction", "其他税后扣款"]];
const money = (value: number | string) => `¥${Number(value).toFixed(2)}`;
const confidenceLabel = (value: string) => value === "user_customized" ? "用户自定义" : value === "policy_matched" ? "政策匹配" : "部分估算";

export function CalculatorPage() {
  const [form, setForm] = useState<FormState>(initial); const [result, setResult] = useState<CalculationResult | null>(null); const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]); const [scenarioName, setScenarioName] = useState("我的薪酬方案"); const [error, setError] = useState(""); const [notice, setNotice] = useState(""); const [loading, setLoading] = useState(false); const [scenarioLoading, setScenarioLoading] = useState(false);
  useEffect(() => { void refreshScenarios(); }, []);
  async function refreshScenarios() { try { setScenarios(await apiClient.listScenarios(true)); } catch { setError("历史方案暂时无法加载。"); } }
  const update = (key: keyof FormState, value: string | number) => {
    setForm((current) => ({ ...current, [key]: value }));
    setResult(null);
  };
  async function submit(event: FormEvent) { event.preventDefault(); setError(""); setNotice(""); setResult(null); if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(form.calculation_month) || Number(form.monthly_salary) < 0) { setError("请填写有效的月份和工资金额。"); return; } setLoading(true); try { setResult(await apiClient.calculate(form)); } catch (err) { setError(err instanceof Error ? err.message : "请求失败，请稍后重试。"); } finally { setLoading(false); } }
  async function saveScenario() { if (!result) { setError("请先完成一次计算，再保存方案。"); return; } if (!scenarioName.trim()) { setError("请填写方案名称。"); return; } setScenarioLoading(true); setError(""); setNotice(""); try { await apiClient.saveScenario(scenarioName.trim(), form); await refreshScenarios(); setNotice("方案已保存"); } catch (err) { setError(err instanceof Error ? err.message : "方案保存失败。"); } finally { setScenarioLoading(false); } }
  async function loadScenario(id: string) { setScenarioLoading(true); setError(""); setNotice(""); try { const scenario: Scenario = await apiClient.getScenario(id); setForm(scenario.input_snapshot); setResult(scenario.result_snapshot); setScenarioName(scenario.name); setNotice(`已载入“${scenario.name}”`); } catch (err) { setError(err instanceof Error ? err.message : "方案载入失败。"); } finally { setScenarioLoading(false); } }
  async function copyScenario(scenario: ScenarioSummary) { await loadScenario(scenario.id); setScenarioName(`${scenario.name} 副本`); setNotice("已复制方案，可修改后另存为新方案"); }
  async function renameScenario(scenario: ScenarioSummary) { const name = window.prompt("新的方案名称", scenario.name)?.trim(); if (!name || name === scenario.name) return; try { await apiClient.renameScenario(scenario.id, name); await refreshScenarios(); setNotice("方案名称已更新"); } catch (err) { setError(err instanceof Error ? err.message : "重命名失败。"); } }
  async function removeScenario(scenario: ScenarioSummary) { if (!window.confirm(`移入回收站：${scenario.name}？`)) return; try { await apiClient.deleteScenario(scenario.id); await refreshScenarios(); setNotice("方案已移入回收站"); } catch (err) { setError(err instanceof Error ? err.message : "删除失败。"); } }
  async function restoreScenario(scenario: ScenarioSummary) { try { await apiClient.restoreScenario(scenario.id); await refreshScenarios(); setNotice("方案已恢复"); } catch (err) { setError(err instanceof Error ? err.message : "恢复失败。"); } }
  function exportResult() {
    if (!result) return;
    const exportPayload = {
      product: "Paywise 薪算清",
      exported_at: new Date().toISOString(),
      calculation_month: result.calculation_month,
      policy_version: result.policy_version,
      policy_source: result.policy_source,
      confidence: confidenceLabel(result.confidence),
      summary: {
        take_home_cash: result.take_home_cash,
        personal_asset_increase: result.personal_asset_increase,
        annual_total_compensation: result.annual_total_compensation,
        estimated_tax: result.estimated_tax,
        estimated_social_security: result.estimated_social_security,
        estimated_housing_fund: result.estimated_housing_fund,
      },
      assumptions: result.assumptions,
      needs_confirmation: result.needs_confirmation,
      privacy_note: "此文件仅包含计算结果，不包含工资、地点或其他原始输入。",
    };
    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `paywise-${result.calculation_month}-result.json`;
    link.click();
    URL.revokeObjectURL(url);
    setNotice("结果已导出（未包含原始输入）");
  }
  async function copyShareSummary() {
    if (!result) return;
    const summary = [
      `Paywise 薪算清｜${result.calculation_month}`,
      `到手现金：${money(result.take_home_cash)}`,
      `个人资产增加：${money(result.personal_asset_increase)}`,
      `税前总包：${money(result.annual_total_compensation)}`,
      `政策版本：${result.policy_version}｜可信度：${confidenceLabel(result.confidence)}`,
      "仅分享结果摘要，不包含原始收入和地点输入。",
    ].join("\n");
    try {
      await navigator.clipboard.writeText(summary);
      setNotice("脱敏结果摘要已复制");
    } catch {
      setError("浏览器未授予剪贴板权限，请改用导出功能。");
    }
  }
  const activeScenarios = scenarios.filter((scenario) => !scenario.deleted_at); const deletedScenarios = scenarios.filter((scenario) => scenario.deleted_at);

  return <section className="page calculator-page">
    <div className="workspace-heading"><div><p className="eyebrow">CALCULATOR / SCENARIOS</p><h1>薪酬计算器</h1></div><p className="muted">输入薪酬信息，查看到手收入与税费明细。</p></div>
    <div className="calculator-workspace">
      <form className="calculator-form" onSubmit={submit}>
        <div className="section-heading"><h2>收入与缴纳地</h2><span className="unit-label">金额单位：元</span></div>
        <fieldset className="form-section"><legend>计算月份与地点</legend><div className="form-grid location-grid">
          <label>计算月份<input type="month" value={form.calculation_month} onChange={(e) => update("calculation_month", e.target.value)} /></label>
          <label>工作城市<input value={form.work_city} onChange={(e) => update("work_city", e.target.value)} /></label>
          <label>社保缴纳地<input value={form.social_security_city} onChange={(e) => update("social_security_city", e.target.value)} /></label>
          <label>公积金缴纳地<input value={form.housing_fund_city} onChange={(e) => update("housing_fund_city", e.target.value)} /></label>
        </div></fieldset>
        <fieldset className="form-section"><legend>工资与奖金</legend><div className="form-grid income-grid">
          {fields.slice(0, 5).map(([key, label]) => <label key={key}>{label}<input type="number" min="0" step="0.01" value={form[key] ?? ""} onChange={(e) => update(key, e.target.value)} /></label>)}
          <label>年终奖发放月份<input type="month" value={form.bonus_payout_month ?? ""} onChange={(e) => update("bonus_payout_month", e.target.value)} /></label>
        </div></fieldset>
        <details className="advanced-settings"><summary>扣除与累计个税 <span>缴费基数、专项扣除等</span></summary>
          <fieldset className="form-section"><legend>缴费基数与扣除</legend><div className="form-grid income-grid">
            {fields.slice(5).map(([key, label]) => <label key={key}>{label}<input type="number" min="0" step="0.01" value={form[key] ?? ""} onChange={(e) => update(key, e.target.value)} /></label>)}
          </div></fieldset>
          <fieldset className="form-section"><legend>累计预扣个税</legend><div className="form-grid">
            <label>累计预扣月份<input type="number" min="1" max="12" value={form.cumulative_months ?? 1} onChange={(e) => update("cumulative_months", Number(e.target.value))} /></label>
            <label>此前累计收入<input type="number" min="0" step="0.01" value={form.prior_cumulative_income ?? "0"} onChange={(e) => update("prior_cumulative_income", e.target.value)} /></label>
            <label>此前累计应纳税所得额（可选）<input type="number" min="0" step="0.01" value={form.prior_cumulative_taxable_income ?? ""} onChange={(e) => update("prior_cumulative_taxable_income", e.target.value)} /></label>
            <label>此前累计已扣个税（可选）<input type="number" min="0" step="0.01" value={form.prior_cumulative_tax ?? ""} onChange={(e) => update("prior_cumulative_tax", e.target.value)} /></label>
          </div></fieldset>
        </details>
        <div className="form-footer"><p className="privacy-note">计算在当前设备和本地服务中处理。保存方案会保留输入；导出与分享仅包含结果摘要。</p><button className="button" type="submit" disabled={loading}>{loading ? "计算中…" : "计算到手收入"}<span aria-hidden="true"> →</span></button></div>
        {error && <p className="error" role="alert">{error}</p>}{notice && <p className="notice" role="status">{notice}</p>}
      </form>
      <div className="calculator-sidebar">
        {result ? <div className="result" aria-live="polite">
          <div className="result-heading"><h2>计算结果</h2><span className="confidence-badge">{confidenceLabel(result.confidence)}</span></div>
          <div className="result-grid"><strong>到手现金<span>{money(result.take_home_cash)}</span></strong><strong>个人资产增加<span>{money(result.personal_asset_increase)}</span></strong><strong>税前总包<span>{money(result.annual_total_compensation)}</span></strong></div>
          <dl className="deduction-summary"><div><dt>本月个税</dt><dd>{money(result.monthly_tax)}</dd></div><div><dt>个人社保</dt><dd>{money(result.estimated_social_security)}</dd></div><div><dt>个人公积金</dt><dd>{money(result.estimated_housing_fund)}</dd></div></dl>
          <p className="result-meta">{result.calculation_month} · {result.policy_version} · {result.policy_source}</p>
          <details className="result-details"><summary>查看税费过程与估算说明</summary>
            <h3>社保与公积金</h3><p>社保基数 {money(result.social_security_base)}，个人 {money(result.estimated_social_security)}，公司 {money(result.employer_social_security)}；公积金基数 {money(result.housing_fund_base)}，个人 {money(result.estimated_housing_fund)}，公司 {money(result.employer_housing_fund)}</p>
            <h3>个税过程</h3><p>累计应税所得 {money(result.cumulative_taxable_income)}，累计税额 {money(result.cumulative_tax)}，税率 {(result.tax_rate * 100).toFixed(0)}%，速算扣除数 {money(result.quick_deduction)}，本月预扣税 {money(result.monthly_tax)}</p>
            <h3>年终奖方案</h3><p>本月发放 {money(result.bonus_paid_this_month)}；单独计税 {money(result.bonus_separate_tax)}；并入综合所得 {money(result.bonus_combined_tax)}；{result.bonus_separate_allowed ? "单独计税方式可用" : "当前匹配政策不允许单独计税"}；推荐{result.bonus_recommended === "separate" ? "单独计税" : result.bonus_recommended === "combined" ? "并入综合所得" : "无年终奖"}</p>
            <p>{result.breakdown.join("；")}</p><p className="muted">{result.assumptions.join("；")}</p><p className="muted">待确认：{result.needs_confirmation.join("；") || "无"}</p>
          </details>
          <div className="result-actions"><div className="save-controls"><input aria-label="方案名称" value={scenarioName} onChange={(e) => setScenarioName(e.target.value)} /><button className="button" type="button" onClick={() => void saveScenario()} disabled={scenarioLoading}>{scenarioLoading ? "保存中…" : "保存方案"}</button></div><div className="export-controls"><button type="button" onClick={exportResult}>导出结果</button><button type="button" onClick={() => void copyShareSummary()}>复制脱敏摘要</button></div></div>
        </div> : <div className="result result-placeholder" aria-live="polite"><div className="section-heading"><h2>收入概览</h2><span className="unit-label">{loading ? "计算中" : "等待计算"}</span></div><div className="placeholder-metrics" aria-hidden="true"><div><span>到手现金</span><strong>—</strong></div><div><span>个人资产增加</span><strong>—</strong></div><div><span>税前总包</span><strong>—</strong></div></div><p>填写收入并点击「计算到手收入」，<br />在这里查看结果与税费明细。</p></div>}
        <section className="scenario-panel" aria-labelledby="scenario-heading"><div className="section-heading"><h2 id="scenario-heading">我的方案</h2><span className="scenario-count">{activeScenarios.length} 个活动方案</span></div>{activeScenarios.length === 0 ? <p className="muted empty-state">计算后保存方案，随时恢复输入或比较 Offer。</p> : <div className="scenario-list">{activeScenarios.map((scenario) => <ScenarioRow key={scenario.id} scenario={scenario} loading={scenarioLoading} onLoad={() => void loadScenario(scenario.id)} onCopy={() => void copyScenario(scenario)} onRename={() => void renameScenario(scenario)} onDelete={() => void removeScenario(scenario)} />)}</div>}{deletedScenarios.length > 0 && <details className="trash"><summary>回收站（{deletedScenarios.length}）</summary><div className="scenario-list">{deletedScenarios.map((scenario) => <div className="scenario-row deleted" key={scenario.id}><div><strong>{scenario.name}</strong><span>{scenario.calculation_month} · {money(scenario.take_home_cash)}</span></div><button type="button" onClick={() => void restoreScenario(scenario)} disabled={scenarioLoading}>恢复</button></div>)}</div></details>}</section>
      </div>
    </div>
  </section>;
}

function ScenarioRow({ scenario, loading, onLoad, onCopy, onRename, onDelete }: { scenario: ScenarioSummary; loading: boolean; onLoad: () => void; onCopy: () => void; onRename: () => void; onDelete: () => void }) { return <div className="scenario-row"><button className="scenario-main" type="button" onClick={onLoad} disabled={loading}><strong>{scenario.name}</strong><span>{scenario.calculation_month} · 到手 {money(scenario.take_home_cash)} · {new Date(scenario.updated_at).toLocaleDateString("zh-CN")}</span></button><div className="scenario-actions"><button type="button" onClick={onCopy} disabled={loading}>复制</button><button type="button" onClick={onRename} disabled={loading}>重命名</button><button type="button" onClick={onDelete} disabled={loading}>删除</button></div></div>; }
