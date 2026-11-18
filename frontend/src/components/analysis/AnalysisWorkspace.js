import React, { useMemo, useRef, useState } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { BookOpen, Users, User, WifiOff, RotateCcw } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Loading, ErrorBox } from '../Shared';
import { Overview, Performance, Potential, Quality } from './SectionsA';
import { TimeSection, Difficulty, Journey, QsByQs } from './SectionsB';
import { CompareBody, ComparePicker } from './CompareBody';
import { ReportActions } from './ReportActions';
import { RESULT, OUT_TONE, TagChip, mmss } from './parts';

export const SECTIONS = [
  ['overview', 'Overview', Overview], ['performance', 'Performance', Performance], ['potential', 'Score Potential', Potential],
  ['quality', 'Attempt Quality', Quality], ['time', 'Time kahan gaya', TimeSection], ['difficulty', 'Difficulty', Difficulty],
  ['journey', 'Question Journey', Journey], ['qs', 'Qs by Qs', QsByQs],
];
const LAST = 'tejas-analysis-section';
const known = k => SECTIONS.some(s => s[0] === k);

function DrillList({ drill, an, onClose, onOpen }) {
  const byId = useMemo(() => Object.fromEntries((an?.questions || []).map(q => [q.id, q])), [an]);
  const rows = (drill?.ids || []).map(i => byId[i]).filter(Boolean);
  return (
    <Dialog open={!!drill} onOpenChange={open => !open && onClose()}>
      <DialogContent className="a2-drill" data-testid="a2-drill">
        <DialogHeader>
          <DialogTitle data-testid="a2-drill-title">{drill?.title}</DialogTitle>
          <DialogDescription>{rows.length} sawaal. Kisi par tap karo, uska solution khulega.</DialogDescription>
        </DialogHeader>
        <div className="a2-drill-list">
          {rows.map(q => (
            <button type="button" key={q.id} className="a2-drill-row" data-testid={'a2-drill-q-' + q.number} onClick={() => { onClose(); onOpen(q.id); }}>
              <b>Q{q.number}</b><span>{q.subject}</span><span className={'a2-out tone-' + OUT_TONE[q.outcome]}>{RESULT[q.outcome]}</span>
              <span>{q.time != null ? mmss(q.time) : '—'}</span><TagChip tag={q.tag} copy={an.copy} />
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function AnalysisWorkspace({ id, state, onOpen, onSolutions, onRetry }) {
  const { data: an, error, offline, reload } = state;
  const [params, setParams] = useSearchParams();
  const location = useLocation();
  const [drill, setDrill] = useState(null);
  const top = useRef(null), touch = useRef(null);
  let stored = null;
  try { stored = localStorage.getItem(LAST); } catch {}
  const key = known(params.get('a')) ? params.get('a') : known(stored) ? stored : 'overview';
  const compare = params.get('mode') === 'compare';
  const set = change => {
    const next = new URLSearchParams(params);
    Object.entries(change).forEach(([k, v]) => (v == null ? next.delete(k) : next.set(k, v)));
    setParams(next, { state: location.state, replace: true });
  };
  const open = k => {
    try { localStorage.setItem(LAST, k); } catch {}
    set({ a: k });
    top.current?.scrollIntoView({ block: 'start' });
  };
  const start = e => { const t = e.touches[0]; touch.current = e.target.closest('.a2-scroll, .a2-pills, .recharts-wrapper') ? null : [t.clientX, t.clientY]; };
  const finish = e => {
    if (!touch.current) return;
    const t = e.changedTouches[0], dx = t.clientX - touch.current[0], dy = t.clientY - touch.current[1];
    touch.current = null;
    if (Math.abs(dx) < 80 || Math.abs(dx) < 2.5 * Math.abs(dy)) return;
    const next = SECTIONS[SECTIONS.findIndex(s => s[0] === key) + (dx < 0 ? 1 : -1)];
    if (next) open(next[0]);
  };
  if (!an) return <div className="a2" data-testid="analysis2"><ErrorBox error={error} retry={reload} />{!error && <Loading text="Analysis khul raha hai…" />}</div>;
  const [, label, Section] = SECTIONS.find(s => s[0] === key);
  return (
    <div className="a2" data-testid="analysis2" ref={top}>
      <div className="a2-top" data-testid="a2-top-bar">
        <div><span className="import-section-label">ANALYSIS · {SECTIONS.findIndex(s => s[0] === key) + 1} / {SECTIONS.length}</span><h2 data-testid="a2-section-title">{label}</h2></div>
        <div className="a2-actions">
          <ReportActions id={id} an={an} />
          {onRetry && <button type="button" className="btn btn-secondary" data-testid="a2-retry-mistakes" onClick={onRetry}><RotateCcw size={16} /> Galat + chhode dobara</button>}
          <button type="button" className="btn btn-primary" data-testid="a2-view-solutions" onClick={onSolutions}><BookOpen size={16} /> Solutions dekho</button>
        </div>
      </div>
      {offline && <p className="a2-offline" role="status" data-testid="a2-offline"><WifiOff size={16} /> Internet nahi hai. Yeh pichhli baar khula hua analysis hai.</p>}
      <ErrorBox error={error} retry={reload} />
      {compare && <ComparePicker an={an} value={params.get('vs') || 'topper'} onChange={v => set({ vs: v })} />}
      <div className="a2-stage" data-testid={'a2-section-' + key} onTouchStart={start} onTouchEnd={finish}>
        {compare && <CompareBody an={an} part={key} />}
        <Section an={an} onDrill={(title, ids) => setDrill({ title, ids })} onOpen={onOpen} go={open} />
      </div>
      <nav className="a2-bar" aria-label="Analysis sections" data-testid="a2-bottom-bar">
        <div className="a2-mode" role="group" aria-label="Personal ya Comparative">
          <button type="button" aria-pressed={!compare} className={!compare ? 'on' : ''} data-testid="a2-mode-personal" onClick={() => set({ mode: null })}><User size={14} /> Personal</button>
          <button type="button" aria-pressed={compare} className={compare ? 'on' : ''} data-testid="a2-mode-compare" onClick={() => set({ mode: 'compare' })}><Users size={14} /> Comparative</button>
        </div>
        <div className="a2-nav">
          {SECTIONS.map(([k, name], i) => (
            <button type="button" key={k} aria-current={k === key ? 'page' : undefined} className={k === key ? 'on' : ''} data-testid={'a2-nav-' + k} onClick={() => open(k)}><i>{i + 1}</i>{name}</button>
          ))}
        </div>
      </nav>
      <DrillList drill={drill} an={an} onClose={() => setDrill(null)} onOpen={onOpen} />
    </div>
  );
}
