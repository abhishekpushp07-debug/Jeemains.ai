import React from 'react';
import { TagChip, mmss, pc } from './parts';

// One line above a solution: the student's time against par and against the class.
export function SolutionInsight({ q, copy }) {
  if (!q) return null;
  const c = q.class;
  return (
    <div className="a2-solution-line" data-testid="solution-insight-line">
      <b>Q{q.number}</b><span>{q.subject}</span><span>{copy.levels[q.difficulty]}</span>
      {q.time != null && <span data-testid="solution-insight-time">Aapka time {mmss(q.time)}</span>}
      {q.par != null && <span title={q.par_source === 'solvers' ? `${q.par_n} solvers se` : 'paper standard'}>Par {mmss(q.par)}</span>}
      {c && <span data-testid="solution-insight-class">{pc(c.correct)} ne sahi kiya</span>}
      {c?.topper_time > 0 && <span>Topper {mmss(c.topper_time)}</span>}
      {c?.top_wrong && <span>Sabse zyada galti: option {c.top_wrong.option} ({c.top_wrong.percent}%)</span>}
      {q.visits > 1 && <span>{q.visits} baar dekha</span>}
      {q.changed && <span>Jawab badla {q.changed}</span>}
      {q.tag && <TagChip tag={q.tag} copy={copy} />}
    </div>
  );
}
