// The Mission share card (a short letter from the maker on royal night blue with gold), the impact panel, the big
// red share button, and the web share flow: card picture + caption via the phone's share sheet, else WhatsApp / copy.
import React, { forwardRef, useCallback, useEffect, useRef, useState } from 'react';
import { toBlob } from 'html-to-image';
import { Dna, GraduationCap, HandHeart, Heart, Loader2, Rocket, Target, TrendingUp, Zap } from 'lucide-react';
import { MAKER, nextStep, SEGMENTS, shortCount, SITE } from './missionApi';

export const ICONS = { dna: Dna, target: Target, zap: Zap, cap: GraduationCap, heart: Heart, rocket: Rocket };

export const MissionCard = forwardRef(function MissionCard({ helped = 0, name = '' }, ref) {
  const thanks = helped > 0;
  const n = shortCount(helped);
  return <div ref={ref} className={'ms-card' + (thanks ? ' has-thanks' : '')} data-testid="mission-card">
    <i className="ms-glow" aria-hidden="true" />
    <div className="ms-ribbon" aria-hidden="true"><span>100% MADE BY AI ASTRA</span></div>
    <small className="ms-eyebrow">EK CHHOTI SI BAAT</small>
    <div className="ms-letter"><span className="ms-quote">“</span>
      <p>Maine ise AI ke saath, apne kharche par, bahut mehnat se banaya hai. Taaki har JEE student <em>100% free</em> mein padh sake.</p></div>
    <div className="ms-sign"><i /><div><b>{MAKER}</b><small>Creator, JEELIVE.AI</small></div><span className="ms-seal">AP</span></div>
    {thanks ? <div className="ms-thanks" data-testid="mission-card-thanks"><span className="ms-medal"><b data-testid="mission-card-thanks-count">{n}</b><small>DOST</small></span>
      <div><small>THANK YOU{name ? `, ${name.toUpperCase()}` : ''} 🙏</small><p>Aapne <b>{n} {helped === 1 ? 'dost' : 'logon'}</b> ki free education mein help ki</p></div></div> : null}
    <div className="ms-chips">{SEGMENTS.map(([icon, title, short]) => { const I = ICONS[icon]; return <div key={title}><I size={13} /><span><b>{title}</b><small>{short}</small></span></div>; })}</div>
    <div className="ms-foot"><b>100% FREE</b><span>🙏 Please share karo · {SITE}</span></div>
  </div>;
});

function useCountUp(n) {
  const shown = useRef(0);
  const [v, setV] = useState(0);
  useEffect(() => {
    const from = shown.current;
    if (n <= from || window.matchMedia('(prefers-reduced-motion: reduce)').matches) { shown.current = n; setV(n); return undefined; }
    const t0 = performance.now();
    let raf = 0;
    const step = t => { const p = Math.min(1, (t - t0) / 900); const x = Math.round(from + (n - from) * (1 - Math.pow(1 - p, 3))); shown.current = x; setV(x); if (p < 1) raf = requestAnimationFrame(step); };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [n]);
  return v;
}

export function ImpactPanel({ stats, loading }) {
  const helped = stats?.helped ?? 0;
  const shown = useCountUp(helped);
  if (loading) return <div className="ms-impact is-loading" data-testid="mission-impact-loading" />;
  if (!stats) return null;
  const goal = nextStep(helped);
  return <section className="ms-impact" data-testid="mission-impact">
    <div className="ms-impact-row">
      <span className="ms-ring"><span>{helped > 0 ? <><b data-testid="mission-impact-count">{shortCount(shown)}</b><small>DOST</small></> : <HandHeart size={30} />}</span></span>
      <div><small className="ms-gold">{helped > 0 ? 'THANK YOU! 🙏' : 'AAPKA IMPACT'}</small>
        <p data-testid="mission-impact-line">{helped > 0 ? <>Aapne <b>{shortCount(helped)} {helped === 1 ? 'dost' : 'logon'}</b> ki free education mein help ki</> : 'Aapka pehla share kisi ki free taiyari shuru karega'}</p>
        {stats.week > 0 ? <span className="ms-week" data-testid="mission-impact-week"><TrendingUp size={13} />+{shortCount(stats.week)} is hafte</span> : null}</div>
    </div>
    {helped > 0 ? <div className="ms-goal"><div><span>Agla padaav: {shortCount(goal)} dost</span><b data-testid="mission-impact-goal">{shortCount(helped)}/{shortCount(goal)}</b></div>
      <i><i style={{ width: `${Math.max(6, Math.min(100, (helped / goal) * 100))}%` }} /></i></div> : null}
    <hr /><p className="ms-how" data-testid="mission-impact-how">Jab koi dost aapke link se JEELIVE.AI kholta hai, wo yahan gina jaata hai. Har dost sirf ek baar.</p>
  </section>;
}

const WA = <svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.2 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.8s.7-2 .9-2.3c.3-.3.6-.3.8-.3h.6c.2 0 .4 0 .6.5l.9 2.1c.1.2.1.4 0 .6l-.4.6-.4.4c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.7-.1l.9-1.1c.2-.3.4-.2.7-.1l2 1c.3.1.5.2.5.3.1.2.1.6-.1 1.2Z" /></svg>;
export const ShareCta = ({ testId, title, busy, onClick }) => <button type="button" className="ms-cta" onClick={onClick} disabled={busy} data-testid={testId} aria-label={`${title}, aur free education ko support karo`}>
  {busy ? <Loader2 className="spin" size={28} /> : WA}<span><b>{title}</b><small>aur free education ko support karo</small></span></button>;

/** Resolves once the student has left the page (WhatsApp tab / app) and come back; after 3 s if the page never leaves. */
function watchReturn() {
  let left = false, wake = () => {}, timer;
  const on = () => { if (document.visibilityState === 'hidden') { left = true; clearTimeout(timer); } else if (left) wake(); };
  document.addEventListener('visibilitychange', on);
  return {
    back: () => new Promise(done => { wake = done; if (!left) timer = setTimeout(done, 3000); else if (document.visibilityState === 'visible') done(); }),
    stop: () => { clearTimeout(timer); document.removeEventListener('visibilitychange', on); },
  };
}
const download = file => { const url = URL.createObjectURL(file); const a = document.createElement('a'); a.href = url; a.download = file.name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 5000); };
const aborted = e => e?.name === 'AbortError';

async function sendCard(file, toWhatsApp, caption) {
  if (file && navigator.canShare?.({ files: [file] })) {
    try { await navigator.share({ files: [file], text: caption }); return { shared: true, away: false, note: 'Shukriya! 🙏' }; } catch (e) { if (aborted(e)) return { shared: false }; }
  }
  if (toWhatsApp) {
    window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(caption), '_blank', 'noopener');
    if (file) download(file);
    return { shared: true, away: true, note: file ? 'Card ki photo download ho gayi: WhatsApp mein message ke saath bhej do.' : '' };
  }
  if (navigator.share) { try { await navigator.share({ text: caption }); return { shared: true, away: false, note: 'Shukriya! 🙏' }; } catch (e) { if (aborted(e)) return { shared: false }; } }
  try { await navigator.clipboard.writeText(caption); } catch {}
  if (file) download(file);
  return { shared: true, away: false, note: 'Message copy ho gaya aur card ki photo download ho gayi. Kisi bhi app mein paste karke bhejo.' };
}

/** The card's picture is drawn ahead of time so the share sheet opens straight from the tap. */
export function useMissionShare(card, caption, onShared, ready = true) {
  const [busy, setBusy] = useState(false), [note, setNote] = useState('');
  const file = useRef(null);
  const draw = useCallback(async () => {
    const node = card.current;
    if (!node) return null;
    const blob = await toBlob(node, { pixelRatio: 1080 / node.offsetWidth, cacheBust: true }).catch(() => null);
    file.current = blob ? new File([blob], 'JEELIVE-Mission.png', { type: 'image/png' }) : null;
    return file.current;
  }, [card]);
  useEffect(() => { if (!ready) return undefined; const t = setTimeout(draw, 700); return () => clearTimeout(t); }, [draw, ready]);
  const share = async toWhatsApp => {
    if (busy) return;
    setBusy(true); setNote('');
    const trip = watchReturn();
    try {
      const out = await sendCard(file.current || await draw(), toWhatsApp, caption);
      if (!out.shared) { if (onShared) setNote('Share pura nahi hua. Result dekhne ke liye ek baar share karo.'); return; }
      if (onShared && out.away) { setNote('WhatsApp par bhej kar wapas aao, result yahin khul jaayega.'); await trip.back(); }
      setNote(out.note);
      onShared?.();
    } catch { setNote('Share nahi khula. Dobara try karo.'); }
    finally { trip.stop(); setBusy(false); }
  };
  return { busy, note, share };
}
