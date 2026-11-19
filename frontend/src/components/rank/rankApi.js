// Rank: every number, tag and sentence comes live from the JEELIVE.AI app server (through our /api/rank connector).
import { api, API } from '../../lib/api';

const NETWORK = 'Network kamzor hai. Retry dabao.';
/** 15 s like the app; a dropped or slow network reads as one plain sentence, server sentences pass as they are. */
function call(path, options = {}) {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), 15000);
  return api(path, { ...options, signal: c.signal })
    .catch(e => { throw e.name === 'AbortError' || !e.status ? new Error(NETWORK) : e; })
    .finally(() => clearTimeout(t));
}
const post = (path, b) => call(path, { method: 'POST', body: JSON.stringify(b) });

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
  targetBitsat: () => call('/rank/target/bitsat'),
  compare: items => post('/rank/compare', { items }),
  compareColleges: (items, profile) => post('/rank/compare/colleges', { items, ...profile }),
};

const once = load => { let p; return () => (p ||= load().catch(e => { p = null; throw e; })); };
export const getMeta = once(() => call('/rank/meta'));
export const getColleges = once(() => call('/rank/colleges'));

/** Indian grouping: 107693 -> 1,07,693. */
export function fmt(n) {
  const s = String(Math.round(n));
  if (s.length <= 3) return s;
  return s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + s.slice(-3);
}
export const fmtRange = r => (r[0] === r[1] ? fmt(r[0]) : `${fmt(r[0])} – ${fmt(r[1])}`);
export const fmtPct = r => (r[0] === r[1] ? r[0].toFixed(2) : `${r[0].toFixed(2)} – ${r[1].toFixed(2)}`);
export const rupees = v => (v ? '₹' + fmt(v) : '—');

const PDF_FAIL = 'PDF nahi bani. Network check karke dobara try karo.';
/** The server draws the PDF (up to 30 s on a slow network) and names the file. */
export async function downloadPdf(path, body, filename) {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), 30000);
  let res;
  try {
    res = await fetch(API + '/rank/pdf' + path, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: c.signal });
  } catch { throw new Error(PDF_FAIL); } finally { clearTimeout(t); }
  if (!res.ok) {
    let d; try { d = await res.json(); } catch {}
    const msg = d?.error?.message || d?.detail;
    throw new Error(typeof msg === 'string' ? msg : PDF_FAIL);
  }
  const named = /filename="?([^";]+)"?/i.exec(res.headers.get('content-disposition') || '');
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement('a');
  a.href = url; a.download = named ? named[1] : filename; a.click();
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
