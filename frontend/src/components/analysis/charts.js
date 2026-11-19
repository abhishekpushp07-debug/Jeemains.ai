import React, { useState } from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, BarChart, Bar, LineChart, Line, XAxis, YAxis, ZAxis, Tooltip, Legend, CartesianGrid, ReferenceLine, ReferenceArea, Cell, LabelList } from 'recharts';
import { OUT_TONE, RESULT, TAG, TIP, LEGEND, AXIS, GRID, mmss } from './parts';

const TAG_ORDER = ['perfect', 'slow_correct', 'wasted', 'concept_gap', 'costly_overtime', 'confused', 'smart_skip'];

export function ScoreRing({ score, maximum, percentage }) {
  const r = 84, c = 2 * Math.PI * r, share = Math.max(0, Math.min(1, score / (maximum || 1)));
  return (
    <div className="a2-ring" data-testid="a2-score-ring">
      <svg viewBox="0 0 200 200" aria-hidden="true">
        <circle cx="100" cy="100" r={r} className="track" />
        <circle cx="100" cy="100" r={r} className="arc" style={{ '--c': c }} strokeDasharray={c} strokeDashoffset={c * (1 - share)} />
      </svg>
      <div><strong data-testid="a2-score">{score}</strong><span>/ {maximum}</span>{percentage != null && <em>{percentage}%</em>}</div>
    </div>
  );
}

export function Histogram({ dist }) {
  const most = Math.max(1, ...dist.bins.map(b => b.count));
  return (
    <div className="a2-hist" data-testid="a2-distribution" role="img" aria-label={`${dist.n} students ke Score ka chart`}>
      {dist.bins.map((b, i) => (
        <div key={i} className={'a2-hist-col' + (b.you ? ' you' : '')} title={`${b.from} se ${b.to}: ${b.count} students`} data-testid={b.you ? 'a2-distribution-you' : undefined}>
          <span className="n">{b.count || ''}</span>
          <i style={{ height: (b.count ? Math.max(6, (100 * b.count) / most) : 2) + '%' }} />
          <small>{b.from}</small>
          {b.you && <em>Aap</em>}
        </div>
      ))}
    </div>
  );
}

// One cell per question. detail: split by MCQ / Numerical, a dot in the tag's colour and a strip for the class's % correct.
export function QGrid({ an, onOpen, detail }) {
  const groups = {}, kinds = {};
  an.questions.forEach(q => (kinds[q.subject] = kinds[q.subject] || new Set()).add(q.type));
  an.questions.forEach(q => {
    const name = detail && kinds[q.subject].size > 1 ? `${q.subject} · ${q.type === 'integer' ? 'Numerical' : 'MCQ'}` : q.subject;
    (groups[name] = groups[name] || []).push(q);
  });
  return (
    <div className="a2-qgrid" data-testid={detail ? 'a2-qs-grid' : 'a2-qgrid'}>
      {Object.entries(groups).map(([name, qs]) => (
        <div key={name} className="a2-qgrid-group">
          <h4>{name}<small>{qs.filter(q => q.outcome === 'correct').length}/{qs.length} sahi</small></h4>
          <div className="a2-qgrid-cells">
            {qs.map(q => {
              const share = detail ? q.class?.correct : null, tag = detail && q.tag ? an.copy.tags[q.tag][0] : '';
              return (
                <button type="button" key={q.id} className={'a2-qcell o-' + q.outcome + ' tone-' + OUT_TONE[q.outcome] + (detail ? ' detail' : '')} aria-label={`Q${q.number} ${RESULT[q.outcome]}${tag ? ', ' + tag : ''}`}
                  title={`Q${q.number} · ${RESULT[q.outcome]}${tag ? ' · ' + tag : ''}${q.time != null ? ' · ' + mmss(q.time) : ''}${share != null ? ` · class mein ${share}% sahi` : ''}`} data-testid={'a2-qgrid-q-' + q.number} onClick={() => onOpen(q.id)}>
                  {q.number}{q.marked && <i className="flag" aria-label="Marked" />}
                  {detail && q.tag && <i className={'tagdot tone-' + TAG[q.tag][0]} aria-hidden="true" />}
                  {share != null && <i className="heat" style={{ width: Math.max(6, share * 0.6) + '%' }} aria-hidden="true" />}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

const LANE = { correct: 2, incorrect: 1, skipped: 0 };
function MapTip({ active, payload, copy }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return <div className="a2-tip"><b>Q{p.n}</b> · {RESULT[p.o]}<br />{mmss(p.t)} · Par {mmss(p.p)}{p.tag ? <><br />{copy.tags[p.tag][0]}</> : null}</div>;
}

export function SpeedMap({ an, onOpen }) {
  const [off, setOff] = useState([]);
  const all = an.questions.filter(q => q.time != null && q.par && q.outcome in LANE && (q.time > 0 || q.outcome !== 'skipped')).map(q => ({
    id: q.id, n: q.number, o: q.outcome, t: q.time, p: q.par, tag: q.tag,
    x: Math.min(3, Math.round((100 * q.time) / q.par) / 100), y: LANE[q.outcome] + (((q.number * 37) % 100) / 100) * 0.56 - 0.28,
  }));
  if (!all.length) return null;
  const present = TAG_ORDER.filter(t => all.some(p => p.tag === t));
  const pts = all.filter(p => !off.includes(p.tag));
  const open = d => onOpen((d?.payload || d)?.id);
  const flip = t => setOff(old => (old.includes(t) ? old.filter(x => x !== t) : [...old, t]));
  return <>
    <div className="a2-toggles" role="group" aria-label="Tag dikhao ya chhupao" data-testid="a2-speed-map-tags">
      {present.map(t => {
        const Icon = TAG[t][1];
        return <button type="button" key={t} className={'a2-chipbtn tone-' + TAG[t][0]} aria-pressed={!off.includes(t)} data-testid={'a2-speed-map-tag-' + t} onClick={() => flip(t)}><Icon size={13} aria-hidden="true" /> {an.copy.tags[t][0]} ({all.filter(p => p.tag === t).length})</button>;
      })}
    </div>
    <div className="a2-chart" data-testid="a2-speed-map">
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 10, right: 14, left: 4, bottom: 4 }}>
          <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" />
          <ReferenceArea x1={0} x2={0.5} y1={0.5} y2={1.5} fill="var(--a-bad)" fillOpacity={0.1} label={{ value: 'Careless zone', position: 'insideTopLeft', fill: 'var(--a-bad)', fontSize: 11 }} />
          <ReferenceArea x1={1.5} x2={3} y1={0.5} y2={1.5} fill="var(--a-warn)" fillOpacity={0.1} label={{ value: 'Mehnga overtime', position: 'insideTopRight', fill: 'var(--a-warn)', fontSize: 11 }} />
          <ReferenceArea x1={0} x2={1.25} y1={1.5} y2={2.5} fill="var(--a-good)" fillOpacity={0.07} label={{ value: 'Perfect zone', position: 'insideTopLeft', fill: 'var(--a-good)', fontSize: 11 }} />
          <XAxis type="number" dataKey="x" domain={[0, 3]} ticks={[0, 0.5, 1, 1.5, 2, 3]} tickFormatter={v => (v === 1 ? 'Par' : v === 3 ? '3x+' : v + 'x')} tick={AXIS} />
          <YAxis type="number" dataKey="y" domain={[-0.5, 2.5]} ticks={[0, 1, 2]} tickFormatter={v => ['Chhoda', 'Galat', 'Sahi'][v]} tick={AXIS} width={58} />
          <ZAxis range={[70, 70]} />
          <ReferenceLine x={1} stroke="var(--ink)" strokeDasharray="5 4" />
          <Tooltip content={<MapTip copy={an.copy} />} cursor={{ strokeDasharray: '3 3' }} />
          <Scatter data={pts} onClick={open} cursor="pointer" isAnimationActive={false}>
            {pts.map(p => <Cell key={p.id} fill={`var(--a-${OUT_TONE[p.o]})`} stroke="var(--surface-card)" strokeWidth={1.5} />)}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  </>;
}

export function Waterfall({ p }) {
  const step = Object.fromEntries(p.steps.map(s => [s.key, s.marks]));
  let run = p.current;
  const rows = [{ name: 'Abhi', base: 0, v: p.current, label: String(p.current), tone: 'mute' }];
  [['careless', 'Careless'], ['guard', 'Risk'], ['reinvest', 'Time']].forEach(([k, name]) => {
    rows.push({ name, base: Math.max(0, run), v: step[k], label: '+' + step[k], tone: 'warn' });
    run += step[k];
  });
  rows.push({ name: 'Target', base: 0, v: p.realistic, label: String(p.realistic), tone: 'good' }, { name: 'Max', base: 0, v: p.maximum, label: String(p.maximum), tone: 'info' });
  return (
    <div className="a2-chart" data-testid="a2-potential-waterfall">
      <ResponsiveContainer width="100%" height={270}>
        <BarChart data={rows} margin={{ top: 22, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} interval={0} /><YAxis tick={AXIS} domain={[0, 'auto']} />
          <Bar dataKey="base" stackId="w" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="v" stackId="w" radius={[6, 6, 0, 0]} minPointSize={2}>
            {rows.map(r => <Cell key={r.name} fill={`var(--a-${r.tone})`} />)}
            <LabelList dataKey="label" position="top" fill="var(--ink)" fontSize={12} fontWeight={700} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

const PACE = [['Sab jawab', 'var(--ink)', 2.6, undefined], ['Sahi', 'var(--a-good)', 2, undefined], ['Galat', 'var(--a-bad)', 2, '5 4']];
export function PaceChart({ an }) {
  const [off, setOff] = useState([]);
  const t = an.time, step = an.paper.duration / Math.max(1, t.pace.length - 1), split = t.pace_split;
  const data = t.pace.map((v, i) => ({ min: Math.round((i * step) / 60), 'Sab jawab': v, Sahi: split?.correct[i], Galat: split?.incorrect[i] }));
  const lines = PACE.filter(l => split || l[0] === 'Sab jawab');
  const flip = k => setOff(old => (old.includes(k) ? old.filter(x => x !== k) : old.length < lines.length - 1 ? [...old, k] : old));
  return <>
    {lines.length > 1 && <div className="a2-toggles" role="group" aria-label="Line dikhao ya chhupao" data-testid="a2-pace-toggles">
      {lines.map(([k, color]) => <button type="button" key={k} className="a2-chipbtn" aria-pressed={!off.includes(k)} data-testid={'a2-pace-toggle-' + k.split(' ')[0].toLowerCase()} onClick={() => flip(k)}><i className="swatch" style={{ background: color }} aria-hidden="true" /> {k}</button>)}
    </div>}
    <div className="a2-chart" data-testid="a2-pace-chart">
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data} margin={{ top: 8, right: 14, left: -18, bottom: 0 }}>
          <CartesianGrid {...GRID} /><XAxis dataKey="min" tick={AXIS} unit="m" /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} labelFormatter={v => v + ' min tak'} />
          {lines.filter(l => !off.includes(l[0])).map(([k, color, width, dash]) => <Line key={k} type="monotone" dataKey={k} stroke={color} strokeWidth={width} dot={false} strokeDasharray={dash} />)}
        </LineChart>
      </ResponsiveContainer>
    </div>
  </>;
}

// Each subject: the student against the class average, the top 10% and the topper.
export function SubjectVs({ rows }) {
  const wide = rows.some(r => r.average != null);
  const data = rows.map(r => ({ name: r.name, Aap: r.you, 'Class average': r.average, 'Top 10%': r.top10, Topper: r.topper }));
  return (
    <div className="a2-chart" data-testid="a2-subject-vs-chart">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
          <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} /><YAxis tick={AXIS} /><Tooltip {...TIP} /><Legend {...LEGEND} />
          <Bar dataKey="Aap" fill="var(--a-fill)" radius={[5, 5, 0, 0]} />
          {wide && <Bar dataKey="Class average" fill="var(--a-mute)" radius={[5, 5, 0, 0]} />}
          {wide && <Bar dataKey="Top 10%" fill="var(--a-info)" radius={[5, 5, 0, 0]} />}
          <Bar dataKey="Topper" fill="var(--a-gold)" radius={[5, 5, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export const Split = ({ parts, testId, label }) => {
  const total = Math.max(1, parts.reduce((a, [, v]) => a + Math.max(0, v || 0), 0));
  return (
    <div className="a2-split" data-testid={testId} role="img" aria-label={label}>
      {parts.map(([k, v, tone]) => v > 0 && <i key={k} className={'tone-' + tone} style={{ width: (100 * v) / total + '%' }} title={`${k}: ${v}`} />)}
    </div>
  );
};
