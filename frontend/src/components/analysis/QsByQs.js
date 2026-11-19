import React, { useState } from 'react';
import { Block, Pills, Key, TagChip, RESULT, OUT_TONE, mmss, pc } from './parts';
import { QGrid } from './charts';

const FILTERS = [['all', 'Sab'], ['wrong', 'Galat'], ['skipped', 'Chhode'], ['not_seen', 'Dekha hi nahi'], ['seen_skipped', 'Dekha, jawab nahi'], ['careless', 'Careless'], ['overtime', 'Overtime'], ['confused', 'Confused'], ['marked', 'Marked'], ['changed', 'Jawab badla']];
const TEST = {
  all: () => true, wrong: q => q.outcome === 'incorrect', skipped: q => q.outcome === 'skipped', careless: q => q.tag === 'wasted',
  not_seen: q => q.outcome === 'skipped' && q.seen === false, seen_skipped: q => q.outcome === 'skipped' && q.seen !== false,
  overtime: q => ['slow_correct', 'costly_overtime'].includes(q.tag), confused: q => q.tag === 'confused', marked: q => q.marked, changed: q => !!q.changed,
};
const SORT = { number: (a, b) => a.number - b.number, time: (a, b) => (b.time || 0) - (a.time || 0), hard: (a, b) => (a.class?.correct ?? 101) - (b.class?.correct ?? 101), marks: (a, b) => a.marks - b.marks };
const LEVELS = ['easy', 'moderate', 'tough', 'unrated'];
const result = q => (q.outcome === 'skipped' && q.seen === false ? 'Dekha nahi' : RESULT[q.outcome]);

function Row({ q, an, them, onOpen }) {
  const c = q.class, L = an.copy.levels;
  return (
    <tr className="tap" data-testid={'a2-qs-row-' + q.number} onClick={() => onOpen(q.id)}>
      <td><b>{q.number}</b></td><td>{q.subject}</td>{an.performance.has_chapters && <td>{q.topic || '—'}</td>}<td>{L[q.difficulty]}</td>
      <td>{q.response || '—'}{q.changed ? <small> ({q.changed})</small> : null}</td><td>{q.answer}</td>
      <td><span className={'a2-out tone-' + OUT_TONE[q.outcome]}>{result(q)}</span></td><td className={q.marks < 0 ? 'bad' : q.marks > 0 ? 'good' : ''}>{q.marks > 0 ? '+' : ''}{q.marks}</td>
      <td className="a2-mono">{mmss(q.time)}</td><td className="a2-mono">{mmss(q.par)}</td>
      {them && <td className="a2-mono">{mmss(them[q.id] || null)}</td>}
      <td className="a2-mono">{mmss(c?.avg_time)}</td><td className="a2-mono">{mmss(c?.topper_time || null)}</td><td>{pc(c?.correct)}</td>
      <td>{c?.top_wrong ? `${c.top_wrong.option} (${c.top_wrong.percent}%)` : '—'}</td><td>{q.visits ?? '—'}</td><td><TagChip tag={q.tag} copy={an.copy} /></td>
    </tr>
  );
}

function Card({ q, an, them, onOpen }) {
  const c = q.class, L = an.copy.levels;
  return (
    <button type="button" className={'a2-qs-card tone-' + OUT_TONE[q.outcome]} data-testid={'a2-qs-card-' + q.number} onClick={() => onOpen(q.id)}>
      <div><b>Q{q.number}</b><span>{q.subject} · {L[q.difficulty]}</span><span className={'a2-out tone-' + OUT_TONE[q.outcome]}>{result(q)} {q.marks > 0 ? '+' : ''}{q.marks}</span></div>
      <p>Aapka <b>{q.response || '—'}</b> · Sahi <b>{q.answer}</b>{q.changed ? ` · badla ${q.changed}` : ''}</p>
      <p className="a2-mono">Time {mmss(q.time)} · Par {mmss(q.par)}{them ? ` · Unka ${mmss(them[q.id] || null)}` : ''}</p>
      {c && <p>Class: {pc(c.correct)} sahi · avg {mmss(c.avg_time)} · topper {mmss(c.topper_time || null)}{c.top_wrong ? ` · ${c.top_wrong.percent}% ne ${c.top_wrong.option} chuna` : ''}</p>}
      <TagChip tag={q.tag} copy={an.copy} />
    </button>
  );
}

export function QsByQs({ an, onOpen }) {
  const [f, setF] = useState('all');
  const [subject, setSubject] = useState('all');
  const [level, setLevel] = useState('all');
  const [sort, setSort] = useState('number');
  const subjects = [...new Set(an.questions.map(q => q.subject))];
  const levels = LEVELS.filter(l => an.questions.some(q => q.difficulty === l));
  const base = an.questions.filter(q => (subject === 'all' || q.subject === subject) && (level === 'all' || q.difficulty === level));
  const rows = base.filter(TEST[f]).sort(SORT[sort]);
  const them = an.compare?.available ? an.compare.times : null;
  const heat = an.questions.some(q => q.class);
  return <>
    <Block id="qs-grid" kicker="POORA PAPER EK NAZAR MEIN" title="Sawaalon ka grid" note={`Rang = aapka result. Kone ka dot = tag ka rang.${heat ? ' Neeche ki neeli patti = class mein kitne % ne sahi kiya.' : ''} Number par tap karo, solution khulega.`}>
      <QGrid an={an} onOpen={onOpen} detail />
      <Key items={[['Sahi', 'good'], ['Galat', 'bad'], ['Chhoda', 'mute'], ['Marked for review', 'warn'], ...(heat ? [['Class mein % sahi', 'info']] : [])]} />
    </Block>
    <Block id="qs" kicker="QS BY QS" title="Har sawaal ka hisaab" note={`${rows.length} / ${an.questions.length} sawaal. Kisi bhi sawaal par tap karo, uska solution khulega.`}
      action={<>
        {levels.length > 1 && <label className="a2-sort">Level <select value={level} onChange={e => setLevel(e.target.value)} data-testid="a2-qs-level"><option value="all">Sab level</option>{levels.map(l => <option key={l} value={l}>{an.copy.levels[l]}</option>)}</select></label>}
        <label className="a2-sort">Sort <select value={sort} onChange={e => setSort(e.target.value)} data-testid="a2-qs-sort"><option value="number">Sawaal number</option><option value="time">Sabse zyada time</option><option value="hard">Class mein sabse mushkil</option><option value="marks">Sabse zyada marks gaye</option></select></label>
      </>}>
      {subjects.length > 1 && <Pills id="qs-subject" value={subject} onChange={setSubject} items={[['all', 'Sab subjects'], ...subjects.map(s => [s, s])]} />}
      <Pills id="qs-filter" value={f} onChange={setF} items={FILTERS.map(([k, l]) => [k, `${l} (${base.filter(TEST[k]).length})`])} />
      {!rows.length && <p className="a2-empty" data-testid="a2-qs-empty">Is filter mein koi sawaal nahi.</p>}
      {rows.length > 0 && <div className="a2-scroll a2-qs-wide"><table className="a2-table" data-testid="a2-qs-table">
        <thead><tr><th>Q</th><th>Subject</th>{an.performance.has_chapters && <th>Chapter</th>}<th>Level</th><th>Aapka</th><th>Sahi jawab</th><th>Result</th><th>Marks</th><th>Time</th><th>Par</th>{them && <th>{an.compare.label} · time</th>}<th>Class avg</th><th>Class topper</th><th>Class % sahi</th><th>Sabse zyada galti</th><th>Visits</th><th>Tag</th></tr></thead>
        <tbody>{rows.map(q => <Row key={q.id} q={q} an={an} them={them} onOpen={onOpen} />)}</tbody>
      </table></div>}
      <div className="a2-qs-cards">{rows.map(q => <Card key={q.id} q={q} an={an} them={them} onOpen={onOpen} />)}</div>
    </Block>
  </>;
}
