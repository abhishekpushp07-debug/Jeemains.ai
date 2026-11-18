// Dream college: up to 5 dream seats per exam kept with the account, each measured against the student's latest
// released full mock ("kitne marks door"), plus the mocks so far as a small trend line.
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Trash2, Lock } from 'lucide-react';
import { useAuth } from '../../lib/auth';
import { EXAM_LABEL } from './rankApi';
import { Heading, Panel, Switch } from './RankUi';
import { dreamsOf, EXAMS, FULL, MAX_DREAMS, mocksOf, removeDream, useDreams } from './rankStore';

/** One dream on a 0..full track: the gold notch is the marks it needs, the fill is the student's score. */
export function DreamMeter({ dream, score, max, testId, onRemove }) {
  const has = score != null;
  const gap = has ? Math.ceil(dream.need - score) : null;
  const pos = v => `${Math.max(0, Math.min(100, (v / max) * 100))}%`;
  return <div className={'rk-dream' + (has && gap <= 0 ? ' is-in' : '')} data-testid={testId}>
    <div className="rk-dream-head"><div><b>{dream.college}</b><small>{dream.branch}</small></div>
      {onRemove ? <button type="button" className="rk-remove" onClick={onRemove} aria-label={`${dream.college} hatao`} data-testid={testId + '-remove'}><Trash2 size={16} /></button> : null}</div>
    <div className="rk-dream-track" aria-hidden="true">
      {dream.range ? <i className="range" style={{ left: pos(dream.range[0]), width: `calc(${pos(dream.range[1])} - ${pos(dream.range[0])})` }} /> : null}
      {has ? <i className="fill" style={{ width: pos(Math.max(0, score)) }} /> : null}
      <i className="need" style={{ left: pos(dream.need) }} />
    </div>
    <p className="rk-dream-line" data-testid={testId + '-line'}>
      {!has ? <>Chahiye <b>{Math.round(dream.need)}</b> / {max}. Ek full mock do, phir yahan dikhega kitne marks door ho.</>
        : gap <= 0 ? <><Sparkles size={15} /> Aapka <b>{score}</b> is seat ke <b>{Math.round(dream.need)}</b> se upar hai. Ise pakka rakho!</>
          : <>Aapka <b>{score}</b>, chahiye <b>{Math.round(dream.need)}</b>: bas <b>{gap} marks</b> door.</>}
    </p>
    {dream.note ? <small className="rk-dim">{dream.note}</small> : null}
  </div>;
}

function Trend({ mocks, dreams, max }) {
  const pts = mocks.slice(0, 8).reverse();
  if (pts.length < 2) return null;
  const W = 320, H = 120, x = i => 16 + (i * (W - 32)) / (pts.length - 1), y = v => H - 14 - (Math.max(0, v) / max) * (H - 28);
  return <figure className="rk-trend" data-testid="dream-trend"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Full mock scores ka trend">
    {dreams.map(d => <line key={d.id} x1="8" x2={W - 8} y1={y(d.need)} y2={y(d.need)} className="need" />)}
    <polyline points={pts.map((m, i) => `${x(i)},${y(m.score)}`).join(' ')} className="line" />
    {pts.map((m, i) => <circle key={m.id} cx={x(i)} cy={y(m.score)} r="4" className="dot" />)}
  </svg><figcaption>Aakhri {pts.length} full mocks · dotted line = dream ke liye chahiye</figcaption></figure>;
}

export function DreamPanel({ onTool }) {
  const { user } = useAuth();
  const s = useDreams();
  const [exam, setExam] = useState('jee');
  if (!user) return <Panel testId="dream-signin"><div className="rk-locked"><Lock size={22} /><div><b>Dream college aapke account ke saath save hote hain</b>
    <p>Sign in karo, 5 dream college chuno, aur har full mock ke baad dekho ki aap kitne marks door ho.</p>
    <Link className="rk-go as-link" to="/login?next=%2Frank%3Ftool%3Ddream" data-testid="dream-signin-link">Sign in karo<ArrowRight size={18} /></Link></div></div></Panel>;
  const dreams = dreamsOf(s, exam), mocks = mocksOf(s, exam), latest = mocks[0];
  return <div className="rk-stack">
    <Switch prefix="dream-exam" value={exam} onChange={setExam} items={EXAMS.map(e => ({ key: e, label: `${EXAM_LABEL[e]} · ${dreamsOf(s, e).length}` }))} />
    {s.notice ? <p className="rk-problem" role="alert" data-testid="dream-notice">{s.notice}</p> : null}
    {!s.loaded ? <div className="rk-loading" data-testid="dream-loading" /> : <>
      <Heading title={dreams.length ? `${dreams.length} / ${MAX_DREAMS} dream college` : 'Abhi koi dream college nahi'}
        sub={latest ? `Aakhri full mock: ${latest.title} · ${latest.score} / ${FULL[exam]}${latest.rawMax !== FULL[exam] ? ` (asli ${latest.raw} / ${latest.rawMax})` : ''}` : `${EXAM_LABEL[exam]} ka full mock dene ke baad yahan aapka score dikhega.`} />
      <div className="rk-list" data-testid="dream-list">{dreams.map((d, i) => <DreamMeter key={d.id} dream={d} score={latest?.score ?? null} max={FULL[exam]} testId={`dream-item-${i}`} onRemove={() => removeDream(d.id)} />)}</div>
      <Trend mocks={mocks} dreams={dreams} max={FULL[exam]} />
      {dreams.length < MAX_DREAMS ? <button type="button" className="rk-outline" onClick={() => onTool('target')} data-testid="dream-add">Dream college jodo (Target marks se)<ArrowRight size={18} /></button> : null}
      <small className="rk-dim">Har college card par "Dream college" dabao. Marks = normal paper par 2026 ki final closing tak pahunchne ke liye.</small>
    </>}
  </div>;
}
