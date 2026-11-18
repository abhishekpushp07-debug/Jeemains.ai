import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, LineChart, Line } from 'recharts';
import { Flag, Droplets } from 'lucide-react';
import { Block, Tile, Later, Pills, TagChip, TAG, RESULT, OUT_TONE, mmss, pc, pick, TIP, AXIS } from './parts';

const index = an => Object.fromEntries(an.questions.map(q => [q.id, q]));
const METRIC = { time: ['Time (min)', 'var(--a-brand)'], questions: ['Attempted', 'var(--a-info)'], accuracy: ['Accuracy %', 'var(--a-good)'] };

export function TimeSection({ an, onOpen }) {
  const t = an.time;
  const [metric, setMetric] = useState('time');
  if (!t.available) return <Later id="time" />;
  const byId = index(an), o = t.by_outcome, total = Math.max(1, o.correct + o.incorrect + o.unanswered);
  const subjects = t.by_subject.map(s => ({ name: s.name, time: Math.round((s.time || 0) / 6) / 10, questions: s.attempted, accuracy: s.accuracy ?? 0 }));
  const blocks = t.blocks.map(b => ({ name: `${Math.round(b.from / 60)}–${Math.round(b.to / 60)}m`, Sahi: b.correct, Galat: b.incorrect }));
  const step = an.paper.duration / Math.max(1, (t.pace || [1]).length - 1);
  const pace = (t.pace || []).map((v, i) => ({ min: Math.round((i * step) / 60), Jawab: v }));
  const part = [['correct', 'Sahi par', 'good'], ['incorrect', 'Galat par', 'bad'], ['unanswered', 'Bina jawab', 'mute']];
  return <>
    <Block id="time" title="Time kahan gaya" note={an.copy.time_label}>
      <div className="a2-tiles four">
        <Tile id="time-elapsed" label="Paper mein laga" value={mmss(t.elapsed)} tone="brand" />
        <Tile id="time-screen" label="Sawaalon par (screen)" value={mmss(t.on_screen)} />
        <Tile id="time-correct" label="Sahi par" value={mmss(o.correct)} tone="good" />
        <Tile id="time-wrong" label="Galat par" value={mmss(o.incorrect)} tone="bad" />
      </div>
      <div className="a2-split" data-testid="a2-time-quality-bar" role="img" aria-label="Time sahi, galat aur bina jawab wale sawaalon par">
        {part.map(([k, , tone]) => o[k] > 0 && <i key={k} className={'tone-' + tone} style={{ width: (100 * o[k]) / total + '%' }} />)}
      </div>
      <div className="a2-row wrap">{part.map(([k, name, tone]) => <span key={k} className={'a2-out tone-' + tone}>{name}: {mmss(o[k])} ({Math.round((100 * o[k]) / total)}%)</span>)}</div>
    </Block>
    <Block id="time-subjects" title="Subject-wise time" action={<Pills id="time-metric" value={metric} onChange={setMetric} items={[['time', 'Time'], ['questions', 'Questions'], ['accuracy', 'Accuracy']]} />}>
      <div className="a2-chart" data-testid="a2-time-subject-chart"><ResponsiveContainer width="100%" height={220}><BarChart data={subjects} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" /><XAxis dataKey="name" tick={AXIS} /><YAxis tick={AXIS} /><Tooltip {...TIP} />
        <Bar dataKey={metric} name={METRIC[metric][0]} fill={METRIC[metric][1]} radius={[4, 4, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-time-table">
        <thead><tr><th>Subject</th><th>Time</th><th>Attempted</th><th>Accuracy</th></tr></thead>
        <tbody>{t.by_subject.map(s => <tr key={s.name}><td>{s.name}</td><td>{mmss(s.time)}</td><td>{s.attempted} / {s.count}</td><td>{pc(s.accuracy)}</td></tr>)}</tbody>
      </table></div>
    </Block>
    <Block id="time-journey" title="Time journey" note={`Har ${Math.round(an.paper.block / 60)} min mein kitne jawab diye, kitne sahi aur kitne galat.`}>
      <div className="a2-chart" data-testid="a2-time-blocks-chart"><ResponsiveContainer width="100%" height={220}><BarChart data={blocks} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" /><XAxis dataKey="name" tick={AXIS} /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Sahi" stackId="a" fill="var(--a-good)" /><Bar dataKey="Galat" stackId="a" fill="var(--a-bad)" radius={[4, 4, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
    </Block>
    {pace.length > 1 && <Block id="pace" title="Pace curve" note="Time ke saath kul kitne sawaalon ke jawab ho chuke the.">
      <div className="a2-chart" data-testid="a2-pace-chart"><ResponsiveContainer width="100%" height={220}><LineChart data={pace} margin={{ top: 8, right: 12, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" /><XAxis dataKey="min" tick={AXIS} unit="m" /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} />
        <Line type="monotone" dataKey="Jawab" stroke="var(--a-brand)" strokeWidth={2.5} dot={false} />
      </LineChart></ResponsiveContainer></div>
    </Block>}
    <Block id="slowest" title="Sabse dheeme 5 sawaal" note="Tap karo, solution khulega.">
      <div className="a2-drill-list">{t.slowest.map(i => byId[i]).filter(Boolean).map(q => (
        <button type="button" key={q.id} className="a2-drill-row" data-testid={'a2-slowest-q-' + q.number} onClick={() => onOpen(q.id)}>
          <b>Q{q.number}</b><span>{q.subject}</span><span className={'a2-out tone-' + OUT_TONE[q.outcome]}>{RESULT[q.outcome]}</span><span>{mmss(q.time)} · Par {mmss(q.par)}</span><TagChip tag={q.tag} copy={an.copy} />
        </button>
      ))}</div>
    </Block>
  </>;
}

const LEVELS = ['easy', 'moderate', 'tough', 'unrated'];
const COLS = [['correct', 'Sahi', 'good'], ['incorrect', 'Galat', 'bad'], ['skipped', 'Chhode', 'mute']];

export function Difficulty({ an, onDrill }) {
  const d = an.difficulty, L = an.copy.levels;
  const [name, setName] = useState('all');
  const levels = name === 'all' ? d.all : d.by_subject.find(s => s.name === name)?.levels || d.all;
  const shown = LEVELS.filter(l => levels[l]?.count);
  const ids = (l, o) => pick(an, q => q.difficulty === l && q.outcome === o && (name === 'all' || q.subject === name));
  const data = shown.map(l => ({ name: L[l], Sahi: levels[l].correct, Galat: levels[l].incorrect, Chhode: levels[l].skipped }));
  const leak = d.leak, lost = leak.wrong.length + leak.skipped.length;
  return <>
    <Pills id="difficulty-subject" value={name} onChange={setName} items={[['all', 'Sab subjects'], ...d.by_subject.map(s => [s.name, s.name])]} />
    <Block id="difficulty" title="Difficulty ke hisaab se" note="Level students ke result se banta hai. Jahan data kam hai wahan Not rated likha hai, andaaza nahi lagaya.">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-difficulty-table">
        <thead><tr><th>Level</th>{COLS.map(c => <th key={c[0]}>{c[1]}</th>)}</tr></thead>
        <tbody>{shown.map(l => <tr key={l}><td>{L[l]} <small>({levels[l].count})</small></td>{COLS.map(([k, label, tone]) => {
          const list = ids(l, k);
          return <td key={k}>{list.length ? <button type="button" className={'a2-cell tone-' + tone} data-testid={`a2-difficulty-${l}-${k}`} onClick={() => onDrill(`${L[l]} · ${label}`, list)}>{levels[l][k]} / {levels[l].count}</button> : `${levels[l][k]} / ${levels[l].count}`}</td>;
        })}</tr>)}</tbody>
      </table></div>
      <div className="a2-chart" data-testid="a2-difficulty-chart"><ResponsiveContainer width="100%" height={220}><BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" /><XAxis dataKey="name" tick={AXIS} /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Sahi" fill="var(--a-good)" radius={[3, 3, 0, 0]} /><Bar dataKey="Galat" fill="var(--a-bad)" radius={[3, 3, 0, 0]} /><Bar dataKey="Chhode" fill="var(--a-mute)" radius={[3, 3, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
    </Block>
    <div className={'a2-leak' + (lost ? '' : ' none')} data-testid="a2-leak">
      <Droplets size={22} />
      <div><strong>Leak: Easy sawaal</strong>
        <p>{lost ? `${leak.wrong.length} Easy galat aur ${leak.skipped.length} Easy chhoote. Yahan se ${leak.marks} marks bach sakte the.` : 'Easy sawaalon mein koi leak nahi mila.'}</p>
        {lost > 0 && <button type="button" className="a2-link" data-testid="a2-leak-questions" onClick={() => onDrill('Leak: Easy sawaal', [...leak.wrong, ...leak.skipped])}>{lost} sawaal dekho</button>}
      </div>
    </div>
  </>;
}

const nth = n => (n === 2 ? '2nd' : n === 3 ? '3rd' : n + 'th');

export function Journey({ an, onOpen }) {
  const j = an.journey;
  const [tags, setTags] = useState(true);
  if (!j.available) return <Later id="journey" />;
  const byId = index(an), s = j.summary, first = j.first_block, groups = {};
  j.visits.forEach(v => { const i = Math.floor(v.a / j.block); (groups[i] = groups[i] || []).push(v); });
  return <>
    <Block id="journey" title="Aap paper mein kaise chale" action={<button type="button" className="a2-link" aria-pressed={tags} data-testid="a2-journey-tags-toggle" onClick={() => setTags(!tags)}>{tags ? 'Tag chhupao' : 'Tag dikhao'}</button>}>
      <p className="a2-lead" data-testid="a2-journey-summary">{s.total} mein se {s.visited} sawaal dekhe, {s.revisits} baar wapas gaye, {s.thrice} sawaal 3 ya zyada baar dekhe.</p>
      <p className="a2-empty" data-testid="a2-journey-order">Subject order: {j.order.join(' → ') || '—'}.{first ? ` Pehle ${first.minutes} min mein ${first.answered} jawab (${first.correct} sahi, ${first.incorrect} galat).` : ''}</p>
    </Block>
    {Object.keys(groups).map(Number).sort((a, b) => a - b).map(i => (
      <Block key={i} id={'journey-' + i} title={`${Math.round((i * j.block) / 60)}–${Math.round(((i + 1) * j.block) / 60)} min`} note={`${groups[i].length} visits`}>
        <div className="a2-journey">{groups[i].map((v, k) => {
          const q = byId[v.q], tone = tags && q?.tag ? TAG[q.tag][0] : 'plain';
          return <button type="button" key={k} className={'a2-visit tone-' + tone} title={q?.tag ? an.copy.tags[q.tag][0] : ''} data-testid={`a2-visit-${i}-${k}`} onClick={() => onOpen(v.q)}>
            <b>Q{v.n}</b>{v.v > 1 && <sup>{nth(v.v)}</sup>}<small>{mmss(v.d)}</small>{v.mark && <Flag size={11} aria-label="Marked for review" />}{v.set && <em>{v.set}</em>}
          </button>;
        })}</div>
      </Block>
    ))}
  </>;
}

const FILTERS = [['all', 'Sab'], ['wrong', 'Galat'], ['skipped', 'Chhode'], ['careless', 'Careless'], ['overtime', 'Overtime'], ['confused', 'Confused'], ['marked', 'Marked'], ['changed', 'Jawab badla']];
const TEST = {
  all: () => true, wrong: q => q.outcome === 'incorrect', skipped: q => q.outcome === 'skipped', careless: q => q.tag === 'wasted',
  overtime: q => ['slow_correct', 'costly_overtime'].includes(q.tag), confused: q => q.tag === 'confused', marked: q => q.marked, changed: q => !!q.changed,
};

export function QsByQs({ an, onOpen }) {
  const [f, setF] = useState('all');
  const rows = an.questions.filter(TEST[f]), L = an.copy.levels;
  return <Block id="qs" title="Har sawaal ka hisaab" note={`${rows.length} / ${an.questions.length} sawaal. Kisi bhi sawaal par tap karo, uska solution khulega.`}>
    <Pills id="qs-filter" value={f} onChange={setF} items={FILTERS.map(([k, l]) => [k, `${l} (${an.questions.filter(TEST[k]).length})`])} />
    {!rows.length && <p className="a2-empty" data-testid="a2-qs-empty">Is filter mein koi sawaal nahi.</p>}
    <div className="a2-scroll a2-qs-wide"><table className="a2-table" data-testid="a2-qs-table">
      <thead><tr><th>Q</th><th>Subject</th><th>Chapter</th><th>Level</th><th>Aapka</th><th>Sahi jawab</th><th>Result</th><th>Time</th><th>Par</th><th>Class % sahi</th><th>Tag</th></tr></thead>
      <tbody>{rows.map(q => (
        <tr key={q.id} className="tap" data-testid={'a2-qs-row-' + q.number} onClick={() => onOpen(q.id)}>
          <td><b>{q.number}</b></td><td>{q.subject}</td><td>{q.topic || '—'}</td><td>{L[q.difficulty]}</td><td>{q.response || '—'}{q.changed ? <small> ({q.changed})</small> : null}</td><td>{q.answer}</td>
          <td><span className={'a2-out tone-' + OUT_TONE[q.outcome]}>{RESULT[q.outcome]}</span></td><td>{mmss(q.time)}</td><td>{mmss(q.par)}</td><td>{pc(q.class?.correct)}</td><td><TagChip tag={q.tag} copy={an.copy} /></td>
        </tr>
      ))}</tbody>
    </table></div>
    <div className="a2-qs-cards">{rows.map(q => (
      <button type="button" key={q.id} className="a2-qs-card" data-testid={'a2-qs-card-' + q.number} onClick={() => onOpen(q.id)}>
        <div><b>Q{q.number}</b><span>{q.subject} · {L[q.difficulty]}</span><span className={'a2-out tone-' + OUT_TONE[q.outcome]}>{RESULT[q.outcome]}</span></div>
        <p>Aapka {q.response || '—'} · Sahi {q.answer}{q.changed ? ` · badla ${q.changed}` : ''}</p>
        <p>Time {mmss(q.time)} · Par {mmss(q.par)}{q.class ? ` · Class ${pc(q.class.correct)} sahi` : ''}</p>
        <TagChip tag={q.tag} copy={an.copy} />
      </button>
    ))}</div>
  </Block>;
}
