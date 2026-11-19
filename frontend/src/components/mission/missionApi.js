// Mission share stats (the student's own link) and the words of the Mission card, in one place.
import { useCallback, useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/auth';

export const MAKER = 'Abhishek Pushp';
export const SITE = 'jeelive.ai';
export const SEGMENTS = [
  ['dna', 'PYQ DNA', '4,000+ PYQs se bana har sawaal'],
  ['target', 'Target 200+', 'har session 200+ marks ka target'],
  ['zap', 'Rapid Fire', 'revision ka competitive game'],
  ['cap', 'Rank + College', 'dream college kitni door?'],
];
export const POINTS = [
  ['heart', '100% free, hamesha', 'Koi fees nahi, koi paywall nahi. Abhishek Pushp ne ise AI ke saath, apne kharche par, bahut mehnat se banaya hai.'],
  ['dna', 'Har sawaal ka DNA = PYQ', 'Saare sawaal deeply PYQ-based hain. Har sawaal ka DNA 4,000+ PYQs analyse karke bana hai, isliye ye kisi bhi institute se better hain.'],
  ['target', 'Target: 200+ marks', 'Hamara target hai ki har session mein 200+ marks ke sawaal bilkul isi Mock aur All India Test Series jaise aayein.'],
  ['zap', 'Rapid Fire', 'Aapke revision ke liye ek highly competitive game. 15 second mein ek concept, doston se seedha muqabla.'],
  ['cap', 'Rank + College predictor', 'Aapke mann ki shaanti ke liye, taaki pata rahe ki aapka dream college bas kitni door hai.'],
  ['rocket', 'Aage aur bhi aayega', 'Koshish hai ki aane wale waqt mein features aur badhein. Aapka ek share is mission ko aage badhata hai.'],
];
export const caption = link => [
  '🙏 Please share karo aur free education ko support karo!', '',
  'JEELIVE.AI: 100% free JEE Main, BITSAT & COMEDK prep. Abhishek Pushp ne ise AI ke saath, apne kharche par banaya hai.', '',
  '🧬 Har sawaal ka DNA 4,000+ PYQs analyse karke bana',
  '🎯 Target: har session 200+ marks ke sawaal isi Mock aur All India Test Series se',
  '⚡ Rapid Fire: revision ka competitive game',
  '🎓 Rank + College predictor: dream college kitni door?', '',
  `Abhi kholo 👉 ${link}`,
].join('\n');

const STEPS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
export const nextStep = n => STEPS.find(x => x > n) ?? Math.ceil((n + 1) / 10000) * 10000;
export const shortCount = n => (n < 10000 ? n.toLocaleString('en-IN') : `${Math.floor(n / 1000)}k+`);
export const linkOf = s => s?.link || 'https://jeelive.ai';
const firstName = name => { const w = (name || '').trim().split(/\s+/)[0] || ''; return /\d/.test(w) ? '' : w.slice(0, 14); };

let cache = null;
export function useMissionStats() {
  const { user } = useAuth();
  const uid = user?.id;
  const hit = !!uid && cache?.uid === uid;
  const [stats, setStats] = useState(hit ? cache.data : null);
  const [loading, setLoading] = useState(!!uid && !hit);
  const reload = useCallback(() => {
    if (!uid) return;
    api('/mission/me').then(d => { cache = { uid, data: d }; setStats(d); }).catch(() => {}).finally(() => setLoading(false));
  }, [uid]);
  useEffect(() => { reload(); }, [reload]);
  const link = linkOf(stats);
  return { stats, loading, reload, link, caption: caption(link), name: firstName(user?.display_name || user?.name) };
}
/** The student's own link for any share text (Rank cards), so friends who open it count on the Mission card. */
export const useShareLink = () => useMissionStats().link;
