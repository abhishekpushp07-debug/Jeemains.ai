// Rank: six jewel tools on the app's black page, open to everyone (no sign-in). Built on official 2026 counselling data.
import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowLeftRight, BarChart3, GraduationCap, ListChecks, Sparkles, Target } from 'lucide-react';
import { Gem, ToolCtx } from '../components/rank/RankUi';
import { compareColleges, shortlist, useDreams } from '../components/rank/rankStore';
import { RankPredictor } from '../components/rank/RankPredictor';
import { Cutoff } from '../components/rank/Cutoff';
import { ProfileBar } from '../components/rank/ProfileBar';
import { useProfileSaves } from '../components/rank/profile';
import { TargetMarks } from '../components/rank/TargetMarks';
import { CollegePredictor } from '../components/rank/CollegePredictor';
import { Compare } from '../components/rank/Compare';
import { DreamPanel } from '../components/rank/DreamPanel';
import { track } from '../lib/track';
import '../rank.css';

// Order, colours and words as the app's Rank tab: each tile in its tool's own colour, the form below in that tool's accent.
const TOOLS = [
  { key: 'rank', title: 'Rank predictor', sub: 'marks se rank', Icon: BarChart3, jewel: 'maroon', lead: 'JEE Main ya COMEDK ke marks daalo: percentile aur rank, teeno paper type ke saath.' },
  { key: 'cutoff', title: 'Cut off', sub: 'college / branch', Icon: ListChecks, jewel: 'indigo', badge: 'NEW', lead: 'Ek college ya ek branch chuno: har round ka 2026 cut off. Score daalo to sirf wahi jahan aap eligible ho.' },
  { key: 'target', title: 'Target marks', sub: 'college ke liye', Icon: Target, jewel: 'teal', badge: 'NEW', lead: 'College chuno: har branch ke liye kitne marks chahiye, round by round.' },
  { key: 'college', title: 'College predictor', sub: 'colleges + cutoffs', Icon: GraduationCap, jewel: 'blood', lead: 'JEE Main, BITSAT ya COMEDK: aapki pahunch ki har seat, har round ka cutoff.' },
  { key: 'compare', title: 'College compare', sub: 'side by side', Icon: ArrowLeftRight, jewel: 'champ', badge: 'NEW', lead: '2–3 college ya saved branches ko seats, fee aur cutoff par side by side dekho.' },
  { key: 'dream', title: 'Dream college', sub: 'kitne marks door', Icon: Sparkles, jewel: 'violet', badge: 'NEW', lead: '5 dream college chuno; har full mock ke baad dekho kitne marks door ho.' },
];

function ToolGrid({ value, onChange }) {
  const saved = shortlist.useList().length, colleges = compareColleges.useList().length, dreams = useDreams().dreams.length;
  const compare = [colleges ? `${colleges} college` : null, saved ? `${saved} branch` : null].filter(Boolean).join(' · ');
  const valueOf = t => (t.key === 'compare' && compare ? compare : t.key === 'dream' && dreams ? `${dreams} dream chune` : t.sub);
  return <div className="rk-tools" role="tablist" aria-label="Rank tools" data-testid="rank-tools">
    {TOOLS.map((t, i) => { const on = value === t.key; return <button key={t.key} type="button" role="tab" aria-selected={on} onClick={() => onChange(t.key)}
      className={`rk-tile jewel-${t.jewel}${on ? ' is-on' : ''}`} style={{ '--i': i }} aria-label={`${t.title}. ${valueOf(t)}`} data-testid={`rank-tool-${t.key}`}>
      <i className="rk-tile-face" aria-hidden="true" /><i className="rk-tile-edge" aria-hidden="true" />
      <Gem size={46} sparkle={on} className="rk-tile-gem" />
      <span className="rk-tile-icon"><t.Icon size={17} strokeWidth={1.6} />{t.badge && !on ? <em data-testid={`rank-tool-${t.key}-badge`}>{t.badge}</em> : null}</span>
      <span className="rk-tile-text"><b data-testid={`rank-tool-${t.key}-title`}>{t.title.toUpperCase()}</b><small data-testid={`rank-tool-${t.key}-value`}>{valueOf(t)}</small></span>
    </button>; })}
  </div>;
}

export default function Rank() {
  const [params, setParams] = useSearchParams();
  const asked = params.get('tool') === 'pct' ? 'cutoff' : params.get('tool');  // the old Percentile tool's links open Cut off
  const tool = TOOLS.some(t => t.key === asked) ? asked : 'rank';
  const saves = useProfileSaves();
  const [seen, setSeen] = useState(() => new Set([tool]));
  const [handover, setHandover] = useState(null);
  const stage = useRef(null);
  useEffect(() => { setSeen(s => (s.has(tool) ? s : new Set(s).add(tool))); }, [tool]);
  useEffect(() => { track('rank_tool_open', { tool }); }, [tool]);
  const pick = (key, scroll = true) => {
    const next = new URLSearchParams(params);
    if (key === 'rank') next.delete('tool'); else next.set('tool', key);
    setParams(next, { replace: true });
    if (scroll) requestAnimationFrame(() => stage.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  };
  const toColleges = q => { setHandover({ ...q, at: Date.now() }); pick('college'); };
  const meta = TOOLS.find(t => t.key === tool);
  const panes = { rank: <RankPredictor onColleges={toColleges} />, cutoff: <Cutoff />, target: <TargetMarks />,
    college: <CollegePredictor handover={handover} />, compare: <Compare onTool={pick} />, dream: <DreamPanel onTool={pick} /> };
  return <div className="rk-night rk-screen"><div className="rk-page" data-testid="rank-page">
    <header className="rk-hero">
      <small className="rk-kicker"><i aria-hidden="true" />JEELIVE.AI · RANK</small>
      <h1>Rank &amp; college predictor</h1>
      <p>JoSAA · CSAB · JAC Delhi · BITSAT · COMEDK, 2026 cutoffs <span className="rk-free">Free · bina login ke</span></p>
    </header>
    <ProfileBar />
    <ToolGrid value={tool} onChange={pick} />
    <section ref={stage} className={`rk-stage acc-${tool}`} data-testid="rank-stage">
      <div className="rk-stage-head"><span className={`rk-stage-icon jewel-${meta.jewel}`}><meta.Icon size={20} /></span><div><h2 data-testid="rank-stage-title">{meta.title}</h2><p>{meta.lead}</p></div></div>
      {/* After "Meri details" is saved every tool is drawn again from its freshly filled form. */}
      {TOOLS.map(t => (seen.has(t.key) ? <div key={`${t.key}-${saves}`} hidden={t.key !== tool} className="rk-pane" data-testid={`rank-pane-${t.key}`}><ToolCtx.Provider value={t}>{panes[t.key]}</ToolCtx.Provider></div> : null))}
    </section>
    <p className="rk-foot" data-testid="rank-disclaimer">Saare numbers 2026 ke official counselling data par estimate hain, guarantee nahi. Admission ke liye hamesha official portal dekho. NTA, JoSAA, BITS ya COMEDK se affiliated nahi.</p>
  </div></div>;
}
