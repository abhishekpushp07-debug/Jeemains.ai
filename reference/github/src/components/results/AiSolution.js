import React from 'react';
import { Sparkles, Lightbulb, Zap, AlertTriangle, Timer, Target } from 'lucide-react';
import { MathText } from '../QuestionContent';

const Pending = ({ state, number }) => <div className="ai-solution is-pending" data-testid={'ai-solution-pending-' + number}>
  <Sparkles size={16} /> <span>{state === 'under_review' ? 'The AI solution for this question is being double-checked against the answer key by our team.' : 'No saved AI solution is available for this question. Viewing results does not generate one.'}</span>
</div>;

export const AiSolution = ({ item, number }) => {
  if (!item) return null;
  if (item.state !== 'ready' || !item.solution) return <Pending state={item.state} number={number} />;
  const raw = item.solution;
  const s = {...raw,
    difficulty: typeof raw.difficulty === 'string' && raw.difficulty ? raw.difficulty : 'Not rated',
    given: Array.isArray(raw.given) ? raw.given : [],
    steps: Array.isArray(raw.steps) ? raw.steps.filter(st => st && typeof st === 'object') : [],
    common_mistakes: Array.isArray(raw.common_mistakes) ? raw.common_mistakes : [],
  };
  return <section className="ai-solution" data-testid={'ai-solution-' + number}>
    <header className="ai-solution-head">
      <span className="ai-badge" data-testid={'ai-solution-badge-' + number}><Sparkles size={13} /> AI generated</span>
      <h3>Step-by-step solution · 10-mark</h3>
      <span data-testid={'ai-difficulty-' + number} className={'ai-difficulty d-' + s.difficulty.toLowerCase()}>{s.difficulty}</span>
    </header>
    {item.flag && <p className="ai-flag" role="note" data-testid={'ai-solution-flag-' + number}><AlertTriangle size={14} /> {item.flag}</p>}
    <div className="ai-concept"><Target size={15} /><div><strong>Concept</strong><MathText text={s.concept} /></div></div>
    {s.given.length > 0 && <div className="ai-given"><strong>Given</strong><ul>{s.given.map((g, i) => <li key={i}><MathText text={g} /></li>)}</ul></div>}
    <ol className="ai-steps">{s.steps.map((st, i) => <li key={i} data-testid={`ai-step-${number}-${i + 1}`}><span className="ai-step-no">{i + 1}</span><div><strong><MathText text={String(st.title || '').replace(/^\d+\.\s*/, '')} /></strong><MathText text={st.explanation} /></div></li>)}</ol>
    <p className="ai-answer" data-testid={'ai-solution-answer-' + number}>Answer: <strong>({s.final_answer || '—'})</strong></p>
    <div className="ai-cards">
      <div className="ai-card insight"><Lightbulb size={15} /><div><strong>Insight</strong><MathText text={s.insight} /></div></div>
      {s.shortcut && <div className="ai-card shortcut"><Zap size={15} /><div><strong>Exam shortcut</strong><MathText text={s.shortcut} /></div></div>}
      {s.common_mistakes.length > 0 && <div className="ai-card mistakes"><AlertTriangle size={15} /><div><strong>Common mistakes</strong><ul>{s.common_mistakes.map((m, i) => <li key={i}><MathText text={m} /></li>)}</ul></div></div>}
      <div className="ai-card time"><Timer size={15} /><div><strong>Time tip</strong><MathText text={s.time_tip} /></div></div>
    </div>
    <p className="import-fineprint">AI-generated study explanation. AI can make mistakes; the supplied key and your score are never changed by it.</p>
  </section>;
};

export const PeerQuestionStat = ({ p, number }) => {
  if (!p) return null;
  const tried = p.correct + p.incorrect;
  const top = Object.entries(p.option_counts || {}).sort((a, b) => b[1] - a[1])[0];
  return <div className="peer-q-stat" data-testid={'peer-question-stat-' + number}>
    <div className="peer-q-bar" aria-hidden="true"><span className="c" style={{ width: `${(100 * p.correct) / (p.denominator || 1)}%` }} /><span className="w" style={{ width: `${(100 * p.incorrect) / (p.denominator || 1)}%` }} /></div>
    <span><strong>{p.correct} of {tried}</strong> students who attempted solved it{tried ? ` (${Math.round((100 * p.correct) / tried)}%)` : ''} · {p.skipped} skipped · {p.denominator} took the test{top && top[1] ? ` · most chosen: ${top[0]}` : ''}</span>
  </div>;
};
