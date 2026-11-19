// A light sparkle when a released result beats the student's own best or reaches 40%, plus the Dream College Meter
// for full mocks (and a cheer when a dream seat is crossed for the first time). Shown once per attempt in this browser.
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Trophy, X } from 'lucide-react';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/auth';
import { claimCheer, reloadDreams, useDreams } from '../rank/rankStore';
import { DreamMeter } from '../rank/DreamMeter';
import '../../celebrate.css';

const COLORS = ['#D90F23', '#F2C14E', '#FFFFFF', '#8A1538', '#FF8E98', '#FFE6A3'];
function Burst() {
  const bits = useMemo(() => Array.from({ length: 34 }, (_, i) => ({ x: Math.round(Math.random() * 100), d: Math.round(Math.random() * 700), s: 6 + Math.round(Math.random() * 8),
    r: Math.round(Math.random() * 360), dur: 1700 + Math.round(Math.random() * 900), c: COLORS[i % COLORS.length], star: i % 3 === 0 })), []);
  return <div className="cb-burst" aria-hidden="true" data-testid="result-sparkle-burst">{bits.map((b, i) => <i key={i} className={b.star ? 'star' : ''}
    style={{ left: b.x + '%', width: b.s, height: b.star ? b.s : b.s * 0.45, background: b.c, animationDelay: b.d + 'ms', animationDuration: b.dur + 'ms', '--r': b.r + 'deg' }} />)}</div>;
}

export function ResultSparkle({ id, enabled }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  useDreams();
  const [c, setC] = useState(null), [won, setWon] = useState(null), [burst, setBurst] = useState(false), [hidden, setHidden] = useState(false);
  useEffect(() => {
    if (!enabled) return undefined;
    let live = true;
    api(`/dream/celebration/${id}`).then(d => { if (live) setC(d); }).catch(() => {});
    return () => { live = false; };
  }, [id, enabled]);
  useEffect(() => {
    if (!c?.full || !c.dream_exam || !user) return undefined;
    let live = true;
    reloadDreams(user.id).then(() => { const w = live && claimCheer(c.dream_exam, id); if (w) setWon(w); });
    return () => { live = false; };
  }, [c, id, user]);
  const party = !!(c?.celebrate || won);
  useEffect(() => {
    if (!party) return undefined;
    const key = 'sparkle.' + id;
    let seen = true;
    try { seen = !!localStorage.getItem(key); localStorage.setItem(key, '1'); } catch {}
    if (seen || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    setBurst(true);
    const t = setTimeout(() => setBurst(false), 3200);
    return () => clearTimeout(t);
  }, [party, id]);
  if (!c) return null;
  const title = won ? `Dream college cross! ${won.dreams[0].college}` : c.beat_best ? 'Naya personal best! 🎉' : 'Shabaash! 40%+ score ✨';
  const sub = won ? `${won.dreams[0].branch}: chahiye the ${Math.round(won.dreams[0].need)}, aapke ${won.mock.score} / ${won.mock.max}.${won.dreams.length > 1 ? ` Aur ${won.dreams.length - 1} dream bhi paar!` : ''}`
    : c.beat_best ? `${c.pct}% · pichhla best ${c.best_before.pct}% (${c.best_before.score} / ${c.best_before.maximum}). Isi raftaar se aage badho.`
      : `${c.score} / ${c.maximum} · ${c.pct}%. Ab agla target: apna hi record todna.`;
  return <>
    {burst ? <Burst /> : null}
    {party && !hidden ? <div className={'cb-banner' + (won ? ' is-dream' : '')} role="status" data-testid="result-sparkle">
      <span className="cb-icon">{won || c.beat_best ? <Trophy size={22} /> : <Sparkles size={22} />}</span>
      <div><b data-testid="result-sparkle-title">{title}</b><small data-testid="result-sparkle-sub">{sub}</small></div>
      <button type="button" onClick={() => setHidden(true)} aria-label="Band karo" data-testid="result-sparkle-close"><X size={16} /></button>
    </div> : null}
    {c.full && c.dream_exam && user ? <div className="cb-meter" data-testid="result-dreams">
      <DreamMeter exam={c.dream_exam} testId="result-dream-meter" mockId={id} chart="full" onAdd={() => navigate('/rank?tool=college')} />
    </div> : null}
  </>;
}
