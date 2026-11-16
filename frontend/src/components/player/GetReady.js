import React, { useState } from 'react';
import { Loader2, CheckCircle2, ArrowRight, Clock3, Save, Flag, WifiOff, Trophy, Target } from 'lucide-react';
import { Button } from '../ui/button';

const R = 54, RING = 2 * Math.PI * R;

function rulesFor(a) {
  const { correct, wrong, minutes } = a.rules;
  const result = a.mode === 'series_live'
    ? 'Submit and your score and solutions open right away. Your All India rank for today joins at 11:59 PM.'
    : a.competition_end
      ? 'Submit and your score shows right away. Solutions open when the exam closes for everyone.'
      : 'Submit and your score and solutions open right away.';
  return [
    [Target, `+${correct} for a right answer, ${wrong} for a wrong one, 0 for a skip. Not sure? A smart skip beats a wild guess.`],
    [Clock3, minutes ? `${minutes} minutes on your clock. It starts only when you press Begin now or this countdown reaches zero.` : 'No clock today. Take your time and think it through.'],
    [Save, 'Every answer saves by itself. Watch for “All responses saved” at the top.'],
    [Flag, 'Stuck? Mark it for review, move on, come back later. You can jump to any question anytime.'],
    [WifiOff, 'Net dropped? Keep solving. Your answers wait safely on this phone and send when you are back.'],
    [Trophy, result],
  ];
}

function Countdown({ seconds }) {
  return <div className="get-ready-ring" role="timer" aria-label={`${seconds} seconds left`} data-testid="get-ready-countdown">
    <svg viewBox="0 0 120 120" aria-hidden="true">
      <circle cx="60" cy="60" r={R} className="track" />
      <circle cx="60" cy="60" r={R} className="bar" style={{ strokeDasharray: RING, strokeDashoffset: RING * (1 - Math.min(60, seconds) / 60) }} />
    </svg>
    <strong data-testid="get-ready-seconds">{seconds}</strong><span>sec</span>
  </div>;
}

function PaperLoad({ loaded }) {
  const done = loaded.total === 0 || loaded.done >= loaded.total;
  const pct = loaded.total ? Math.round(100 * loaded.done / loaded.total) : 100;
  return <div className={'get-ready-load' + (done ? ' is-done' : '')} data-testid="get-ready-load">
    <div className="get-ready-load-row">
      <span>{done ? <><CheckCircle2 size={16} /> Whole paper loaded</> : <><Loader2 size={16} className="spin" /> Loading your paper · {loaded.done} / {loaded.total} pictures</>}</span>
      <strong data-testid="get-ready-load-percent">{pct}%</strong>
    </div>
    <div className="get-ready-bar"><i style={{ width: pct + '%' }} /></div>
  </div>;
}

export function GetReady({ attempt: a, seconds, loaded, onBegin }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const done = loaded.total === 0 || loaded.done >= loaded.total;
  async function go() {
    setBusy(true); setError('');
    try { await onBegin(); } catch (e) { setError(e.message); setBusy(false); }
  }
  return <div className="get-ready" data-testid="get-ready-screen">
    <div className="get-ready-card">
      <div className="get-ready-top">
        <Countdown seconds={seconds} />
        <div>
          <span className="get-ready-kicker">GET SET · 60 SECONDS</span>
          <h1 data-testid="get-ready-title">Deep breath. You’ve got this.</h1>
          <p data-testid="get-ready-paper">{a.title} · {a.count} questions{a.rules.minutes ? ` · ${a.rules.minutes} minutes` : ''}</p>
        </div>
      </div>
      <ol className="get-ready-rules" data-testid="get-ready-rules">
        {rulesFor(a).map(([Icon, text], i) => <li key={i} style={{ animationDelay: `${i * 90}ms` }}><Icon size={18} aria-hidden="true" /><span>{text}</span></li>)}
      </ol>
      <PaperLoad loaded={loaded} />
      {error && <p className="get-ready-error" role="alert" data-testid="get-ready-error">{error}</p>}
      <Button className="btn btn-primary full-width get-ready-begin" data-testid="get-ready-begin" disabled={!done || busy} onClick={go}>
        {busy ? <Loader2 className="spin" size={18} /> : null}{done ? 'Begin now' : 'Loading paper…'}<ArrowRight size={18} />
      </Button>
      <small className="get-ready-note" data-testid="get-ready-note">{done ? `Or relax. The paper opens by itself in ${seconds} s.` : 'The paper opens by itself when the countdown ends. Loading keeps going in the background.'}</small>
    </div>
  </div>;
}
