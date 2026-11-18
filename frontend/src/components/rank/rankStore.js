// Saved branches and compared colleges stay in this browser; dream colleges stay with the student's account.
import { useEffect, useState, useSyncExternalStore } from 'react';
import { api, post, put } from '../../lib/api';
import { useAuth } from '../../lib/auth';
import { fmt, rank } from './rankApi';

function listStore(key, max) {
  let items = null;
  const subs = new Set();
  const read = () => {
    if (items === null) {
      try { const v = JSON.parse(localStorage.getItem(key) || '[]'); items = Array.isArray(v) ? v : []; } catch { items = []; }
    }
    return items;
  };
  const set = next => { items = next; try { localStorage.setItem(key, JSON.stringify(next)); } catch {} subs.forEach(f => f()); };
  const subscribe = f => { subs.add(f); return () => subs.delete(f); };
  return {
    useList: () => useSyncExternalStore(subscribe, read, read),
    toggle: x => { const cur = read(); set(cur.some(i => i.id === x.id) ? cur.filter(i => i.id !== x.id) : [x, ...cur].slice(0, max)); },
    remove: id => set(read().filter(i => i.id !== id)),
  };
}
/** Loads shared Rank data once (meta, college lists); null until it arrives. */
export function useRankData(load) {
  const [data, setData] = useState(null), [error, setError] = useState('');
  useEffect(() => { let live = true; load().then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); }); return () => { live = false; }; }, [load]);
  return { data, error };
}

export const shortlist = listStore('rank.shortlist.v1', 50);
export const compareColleges = listStore('rank.compare.colleges.v1', 20);

export const jeeSaved = s => ({ id: `jee-${s.prog}`, exam: 'jee', title: s.college, sub: `${s.branch}${s.degree ? ` (${s.degree})` : ''}`,
  line: `Closing ${fmt(s.close)} ${s.rank_type} · ${s.round} · ${s.path}`, tag: s.tag ?? null, seat: s });
export const bitsatSaved = b => ({ id: `bitsat-${b.id}`, exam: 'bitsat', title: b.college, sub: b.program, line: `BITSAT 2026 cutoff ${b.cutoff} / 390`, tag: b.tag });
export const comedkSaved = c => ({ id: `comedk-${c.id}`, exam: 'comedk', title: c.college, sub: c.course, line: `COMEDK 2026 closing ${fmt(c.close)} · ${c.round} · GM`, tag: c.tag ?? null });
export const jeeRowSaved = (college, r) => ({ id: `jee-${r.prog}`, exam: 'jee', title: college, sub: `${r.branch}${r.degree ? ` (${r.degree})` : ''}`,
  line: `Closing ${fmt(r.final.close)} ${r.rank_type} · ${r.final.label} · ${r.path}`, tag: null, jee: { prog: r.prog, quota: r.quota, gender: r.gender, path: r.path } });
export const comedkRowSaved = (code, college, r) => ({ id: `comedk-${code}|${r.cc}`, exam: 'comedk', title: college, sub: r.course, line: `COMEDK 2026 closing ${fmt(r.final.close)} · ${r.final.label} · GM`, tag: null });
export const bitsatRowSaved = r => ({ id: `bitsat-${r.id}`, exam: 'bitsat', title: r.college, sub: r.program, line: `BITSAT 2026 cutoff ${r.cutoff} / 390`, tag: null });

export function toCompareItem(s) {
  const j = s.seat ?? s.jee;
  if (s.exam === 'jee') return { exam: 'jee', id: s.id, prog: j?.prog, quota: j?.quota, gender: j?.gender, path: j?.path };
  return { exam: s.exam, id: s.id.replace(/^(comedk|bitsat)-/, '') };
}
export const savedPdfBody = (list, pick = []) => ({ items: list.map(toCompareItem), tags: list.map(s => s.tag), pick: pick.map(id => list.findIndex(s => s.id === id)).filter(i => i >= 0) });

// ---------- dream colleges (account) ----------
export const FULL = { jee: 300, bitsat: 390, comedk: 180 };
export const EXAMS = ['jee', 'bitsat', 'comedk'];
export const MAX_DREAMS = 5;
const EMPTY = { dreams: [], mocks: [], cheered: [], loaded: false, owner: null, notice: '' };
let dream = EMPTY, base = [], loading = null;
const dsubs = new Set();
const setDream = p => { dream = { ...dream, ...p }; dsubs.forEach(f => f()); };
const dsubscribe = f => { dsubs.add(f); return () => dsubs.delete(f); };
const dread = () => dream;

export function reloadDreams(uid = dream.owner) {
  if (!uid) return Promise.resolve();
  if (dream.owner !== uid) { dream = { ...EMPTY, owner: uid }; base = []; }
  loading = api('/dream').then(d => {
    if (dream.owner !== uid) return;
    base = d.dreams.map(x => x.id);
    setDream({ dreams: d.dreams, mocks: d.mocks, cheered: d.cheered, loaded: true });
  }).catch(() => setDream({ loaded: true })).finally(() => { loading = null; });
  return loading;
}

export function useDreams() {
  const { user } = useAuth();
  const uid = user?.id || null;
  useEffect(() => {
    if (!uid) { if (dream.owner) { dream = EMPTY; base = []; dsubs.forEach(f => f()); } return; }
    if (dream.owner !== uid || (!dream.loaded && !loading)) reloadDreams(uid);
  }, [uid]);
  return useSyncExternalStore(dsubscribe, dread, dread);
}
export const dreamsOf = (s, exam) => s.dreams.filter(d => d.exam === exam);
export const mocksOf = (s, exam) => s.mocks.filter(m => m.exam === exam);

async function saveDreams(next) {
  setDream({ dreams: next, notice: '' });
  try {
    const r = await put('/dream/dreams', { dreams: next, base });
    base = r.dreams.map(x => x.id);
    setDream({ dreams: r.dreams });
  } catch (e) {
    setDream({ notice: e.message || 'Ye badlav save nahi hua. Dobara try karo.' });
    await reloadDreams();
  }
}
export async function toggleDream(d) {
  if (!dream.owner) return 'login';
  if (dream.dreams.some(x => x.id === d.id)) { await saveDreams(dream.dreams.filter(x => x.id !== d.id)); return 'removed'; }
  if (dreamsOf(dream, d.exam).length >= MAX_DREAMS) return 'full';
  await saveDreams([...dream.dreams, d]);
  return 'added';
}
export const removeDream = id => saveDreams(dream.dreams.filter(x => x.id !== id));

/** Dreams the newest full mock of `exam` crossed for the first time (picked before that mock), hardest first; marked as celebrated at once. */
export function claimCheer(exam, mockId) {
  if (!dream.owner || !dream.loaded) return null;
  const m = mocksOf(dream, exam)[0];
  if (!m || (mockId && m.id !== mockId) || Date.now() - m.at > 7 * 86400000) return null;
  const done = new Set(dream.cheered);
  const won = dreamsOf(dream, exam).filter(d => !done.has(d.id) && d.at <= m.at && m.score >= d.need).sort((a, b) => b.need - a.need);
  if (!won.length) return null;
  setDream({ cheered: [...dream.cheered, ...won.map(d => d.id)] });
  post('/dream/cheered', { ids: won.map(d => d.id) }).catch(() => {});
  return { mock: m, dreams: won };
}

// The marks each dream seat needs (normal paper; easy..tough range), worked out when the student pins it.
let jeeProfile = { category: 'GEN', female: false, pwd: false, state: null };
export const setJeeProfile = p => { jeeProfile = p; };
export const getJeeProfile = () => jeeProfile;
const MISSING = 'Is seat ka target abhi nahi mila. Thodi der baad dobara try karo.';
const jeeFromRow = (college, row, cell) => {
  const m = cell?.marks ?? row.final.marks;
  return { id: `jee-${row.prog}`, exam: 'jee', college, branch: `${row.branch}${row.degree ? ` (${row.degree})` : ''}`, need: m.normal,
    range: [Math.min(m.easy, m.tough), Math.max(m.easy, m.tough)], note: `${cell ? cell.label : row.final.label} closing ${fmt(cell?.close ?? row.final.close)} ${row.rank_type}`, at: Date.now() };
};
export async function jeeDream(s) {
  const t = await rank.targetJee({ inst: s.inst, ...jeeProfile });
  const rows = t.rows.filter(r => r.prog === s.prog);
  const row = rows.find(r => r.path === s.path) ?? rows[0];
  if (!row) throw new Error(MISSING);
  const cell = row.path === s.path ? row.cells.find(c => c.label === s.round && c.close === s.close && c.marks) : undefined;
  return jeeFromRow(s.college, row, cell);
}
export const jeeRowDream = (college, row) => jeeFromRow(college, row);
export async function comedkDream(c) {
  const t = await rank.targetComedk(c.code);
  const row = t.rows.find(r => r.cc === c.cc);
  if (!row) throw new Error(MISSING);
  return comedkRowDream(c.code, c.college, row);
}
export const comedkRowDream = (code, college, row) => ({ id: `comedk-${code}|${row.cc}`, exam: 'comedk', college, branch: row.course, need: row.final.mid,
  range: [Math.min(...row.final.marks), Math.max(...row.final.marks)], note: `${row.final.label} closing ${fmt(row.final.close)} GM`, at: Date.now() });
export const bitsatDream = b => ({ id: `bitsat-${b.id}`, exam: 'bitsat', college: b.college, branch: b.program, need: b.cutoff, note: 'BITSAT 2026 cutoff', at: Date.now() });

/** The Dream button on a college card: pins / unpins the seat, says when the exam already has 5 or sign-in is needed. */
export function useDreamToggle(id, build) {
  const s = useDreams();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const on = s.dreams.some(d => d.id === id);
  const toggle = async () => {
    if (busy) return;
    setBusy(true); setMsg('');
    try {
      const out = await toggleDream(on ? { id } : await build());
      setMsg(out === 'login' ? 'Dream college save karne ke liye sign in karo.' : out === 'full' ? `Is exam ke ${MAX_DREAMS} dream college pehle se hain. Ek hatao, phir jodo.`
        : out === 'added' ? 'Dream mein juda! Har mock ke baad dikhega kitne marks door ho.' : '');
    } catch (e) { setMsg(e.message); }
    finally { setBusy(false); }
  };
  return { on, busy, msg, toggle };
}
