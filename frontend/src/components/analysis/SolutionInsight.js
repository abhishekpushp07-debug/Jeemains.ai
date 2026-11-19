import React from 'react';
import { TagChip, Meter, Info, mmss, pc } from './parts';
import { Split } from './charts';
import { explain } from './explain';

const baar = n => (n === 1 ? 'Pehli baar khola' : n === 2 ? 'Doosri baar khola' : n === 3 ? 'Teesri baar khola' : `${n}vi baar khola`);
const did = v => (!v.set ? 'jawab nahi diya, aage badhe' : v.set === 'Clear' ? 'jawab hata diya' : v.set.includes('→') ? `jawab badla ${v.set}` : `jawab diya ${v.set}`);
const r1 = v => Math.round(v * 10) / 10;

function TimeCard({ q, about }) {
  const ratio = q.time != null && q.par ? q.time / q.par : null;
  return (
    <article className="a2-sol-card" data-testid="solution-card-time">
      <span className="k">Aapka time vs Par {about && <Info id="sol-par" title="Par time" text={about} />}</span>
      {q.time == null ? <small>Is attempt mein har sawaal ka time record nahi hua tha.</small> : <>
        <div className="pair"><strong data-testid="solution-insight-time">{mmss(q.time)}</strong><small>Par {mmss(q.par)}</small></div>
        {ratio != null && <Meter value={Math.min(ratio, 2)} max={2} tone={ratio <= 1.25 ? 'good' : ratio <= 1.5 ? 'warn' : 'bad'} label="Aapka time, Par ke muqable" />}
        {ratio != null && <small>{q.time <= q.par ? `Par se ${mmss(q.par - q.time)} kam` : `Par se ${mmss(q.time - q.par)} zyada`} · Par {q.par_source === 'solvers' ? `${q.par_n} students ke median se` : 'paper standard se'}</small>}
      </>}
    </article>
  );
}

// Above every solution: the student's time against par, the class on this question, and the student's own path through it.
export function SolutionInsight({ q, an }) {
  if (!q) return null;
  const c = q.class, copy = an.copy, X = explain(an);
  const visits = (an.journey?.visits || []).filter(v => v.q === q.id);
  const least = an.class?.min_finishers || 10;
  const wrong = c?.right_of_attempted != null ? r1(100 - c.right_of_attempted) : null;
  const wait = <small data-testid="solution-class-wait">Class ka data kam se kam {least} students ke baad dikhta hai{an.class?.n ? `. Abhi ${an.class.n} students ne diya hai.` : '.'}</small>;
  return (
    <div className="a2-sol" data-testid="solution-insight">
      <div className="a2-solution-line" data-testid="solution-insight-line">
        <b>Q{q.number}</b><span>{q.subject}</span>{q.topic && <span>{q.topic}</span>}<span>{copy.levels[q.difficulty]}</span>
        {q.visits > 1 && <span>{q.visits} baar dekha</span>}
        {q.changed && <span>Jawab badla {q.changed}</span>}
        {q.tag && <TagChip tag={q.tag} copy={copy} />}
      </div>
      <div className="a2-sol-cards">
        <TimeCard q={q} about={X.par} />
        <article className="a2-sol-card" data-testid="solution-card-class-time">
          <span className="k">Class ka time</span>
          {c ? <>
            <div className="pair"><strong>{mmss(c.avg_time)}</strong><small>average</small></div>
            <small>Topper ka time: <b>{mmss(c.topper_time || null)}</b></small>
          </> : wait}
        </article>
        <article className="a2-sol-card" data-testid="solution-card-right">
          <span className="k">Attempt karne walon mein</span>
          {c && c.right_of_attempted != null ? <>
            <div className="pair"><strong className="good" data-testid="solution-insight-class">{pc(c.right_of_attempted)}</strong><small>sahi</small><strong className="bad">{pc(wrong)}</strong><small>galat</small></div>
            <Split testId="solution-right-bar" label="Attempt karne walon mein sahi aur galat" parts={[['Sahi', c.right_of_attempted, 'good'], ['Galat', wrong, 'bad']]} />
            {c.top_wrong && <small>Sabse zyada chuna galat option: <b>{c.top_wrong.option}</b> ({c.top_wrong.percent}% students)</small>}
          </> : c ? <small>Class mein kisi ne yeh sawaal attempt nahi kiya.</small> : wait}
        </article>
        <article className="a2-sol-card" data-testid="solution-card-attempted">
          <span className="k">Kitno ne attempt kiya</span>
          {c ? <>
            <div className="pair"><strong>{pc(c.attempted)}</strong><small>attempt</small><strong className="mute">{pc(c.skipped)}</strong><small>chhoda</small></div>
            <Split testId="solution-attempt-bar" label="Kitne students ne attempt kiya aur kitno ne chhoda" parts={[['Attempt', c.attempted, 'info'], ['Chhoda', c.skipped, 'mute']]} />
            <small>{c.n} students mein</small>
          </> : wait}
        </article>
      </div>
      {visits.length > 0 && (
        <div className="a2-sol-journey" data-testid="solution-journey">
          <h4>Is sawaal ki journey <small>time = paper shuru hone ke kitni der baad</small></h4>
          <ol>{visits.map((v, i) => (
            <li key={i} data-testid={'solution-journey-step-' + i}>
              <b className="a2-mono">{mmss(v.a)}</b>
              <span>{baar(v.v)} · {mmss(v.d)} ruke · {did(v)}{v.mark === true ? ' · review ke liye mark kiya' : v.mark === false ? ' · mark hataya' : ''}</span>
            </li>
          ))}</ol>
        </div>
      )}
    </div>
  );
}
