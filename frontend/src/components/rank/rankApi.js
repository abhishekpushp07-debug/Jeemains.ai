// Rank data: every number comes from our server (/api/rank), built from official 2026 JoSAA / CSAB / JAC / BITSAT / COMEDK data.
import { api, post, API } from '../../lib/api';

export const rank = {
  estimate: b => post('/rank/estimate', b),
  predict: b => post('/rank/predict', b),
  college: b => post('/rank/college', b),
  bitsat: b => post('/rank/bitsat', b),
  comedk: b => post('/rank/comedk', b),
  comedkCollege: b => post('/rank/comedk/college', b),
  percentile: b => post('/rank/percentile', b),
  targetJee: b => post('/rank/target/jee', b),
  targetComedk: code => post('/rank/target/comedk', { code }),
  targetBitsat: () => api('/rank/target/bitsat'),
  compare: items => post('/rank/compare', { items }),
  compareColleges: (items, profile) => post('/rank/compare/colleges', { items, ...profile }),
};

const once = load => { let p; return () => (p ||= load().catch(e => { p = null; throw e; })); };
export const getMeta = once(() => api('/rank/meta'));
export const getColleges = once(() => api('/rank/colleges'));

/** Indian grouping: 107693 -> 1,07,693. */
export function fmt(n) {
  const s = String(Math.round(n));
  if (s.length <= 3) return s;
  return s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + s.slice(-3);
}
export const fmtRange = r => (r[0] === r[1] ? fmt(r[0]) : `${fmt(r[0])} – ${fmt(r[1])}`);
export const fmtPct = r => (r[0] === r[1] ? r[0].toFixed(2) : `${r[0].toFixed(2)} – ${r[1].toFixed(2)}`);
export const rupees = v => (v ? '₹' + fmt(v) : '—');

export async function downloadPdf(path, body, filename) {
  const res = await fetch(API + '/rank/pdf' + path, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error('PDF abhi nahi bana. Dobara try karo.');
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}

export const shareWhatsApp = text => window.open('https://api.whatsapp.com/send?text=' + encodeURIComponent(text), '_blank', 'noopener');
export const ESTIMATE = '2026 ke data par estimate, guarantee nahi.';
export const invite = link => `Apna rank aur college free mein dekho 👉 ${link}`;

export const TAG = { safe: 'Safe', likely: 'Likely', borderline: 'Borderline' };
export const KIND = { NIT: 'NIT', IIIT: 'IIIT', GFTI: 'GFTI', DELHI: 'Delhi' };
export const LEVEL = { tough: 'Tough', normal: 'Normal', easy: 'Easy' };
export const LEVELS = ['tough', 'normal', 'easy'];
export const CATS = ['GEN', 'EWS', 'OBC-NCL', 'SC', 'ST'];
export const CATEGORY_LABEL = { GEN: 'General', EWS: 'EWS', 'OBC-NCL': 'OBC-NCL', SC: 'SC', ST: 'ST' };
export const SEGMENTS = [['all', 'All'], ['NIT', 'NIT'], ['IIIT', 'IIIT'], ['GFTI', 'GFTI'], ['DELHI', 'Delhi']];
export const EXAM_LABEL = { jee: 'JEE Main', bitsat: 'BITSAT', comedk: 'COMEDK' };
