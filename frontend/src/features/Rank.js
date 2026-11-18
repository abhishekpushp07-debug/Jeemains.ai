// Rank: six jewel tools on a light page, open to everyone (no sign-in). Built on official 2026 counselling data.
import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowLeftRight, BarChart3, GraduationCap, LineChart, Sparkles, Target } from 'lucide-react';
import { Gem } from '../components/rank/RankUi';
import { RankPredictor } from '../components/rank/RankPredictor';
import { PercentileRank } from '../components/rank/PercentileRank';
import { TargetMarks } from '../components/rank/TargetMarks';
import { CollegePredictor } from '../components/rank/CollegePredictor';
import { Compare } from '../components/rank/Compare';
import { DreamPanel } from '../components/rank/DreamPanel';
import '../rank.css';

const TOOLS = [
  { key: 'rank', title: 'Rank predictor', sub: 'Marks se rank', Icon: BarChart3, jewel: 'ruby', lead: 'JEE Main ya COMEDK ke marks daalo: percentile aur rank, teeno paper type ke saath.' },
  { key: 'pct', title: 'Percentile se rank', sub: 'NTA percentile', Icon: LineChart, jewel: 'sapphire', lead: 'Scorecard ka percentile daalo: CRL, category rank aur us percentile ke marks.' },
  { key: 'target', title: 'Target marks', sub: 'College ke liye', Icon: Target, jewel: 'emerald', lead: 'College chuno: har branch ke liye kitne marks chahiye, round by round.' },
  { key: 'college', title: 'College predictor', sub: 'Colleges + cutoffs', Icon: GraduationCap, jewel: 'garnet', lead: 'JEE Main, BITSAT ya COMEDK: aapki pahunch ki har seat, har round ka cutoff.' },
  { key: 'compare', title: 'College compare', sub: 'Side by side', Icon: ArrowLeftRight, jewel: 'topaz', lead: '2–3 college ya saved branches ko seats, fee aur cutoff par side by side dekho.' },
  { key: 'dream', title: 'Dream college', sub: 'Kitne marks door', Icon: Sparkles, jewel: 'amethyst', lead: '5 dream college chuno; har full mock ke baad dekho kitne marks door ho.' },
];

function ToolGrid({ value, onChange }) {
  return <div className="rk-tools" role="tablist" aria-label="Rank tools" data-testid="rank-tools">
    {TOOLS.map(({ key, title, sub, Icon, jewel }, i) => <button key={key} type="button" role="tab" aria-selected={value === key} onClick={() => onChange(key)}
      className={`rk-tile jewel-${jewel}${value === key ? ' is-on' : ''}`} style={{ '--i': i }} data-testid={`rank-tool-${key}`}>
      <i className="rk-tile-sheen" aria-hidden="true" /><Gem size={58} className="rk-tile-gem" />
      <span className="rk-tile-icon"><Icon size={20} /></span>
      <span className="rk-tile-text"><b>{title}</b><small>{sub}</small></span>
    </button>)}
  </div>;
}

export default function Rank() {
  const [params, setParams] = useSearchParams();
  const tool = TOOLS.some(t => t.key === params.get('tool')) ? params.get('tool') : 'rank';
  const [seen, setSeen] = useState(() => new Set([tool]));
  const [handover, setHandover] = useState(null);
  const stage = useRef(null);
  useEffect(() => { setSeen(s => (s.has(tool) ? s : new Set(s).add(tool))); }, [tool]);
  const pick = (key, scroll = true) => {
    const next = new URLSearchParams(params);
    if (key === 'rank') next.delete('tool'); else next.set('tool', key);
    setParams(next, { replace: true });
    if (scroll) requestAnimationFrame(() => stage.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  };
  const toColleges = q => { setHandover({ ...q, at: Date.now() }); pick('college'); };
  const meta = TOOLS.find(t => t.key === tool);
  const panes = { rank: <RankPredictor onColleges={toColleges} />, pct: <PercentileRank onColleges={toColleges} />, target: <TargetMarks />,
    college: <CollegePredictor handover={handover} />, compare: <Compare onTool={pick} />, dream: <DreamPanel onTool={pick} /> };
  return <div className="rk-page" data-testid="rank-page">
    <header className="rk-hero">
      <small className="rk-kicker"><Gem size={14} />RANK · 2026 OFFICIAL DATA</small>
      <h1>Apna rank. Apna college.</h1>
      <p>JoSAA, CSAB, JAC Delhi, BITSAT aur COMEDK 2026 ke official data par chhe tools. Bilkul free, bina login ke.</p>
    </header>
    <ToolGrid value={tool} onChange={pick} />
    <section ref={stage} className={`rk-stage acc-${tool}`} data-testid="rank-stage">
      <div className="rk-stage-head"><span className={`rk-stage-icon jewel-${meta.jewel}`}><meta.Icon size={20} /></span><div><h2 data-testid="rank-stage-title">{meta.title}</h2><p>{meta.lead}</p></div></div>
      {TOOLS.map(t => (seen.has(t.key) ? <div key={t.key} hidden={t.key !== tool} className="rk-pane" data-testid={`rank-pane-${t.key}`}>{panes[t.key]}</div> : null))}
    </section>
    <p className="rk-foot" data-testid="rank-disclaimer">Saare numbers 2026 ke official counselling data par estimate hain, guarantee nahi. Admission ke liye hamesha official portal dekho. NTA, JoSAA, BITS ya COMEDK se affiliated nahi.</p>
  </div>;
}
