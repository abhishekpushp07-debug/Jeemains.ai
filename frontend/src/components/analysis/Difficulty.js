import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { Droplets, Trophy } from 'lucide-react';
import { Block, Pills, Meter, QChips, pc, pick, TIP, AXIS, GRID } from './parts';

const LEVELS = ['easy', 'moderate', 'tough', 'unrated'];
const COLS = [['correct', 'Sahi', 'good'], ['incorrect', 'Galat', 'bad'], ['skipped', 'Chhode', 'mute']];
const SOURCE = { students: 'students ke result se', early: 'shuruaati result se', paper: 'paper ke tag se', none: 'abhi Not rated' };
const LTONE = { easy: 'good', moderate: 'warn', tough: 'bad', unrated: 'mute' };

function Table({ an, name, levels, onDrill }) {
  const L = an.copy.levels, shown = LEVELS.filter(l => levels[l]?.count);
  const ids = (l, o) => pick(an, q => q.difficulty === l && q.outcome === o && (name === 'all' || q.subject === name));
  const data = shown.map(l => ({ name: L[l], Sahi: levels[l].correct, Galat: levels[l].incorrect, Chhode: levels[l].skipped }));
  return <>
    <div className="a2-scroll"><table className="a2-table" data-testid="a2-difficulty-table">
      <thead><tr><th>Level</th>{COLS.map(c => <th key={c[0]}>{c[1]}</th>)}<th className="w">Accuracy</th></tr></thead>
      <tbody>{shown.map(l => {
        const x = levels[l], tried = x.correct + x.incorrect, acc = tried ? Math.round((1000 * x.correct) / tried) / 10 : null;
        return <tr key={l}><td><span className={'a2-dot tone-' + LTONE[l]} /><b>{L[l]}</b> <small>({x.count})</small></td>{COLS.map(([k, label, tone]) => {
          const list = ids(l, k);
          return <td key={k}>{list.length ? <button type="button" className={'a2-cell tone-' + tone} data-testid={`a2-difficulty-${l}-${k}`} onClick={() => onDrill(`${L[l]} · ${label}`, list)}>{x[k]} / {x.count}</button> : `${x[k]} / ${x.count}`}</td>;
        })}<td className="w"><div className="a2-twin one"><Meter value={acc || 0} tone={LTONE[l]} /><span>{pc(acc)}</span></div></td></tr>;
      })}</tbody>
    </table></div>
    <div className="a2-chart" data-testid="a2-difficulty-chart"><ResponsiveContainer width="100%" height={230}><BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
      <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
      <Bar dataKey="Sahi" fill="var(--a-good)" radius={[4, 4, 0, 0]} /><Bar dataKey="Galat" fill="var(--a-bad)" radius={[4, 4, 0, 0]} /><Bar dataKey="Chhode" fill="var(--a-mute)" radius={[4, 4, 0, 0]} />
    </BarChart></ResponsiveContainer></div>
  </>;
}

function Leak({ leak, onDrill }) {
  const lost = leak.wrong.length + leak.skipped.length;
  return (
    <div className={'a2-leak' + (lost ? '' : ' none')} data-testid="a2-leak">
      <Droplets size={24} aria-hidden="true" />
      <div><strong>Leak: Easy sawaal</strong>
        <p>{lost ? `${leak.wrong.length} Easy galat aur ${leak.skipped.length} Easy chhoote. Yahan se ${leak.marks} marks bach sakte the. Easy marks sabse sasta Rank hai.` : 'Easy sawaalon mein koi leak nahi mila. Shaandaar!'}</p>
        {lost > 0 && <button type="button" className="a2-link" data-testid="a2-leak-questions" onClick={() => onDrill('Leak: Easy sawaal', [...leak.wrong, ...leak.skipped])}>{lost} sawaal dekho</button>}
      </div>
    </div>
  );
}

export function Difficulty({ an, onDrill, onOpen }) {
  const d = an.difficulty;
  const [name, setName] = useState('all');
  const levels = name === 'all' ? d.all : d.by_subject.find(s => s.name === name)?.levels || d.all;
  const tough = name === 'all' ? d.tough_solved : d.tough_solved.filter(i => an.questions.find(q => q.id === i)?.subject === name);
  const sources = Object.entries(d.sources || {}).map(([k, n]) => `${n} sawaal ${SOURCE[k] || k}`).join(', ');
  return <>
    <Pills id="difficulty-subject" value={name} onChange={setName} items={[['all', 'Sab subjects'], ...d.by_subject.map(s => [s.name, s.name])]} />
    <Leak leak={d.leak} onDrill={onDrill} />
    <Block id="difficulty" kicker="EASY · MODERATE · TOUGH" title="Difficulty ke hisaab se" note={`Level kahan se aaya: ${sources}. Jahan data kam hai wahan Not rated likha hai, andaaza nahi lagaya.`}>
      <Table an={an} name={name} levels={levels} onDrill={onDrill} />
      {d.unlock && <p className="a2-foot" data-testid="a2-difficulty-unlock">{d.unlock.unrated} sawaal abhi Not rated hain. Jaise-jaise aur students yeh paper denge, unka level students ke result se pakka hota jaayega.</p>}
    </Block>
    {tough.length > 0 && <Block id="tough-solved" kicker="AAPKI TAAQAT" title="Tough sawaal jo aapne nikale" note="Yeh woh sawaal hain jo zyadatar students se nahi bane. Inka tareeka yaad rakho.">
      <div className="a2-row"><Trophy size={20} className="a2-gold" aria-hidden="true" /><QChips id="tough" ids={tough} an={an} onOpen={onOpen} /></div>
    </Block>}
  </>;
}
