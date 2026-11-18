import React from 'react';
import { ResponsiveContainer, ScatterChart, Scatter, BarChart, Bar, LineChart, Line, XAxis, YAxis, ZAxis, Tooltip, Legend, CartesianGrid, ReferenceLine, ReferenceArea, Cell, LabelList } from 'recharts';
import { OUT_TONE, RESULT, TIP, AXIS, GRID, mmss } from './parts';

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

export function QGrid({ an, onOpen }) {
  const groups = {};
  an.questions.forEach(q => (groups[q.subject] = groups[q.subject] || []).push(q));
  return (
    <div className="a2-qgrid" data-testid="a2-qgrid">
      {Object.entries(groups).map(([name, qs]) => (
        <div key={name} className="a2-qgrid-group">
          <h4>{name}<small>{qs.filter(q => q.outcome === 'correct').length}/{qs.length} sahi</small></h4>
          <div className="a2-qgrid-cells">
            {qs.map(q => (
              <button type="button" key={q.id} className={'a2-qcell o-' + q.outcome + ' tone-' + OUT_TONE[q.outcome]} aria-label={`Q${q.number} ${RESULT[q.outcome]}`}
                title={`Q${q.number} · ${RESULT[q.outcome]}${q.time != null ? ' · ' + mmss(q.time) : ''}`} data-testid={'a2-qgrid-q-' + q.number} onClick={() => onOpen(q.id)}>
                {q.number}{q.marked && <i className="flag" aria-label="Marked" />}
              </button>
            ))}
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
  const pts = an.questions.filter(q => q.time != null && q.par && q.outcome in LANE && (q.time > 0 || q.outcome !== 'skipped')).map(q => ({
    id: q.id, n: q.number, o: q.outcome, t: q.time, p: q.par, tag: q.tag,
    x: Math.min(3, Math.round((100 * q.time) / q.par) / 100), y: LANE[q.outcome] + (((q.number * 37) % 100) / 100) * 0.56 - 0.28,
  }));
  if (!pts.length) return null;
  const open = d => onOpen((d?.payload || d)?.id);
  return (
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
          <Scatter data={pts} onClick={open} cursor="pointer">
            {pts.map(p => <Cell key={p.id} fill={`var(--a-${OUT_TONE[p.o]})`} stroke="var(--surface-card)" strokeWidth={1.5} />)}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Waterfall({ p }) {
  const step = Object.fromEntries(p.steps.map(s => [s.key, s.marks]));
  let run = p.current;
  const rows = [{ name: 'Abhi', base: 0, v: p.current, label: String(p.current), tone: 'mute' }];
  [['careless', 'Careless'], ['guard', 'Risk'], ['reinvest', 'Time']].forEach(([k, name]) => {
    rows.push({ name, base: Math.max(0, run), v: step[k], label: '+' + step[k], tone: 'warn' });
    run += step[k];
  });
  rows.push({ name: 'Max', base: 0, v: p.maximum, label: String(p.maximum), tone: 'good' });
  return (
    <div className="a2-chart" data-testid="a2-potential-waterfall">
      <ResponsiveContainer width="100%" height={270}>
        <BarChart data={rows} margin={{ top: 22, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} interval={0} /><YAxis tick={AXIS} domain={[0, 'auto']} />
          <ReferenceLine y={p.realistic} stroke="var(--a-good)" strokeDasharray="6 4" ifOverflow="extendDomain" label={{ value: `Target ${p.realistic}`, position: 'insideTopLeft', fill: 'var(--a-good)', fontSize: 11, fontWeight: 700 }} />
          <Bar dataKey="base" stackId="w" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="v" stackId="w" radius={[6, 6, 0, 0]}>
            {rows.map(r => <Cell key={r.name} fill={`var(--a-${r.tone})`} />)}
            <LabelList dataKey="label" position="top" fill="var(--ink)" fontSize={12} fontWeight={700} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PaceChart({ an }) {
  const t = an.time, step = an.paper.duration / Math.max(1, t.pace.length - 1), split = t.pace_split;
  const data = t.pace.map((v, i) => ({ min: Math.round((i * step) / 60), 'Sab jawab': v, Sahi: split?.correct[i], Galat: split?.incorrect[i] }));
  return (
    <div className="a2-chart" data-testid="a2-pace-chart">
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data} margin={{ top: 8, right: 14, left: -18, bottom: 0 }}>
          <CartesianGrid {...GRID} /><XAxis dataKey="min" tick={AXIS} unit="m" /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} labelFormatter={v => v + ' min tak'} /><Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="Sab jawab" stroke="var(--a-fill)" strokeWidth={2.6} dot={false} />
          {split && <Line type="monotone" dataKey="Sahi" stroke="var(--a-good)" strokeWidth={2} dot={false} />}
          {split && <Line type="monotone" dataKey="Galat" stroke="var(--a-bad)" strokeWidth={2} dot={false} strokeDasharray="5 4" />}
        </LineChart>
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
