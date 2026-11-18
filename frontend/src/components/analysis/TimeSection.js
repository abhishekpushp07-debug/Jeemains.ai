import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { Block, Tile, Later, Pills, Meter, Key, TagChip, RESULT, OUT_TONE, mmss, pc, index, TIP, AXIS, GRID } from './parts';
import { PaceChart, Split } from './charts';

const METRIC = { time: ['Time (min)', 'var(--a-fill)'], questions: ['Attempted', 'var(--a-info)'], accuracy: ['Accuracy %', 'var(--a-good)'] };

function Where({ t }) {
  const o = t.by_outcome, total = Math.max(1, o.correct + o.incorrect + o.unanswered);
  const part = [['correct', 'Sahi par', 'good'], ['incorrect', 'Galat par', 'bad'], ['unanswered', 'Bina jawab', 'mute']];
  return (
    <Block id="time" kicker="TIME ON SCREEN" title="Time kahan gaya" note={t.off_screen != null ? 'Paper ka time = sawaalon par screen time + screen se bahar (tab band, app background).' : ''}>
      <div className="a2-tiles five">
        <Tile id="time-elapsed" label="Paper mein laga" value={mmss(t.elapsed)} tone="brand" />
        <Tile id="time-screen" label="Sawaalon par" value={mmss(t.on_screen)} />
        <Tile id="time-off" label="Screen se bahar" value={mmss(t.off_screen)} tone="mute" />
        <Tile id="time-correct" label="Sahi par" value={mmss(o.correct)} tone="good" />
        <Tile id="time-wrong" label="Galat par" value={mmss(o.incorrect)} tone="bad" />
      </div>
      <Split testId="a2-time-quality-bar" label="Time sahi, galat aur bina jawab wale sawaalon par" parts={part.map(([k, , tone]) => [k, o[k], tone])} />
      <Key items={part.map(([k, name, tone]) => [`${name}: ${mmss(o[k])} (${Math.round((100 * o[k]) / total)}%)`, tone])} />
      {o.incorrect + o.unanswered > o.correct && <p className="a2-foot warn">Aadhe se zyada time aise sawaalon par gaya jinke marks nahi bane. Score Potential mein dekho yeh time kahan lagta.</p>}
    </Block>
  );
}

function Subjects({ t }) {
  const [metric, setMetric] = useState('time');
  const share = Object.fromEntries((t.share || []).map(s => [s.name, s]));
  const data = t.by_subject.map(s => ({ name: s.name, time: Math.round((s.time || 0) / 6) / 10, questions: s.attempted, accuracy: s.accuracy ?? 0 }));
  return (
    <Block id="time-subjects" kicker="SUBJECT-WISE" title="Kis subject ko kitna time" action={<Pills id="time-metric" value={metric} onChange={setMetric} items={[['time', 'Time'], ['questions', 'Questions'], ['accuracy', 'Accuracy']]} />}>
      <div className="a2-chart" data-testid="a2-time-subject-chart"><ResponsiveContainer width="100%" height={220}><BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} /><YAxis tick={AXIS} /><Tooltip {...TIP} />
        <Bar dataKey={metric} name={METRIC[metric][0]} fill={METRIC[metric][1]} radius={[6, 6, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-time-table">
        <thead><tr><th>Subject</th><th>Time</th><th>Attempted</th><th>Accuracy</th><th className="w">Time ka hissa vs marks ka hissa</th></tr></thead>
        <tbody>{t.by_subject.map(s => {
          const x = share[s.name];
          return <tr key={s.name}><td><b>{s.name}</b></td><td>{mmss(s.time)}</td><td>{s.attempted} / {s.count}</td><td>{pc(s.accuracy)}</td>
            <td className="w">{x ? <div className="a2-twin"><Meter value={x.time_pct} tone="brand" label="Time ka hissa" /><span>{pc(x.time_pct)}</span><Meter value={x.weight_pct} tone="info" label="Marks ka hissa" /><span>{pc(x.weight_pct)}</span></div> : '—'}</td></tr>;
        })}</tbody>
      </table></div>
      <Key items={[['Time ka hissa', 'brand'], ['Paper mein marks ka hissa', 'info']]} />
    </Block>
  );
}

function Blocks({ an }) {
  const t = an.time;
  const data = t.blocks.map(b => ({ name: `${Math.round(b.from / 60)}–${Math.round(b.to / 60)}m`, Sahi: b.correct, Galat: b.incorrect }));
  return (
    <Block id="time-journey" kicker="TIME JOURNEY" title="Paper ke har hisse mein kya hua" note={`Har ${Math.round(an.paper.block / 60)} min mein kitne jawab diye, kitne sahi aur kitne galat.`}>
      <div className="a2-chart" data-testid="a2-time-blocks-chart"><ResponsiveContainer width="100%" height={230}><BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Sahi" stackId="a" fill="var(--a-good)" /><Bar dataKey="Galat" stackId="a" fill="var(--a-bad)" radius={[6, 6, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
    </Block>
  );
}

function Looks({ t, last }) {
  const f = t.first_look;
  return (
    <div className="a2-duo">
      {f && <Block id="first-look" kicker="PEHLI NAZAR VS WAPAS AAKAR" title="Kab ke jawab zyada sahi" note="Jawab pehli baar khulte hi diya, ya baad mein wapas aakar.">
        <div className="a2-tiles two">
          <Tile id="look-first" label="Pehli nazar mein" value={pc(f.first.accuracy)} sub={`${f.first.correct} / ${f.first.count} sahi · ${mmss(f.first.time)}`} tone="info" />
          <Tile id="look-return" label="Wapas aakar" value={pc(f.return.accuracy)} sub={`${f.return.correct} / ${f.return.count} sahi · ${mmss(f.return.time)}`} tone="warn" />
        </div>
      </Block>}
      <Block id="last-stretch" kicker="AAKHRI 20% TIME" title="Thakaan ka asar">
        {last ? <div className="a2-tiles two">
          <Tile id="last-early" label="Usse pehle" value={pc(last.early.accuracy)} sub={`${last.early.count} jawab`} tone="info" />
          <Tile id="last-late" label="Aakhri 20% mein" value={pc(last.late.accuracy)} sub={`${last.late.count} jawab`} tone={(last.late.accuracy ?? 0) + 10 < (last.early.accuracy ?? 0) ? 'bad' : 'good'} />
        </div> : <p className="a2-empty" data-testid="a2-last-stretch-empty">Dono hisson mein kam se kam 5 jawab hone par yeh compare banta hai.</p>}
      </Block>
    </div>
  );
}

function Slowest({ an, onOpen }) {
  const byId = index(an);
  return (
    <Block id="slowest" kicker="SABSE ZYADA TIME" title="Sabse dheeme 5 sawaal" note="Tap karo, solution khulega.">
      <div className="a2-drill-list">{an.time.slowest.map(i => byId[i]).filter(Boolean).map(q => (
        <button type="button" key={q.id} className="a2-drill-row" data-testid={'a2-slowest-q-' + q.number} onClick={() => onOpen(q.id)}>
          <b>Q{q.number}</b><span>{q.subject}</span><span className={'a2-out tone-' + OUT_TONE[q.outcome]}>{RESULT[q.outcome]}</span>
          <span className="a2-mono">{mmss(q.time)} · Par {mmss(q.par)}</span><TagChip tag={q.tag} copy={an.copy} />
        </button>
      ))}</div>
    </Block>
  );
}

export function TimeSection({ an, onOpen }) {
  const t = an.time;
  if (!t.available) return <Later id="time" />;
  return <>
    <Where t={t} />
    <Subjects t={t} />
    <Blocks an={an} />
    {t.pace?.length > 1 && <Block id="pace" kicker="PACE CURVE" title="Jawab kitni tezi se aaye" note="Time ke saath kul kitne jawab ho chuke the. Seedhi line = barabar speed, sapaat hissa = atke hue.">
      <PaceChart an={an} />
    </Block>}
    <Looks t={t} last={an.habits?.last} />
    <Slowest an={an} onOpen={onOpen} />
  </>;
}
