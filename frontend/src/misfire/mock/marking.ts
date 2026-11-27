// Marking a Misfire Mock on the phone, with the paper's own rule for each kind of answer, and the website hearing of
// every right answer: first a try with the same answer (the website's own check, as Misfire's "Check karo"), then
// "Samajh gaya" (the website refuses that before a right try). What the website does not take as right counts as wrong.
import { useEffect } from "react";
import { ApiError } from "@/src/api/client";
import { invalidate } from "@/src/useCached";
import { SUBJECTS } from "@/src/choice/api";
import { markDone, misfireKey, tryAgain } from "../api";
import { patchMisfire } from "../store";
import { MARKS, Marked, Mock, MockQ, MockRow, Outcome, Sync, getMock, latest, saveState } from "./store";

const MINUS = /[\u2212\u2010-\u2015\uFE63\uFF0D]/g;
const INTEGER = /^[+-]?\d{1,20}$/;
const canon = (s: string) => { const neg = s.startsWith("-"); const digits = s.replace(/^[+-]/, "").replace(/^0+(?=\d)/, ""); return (neg && digits !== "0" ? "-" : "") + digits; };

/** Whether this answer is right. An option: one of the keys. A number: the website's rule ("integer_exact": signs,
 *  Unicode minus and leading zeros accepted, no decimals; any other rule: the same value). */
export function isRight(q: MockQ, given: string): boolean {
  const value = given.trim();
  if (!value) return false;
  const keys = q.accepted.length ? q.accepted : [q.answer];
  if (q.options && Object.keys(q.options).length) return keys.includes(value);
  const a = value.replace(MINUS, "-").replace(/\s+/g, "");
  return keys.some((k) => {
    const b = String(k).replace(MINUS, "-").replace(/\s+/g, "");
    if (q.numeric === "integer_exact") return INTEGER.test(a) && INTEGER.test(b) ? canon(a) === canon(b) : a === b;
    if (a === b) return true;
    const x = Number(a), y = Number(b);
    return Number.isFinite(x) && Number.isFinite(y) && Math.abs(x - y) < 1e-9;
  });
}

/** The mock's result. `refused`: right on the phone, but the website did not take them as right. */
export function mark(m: Mock, submittedAt: number, refused: string[] = []): Marked {
  const no = new Set(refused), outcomes: Record<string, Outcome> = {};
  for (const q of m.questions) {
    const v = m.answers[q.id]?.value?.trim() || "";
    outcomes[q.id] = !v ? "skipped" : isRight(q, v) && !no.has(q.id) ? "correct" : "incorrect";
  }
  const sum = (qs: MockQ[]) => {
    const n = (o: Outcome) => qs.filter((q) => outcomes[q.id] === o).length;
    const correct = n("correct"), incorrect = n("incorrect");
    return { count: qs.length, correct, incorrect, skipped: n("skipped"), score: correct * MARKS.correct + incorrect * MARKS.wrong, maximum: qs.length * MARKS.correct };
  };
  const all = sum(m.questions);
  const tried = all.correct + all.incorrect;
  const used = m.started_at ? Math.max(0, Math.round((Math.min(submittedAt, m.deadline || submittedAt) - m.started_at) / 1000)) : 0;
  return {
    ...all, accuracy: tried ? Math.round((1000 * all.correct) / tried) / 10 : null, used, outcomes,
    subjects: SUBJECTS.map((name) => ({ name, ...sum(m.questions.filter((q) => q.subject === name)) })).filter((s) => s.count > 0),
  };
}

/** Ends the mock (the student's Submit, or the clock ran out): marked, and its right answers lined up for the website. */
export function submit(m: Mock, at = Date.now()): Mock {
  const now = latest(m);
  if (now.status === "done") return now;
  const result = mark(now, at);
  const sync: Sync = { todo: now.questions.filter((q) => result.outcomes[q.id] === "correct").map((q) => q.id), moved: [], refused: [], gone: [] };
  const done = saveState(now, { status: "done", submitted_at: at, result, sync });
  void sendRight(done.id);
  return done;
}

/** A mock whose clock ran out while the app was closed is submitted when it is next seen. */
export function settle(m: Mock): Mock {
  return m.status === "active" && m.deadline && Date.now() >= m.deadline ? submit(m, m.deadline) : m;
}

const later = (e: unknown) => !(e instanceof ApiError) || e.status === 0 || e.status === 401 || e.status === 403 || e.status === 408 || e.status === 429 || e.status >= 500;
const sending = new Map<string, Promise<void>>();

/** Sends the mock's right answers still waiting, three at a time. A line that drops leaves the rest for the next time
 *  the mock or the list is seen. Never sends a wrong or a left question. */
export function sendRight(id: string): Promise<void> {
  const going = sending.get(id);
  if (going) return going;
  const work = (async () => {
    let m = await getMock(id);
    if (!m?.sync?.todo.length) return;
    const by = new Map(m.questions.map((q) => [q.id, q]));
    const moved: string[] = [], refused: string[] = [], gone: string[] = [];
    let stop = false;
    const one = async (qid: string) => {
      const q = by.get(qid), value = m!.answers[qid]?.value?.trim() || "";
      if (!q || !value) { gone.push(qid); return; }
      try {
        const res = await tryAgain(q.misfire_id, value);
        if (!res?.correct) { refused.push(qid); return; }
        await markDone(q.misfire_id);
        patchMisfire(q.misfire_id, { status: "fixed", tries: res.item?.tries, last_correct: true });
        moved.push(qid);
      } catch (e) {
        if (later(e)) stop = true; else gone.push(qid); // a question no longer in Misfire (or already understood) is let go
      }
    };
    const todo = [...m.sync.todo];
    while (todo.length && !stop) await Promise.all(todo.splice(0, 3).map(one));
    m = latest(m);
    const handled = new Set([...moved, ...refused, ...gone]);
    const sync: Sync = { todo: m.sync!.todo.filter((x) => !handled.has(x)), moved: [...m.sync!.moved, ...moved], refused: [...m.sync!.refused, ...refused], gone: [...m.sync!.gone, ...gone] };
    const patch = refused.length ? { sync, result: mark(m, m.submitted_at || Date.now(), sync.refused) } : { sync };
    saveState(m, patch);
    if (moved.length) { invalidate(misfireKey(m.uid)); }
  })().catch(() => {}).finally(() => { sending.delete(id); });
  sending.set(id, work);
  return work;
}

/** Sends the right answers of every finished mock still waiting (a list of mocks on screen asks for it). */
export function useSendWaiting(rows: MockRow[]) {
  const waiting = rows.filter((r) => r.status === "done" && r.waiting).map((r) => r.id).join("|");
  useEffect(() => { if (waiting) waiting.split("|").forEach((id) => { void sendRight(id); }); }, [waiting]);
}
