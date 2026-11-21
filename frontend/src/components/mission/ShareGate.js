// Shown after every fresh test submission, before the result: the Mission card on royal night blue and a red
// "Share to view results" button above and below it. On a phone the result opens once the student shares (or comes
// back from WhatsApp); on a laptop or desktop the card shows for 5 seconds and the result then opens by itself.
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ChevronLeft, Clock3, Heart, Lock, Share2 } from 'lucide-react';
import { MissionCard, ShareCta, useMissionShare } from './MissionCard';
import { useMissionStats } from './missionApi';
import '../../mission.css';

const WAIT = 5;
const isDesktop = () => !!window.matchMedia?.('(hover: hover) and (pointer: fine)').matches && window.innerWidth >= 1024;

function useCountdown(on, done) {
  const [left, setLeft] = useState(WAIT);
  const finish = useRef(done);
  finish.current = done;
  useEffect(() => {
    if (!on) return undefined;
    const started = Date.now();
    const t = setInterval(() => {
      const rest = Math.max(0, WAIT - Math.floor((Date.now() - started) / 1000));
      setLeft(rest);
      if (!rest) { clearInterval(t); finish.current(); }
    }, 250);
    return () => clearInterval(t);
  }, [on]);
  return left;
}

export function ShareGate({ onOpen }) {
  const nav = useNavigate();
  const card = useRef(null);
  const [thanks, setThanks] = useState(false), [from, setFrom] = useState('top'), [desktop] = useState(isDesktop);
  const opening = useRef(null), open = useRef(onOpen), fired = useRef(false);
  open.current = onOpen;
  const fire = () => { if (!fired.current) { fired.current = true; open.current(); } };
  useEffect(() => () => { if (opening.current) { clearTimeout(opening.current); fire(); } }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const left = useCountdown(desktop, fire);
  const mission = useMissionStats();
  const { busy, note, share } = useMissionShare(card, mission.caption, () => {
    setThanks(true);
    opening.current = setTimeout(() => { opening.current = null; fire(); }, 900);
  }, !mission.loading);
  const action = where => (thanks
    ? <div className="ms-thanks-btn" role="status" data-testid={`share-gate-thanks${where === 'top' ? '' : '-bottom'}`}><Heart size={22} />Shukriya! Result khul raha hai…</div>
    : <ShareCta testId={where === 'top' ? 'share-gate-share' : 'share-gate-share-bottom'} title={desktop ? 'Share karo' : 'Share to view results'} busy={busy} onClick={() => { setFrom(where); share(true); }} />);
  const noteView = where => (note && from === where ? <p className="ms-note" role="status" data-testid="share-gate-note">{note}</p> : null);
  return <div className="ms-gate" data-testid="share-gate">
    <div className="ms-gate-inner">
      <div className="ms-gate-bar"><button type="button" className="ms-back" onClick={() => (window.history.length > 1 ? nav(-1) : nav('/home'))} aria-label="Back" data-testid="share-gate-back"><ChevronLeft size={24} /></button>
        <span className="ms-badge"><Check size={20} strokeWidth={2.6} /></span><span className="ms-back ghost" /></div>
      <header className="ms-gate-head"><small>TEST SUBMIT HO GAYA</small>
        <h1 data-testid="share-gate-title">{desktop ? 'Aapka result taiyaar ho raha hai 🎉' : 'Aapka result bas ek share door hai 🎉'}</h1>
        {desktop
          ? <span className="ms-lock ms-countdown" role="timer" data-testid="share-gate-countdown"><Clock3 size={14} />Result aur analysis {left} second mein khulenge<i style={{ '--p': `${((WAIT - left) / WAIT) * 100}%` }} /></span>
          : <span className="ms-lock"><Lock size={14} />Score, rank aur solutions ek share ke baad khulenge</span>}
      </header>
      <div className="ms-gate-action">{action('top')}{noteView('top')}</div>
      <div className="ms-card-wrap"><MissionCard ref={card} helped={mission.stats?.helped} name={mission.name} /></div>
      <div className="ms-gate-action">{action('bottom')}
        <button type="button" className="ms-more" onClick={() => { setFrom('bottom'); share(false); }} disabled={busy || thanks} data-testid="share-gate-more"><Share2 size={16} />Doosre app se share karo</button>
        {noteView('bottom')}</div>
    </div>
  </div>;
}
