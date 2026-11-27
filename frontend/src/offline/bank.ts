// Rapid Fire's cards on the phone itself (the server's side: backend/rf_bank.py).
//
// When the app opens with a confirmed session, the list of parts is asked for (one part per subject, each with the hash
// of its bytes) and only the parts the phone does not have are fetched, one after another, quietly. A subject can be
// played from the phone the moment its part is here. The cards are the same for everybody, so they are kept for the
// phone, not for one account, and signing out leaves them.
//
// With the cards here a Solo Sprint is dealt on the phone (`dealRound`, the same rules as backend/rapid_deck.py `choose`):
// at once on a slow line and with no line at all. The finished round goes up later (./rounds.ts).
import { useSyncExternalStore } from "react";
import { ApiError, RF_BASE, rapidAccess, rf } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { CLASSIC_PICKS, CatalogSubject, Pick, SUBJECTS, cardCount } from "@/src/rapid/scope";
import { shelf } from "./shelf";

export type BankCard = { id: string; exam: string; subject: string; chapter: string; topic: string; prompt: string; formula: string; options: string[]; answer: number; explain: string; diagram?: any };
type Part = { subject: string; hash: string; cards: number; bytes: number; chapters: { name: string; count: number }[] };
type Kept = { parts: Part[]; checked: number };
export type BankView = { ready: boolean; cards: number; subjects: CatalogSubject[]; busy: boolean };

const EXAM = "JEE", KEY = "kept.bank.JEE.v1", SEEN_KEY = "kept.bank.seen.v1";
const RECHECK_MS = 6 * 3600 * 1000; // the list is asked for again at most this often
const SEEN_MAX = 1500; // the cards dealt lately on this phone: dealt again only after the others
const fileOf = (subject: string) => `bank.jee.${subject.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.json`;
const place = (subject: string) => { const i = (SUBJECTS as readonly string[]).indexOf(subject); return i < 0 ? 9 : i; };
const validPart = (p: any): p is Part => !!p && typeof p.subject === "string" && (SUBJECTS as readonly string[]).includes(p.subject) && typeof p.hash === "string" && /^[a-f0-9]{8,64}$/.test(p.hash)
  && Number.isInteger(p.cards) && p.cards > 0 && Array.isArray(p.chapters) && p.chapters.every((c: any) => c && typeof c.name === "string" && Number.isInteger(c.count));
const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

let kept: Kept | null = null, opened: Promise<void> | null = null, running: Promise<void> | null = null;
let view: BankView = { ready: false, cards: 0, subjects: [], busy: false };
const listeners = new Set<() => void>();
function publish(busy: boolean) {
  const parts = kept?.parts || [];
  view = { ready: parts.length > 0, cards: parts.reduce((n, p) => n + p.cards, 0), subjects: parts.map((p) => ({ name: p.subject, total: p.cards, chapters: p.chapters })), busy };
  listeners.forEach((f) => f());
}
async function save(next: Kept) {
  kept = { parts: [...next.parts].sort((a, b) => place(a.subject) - place(b.subject)), checked: next.checked };
  await storage.setItem(KEY, JSON.stringify(kept));
  publish(!!running);
}

/** What the phone has, read once per run of the app. */
export function openBank(): Promise<void> {
  return (opened ||= (async () => {
    try {
      const saved = JSON.parse((await storage.getItem<string | null>(KEY, null)) || "null");
      if (saved && Array.isArray(saved.parts) && saved.parts.every(validPart)) kept = { parts: saved.parts, checked: Number(saved.checked) || 0 };
    } catch { kept = null; }
    publish(!!running);
  })());
}
export const bankView = () => view;
/** The cards on this phone: `subjects` has the shape of the server's catalog, so the chapter picker can list them. */
export const useBank = () => useSyncExternalStore((f) => { listeners.add(f); void openBank(); return () => { listeners.delete(f); }; }, bankView, bankView);

async function fetchPart(uid: string, part: Part): Promise<string> {
  const token = await rapidAccess(uid);
  const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 180000); // a slow line gets its time: nobody is waiting for this
  try {
    const res = await fetch(`${RF_BASE}/bank/part?exam=${EXAM}&subject=${encodeURIComponent(part.subject)}&h=${part.hash}`, { headers: { Authorization: `Bearer ${token}` }, signal: ctl.signal });
    if (!res.ok) throw new ApiError("The cards could not be fetched.", res.status);
    return await res.text();
  } finally { clearTimeout(timer); }
}

/**
 * Brings the phone's cards up to date. Safe to call often: one run at a time, and the list is asked for at most every
 * six hours (`force` asks now). Trouble of any kind is left for the next call; what is already on the phone stays.
 */
export function syncBank(uid: string, force = false): Promise<void> {
  if (running) return running;
  running = (async () => {
    await openBank();
    if (!uid || (!force && kept?.parts.length && Date.now() - kept.checked < RECHECK_MS)) return;
    publish(true);
    const list = await rf<{ parts?: unknown[] }>(`/bank?exam=${EXAM}`, uid);
    const wanted = (Array.isArray(list?.parts) ? list.parts : []).filter(validPart).sort((a, b) => place(a.subject) - place(b.subject));
    if (!wanted.length) return;
    const gone = (kept?.parts || []).filter((p) => !wanted.some((w) => w.subject === p.subject));
    let parts = (kept?.parts || []).filter((p) => !gone.includes(p));
    for (const part of wanted) {
      if (parts.find((p) => p.subject === part.subject)?.hash === part.hash) continue;
      const text = await fetchPart(uid, part);
      const body = JSON.parse(text);
      if (!Array.isArray(body?.cards) || body.cards.length !== part.cards) throw new Error("The part is not whole.");
      if (!(await shelf.write(fileOf(part.subject), text))) throw new Error("The phone did not keep the part.");
      parsed.delete(part.subject);
      parts = [...parts.filter((p) => p.subject !== part.subject), part];
      await save({ parts, checked: kept?.checked || 0 }); // this subject can be played from the phone from now on
      await pause(250);
    }
    await save({ parts, checked: Date.now() });
    for (const p of gone) await shelf.remove(fileOf(p.subject));
  })().catch(() => {}).finally(() => { running = null; publish(false); });
  return running;
}

// ---- Dealing a round on the phone ----
type Pool = Map<string, BankCard[]>; // one subject's cards by chapter
const parsed = new Map<string, Pool>();
let release: ReturnType<typeof setTimeout> | undefined;
async function pool(subject: string): Promise<Pool | null> {
  const hit = parsed.get(subject);
  if (hit) return hit;
  let cards: any[] | null = null;
  try { const body = JSON.parse((await shelf.read(fileOf(subject))) || "null"); cards = Array.isArray(body?.cards) ? body.cards : null; } catch { cards = null; }
  if (!cards) { // the file is gone or broken: the phone no longer says it has this subject, and the next sync fetches it again
    if (kept) await save({ parts: kept.parts.filter((p) => p.subject !== subject), checked: 0 });
    return null;
  }
  const groups: Pool = new Map();
  for (const c of cards) {
    if (!c || typeof c.id !== "string" || typeof c.prompt !== "string" || !Array.isArray(c.options)) continue;
    const card: BankCard = { ...c, exam: EXAM, subject };
    const rows = groups.get(card.chapter);
    if (rows) rows.push(card); else groups.set(card.chapter, [card]);
  }
  parsed.set(subject, groups);
  clearTimeout(release);
  release = setTimeout(() => parsed.clear(), 180000); // a few megabytes of cards are not held once the rounds stop
  return groups;
}

const mark = (prompt: string) => prompt.trim().toLowerCase().replace(/\s+/g, " ");
/**
 * The server's own way of dealing (backend/rapid_deck.py `choose`): every pick (a whole subject or one chapter) gets an
 * even share, inside a whole subject every chapter does, no prompt comes twice, and inside a chapter the cards in
 * `avoid` come last. null = these picks do not have `count` different cards.
 */
export function choose(pools: Record<string, Pool>, picks: Pick[], count: number, avoid: Set<string>, random: () => number = Math.random): BankCard[] | null {
  const shuffle = <T,>(list: T[]) => { for (let i = list.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [list[i], list[j]] = [list[j], list[i]]; } return list; };
  type Lane = { groups: Pool; keys: string[]; turn: number; left: Map<string, [BankCard[], BankCard[]]> };
  const lanes: Lane[] = picks.map((p) => {
    const groups = pools[p.subject] || new Map();
    return { groups, keys: shuffle((p.chapter ? [p.chapter] : [...groups.keys()]).filter((k) => groups.get(k)?.length)), turn: 0, left: new Map() };
  });
  if (lanes.length > CLASSIC_PICKS) shuffle(lanes); // many chapters ticked one by one: which of them get a card must not follow the alphabet
  const draw = (lane: Lane, key: string) => {
    let left = lane.left.get(key);
    if (!left) { const rows = lane.groups.get(key)!; left = [rows.filter((c) => !avoid.has(c.id)), rows.filter((c) => avoid.has(c.id))]; lane.left.set(key, left); } // the kept cards themselves are never changed
    for (const rows of left) if (rows.length) { const i = Math.floor(random() * rows.length); [rows[i], rows[rows.length - 1]] = [rows[rows.length - 1], rows[i]]; return rows.pop()!; }
    return null;
  };
  const used = new Set<string>(), picked: BankCard[] = [];
  const take = (lane: Lane) => {
    while (lane.keys.length) {
      const key = lane.keys[lane.turn % lane.keys.length], card = draw(lane, key);
      if (!card) { lane.keys.splice(lane.keys.indexOf(key), 1); continue; }
      lane.turn++;
      if (!used.has(mark(card.prompt))) { used.add(mark(card.prompt)); return card; }
    }
    return null;
  };
  while (picked.length < count && lanes.some((lane) => lane.keys.length)) for (const lane of lanes) { const card = picked.length < count ? take(lane) : null; if (card) picked.push(card); }
  return picked.length < count ? null : picked;
}

async function seen(): Promise<string[]> {
  try { const list = JSON.parse((await storage.getItem<string | null>(SEEN_KEY, null)) || "[]"); return Array.isArray(list) ? list.filter((x) => typeof x === "string") : []; } catch { return []; }
}

/** Can a round of `count` cards on these picks be dealt from the phone right now? */
export async function bankCanDeal(picks: Pick[], count: number): Promise<boolean> {
  await openBank();
  return picks.length > 0 && picks.every((p) => view.subjects.some((s) => s.name === p.subject)) && cardCount(picks, view.subjects) >= count;
}

/** A round dealt from the phone's cards: null when the phone cannot (a subject is not here, or too few cards). */
export async function dealRound(picks: Pick[], count: number): Promise<BankCard[] | null> {
  if (!(await bankCanDeal(picks, count))) return null;
  const pools: Record<string, Pool> = {};
  for (const subject of new Set(picks.map((p) => p.subject))) { const groups = await pool(subject); if (!groups) return null; pools[subject] = groups; }
  const before = await seen();
  const cards = choose(pools, picks, count, new Set(before));
  if (cards) await storage.setItem(SEEN_KEY, JSON.stringify([...before, ...cards.map((c) => c.id)].slice(-SEEN_MAX)));
  return cards;
}

// The missed cards of a round, handed to the next screen to be played again (they are already in memory).
let handed: { token: string; cards: BankCard[] } | null = null;
export const handRound = (token: string, cards: BankCard[]) => { handed = { token, cards }; };
export const takeRound = (token?: string) => (token && handed?.token === token ? handed.cards : null);
