// Solo Sprints that are finished on the phone but not yet on the server: each is kept here, under the account it belongs
// to, until the server has answered for it. Two kinds:
//   - a round dealt on the phone from its own cards (./bank.ts): goes up whole (POST /api/rf/sessions/offline);
//   - a sprint the server dealt whose answers could not be sent at the end (the line dropped): its answers go to that
//     sprint (POST /api/rf/sessions/<id>/complete); if the server closed it meanwhile, it goes up as a round of its own.
// The same request_id is the same sprint on the server, so sending a round twice never pays it twice.
import { useSyncExternalStore } from "react";
import { ApiError, rf } from "@/src/api/client";
import { resources } from "@/src/resourceCache";
import { storage } from "@/src/utils/storage";
import type { Pick } from "@/src/rapid/scope";

export type Res = { card_id: string; outcome: "correct" | "incorrect" | "skipped" | "timed_out"; choice: number | null; ms: number };
export type KeptRound = { request_id: string; session?: string; picks?: Pick[] | null; card_ids: string[]; results: Res[]; played_at: string; repeat?: boolean };
type Marked = { id: string; chapter: string; topic?: string; answer: number };

const MAX_KEPT = 200; // about 6,000 cards played without ever reaching the server; beyond it the oldest round gives way
const listKey = (uid: string) => `kept.rounds.${uid}`, roundKey = (id: string) => `kept.round.${id}`;
const counts = new Map<string, number>(), listeners = new Set<() => void>();
/** `rewards`: what the server paid for each round that went up in this call, by the round's request_id. */
export type Sent = { sent: number; left: number; rewards: Record<string, any> };
const sending = new Map<string, Promise<Sent>>();

async function ids(uid: string): Promise<string[]> {
  try { const list = JSON.parse((await storage.getItem<string | null>(listKey(uid), null)) || "[]"); return Array.isArray(list) ? list.filter((x) => typeof x === "string") : []; } catch { return []; }
}
async function setIds(uid: string, list: string[]) {
  await storage.setItem(listKey(uid), JSON.stringify(list));
  counts.set(uid, list.length);
  listeners.forEach((f) => f());
}

/** The marking the server will do, done on the phone for the result screen (backend/sprints.py `finish`). */
export function summarise(cards: Marked[], results: Res[]) {
  const by = new Map(results.map((r) => [r.card_id, r]));
  const rows = cards.map((c) => {
    const r = by.get(c.id);
    if (!r) return { card_id: c.id, outcome: "skipped" as const, choice: null, ms: 0, chapter: c.chapter, topic: "" };
    const outcome = r.outcome === "correct" || r.outcome === "incorrect" ? (r.choice === c.answer ? "correct" as const : "incorrect" as const) : r.outcome;
    return { card_id: c.id, outcome, choice: outcome === "correct" || outcome === "incorrect" ? r.choice : null, ms: r.ms, chapter: c.chapter, topic: c.topic || "" };
  });
  const n = (k: Res["outcome"]) => rows.filter((row) => row.outcome === k).length;
  const correct = n("correct"), incorrect = n("incorrect"), answered = correct + incorrect, weak = new Map<string, number>();
  for (const row of rows) if (row.outcome === "incorrect" || row.outcome === "timed_out") weak.set(row.topic || row.chapter, (weak.get(row.topic || row.chapter) || 0) + 1);
  return { results: rows, summary: { total: rows.length, correct, incorrect, skipped: n("skipped"), timed_out: n("timed_out"), answered, score: correct,
    accuracy: answered ? Math.round((1000 * correct) / answered) / 10 : null, revise_topics: [...weak.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k]) => k) } };
}

/** Keeps a finished round on the phone until the server has it. */
export async function keepRound(uid: string, round: KeptRound): Promise<void> {
  if (!uid) return;
  await storage.setItem(roundKey(round.request_id), JSON.stringify({ ...round, uid }));
  const list = [...(await ids(uid)).filter((id) => id !== round.request_id), round.request_id];
  for (const old of list.slice(0, Math.max(0, list.length - MAX_KEPT))) await storage.removeItem(roundKey(old));
  await setIds(uid, list.slice(-MAX_KEPT));
}

const later = (e: unknown) => !(e instanceof ApiError) || e.status === 0 || e.status === 401 || e.status === 403 || e.status === 408 || e.status === 429 || e.status >= 500;

/**
 * Sends this account's kept rounds, oldest first. Needs a signed-in session. Stops at the first round the server could
 * not be reached for (it stays for the next call); a round the server refuses for good is let go.
 */
export function sendRounds(uid: string): Promise<Sent> {
  const going = sending.get(uid);
  if (going) return going;
  const work = (async () => {
    let sent = 0;
    const rewards: Record<string, any> = {};
    for (const id of await ids(uid)) {
      let round: (KeptRound & { uid?: string }) | null = null;
      try { round = JSON.parse((await storage.getItem<string | null>(roundKey(id), null)) || "null"); } catch { round = null; }
      const whole = { request_id: id, exam: "JEE", card_ids: round?.card_ids, results: round?.results, played_at: round?.played_at, repeat: !!round?.repeat, ...(round?.picks?.length ? { picks: round.picks } : {}) };
      try {
        if (round && round.uid === uid && Array.isArray(round.card_ids) && round.card_ids.length) {
          let closed: any;
          if (round.session) {
            try { closed = await rf(`/sessions/${round.session}/complete`, uid, { method: "POST", body: { results: round.results } }); }
            catch (e) { if (later(e)) throw e; closed = await rf("/sessions/offline", uid, { method: "POST", body: whole }); } // the server closed that sprint meanwhile
          } else closed = await rf("/sessions/offline", uid, { method: "POST", body: whole });
          rewards[id] = closed?.reward || null;
          sent++;
        }
      } catch (e) {
        if (later(e)) break;
      }
      await storage.removeItem(roundKey(id));
      await setIds(uid, (await ids(uid)).filter((x) => x !== id));
    }
    if (sent) resources.invalidate(`u.${uid}.revision`); // the missed cards of these rounds belong on the revision list now
    return { sent, left: (await ids(uid)).length, rewards };
  })().finally(() => { sending.delete(uid); });
  sending.set(uid, work);
  return work;
}

/** How many of this account's rounds are still waiting on the phone. */
export function useKeptRounds(uid?: string): number {
  return useSyncExternalStore((f) => {
    listeners.add(f);
    if (uid && !counts.has(uid)) void ids(uid).then((list) => { counts.set(uid, list.length); f(); });
    return () => { listeners.delete(f); };
  }, () => (uid ? counts.get(uid) || 0 : 0), () => 0);
}
