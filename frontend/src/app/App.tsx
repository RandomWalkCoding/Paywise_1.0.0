import { Link, NavLink, Route, Routes } from "react-router-dom";
import { CalculatorPage } from "../pages/CalculatorPage";
import { ComparisonPage } from "../pages/ComparisonPage";

export function App() {
  return <div className="shell">
    <header className="site-header"><Link className="brand" to="/">Paywise <span>薪算清</span></Link><nav aria-label="主导航"><NavLink to="/" end>首页</NavLink><NavLink to="/calculator">薪酬计算器</NavLink><NavLink to="/compare">Offer 对比</NavLink></nav></header>
    <main><Routes><Route path="/" element={<Home />} /><Route path="/calculator" element={<CalculatorPage />} /><Route path="/compare" element={<ComparisonPage />} /></Routes></main>
    <footer>结果用于估算和决策参考，不构成税务、法律或劳动意见。</footer>
  </div>;
}

function Home() { return <section className="hero"><div className="hero-copy"><p className="eyebrow">KNOW YOUR PAY</p><h1>把工资<br />算清楚。</h1><p>拆开税前收入、社保、公积金和个税，先看懂每一项，再做薪酬决定。</p><Link className="button" to="/calculator">开始计算 <span aria-hidden="true">↗</span></Link></div><div className="hero-overview"><p className="eyebrow">YOUR PAY, AT A GLANCE</p><h2>一份薪酬，三个视角。</h2><div className="hero-metrics"><div><span>每月可支配</span><strong>到手现金</strong><p>看清税费和扣款后的实际收入。</p></div><div><span>为自己积累</span><strong>个人资产增加</strong><p>把现金与公积金放在一起看。</p></div><div><span>把握全年</span><strong>税前总包</strong><p>连同年终奖，了解完整薪酬。</p></div></div><Link to="/compare">比较已保存的 Offer <span aria-hidden="true">→</span></Link></div></section>; }
