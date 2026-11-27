// "Meri details": the student's score and category, typed once, kept in this browser in the app's shape (rank.profile.v1).
// Saving writes them into every Rank tool's saved form as its starting values; each tool can still be changed on its own.
import { useSyncExternalStore } from 'react';
import { setJeeProfile } from './rankStore';

export const KEYS = { profile: 'rank.profile.v1', estimate: 'rank.estimate.v1', cutoff: 'rank.cutoff.v1', college: 'rank.college.v1', comedk: 'rank.comedk.v1', bitsat: 'rank.bitsat.v1' };
export const EMPTY = { at: 0, jee: { marks: '', pct: '', rank: '', level: 'normal', category: 'GEN', female: false, pwd: false, state: null }, comedk: { marks: '', rank: '' }, bitsat: { score: '' } };

/** Every score a Rank tool takes, per exam: limits, label, hint and the line shown when it is wrong. */
export const SCORE = {
  jee: {
    marks: { min: -75, max: 300, label: 'Marks / 300', hint: 'e.g. 180', len: 4, signed: true, bad: 'JEE Main marks −75 se 300 ke beech poore ank mein daalo.' },
    percentile: { min: 0, max: 100, label: 'Percentile', hint: 'e.g. 97.4', len: 10, decimal: true, bad: 'Percentile 0 se 100 ke beech daalo.' },
    rank: { min: 1, max: 2000000, label: 'Rank (CRL)', hint: 'e.g. 12000', len: 7, bad: 'JEE Main rank 1 se 20,00,000 ke beech poore ank mein daalo.' },
  },
  comedk: {
    marks: { min: 0, max: 180, label: 'Marks / 180', hint: 'e.g. 110', len: 3, bad: 'COMEDK marks 0 se 180 ke beech poore ank mein daalo.' },
    rank: { min: 1, max: 200000, label: 'COMEDK rank', hint: 'e.g. 4500', len: 6, bad: 'COMEDK rank 1 se 2,00,000 ke beech poore ank mein daalo.' },
  },
  bitsat: { marks: { min: -130, max: 390, label: 'Score / 390', hint: 'e.g. 280', len: 4, signed: true, bad: 'BITSAT score −130 se 390 ke beech poore ank mein daalo.' } },
};

/** Only the characters a box of that kind can hold. */
export const typed = (rule, v) => v.replace(rule.decimal ? /[^0-9.]/g : rule.signed ? /[^0-9-]/g : /[^0-9]/g, '').slice(0, rule.len);

/** Typed text -> the number, null when empty, or the line that says what to fix. */
export function readScore(exam, kind, text) {
  const rule = SCORE[exam][kind], v = String(text ?? '').trim();
  if (!rule || !v) return null;
  const n = Number(v);
  return (rule.decimal ? Number.isFinite(n) : Number.isInteger(n)) && n >= rule.min && n <= rule.max ? n : rule.bad;
}

const read = key => { try { const v = JSON.parse(localStorage.getItem(key) || 'null'); return v && typeof v === 'object' ? v : {}; } catch { return {}; } };
const write = (key, v) => { try { localStorage.setItem(key, JSON.stringify(v)); } catch {} };
const patch = (key, change) => write(key, change(read(key)));

function loadProfile() {
  const p = read(KEYS.profile);
  return { at: Number(p.at) || 0, jee: { ...EMPTY.jee, ...p.jee }, comedk: { ...EMPTY.comedk, ...p.comedk }, bitsat: { ...EMPTY.bitsat, ...p.bitsat } };
}

let state = { profile: loadProfile(), saves: 0 };
const subs = new Set();
const subscribe = f => { subs.add(f); return () => subs.delete(f); };
const snap = () => state;
const emit = () => subs.forEach(f => f());
export const useRankProfile = () => useSyncExternalStore(subscribe, snap, snap).profile;
/** Counts saves since the page opened: the tools are drawn again from their saved forms after each one. */
export const useProfileSaves = () => useSyncExternalStore(subscribe, snap, snap).saves;

/** The first wrong number, with the exam whose form shows it. */
export function problemOf(p) {
  const boxes = [['jee', 'marks', p.jee.marks], ['jee', 'percentile', p.jee.pct], ['jee', 'rank', p.jee.rank], ['comedk', 'marks', p.comedk.marks], ['comedk', 'rank', p.comedk.rank], ['bitsat', 'marks', p.bitsat.score]];
  for (const [exam, kind, text] of boxes) { const v = readScore(exam, kind, text); if (typeof v === 'string') return { exam, text: v }; }
  return null;
}

/** Saves the profile and fills every tool's saved form. An empty score never wipes a tool's own; the Cut off tool starts from the most exact JEE score. */
export function saveProfile(input) {
  const p = { ...input, at: Date.now() }, j = p.jee, c = p.comedk, b = p.bitsat.score;
  const who = { category: j.category, female: j.female, pwd: j.pwd, state: j.state };
  const jee = !!(j.marks || j.pct || j.rank), comedk = !!(c.marks || c.rank);
  const start = (old, kind, text) => ({ by: 'college', college: null, branch: null, ...old, kind, text, score: null });
  write(KEYS.profile, p);
  patch(KEYS.estimate, o => ({ ...o, level: j.level, category: j.category, pwd: j.pwd, ...(j.marks ? { jee: j.marks } : {}), ...(c.marks ? { comedk: c.marks } : {}) }));
  patch(KEYS.cutoff, o => ({ ...o, ...who, level: j.level,
    ...(jee ? { jee: start(o.jee, j.rank ? 'rank' : j.pct ? 'percentile' : 'marks', j.rank || j.pct || j.marks) } : {}),
    ...(comedk ? { comedk: start(o.comedk, c.rank ? 'rank' : 'marks', c.rank || c.marks) } : {}),
    ...(b ? { bitsat: start(o.bitsat, 'marks', b) } : {}) }));
  patch(KEYS.college, o => ({ ...o, ...who, level: j.level, ...(jee ? { marks: j.marks, pct: j.pct, rank: j.rank, mode: j.rank ? 'rank' : j.pct ? 'pct' : 'marks' } : {}) }));
  if (comedk) patch(KEYS.comedk, o => ({ ...o, marks: c.marks, rank: c.rank, mode: c.rank ? 'rank' : 'marks' }));
  if (b) patch(KEYS.bitsat, o => ({ ...o, score: b }));
  setJeeProfile(who);
  state = { profile: p, saves: state.saves + 1 };
  emit();
}

/** Forgets the profile; the tools keep what they hold. */
export function clearProfile() {
  write(KEYS.profile, EMPTY);
  state = { ...state, profile: EMPTY };
  emit();
}
