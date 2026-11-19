import React, { useState } from 'react';
import { Block, Tile, Pills, Meter, pc, pick, mmss } from './parts';
import { explain } from './explain';

const HAAL = { strong: ['Mazboot', 'good'], steady: ['Theek', 'info'], weak: ['Kamzor', 'bad'] };

function AllSubjects({ subjects, setName, X }) {
  const sum = k => subjects.reduce((a, g) => a + (g[k] || 0), 0);
  return (
    <Block id="performance" kicker="SAB SUBJECTS" title="Subject vs subject" info={X.attempt_rate} note="Row par tap karo, us subject ka poora hisaab khulega.">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-subject-table">
        <thead><tr><th>Subject</th><th>Score</th><th className="w">Score %</th><th>Sahi</th><th>Galat</th><th>Chhode</th><th>Dekha hi nahi</th><th>Accuracy</th><th>Attempt rate</th><th>Negative</th><th>Time</th></tr></thead>
        <tbody>{subjects.map(g => (
          <tr key={g.name} className="tap" onClick={() => setName(g.name)} data-testid={'a2-subject-row-' + g.name.toLowerCase()}>
            <td><b>{g.name}</b></td><td>{g.score} / {g.maximum}</td><td className="w"><Meter value={Math.max(0, g.score)} max={g.maximum} /></td>
            <td className="good">{g.correct}</td><td className="bad">{g.incorrect}</td><td>{g.skipped}</td><td>{g.not_seen}</td>
            <td>{pc(g.accuracy)}</td><td>{pc(g.attempt_rate)}</td><td className="bad">{g.negative ? '−' + g.negative : 0}</td><td>{mmss(g.time)}</td>
          </tr>
        ))}
        {subjects.length > 1 && <tr data-testid="a2-subject-row-total"><td><b>Kul</b></td><td><b>{sum('score')} / {sum('maximum')}</b></td><td className="w" /><td>{sum('correct')}</td><td>{sum('incorrect')}</td><td>{sum('skipped')}</td><td>{sum('not_seen')}</td><td /><td /><td className="bad">{sum('negative') ? '−' + sum('negative') : 0}</td><td /></tr>}
        </tbody>
      </table></div>
    </Block>
  );
}

function OneSubject({ an, g, onDrill, X }) {
  const ids = test => pick(an, q => q.subject === g.name && test(q));
  return <>
    <Block id="performance" kicker="SUBJECT" title={g.name} note="Is subject mein aapka poora hisaab. Tile par tap karo, sawaal khulenge.">
      <div className="a2-tiles five">
        <Tile id="perf-score" label="Score" value={`${g.score} / ${g.maximum}`} tone="brand" />
        <Tile id="perf-accuracy" label="Accuracy" value={pc(g.accuracy)} sub={`${g.correct} sahi / ${g.attempted}`} ids={ids(q => q.outcome === 'correct')} onDrill={onDrill} tone="good" />
        <Tile id="perf-attempt-rate" label="Attempt rate" value={pc(g.attempt_rate)} sub={`${g.skipped} chhode`} ids={ids(q => q.outcome === 'skipped')} onDrill={onDrill} info={X.attempt_rate} />
        <Tile id="perf-negative" label="Negative marks" value={g.negative ? '−' + g.negative : 0} sub={`${g.incorrect} galat`} tone="bad" ids={ids(q => q.outcome === 'incorrect')} onDrill={onDrill} info={X.negative} />
        <Tile id="perf-not-seen" label="Dekha hi nahi" value={g.not_seen} sub="khula hi nahi" tone="mute" ids={ids(q => q.outcome === 'skipped' && !q.seen)} onDrill={onDrill} info={X.not_seen} />
      </div>
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-type-table">
        <thead><tr><th>Type</th><th>Sawaal</th><th>Sahi</th><th>Galat</th><th>Chhode</th><th>Accuracy</th><th>Score</th></tr></thead>
        <tbody>{Object.entries(g.types).map(([t, d]) => <tr key={t}><td><b>{t === 'integer' ? 'Numerical' : 'MCQ'}</b></td><td>{d.count}</td><td>{d.correct}</td><td>{d.incorrect}</td><td>{d.skipped}</td><td>{pc(d.accuracy)}</td><td>{d.score} / {d.maximum}</td></tr>)}</tbody>
      </table></div>
    </Block>
    {g.chapters.length > 0 && <Block id="chapters" kicker="CHAPTER-WISE" title={`${g.name} ke chapters`} info={X.chapters} note="3 se kam sawaal wale chapter par Mazboot / Kamzor nahi likha jaata. Row par tap karo, us chapter ke sawaal khulenge.">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-chapter-table">
        <thead><tr><th>Chapter</th><th>Sawaal</th><th>Sahi</th><th>Galat</th><th>Chhode</th><th>Accuracy</th><th>Marks gaye</th><th>Haal</th></tr></thead>
        <tbody>{g.chapters.map(c => (
          <tr key={c.name} className="tap" onClick={() => onDrill(`${g.name} · ${c.name}`, ids(q => q.topic === c.name))} data-testid={'a2-chapter-row-' + c.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}>
            <td><b>{c.name}</b></td><td>{c.count}</td><td>{c.correct}</td><td>{c.incorrect}</td><td>{c.skipped}</td><td>{pc(c.accuracy)}</td>
            <td className={c.lost ? 'bad' : ''}>{c.lost ? '−' + c.lost : 0}</td>
            <td>{c.label ? <span className={'a2-tag tone-' + HAAL[c.label][1]}>{HAAL[c.label][0]}</span> : '—'}</td>
          </tr>
        ))}</tbody>
      </table></div>
    </Block>}
  </>;
}

function Weak({ weak, onDrill }) {
  if (!weak.length) return null;
  const most = Math.max(1, ...weak.map(w => w.lost));
  return (
    <Block id="weak" kicker="SABSE MEHNGE CHAPTERS" title="Marks kis chapter se gaye" note="Galat jawab (marks + negative) aur chhode sawaalon ke marks milaakar. Bar par tap karo.">
      <div className="a2-bars" data-testid="a2-weak-chapters">
        {weak.map(w => (
          <button type="button" key={w.subject + w.name} className="a2-bar-row" onClick={() => onDrill(`${w.name} (${w.subject})`, w.questions)} data-testid={'a2-weak-' + w.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}>
            <span><b>{w.name}</b><small>{w.subject} · {w.wrong} galat, {w.skipped} chhode</small></span>
            <Meter value={w.lost} max={most} tone="bad" /><strong>−{w.lost}</strong>
          </button>
        ))}
      </div>
    </Block>
  );
}

function Sections({ s }) {
  const m = s.main, b = s.bonus;
  return (
    <Block id="sections" kicker="SECTION-WISE" title="Paper ke sections">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-section-table">
        <thead><tr><th>Section</th><th>Score</th><th>Sahi</th><th>Galat</th><th>Chhode</th></tr></thead>
        <tbody>
          {s.sections.map(x => <tr key={x.name}><td><b>{x.name}</b></td><td>{x.score} / {x.maximum}</td><td>{x.correct}</td><td>{x.incorrect}</td><td>{x.skipped}</td></tr>)}
          {m && <tr><td><b>Main total ({m.count})</b></td><td>{m.score} / {m.maximum}</td><td>{m.correct}</td><td>{m.incorrect}</td><td>{m.skipped}</td></tr>}
          {b && <tr><td><b>Bonus ({b.count})</b></td>{b.entered ? <><td>{b.score} / {b.maximum}</td><td>{b.correct}</td><td>{b.incorrect}</td><td>{b.skipped}</td></> : <td colSpan={4}>Bonus khola hi nahi</td>}</tr>}
        </tbody>
      </table></div>
    </Block>
  );
}

export function Performance({ an, onDrill }) {
  const P = an.performance, subjects = P.subjects;
  const [name, setName] = useState('all');
  const g = subjects.find(s => s.name === name), X = explain(an);
  if (!subjects.length) return null;
  return <>
    <Pills id="perf-subject" value={g ? name : 'all'} onChange={setName} items={[['all', 'Sab subjects'], ...subjects.map(s => [s.name, s.name])]} />
    {g ? <OneSubject an={an} g={g} onDrill={onDrill} X={X} /> : <AllSubjects subjects={subjects} setName={setName} X={X} />}
    <Weak weak={g ? P.weak.filter(w => w.subject === g.name) : P.weak} onDrill={onDrill} />
    {!g && P.sections && <Sections s={P.sections} />}
    {!P.has_chapters && <p className="a2-empty" data-testid="a2-no-chapters">Is paper ke sawaalon par chapter ka tag nahi hai, isliye chapter-wise hisaab nahi bana.</p>}
  </>;
}
