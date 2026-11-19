// Shown after every fresh test submission, before the result: the Mission card on royal night blue and a red
// "Share to view results" button above and below it. The result opens once the student shares (or comes back from WhatsApp).
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, ChevronLeft, Heart, Lock, Share2 } from 'lucide-react';
import { MissionCard, ShareCta, useMissionShare } from './MissionCard';
import { useMissionStats } from './missionApi';
import '../../mission.css';

export function ShareGate({ onOpen }) {
  const nav = useNavigate();
  const card = useRef(null);
  const [thanks, setThanks] = useState(false), [from, setFrom] = useState('top');
  const opening = useRef(null), open = useRef(onOpen);
  open.current = onOpen;
  useEffect(() => () => { if (opening.current) { clearTimeout(opening.current); open.current(); } }, []);
  const mission = useMissionStats();
  const { busy, note, share } = useMissionShare(card, mission.caption, () => {
    setThanks(true);
    opening.current = setTimeout(() => { opening.current = null; open.current(); }, 900);
  }, !mission.loading);
  const action = where => (thanks
    ? <div className="ms-thanks-btn" role="status" data-testid={`share-gate-thanks${where === 'top' ? '' : '-bottom'}`}><Heart size={22} />Shukriya! Result khul raha hai…</div>
    : <ShareCta testId={where === 'top' ? 'share-gate-share' : 'share-gate-share-bottom'} title="Share to view results" busy={busy} onClick={() => { setFrom(where); share(true); }} />);
  const noteView = where => (note && from === where ? <p className="ms-note" role="status" data-testid="share-gate-note">{note}</p> : null);
  return <div className="ms-gate" data-testid="share-gate">
    <div className="ms-gate-inner">
      <div className="ms-gate-bar"><button type="button" className="ms-back" onClick={() => (window.history.length > 1 ? nav(-1) : nav('/home'))} aria-label="Back" data-testid="share-gate-back"><ChevronLeft size={24} /></button>
        <span className="ms-badge"><Check size={20} strokeWidth={2.6} /></span><span className="ms-back ghost" /></div>
      <header className="ms-gate-head"><small>TEST SUBMIT HO GAYA</small><h1 data-testid="share-gate-title">Aapka result bas ek share door hai 🎉</h1>
        <span className="ms-lock"><Lock size={14} />Score, rank aur solutions ek share ke baad khulenge</span></header>
      <div className="ms-gate-action">{action('top')}{noteView('top')}</div>
      <div className="ms-card-wrap"><MissionCard ref={card} helped={mission.stats?.helped} name={mission.name} /></div>
      {mission.stats?.helped ? <p className="ms-impact-note" data-testid="share-gate-impact-note">Aapka impact card par dikhega</p> : null}
      <div className="ms-gate-action">{action('bottom')}
        <button type="button" className="ms-more" onClick={() => { setFrom('bottom'); share(false); }} disabled={busy || thanks} data-testid="share-gate-more"><Share2 size={16} />Doosre app se share karo</button>
        {noteView('bottom')}</div>
    </div>
  </div>;
}
