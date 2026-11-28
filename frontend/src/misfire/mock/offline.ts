// Offline Misfire without a line: who may make and take one, where its screens are, and the questions it is made from.
//
// - Who: the signed-in student; without a line, the account confirmed on this phone in the last 7 days (the owner's rule,
//   src/offline/identity.ts), whose own store is then opened. Nobody else.
// - Where: inside the app at /misfire/mock/…, and behind the offline door at /offline/misfire/… (the same screens).
// - From what (`phonePool`): the wrong and left questions of the finished papers kept on this phone
//   (src/offline/papers.ts), minus the ones last known as "Samajh gaya" (../known.ts), and only those whose question
//   pictures are on the phone too. With a line the setup reads the website's own open list instead, as before.
// Nothing here starts anything on the website.
import { useEffect, useMemo, useState } from "react";
import { usePathname } from "expo-router";
import { useAuth } from "@/src/auth";
import { getAssetAccount, setAssetAccount } from "@/src/api/client";
import { ARENA } from "@/src/arenaMode";
import { pictureKeys } from "@/src/assets/assetGrants";
import { savedImages } from "@/src/assets/deviceCache/cache";
import { SUBJECTS, Subject } from "@/src/choice/api";
import { isResultLocked } from "@/src/mission/gate";
import { offlineIdentity } from "@/src/offline/identity";
import { keepingHeld, keptResult, keptResults } from "@/src/offline/papers";
import { MisfireItem, fromResult, getPage, getSummary } from "../api";
import { knownChecked, knownFixed, knownVersion, replaceKnown } from "../known";
import { applied } from "../store";

const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// ---- Who, and where ----
export type MockAccess = { state: "checking" } | { state: "closed" } | { state: "open"; uid: string; online: boolean };

/** The signed-in student (online), or without a line the account confirmed on this phone lately (its store opened).
 *  Inside the app (/misfire/mock/…) only the signed-in student: until the session check has answered it waits. Behind
 *  the offline door it does not wait (like the phone's results): it opens at once and turns online if the session comes. */
export function useMockAccess(): MockAccess {
  const { user, expired, ready } = useAuth();
  const door = usePathname().startsWith("/offline");
  const [who, setWho] = useState<{ uid: string } | null | undefined>(user ? { uid: user.id } : undefined);
  useEffect(() => {
    let alive = true;
    (async () => {
      const mine = expired ? null : user ? { uid: user.id } : door ? await offlineIdentity() : ready ? null : undefined; // a session the server ended opens nothing
      if (mine && !user && getAssetAccount() !== mine.uid) setAssetAccount(mine.uid);
      if (alive) setWho(mine);
    })();
    return () => { alive = false; };
  }, [user, expired, ready, door]);
  if (who === undefined) return { state: "checking" };
  return who ? { state: "open", uid: who.uid, online: !!user } : { state: "closed" };
}

/** The Offline Misfire screens' own places: inside the app, or behind the offline door. */
export function useMockPaths() {
  const offline = usePathname().startsWith("/offline");
  return useMemo(() => ({
    offline,
    list: (offline ? "/offline/misfire" : { pathname: "/misfire", params: { tab: "mock" } }) as any,
    make: (offline ? "/offline/misfire/new" : "/misfire/mock/new") as any,
    one: (id: string, short = false) => ({ pathname: offline ? "/offline/misfire/[id]" : "/misfire/mock/[id]", params: { id, short: short ? "1" : "" } }) as any,
    /** The paper a question came from: its result, or behind the offline door the copy this phone keeps. */
    paper: (attempt: string) => (offline ? { pathname: "/offline/result", params: { id: attempt } } : `/result/${attempt}`) as any,
  }), [offline]);
}

// ---- The questions on this phone ----
export type PoolSubjects = Record<Subject, { total: number; chapters: { name: string; count: number }[] }>;
export type PhonePool = { items: MisfireItem[]; papers: number; subjects: PoolSubjects };
/** The chapter of a question whose paper has no chapter names (shown as "PYQ papers ke sawaal (chapter tag nahi)"). */
const UNTAGGED = "Uncategorised";
const hasKey = (q: any) => !!String(q?.answer ?? "").trim() || (Array.isArray(q?.accepted_answers) && q.accepted_answers.some((x: unknown) => String(x ?? "").trim()));
const emptySubjects = (): PoolSubjects => Object.fromEntries(SUBJECTS.map((s) => [s, { total: 0, chapters: [] }])) as unknown as PoolSubjects;
export const NO_POOL: PhonePool = { items: [], papers: 0, subjects: emptySubjects() };

let memo: { uid: string; sig: string; pool: PhonePool } | null = null;

/**
 * Every wrong or left question of the finished papers kept on this phone that can be given without a line: not last
 * known as "Samajh gaya", with its key, with its question pictures on the phone, and once only (the newest paper's copy
 * when a question was in two papers). A result kept but never opened once is left out (as its kept copy is).
 */
export async function phonePool(signal?: AbortSignal): Promise<PhonePool> {
  const uid = getAssetAccount();
  if (!uid) return NO_POOL;
  const [rows, fixed] = await Promise.all([keptResults(), knownFixed()]);
  const sig = `${rows.map((r) => `${r.id}.${r.at}.${r.kept}`).join("|")}#${knownVersion()}.${fixed.size}`;
  if (memo && memo.uid === uid && memo.sig === sig) return memo.pool;
  const items: MisfireItem[] = [], seen = new Set<string>();
  let papers = 0;
  for (const row of rows) {
    if (signal?.aborted || getAssetAccount() !== uid) throw Object.assign(new Error("aborted"), { name: "AbortError" });
    if (await isResultLocked(row.id)) continue;
    const r = await keptResult(row.id);
    if (!r || !Array.isArray(r.questions)) continue;
    const wrong = (r.questions as any[]).map((q) => ({ q, it: fromResult(r, q, false) })).filter(({ q, it }) =>
      (q?.outcome === "incorrect" || q?.outcome === "skipped") && q.disposition !== "bonus_all" && q.disposition !== "dropped" && hasKey(q)
      && (SUBJECTS as readonly string[]).includes(it.subject) && !seen.has(String(q.id)) && !fixed.has(it.id));
    if (!wrong.length) continue;
    const keys = wrong.map(({ q }) => pictureKeys(r.id, q, false).map((k) => k.contentKey));
    const have = await savedImages(keys.flat());
    if (!have) continue; // the store cannot be read just now
    let k = 0, took = 0;
    wrong.forEach(({ q, it }, i) => {
      const whole = have.slice(k, k + keys[i].length).every(Boolean);
      k += keys[i].length;
      const now = applied(it); // marked "Samajh gaya" a moment ago in this app
      if (!whole || now.status !== "open") return;
      seen.add(String(q.id));
      items.push({ ...it, question: null, chapter: String(q.topic || "").trim() || UNTAGGED });
      took++;
    });
    if (took) papers++;
    await pause(0); // the screen stays alive between papers
  }
  const subjects = emptySubjects();
  for (const s of SUBJECTS) {
    const mine = items.filter((it) => it.subject === s), by = new Map<string, number>();
    mine.forEach((it) => by.set(it.chapter || UNTAGGED, (by.get(it.chapter || UNTAGGED) || 0) + 1));
    subjects[s] = { total: mine.length, chapters: [...by].map(([name, count]) => ({ name, count })) };
  }
  const pool = { items, papers, subjects };
  if (getAssetAccount() === uid) memo = { uid, sig, pool };
  return pool;
}

/** `phonePool` for a screen: null while it is being read (or when `on` is false). */
export function usePhonePool(on: boolean): PhonePool | null {
  const [got, setGot] = useState<PhonePool | null>(null);
  useEffect(() => {
    if (!on) return;
    let alive = true;
    const ctl = new AbortController();
    setGot(null);
    phonePool(ctl.signal).then((p) => { if (alive) setGot(p); }, (e) => { if (alive && e?.name !== "AbortError") setGot(NO_POOL); });
    return () => { alive = false; ctl.abort(); };
  }, [on]);
  return on ? got : null;
}

// ---- Keeping ../known.ts close to the website, while signed in ----
const GAP = 15 * 60 * 1000, DAY = 24 * 3600 * 1000, MAX_PAGES = 50, PAGE_GAP = 800;
let lastRefresh = 0, refreshing: Promise<void> | null = null;

/**
 * Reads the website's whole "Samajh gaya" list again when the count the website gives differs from the phone's, or a
 * day after the last full read; otherwise one small summary call. At most once in 15 minutes, never while a paper or a
 * round is being taken. 20 a page, at most 50 pages (1,000 questions): beyond that what is known is only added to.
 */
export function refreshKnown(uid: string): Promise<void> {
  if (refreshing) return refreshing;
  if (ARENA || !uid || getAssetAccount() !== uid || keepingHeld() || Date.now() - lastRefresh < GAP) return Promise.resolve();
  lastRefresh = Date.now();
  const mine = () => getAssetAccount() === uid && !keepingHeld();
  refreshing = (async () => {
    const [s, have] = await Promise.all([getSummary(), knownFixed()]);
    if (!mine()) return;
    if (have.size === (Number(s?.fixed) || 0) && Date.now() - knownChecked() < DAY) return;
    const got: string[] = [];
    let complete = false;
    for (let page = 1; page <= MAX_PAGES && mine(); page++) {
      const d = await getPage("fixed", "", "", page);
      got.push(...(d.items || []).map((i) => i.id).filter(Boolean));
      if (page >= (d.pages || 1)) { complete = true; break; }
      await pause(PAGE_GAP);
    }
    if (mine()) await replaceKnown(got, complete);
  })().catch(() => {}).finally(() => { refreshing = null; });
  return refreshing;
}
