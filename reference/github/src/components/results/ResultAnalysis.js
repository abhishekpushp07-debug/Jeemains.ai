import React, { useMemo } from 'react';
import { Trophy, Users, TrendingUp, Award, Sparkles, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie, Legend, CartesianGrid } from 'recharts';
import { deepInsights } from '../../lib/deepInsights';

const C = { brand: '#5C0025', soft: '#B9C9EE', gold: '#D97706', good: '#0284C7', bad: '#DC2626', mute: '#D97706' };

const Stat = ({ icon: Icon, label, value, sub, testId }) => <div className="peer-stat" data-testid={testId}><Icon size={18} /><span>{label}</span><strong>{value}</strong>{sub && <small>{sub}</small>}</div>;

const RankStrip = ({ c, score }) => {
  if (!c || c.state !== 'available') return <p className="import-fineprint" data-testid="peer-preparing">{c?.reason || 'Preparing live comparison with other students…'}</p>;
  return <div className="peer-stats" data-testid="peer-rank-strip">
    <Stat icon={Trophy} label="App cohort rank" value={`#${c.rank}`} sub={`of ${c.sample_size} profiles · not national rank`} testId="peer-rank" />
    <Stat icon={TrendingUp} label="App percentile" value={c.percentile} sub="within this platform cohort only" testId="peer-percentile" />
    <Stat icon={Users} label="Average score" value={c.average ?? '—'} sub={`median ${c.median ?? '—'}`} testId="peer-average" />
    <Stat icon={Award} label="Top score" value={c.top ?? '—'} sub={`you: ${score}`} testId="peer-top" />
  </div>;
};

const Distribution = ({ c, score }) => {
  if (!c?.distribution?.length) return null;
  const mine = c.distribution.findIndex((b, i) => score >= b.lower && (score < b.upper || i === c.distribution.length - 1));
  return <div className="chart-card" data-testid="chart-score-distribution"><h4>Total marks · how everyone scored</h4>
    <ResponsiveContainer width="100%" height={220}><BarChart data={c.distribution} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
      <CartesianGrid vertical={false} stroke="#eee" /><XAxis dataKey="label" tick={{ fontSize: 10 }} interval={0} angle={-30} textAnchor="end" height={48} /><YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
      <Tooltip formatter={(v) => [v, 'students']} /><Bar dataKey="count" radius={[4, 4, 0, 0]}>{c.distribution.map((_, i) => <Cell key={i} fill={i === mine ? C.brand : C.soft} />)}</Bar>
    </BarChart></ResponsiveContainer><p className="import-fineprint">Dark bar = your score band.</p></div>;
};

const Sections = ({ s, c }) => {
  const rows = (s.sections || Object.entries(s.subjects || {}).map(([name, d]) => ({ name, score: d.score }))).map((x) => ({ name: x.name.replace('Logical Reasoning', 'Logical R.').replace('English Proficiency', 'English'), You: x.score, Average: c?.sections?.find((y) => y.name === x.name)?.average, Top: c?.sections?.find((y) => y.name === x.name)?.top }));
  if (!rows.length) return null;
  return <div className="chart-card" data-testid="chart-section-compare"><h4>Section-wise · you vs average vs top</h4>
    <ResponsiveContainer width="100%" height={220}><BarChart data={rows} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
      <CartesianGrid vertical={false} stroke="#eee" /><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip /><Legend wrapperStyle={{ fontSize: 12 }} />
      <Bar dataKey="You" fill={C.brand} radius={[4, 4, 0, 0]} /><Bar dataKey="Average" fill={C.soft} radius={[4, 4, 0, 0]} /><Bar dataKey="Top" fill={C.gold} radius={[4, 4, 0, 0]} />
    </BarChart></ResponsiveContainer></div>;
};

const Outcomes = ({ s }) => {
  const data = [{ name: 'Correct', value: s.correct, fill: C.good }, { name: 'Wrong', value: s.incorrect, fill: C.bad }, { name: 'Unanswered', value: s.skipped, fill: C.mute }];
  return <div className="chart-card" data-testid="chart-outcomes"><h4>Your answers</h4>
    <ResponsiveContainer width="100%" height={220}><PieChart><Pie data={data} dataKey="value" nameKey="name" innerRadius={52} outerRadius={80} paddingAngle={2}>{data.map((d) => <Cell key={d.name} fill={d.fill} />)}</Pie><Tooltip /><Legend wrapperStyle={{ fontSize: 12 }} /></PieChart></ResponsiveContainer></div>;
};

const HeatMap = ({ r, peer, onOpen }) => {
  return <div className="chart-card wide" data-testid="chart-question-heatmap"><h4>Every question · one tap to its solution</h4>
    <div className="q-heat">{r.questions.map((q) => {
      const p = peer[q.id], tried = p ? p.correct + p.incorrect : 0, rate = tried ? p.correct / tried : null;
      return <button key={q.id} type="button" className={'q-heat-cell o-' + q.outcome} style={{ '--rate': rate ?? 0, color: (rate ?? 0) > 0.45 ? '#fff' : '#4A0A22' }} title={`Q${q.number}: ${p ? `${p.correct} of ${tried} solved` : 'no data'} · you: ${q.outcome}`} onClick={() => onOpen(q.id)} data-testid={'heat-q-' + q.number}>{q.number}</button>;
    })}</div>
    <p className="import-fineprint">Tap a question to open its solution. Fill intensity reflects peer correctness only when available. Your outcome is shown by the labelled question tooltip and outline.</p></div>;
};

const tones = { good: CheckCircle2, warn: AlertTriangle, info: Info };
const INSIGHT_GROUPS=[
 ['Score & accuracy','maroon',['score','accuracy','attempt','penalty','noguess','yield','correct','wrongs','blank','positive','size']],
 ['Subject strengths','emerald',['best','weak','skipsec','spread']],
 ['Time & rhythm','amber',['time','pace','halves','late','cstreak','wstreak','firstten','lastten']],
 ['Decisions & next steps','crimson',['marked','letters','breakeven','bonus','potential','next']],
 ['Platform perspective','sapphire',['rank','percentile','avg','top','easy','hard']]
];
const Insights = ({ list }) => <div className="deep-insights" data-testid="deep-insights"><h3><Sparkles size={18}/>{list.length} insights, in clear chapters.</h3><div className="insight-groups">{INSIGHT_GROUPS.map(([title,tone,keys],group)=>{const rows=list.filter(x=>keys.includes(x.key));if(!rows.length)return null;return <details key={title} className={'insight-group tone-'+tone} open={group===0}><summary data-testid={'insight-group-'+group}>{title}<small>{rows.length} insights</small></summary><ol>{rows.map(x=>{const Icon=tones[x.tone]||Info;return <li key={x.key} className={'insight-card t-'+x.tone} data-testid={'insight-'+x.key}><span className="insight-no">{String(list.indexOf(x)+1).padStart(2,'0')}</span><div><small><Icon size={13}/>{x.title}</small><strong>{x.value}</strong><p>{x.detail}</p></div></li>})}</ol></details>})}</div></div>;

export const ResultAnalysis = ({ r, cohort, peer, onOpen }) => {
  const list = useMemo(() => deepInsights(r, cohort), [r, cohort]);
  return <section className="result-analysis" data-testid="result-analysis">
    <div className="result-analysis-head"><span className="import-section-label">RESULT ANALYSIS</span><h2>How you did, and how everyone else did.</h2>
      {cohort?.state === 'available' && cohort.sample_size < cohort.stable_sample && <p className="import-fineprint" data-testid="peer-early-sample">Live comparison with {cohort.sample_size} student{cohort.sample_size === 1 ? '' : 's'} so far. Ranks become steadier as more students take this paper.</p>}</div>
    <RankStrip c={cohort} score={r.summary.score} />
    <div className="chart-grid"><Distribution c={cohort} score={r.summary.score} /><Sections s={r.summary} c={cohort} /><Outcomes s={r.summary} /><HeatMap r={r} peer={peer} onOpen={onOpen} /></div>
    <Insights list={list} />
  </section>;
};
