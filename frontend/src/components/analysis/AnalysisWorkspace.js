import React, { useMemo, useRef, useState } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { BookOpen, Users, User, WifiOff, RotateCcw, ArrowLeft, ArrowRight } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Loading, ErrorBox } from '../Shared';
import { Overview } from './Overview';
import { Performance } from './Performance';
import { Potential } from './Potential';
import { Quality } from './Quality';
import { TimeSection } from './TimeSection';
import { Difficulty } from './Difficulty';
import { Journey } from './Journey';
import { QsByQs } from './QsByQs';
import { CompareBody, ComparePicker } from './CompareBody';
import { Leaderboard } from './Leaderboard';
import { ReportActions } from './ReportActions';
import { RESULT, OUT_TONE, TagChip, mmss } from './parts';

export const SECTIONS = [
  ['overview', 'Overview', Overview, 'Ek nazar mein poora paper: Score, Rank, marks ka hisaab aur agle mock ke 3 kaam.'],
  ['performance', 'Performance', Performance, 'Har subject aur chapter mein kitne marks bane aur kahan gaye.'],
  ['potential', 'Score Potential', Potential, 'Seedha hisaab: kin galtiyon ko theek karke kitne marks aur kaunsi Rank mil sakti thi.'],
  ['quality', 'Attempt Quality', Quality, 'Har sawaal ko ek tag: sahi time mein sahi, jaldbaazi, overtime ya concept gap.'],
  ['time', 'Time kahan gaya', TimeSection, 'Aapka time kis subject, kis sawaal aur paper ke kis hisse mein gaya.'],
  ['difficulty', 'Difficulty', Difficulty, 'Easy, Moderate aur Tough sawaalon par aapka haal, aur Easy marks ka leak.'],
  ['journey', 'Question Journey', Journey, 'Aap paper mein kis raaste chale: kaun sa sawaal kab khola, kab wapas aaye, kab jawab badla.'],
  ['qs', 'Qs by Qs', QsByQs, 'Har sawaal ki poori report ek jagah: aapka time, Par time aur class ka haal.'],
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
              <span className="a2-mono">{q.time != null ? mmss(q.time) : '—'}</span><TagChip tag={q.tag} copy={an.copy} />
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Pager({ at, open }) {
  const prev = SECTIONS[at - 1], next = SECTIONS[at + 1];
  return (
    <div className="a2-pager">
      {prev ? <button type="button" data-testid="a2-prev-section" onClick={() => open(prev[0])}><ArrowLeft size={16} /><span><small>Pichhla</small>{prev[1]}</span></button> : <i />}
      {next && <button type="button" className="next" data-testid="a2-next-section" onClick={() => open(next[0])}><span><small>Agla</small>{next[1]}</span><ArrowRight size={16} /></button>}
    </div>
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
  const vs = params.get('vs') || 'topper';
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
  const start = e => { const t = e.touches[0]; touch.current = e.target.closest('.a2-scroll, .a2-pills, .recharts-wrapper, .a2-qgrid, input, select') ? null : [t.clientX, t.clientY]; };
  const finish = e => {
    if (!touch.current) return;
    const t = e.changedTouches[0], dx = t.clientX - touch.current[0], dy = t.clientY - touch.current[1];
    touch.current = null;
    if (Math.abs(dx) < 80 || Math.abs(dx) < 2.5 * Math.abs(dy)) return;
    const next = SECTIONS[SECTIONS.findIndex(s => s[0] === key) + (dx < 0 ? 1 : -1)];
    if (next) open(next[0]);
  };
  if (!an) return <div className="a2" data-testid="analysis2"><ErrorBox error={error} retry={reload} />{!error && <Loading text="Analysis khul raha hai…" />}</div>;
  const at = SECTIONS.findIndex(s => s[0] === key);
  const [, label, Section, about] = SECTIONS[at];
  return (
    <div className="a2" data-testid="analysis2" ref={top}>
      <div className="a2-top" data-testid="a2-top-bar">
        <div><span className="a2-kicker">ANALYSIS · {at + 1} / {SECTIONS.length}{compare ? ' · COMPARATIVE' : ''}</span><h2 data-testid="a2-section-title">{label}</h2><p>{about}</p></div>
        <div className="a2-actions">
          <ReportActions id={id} an={an} />
          {onRetry && <button type="button" className="btn btn-secondary" data-testid="a2-retry-mistakes" onClick={onRetry}><RotateCcw size={16} /> Galat + chhode dobara</button>}
          <button type="button" className="btn btn-primary" data-testid="a2-view-solutions" onClick={onSolutions}><BookOpen size={16} /> Solutions dekho</button>
        </div>
      </div>
      {offline && <p className="a2-offline" role="status" data-testid="a2-offline"><WifiOff size={16} /> Internet nahi hai. Yeh pichhli baar khula hua analysis hai.</p>}
      <ErrorBox error={error} retry={reload} />
      {compare && <ComparePicker id={id} value={vs} onChange={v => set({ vs: v })} />}
      <div className="a2-stage" key={key + (compare ? ':c' : '')} data-testid={'a2-section-' + key} onTouchStart={start} onTouchEnd={finish}>
        {compare && <CompareBody an={an} part={key} />}
        {compare && key === 'overview' && an.class.state === 'ready' && <Leaderboard id={id} value={vs} onPick={v => set({ vs: v })} />}
        <Section an={an} id={id} onDrill={(title, ids) => setDrill({ title, ids })} onOpen={onOpen} go={open} />
        <Pager at={at} open={open} />
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
