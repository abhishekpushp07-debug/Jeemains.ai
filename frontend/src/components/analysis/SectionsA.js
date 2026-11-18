import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { ArrowRight } from 'lucide-react';
import { Block, Tile, Later, Pills, mmss, pc, pick, slug, TIP, AXIS } from './parts';

const RANK_NOTE = {
  sealed: 'Rank sabka time khatam hone par aayega', preparing: 'Class ka data ban raha hai…', staff: 'Staff attempt par Rank nahi banta',
  original_only: 'Rank sirf original Score par banta hai', none: 'Is test par Rank nahi banta',
};

export function Overview({ an, onDrill, go }) {
  const o = an.overview, by = t => pick(an, q => q.outcome === t), got = Math.max(0, o.score);
  const ring = [{ v: got }, { v: Math.max(0, o.maximum - got) }];
  return <>
    <Block id="score" title="Aapka Score" note={`${an.paper.count} sawaal · ${an.paper.minutes ? an.paper.minutes + ' min' : 'Untimed'} · +${an.paper.marks.correct} / ${an.paper.marks.wrong}`}>
      <div className="a2-hero">
        <div className="a2-ring" data-testid="a2-score-ring">
          <ResponsiveContainer width="100%" height={190}><PieChart><Pie data={ring} dataKey="v" innerRadius={66} outerRadius={86} startAngle={90} endAngle={-270} stroke="none" isAnimationActive={false}><Cell fill="var(--a-brand)" /><Cell fill="var(--a-track)" /></Pie></PieChart></ResponsiveContainer>
          <div><strong data-testid="a2-score">{o.score}</strong><span>/ {o.maximum}</span></div>
        </div>
        <div className="a2-tiles">
          <Tile id="rank" label="Rank" value={o.rank ? '#' + o.rank : '—'} sub={o.rank ? `${o.of} students mein` : RANK_NOTE[an.class.state]} tone="brand" />
          <Tile id="percentile" label="Percentile" value={o.percentile ?? '—'} sub={o.rank ? 'is paper par' : ''} />
          <Tile id="accuracy" label="Accuracy" value={pc(o.accuracy)} sub={`${o.correct} sahi / ${o.attempted} attempted`} />
          <Tile id="time" label="Time" value={mmss(o.time_used)} sub={o.time_on_screen != null ? 'Screen par ' + mmss(o.time_on_screen) : 'paper mein laga'} />
        </div>
      </div>
      <div className="a2-tiles four">
        <Tile id="attempted" label="Attempted" value={o.attempted} ids={pick(an, q => ['correct', 'incorrect'].includes(q.outcome))} onDrill={onDrill} />
        <Tile id="correct" label="Sahi" value={o.correct} tone="good" ids={by('correct')} onDrill={onDrill} />
        <Tile id="incorrect" label="Galat" value={o.incorrect} tone="bad" ids={by('incorrect')} onDrill={onDrill} />
        <Tile id="skipped" label="Chhode" value={o.skipped} tone="mute" ids={by('skipped')} onDrill={onDrill} />
      </div>
    </Block>
    <Block id="subjects" title="Subject-wise" note="Har subject ka Score, Accuracy aur Time.">
      <div className="a2-cards">
        {o.subjects.map(g => (
          <article className="a2-card" key={g.name} data-testid={'a2-subject-' + slug(g.name)}>
            <h4>{g.name}</h4><strong>{g.score}<small> / {g.maximum}</small></strong>
            <p>{g.correct} sahi · {g.incorrect} galat · {g.skipped} chhode</p>
            <p>Accuracy {pc(g.accuracy)}{g.time != null ? ' · Time ' + mmss(g.time) : ''}</p>
          </article>
        ))}
      </div>
    </Block>
    <Block id="next3" title="Agle mock ke liye 3 kaam" note="Jahan sabse zyada marks daav par hain, wahi pehle. Yeh sirf aapke apne data se bana hai, koi AI nahi.">
      {o.next3.length ? <ol className="a2-next">
        {o.next3.map((x, i) => (
          <li key={x.key} data-testid={'a2-next-' + x.key}>
            <span className="a2-next-no">{i + 1}</span>
            <div><h4>{x.title} <b>+{x.marks} marks</b></h4><p>{x.detail}</p>
              <div className="a2-row">
                {x.questions.length > 0 && <button type="button" className="a2-link" data-testid={'a2-next-questions-' + x.key} onClick={() => onDrill(x.title, x.questions)}>{x.questions.length} sawaal dekho</button>}
                <button type="button" className="a2-link" data-testid={'a2-next-open-' + x.key} onClick={() => go(x.section === 'questions' ? 'qs' : x.section)}>Poora hisaab <ArrowRight size={13} /></button>
              </div>
            </div>
          </li>
        ))}
      </ol> : <p className="a2-empty" data-testid="a2-next-empty">Is attempt mein koi bada sudhaar ka point nahi mila. Ab naye sawaal try karo.</p>}
    </Block>
  </>;
}

const HAAL = { strong: ['Mazboot', 'good'], steady: ['Theek', 'info'], weak: ['Kamzor', 'bad'] };

export function Performance({ an, onDrill }) {
  const subjects = an.performance.subjects;
  const [name, setName] = useState(subjects[0]?.name);
  const g = subjects.find(s => s.name === name) || subjects[0];
  if (!g) return null;
  const ids = test => pick(an, q => q.subject === g.name && test(q));
  return <>
    <Pills id="perf-subject" value={g.name} onChange={setName} items={subjects.map(s => [s.name, s.name])} />
    <Block id="performance" title={g.name} note="Is subject mein aapka poora hisaab.">
      <div className="a2-tiles four">
        <Tile id="perf-score" label="Score" value={`${g.score} / ${g.maximum}`} tone="brand" />
        <Tile id="perf-accuracy" label="Accuracy" value={pc(g.accuracy)} sub={`${g.correct} sahi / ${g.attempted}`} ids={ids(q => q.outcome === 'correct')} onDrill={onDrill} />
        <Tile id="perf-attempt-rate" label="Attempt rate" value={pc(g.attempt_rate)} sub={`${g.skipped} chhode`} ids={ids(q => q.outcome === 'skipped')} onDrill={onDrill} />
        <Tile id="perf-negative" label="Negative marks" value={g.negative ? '−' + g.negative : 0} sub={`${g.incorrect} galat`} tone="bad" ids={ids(q => q.outcome === 'incorrect')} onDrill={onDrill} />
      </div>
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-type-table">
        <thead><tr><th>Type</th><th>Sawaal</th><th>Sahi</th><th>Galat</th><th>Chhode</th><th>Accuracy</th><th>Score</th></tr></thead>
        <tbody>{Object.entries(g.types).map(([t, d]) => <tr key={t}><td>{t === 'integer' ? 'Numerical' : 'MCQ'}</td><td>{d.count}</td><td>{d.correct}</td><td>{d.incorrect}</td><td>{d.skipped}</td><td>{pc(d.accuracy)}</td><td>{d.score}</td></tr>)}</tbody>
      </table></div>
    </Block>
    {g.chapters.length > 0 && <Block id="chapters" title="Chapter-wise" note="3 se kam sawaal wale chapter par Mazboot / Kamzor nahi likha jaata.">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-chapter-table">
        <thead><tr><th>Chapter</th><th>Sawaal</th><th>Sahi</th><th>Galat</th><th>Chhode</th><th>Accuracy</th><th>Haal</th></tr></thead>
        <tbody>{g.chapters.map(c => <tr key={c.name}><td>{c.name}</td><td>{c.count}</td><td>{c.correct}</td><td>{c.incorrect}</td><td>{c.skipped}</td><td>{pc(c.accuracy)}</td><td>{c.label ? <span className={'a2-tag tone-' + HAAL[c.label][1]}>{HAAL[c.label][0]}</span> : '—'}</td></tr>)}</tbody>
      </table></div>
    </Block>}
  </>;
}

const STEP = {
  careless: ['Careless galti theek', 'Jaldbaazi mein galat hue sawaal sahi hote to'],
  guard: ['Mushkil par risk nahi', 'Jo Tough sawaal class mein bhi kam bane, unhe chhod dete to'],
  reinvest: ['Atka time wapas', 'Jahan time atka, woh chhode hue sawaalon ko dete to'],
};
const AT = { current: 'Abhi', realistic: 'Realistic target', maximum: 'Maximum potential' };

export function Potential({ an, onDrill }) {
  const p = an.potential, most = Math.max(p.paper_maximum, 1), w = v => Math.max(0, Math.min(100, (100 * v) / most)) + '%';
  let run = p.current;
  const rows = p.steps.map(s => { const from = run; run += s.marks; return { ...s, from }; });
  const ranked = p.at.filter(x => x.rank);
  return <>
    <Block id="potential" title="Yahan se marks bach sakte the" note="Seedha hisaab hai, koi andaaza nahi. Har step ke peeche ke sawaal dekh sakte ho.">
      {!p.available && <p className="a2-empty" data-testid="a2-potential-partial">Is attempt mein time record nahi hua, isliye Careless aur Time wale step 0 hain. Agle mock se poore dikhenge.</p>}
      <div className="a2-steps" data-testid="a2-potential-steps">
        <div className="a2-step"><span>Abhi ka Score</span><div className="a2-track"><i className="now" style={{ width: w(p.current) }} /></div><strong data-testid="a2-potential-current">{p.current}</strong></div>
        {rows.map(s => (
          <div className="a2-step" key={s.key} data-testid={'a2-potential-step-' + s.key}>
            <span>+ {STEP[s.key][0]}<small>{STEP[s.key][1]}{s.key === 'reinvest' && s.minutes ? ` (${s.minutes} min)` : ''}</small>
              {s.questions.length > 0 && <button type="button" className="a2-link" data-testid={'a2-potential-questions-' + s.key} onClick={() => onDrill(STEP[s.key][0], s.questions)}>{s.questions.length} sawaal dekho</button>}</span>
            <div className="a2-track"><i className="base" style={{ width: w(s.from) }} /><i className="gain" style={{ left: w(s.from), width: w(s.marks) }} /></div>
            <strong>+{s.marks}</strong>
          </div>
        ))}
        <div className="a2-step total"><span>Realistic target<small>Careless + risk poora, time ka aadha</small></span><div className="a2-track"><i className="goal" style={{ width: w(p.realistic) }} /></div><strong data-testid="a2-potential-realistic">{p.realistic}</strong></div>
        <div className="a2-step total"><span>Maximum potential</span><div className="a2-track"><i className="goal" style={{ width: w(p.maximum) }} /></div><strong data-testid="a2-potential-maximum">{p.maximum}</strong></div>
      </div>
    </Block>
    {ranked.length > 0 && <Block id="potential-rank" title="Itne marks par Rank lagbhag" note="Isi paper ke students ke Score se nikala gaya hai.">
      <div className="a2-tiles">{ranked.map(x => <Tile key={x.key} id={'at-' + x.key} label={`${AT[x.key]} · ${x.score} marks`} value={'#' + x.rank} sub={`${x.of} mein · Percentile ${x.percentile}`} tone={x.key === 'current' ? '' : 'good'} />)}</div>
    </Block>}
  </>;
}

const HEAD = ['perfect', 'wasted', 'overtime', 'confused', 'concept_gap'];
const HEAD_TONE = { perfect: 'good', wasted: 'bad', overtime: 'warn', confused: 'warn', concept_gap: 'bad' };
const BARS = [['Perfect', 'var(--a-good)'], ['Careless', 'var(--a-bad)'], ['Overtime', 'var(--a-warn)'], ['Confused', 'var(--a-info)'], ['Concept gap', 'var(--a-mute)']];

export function Quality({ an, onDrill }) {
  const q = an.quality, t = an.copy.tags;
  if (!q.available) return <Later id="quality" />;
  const over = ['slow_correct', 'costly_overtime'];
  const ids = k => pick(an, x => (k === 'overtime' ? over.includes(x.tag) : x.tag === k));
  const name = k => (k === 'overtime' ? 'Overtime' : t[k][0]);
  const about = k => (k === 'overtime' ? 'Par time se kaafi zyada laga (Slow-correct + Mehnga overtime).' : t[k][1]);
  const data = q.by_subject.map(s => ({ name: s.name, Perfect: s.counts.perfect, Careless: s.counts.wasted, Overtime: s.counts.slow_correct + s.counts.costly_overtime, Confused: s.counts.confused, 'Concept gap': s.counts.concept_gap }));
  const from = q.par_from;
  return <>
    <Block id="quality" title="Har sawaal ko ek tag" note={`${an.copy.time_label} Par time: ${from.solvers ? from.solvers + ' sawaal students ke data se, ' : ''}${from.standard || 0} sawaal paper standard se.`}>
      <div className="a2-tiles five">{HEAD.map(k => <Tile key={k} id={'quality-' + k} label={name(k)} value={q.headline[k]} sub={about(k)} tone={HEAD_TONE[k]} ids={ids(k)} onDrill={onDrill} />)}</div>
      <div className="a2-row wrap" data-testid="a2-quality-rest">{[...over, 'smart_skip', 'not_seen', 'no_score'].map(k => q.counts[k] > 0 && <button type="button" key={k} className="a2-link" title={t[k][1]} data-testid={'a2-quality-rest-' + k} onClick={() => onDrill(t[k][0], ids(k))}>{t[k][0]}: {q.counts[k]}</button>)}</div>
    </Block>
    <Block id="quality-subjects" title="Subject × tag">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-quality-table">
        <thead><tr><th>Subject</th>{BARS.map(b => <th key={b[0]}>{b[0]}</th>)}</tr></thead>
        <tbody>{data.map(r => <tr key={r.name}><td>{r.name}</td>{BARS.map(b => <td key={b[0]}>{r[b[0]]}</td>)}</tr>)}</tbody>
      </table></div>
      <div className="a2-chart" data-testid="a2-quality-chart"><ResponsiveContainer width="100%" height={240}><BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" /><XAxis dataKey="name" tick={AXIS} /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
        {BARS.map(b => <Bar key={b[0]} dataKey={b[0]} fill={b[1]} radius={[3, 3, 0, 0]} />)}
      </BarChart></ResponsiveContainer></div>
    </Block>
  </>;
}
