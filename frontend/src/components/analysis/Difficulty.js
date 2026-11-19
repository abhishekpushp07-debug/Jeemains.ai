import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { Droplets, Trophy } from 'lucide-react';
import { Block, Pills, Meter, QChips, pc, pick, TIP, LEGEND, AXIS, GRID } from './parts';
import { explain } from './explain';

const LEVELS = ['easy', 'moderate', 'tough', 'unrated'];
const COLS = [['correct', 'Sahi', 'good'], ['incorrect', 'Galat', 'bad'], ['skipped', 'Chhode', 'mute']];
const SOURCE = { students: 'students ke result se', early: 'shuruaati result se', paper: 'paper ke tag se', none: 'abhi Not rated' };
const LTONE = { easy: 'good', moderate: 'warn', tough: 'bad', unrated: 'mute' };

function Table({ an, name, levels, onDrill }) {
  const L = an.copy.levels, shown = LEVELS.filter(l => levels[l]?.count);
  const inside = q => name === 'all' || q.subject === name;
  const ids = (l, o) => pick(an, q => q.difficulty === l && q.outcome === o && inside(q));
  const from = l => {
    const by = {};
    an.questions.forEach(q => { if (q.difficulty === l && inside(q)) by[q.difficulty_source] = (by[q.difficulty_source] || 0) + 1; });
    return Object.entries(by).map(([k, n]) => (l === 'unrated' ? SOURCE.none : `${n} ${SOURCE[k] || k}`)).join(', ');
  };
  const data = shown.map(l => ({ name: L[l], Sahi: levels[l].correct, Galat: levels[l].incorrect, Chhode: levels[l].skipped }));
  return <>
    <div className="a2-scroll"><table className="a2-table" data-testid="a2-difficulty-table">
      <thead><tr><th>Level</th>{COLS.map(c => <th key={c[0]}>{c[1]}</th>)}<th className="w">Accuracy</th><th>Level kahan se aaya</th></tr></thead>
      <tbody>{shown.map(l => {
        const x = levels[l], tried = x.correct + x.incorrect, acc = tried ? Math.round((1000 * x.correct) / tried) / 10 : null;
        return <tr key={l}><td><span className={'a2-dot tone-' + LTONE[l]} /><b>{L[l]}</b> <small>({x.count})</small></td>{COLS.map(([k, label, tone]) => {
          const list = ids(l, k);
          return <td key={k}>{list.length ? <button type="button" className={'a2-cell tone-' + tone} data-testid={`a2-difficulty-${l}-${k}`} onClick={() => onDrill(`${L[l]} · ${label}`, list)}>{x[k]} / {x.count}</button> : `${x[k]} / ${x.count}`}</td>;
        })}<td className="w"><div className="a2-twin one"><Meter value={acc || 0} tone={LTONE[l]} /><span>{pc(acc)}</span></div></td><td data-testid={'a2-difficulty-source-' + l}><small>{from(l)}</small></td></tr>;
      })}</tbody>
    </table></div>
    <div className="a2-chart" data-testid="a2-difficulty-chart"><ResponsiveContainer width="100%" height={230}><BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
      <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} /><Legend {...LEGEND} />
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

function Unlock({ an }) {
  const u = an.difficulty.unlock, d = an.rules?.difficulty;
  if (!u) return null;
  const have = u.have || 0;
  const next = !d ? '' : have < d.early_attempted ? ` Kisi sawaal ko kam se kam ${d.early_attempted} students attempt karein to shuruaati level khulta hai (${d.early_attempted - have} aur chahiye), aur ${d.min_attempted} par pakka level.`
    : ` Kisi sawaal ko ${d.min_attempted} students attempt karein to uska level pakka hota hai.`;
  return <p className="a2-foot" data-testid="a2-difficulty-unlock"><b>{u.unrated}</b> sawaal abhi Not rated hain: paper mein unka tag nahi hai aur abhi {have ? `${have} students` : 'kisi aur student'} ne yeh paper {have ? 'diya hai' : 'nahi diya'}.{next} Tab tak andaaza nahi lagaya.</p>;
}

export function Difficulty({ an, onDrill, onOpen }) {
  const d = an.difficulty, X = explain(an);
  const [name, setName] = useState('all');
  const levels = name === 'all' ? d.all : d.by_subject.find(s => s.name === name)?.levels || d.all;
  const tough = name === 'all' ? d.tough_solved : d.tough_solved.filter(i => an.questions.find(q => q.id === i)?.subject === name);
  return <>
    <Pills id="difficulty-subject" value={name} onChange={setName} items={[['all', 'Sab subjects'], ...d.by_subject.map(s => [s.name, s.name])]} />
    <Leak leak={d.leak} onDrill={onDrill} />
    <Block id="difficulty" kicker="EASY · MODERATE · TOUGH" title="Difficulty ke hisaab se" info={X.difficulty} note={`Har level ke saath likha hai ki woh kahan se aaya.${d.class_n ? ` Class: ${d.class_n} students.` : ''} Jahan data kam hai wahan Not rated likha hai, andaaza nahi lagaya.`}>
      <Table an={an} name={name} levels={levels} onDrill={onDrill} />
      <Unlock an={an} />
    </Block>
    {tough.length > 0 && <Block id="tough-solved" kicker="AAPKI TAAQAT" title={`${tough.length} Tough sawaal jo aapne nikale`} note="Tough = class mein 35% se kam students se bana, ya paper mein Hard likha tha. Inka tareeka yaad rakho.">
      <div className="a2-row"><Trophy size={20} className="a2-gold" aria-hidden="true" /><QChips id="tough" ids={tough} an={an} onOpen={onOpen} /></div>
    </Block>}
  </>;
}
