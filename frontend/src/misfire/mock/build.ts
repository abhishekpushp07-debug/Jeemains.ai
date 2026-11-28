// Making a Misfire Mock: the student says how many questions of each subject and from which chapters. The questions
// are drawn at random from their own open Misfire list (the website's /my/misfire, a few of its pages), then every
// drawn question is read from the result of the paper it came from (its key and its solution). A paper already kept
// on the phone (src/offline/papers.ts) is read from there; any other result is read once from the website, as
// "Paper ka result" does. Nothing is started on the website and nothing is written there.
import { apiRaw, uuid } from "@/src/api/client";
import { resultIsReleased } from "@/src/assets/paperAssets";
import { originalLook } from "@/src/assets/pieces";
import { Counts, NONE, SUBJECTS, Subject, minutesFor, totalOf } from "@/src/choice/api";
import { keptResult } from "@/src/offline/papers";
import { MisfireItem, getPage } from "../api";
import { applied } from "../store";
import { Mock, MockQ, addMock, loadMocks, nextNumber } from "./store";

/** The owner's rule: 25 questions = Maths 80 min, Physics 60 min, Chemistry 40 min. */
export const PER_QUESTION: Record<Subject, number> = { Physics: 2.4, Chemistry: 1.6, Mathematics: 3.2 };
export const MAX_PER_SUBJECT = 25;
const PAGE = 20, PAPERS = 12;

/** What the student asked for: questions per subject, and the chapters of each (`null` = every chapter). */
export type Ask = { counts: Counts; chapters: Record<Subject, string[] | null>; sizes: Record<Subject, Record<string, number>> };
export type Step = { step: "pick" | "keys"; done: number; total: number };

const shuffle = <T>(list: T[]) => { const a = [...list]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
/** `n` spread over the buckets by their sizes (largest remainder), none above its size. */
function share(n: number, sizes: number[]): number[] {
  const all = sizes.reduce((a, b) => a + b, 0);
  if (!all) return sizes.map(() => 0);
  const exact = sizes.map((s) => (n * s) / all), out = exact.map((x, i) => Math.min(sizes[i], Math.floor(x)));
  let left = Math.min(n, all) - out.reduce((a, b) => a + b, 0);
  const order = exact.map((x, i) => [x - Math.floor(x), i] as const).sort((a, b) => b[0] - a[0]).map(([, i]) => i);
  while (left > 0) { let moved = false; for (const i of order) if (left > 0 && out[i] < sizes[i]) { out[i]++; left--; moved = true; } if (!moved) break; }
  return out;
}

/** Up to about three times as many open questions as are needed, from random pages of this subject (and chapter). */
async function candidates(subject: Subject, chapter: string, need: number, signal: AbortSignal): Promise<MisfireItem[]> {
  const first = await getPage("open", subject, chapter, 1, signal);
  const pages = Math.max(1, first.pages || 1);
  const more = shuffle(Array.from({ length: pages - 1 }, (_, i) => i + 2)).slice(0, Math.max(0, Math.ceil((3 * need) / PAGE) - 1));
  const rest = await Promise.all(more.map((p) => getPage("open", subject, chapter, p, signal).then((d) => d.items || []).catch(() => [] as MisfireItem[])));
  return [...(first.items || []), ...rest.flat()].map(applied)
    .filter((it) => it.status === "open" && it.subject === subject && (it.outcome === "incorrect" || it.outcome === "skipped") && !!it.attempt_id && !!it.question_id);
}

/** The released result of one paper: from the phone when it is kept there, else from the website. Null: not open. */
async function resultOf(attempt: string, signal: AbortSignal): Promise<any | null> {
  const kept = await keptResult(attempt).catch(() => null);
  if (kept) return kept;
  try {
    const r = await apiRaw<any>(`/attempts/${encodeURIComponent(attempt)}/results?score_version=original`, { signal });
    return resultIsReleased(r.status, r.data) ? originalLook(r.data) : null;
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    return null;
  }
}

/** The question as the mock keeps it: what the screens draw, the key, and nothing else of the result. */
function questionOf(it: MisfireItem, q: any, rules: any): MockQ | null {
  if (!q || q.disposition === "bonus_all" || q.disposition === "dropped") return null;
  const accepted = (Array.isArray(q.accepted_answers) ? q.accepted_answers : []).map(String).filter(Boolean);
  const answer = String(q.answer ?? accepted[0] ?? "").trim();
  if (!answer && !accepted.length) return null;
  return {
    id: String(q.id), misfire_id: it.id, attempt_id: it.attempt_id, number: 0, subject: it.subject as Subject, chapter: it.chapter || "", exam: it.exam || "",
    source: it.title || "", source_number: Number(q.number ?? it.number) || 0,
    type: String(q.type || it.type || "mcq"), text: q.text || "", options: q.options || {}, typed_options: q.typed_options || null, pieces: q.pieces || null,
    render_mode: q.render_mode, source_option_labels: q.source_option_labels || null, accessible_text: q.accessible_text || "", asset_count: Number(q.asset_count) || 0,
    asset_revision: q.asset_revision, source_revision: q.source_revision, source_ref: q.source_ref,
    solution: q.solution || "", solution_kind: q.solution_kind || "", solution_asset_count: Number(q.solution_asset_count) || 0,
    answer, accepted: accepted.length ? accepted : [answer], numeric: String(rules?.numeric_policy || ""),
  };
}

/**
 * Makes the mock and keeps it on the phone (not started: its clock starts on "Shuru karo"). `short`: subjects that
 * gave fewer questions than asked (the student's rule: then as many as there are). `phone`: made without a line, from
 * these questions of the papers kept on this phone (./offline.ts phonePool); their keys are read from those copies.
 */
export async function buildMock(uid: string, ask: Ask, onStep: (s: Step) => void, signal: AbortSignal, phone?: MisfireItem[]): Promise<{ mock: Mock; short: Subject[] }> {
  onStep({ step: "pick", done: 0, total: 1 });
  const wanted = SUBJECTS.filter((s) => ask.counts[s] > 0);
  // Every bucket (a subject, or one chapter of it) with how many to draw from it.
  const buckets = wanted.flatMap((s) => {
    const chapters = ask.chapters[s];
    if (!chapters) return [{ subject: s, chapter: "", need: ask.counts[s] }];
    const needs = share(ask.counts[s], chapters.map((c) => ask.sizes[s][c] || 0));
    return chapters.map((c, i) => ({ subject: s, chapter: c, need: needs[i] })).filter((b) => b.need > 0);
  });
  const fromPhone = (b: { subject: Subject; chapter: string }) => Promise.resolve((phone || []).map(applied)
    .filter((it) => it.status === "open" && it.subject === b.subject && (!b.chapter || it.chapter === b.chapter)));
  const pools = await Promise.all(buckets.map((b) => (phone ? fromPhone(b) : candidates(b.subject, b.chapter, b.need, signal)).then((items) => ({ ...b, items: shuffle(items) }))));

  const taken = new Set<string>(), papers = new Set<string>(), picked: MisfireItem[] = [];
  const counted = { ...NONE };
  // Two passes: first only from at most 12 papers (fewer results to read), then from any paper to fill what is left.
  for (const pass of [0, 1]) for (const b of pools) {
    let got = picked.filter((it) => it.subject === b.subject && (!b.chapter || it.chapter === b.chapter)).length;
    for (const it of b.items) {
      if (got >= b.need) break;
      if (taken.has(it.question_id) || (pass === 0 && !papers.has(it.attempt_id) && papers.size >= PAPERS)) continue;
      taken.add(it.question_id); papers.add(it.attempt_id); picked.push(it); got++;
    }
  }

  // The key and the solution of every drawn question, paper by paper (three at a time).
  const attempts = [...new Set(picked.map((it) => it.attempt_id))];
  const results = new Map<string, any>();
  let done = 0;
  onStep({ step: "keys", done, total: attempts.length });
  for (let i = 0; i < attempts.length; i += 3) {
    await Promise.all(attempts.slice(i, i + 3).map(async (a) => {
      results.set(a, phone ? await keptResult(a).catch(() => null) : await resultOf(a, signal));
      done++; onStep({ step: "keys", done, total: attempts.length });
    }));
  }
  const kept: MockQ[] = [];
  for (const it of picked) {
    const r = results.get(it.attempt_id);
    const q = questionOf(it, (r?.questions || []).find((x: any) => String(x?.id) === it.question_id), r?.rules);
    if (q) kept.push(q);
  }
  // A question that could not be read (its paper's result is not open, or it was made a bonus) is replaced from a paper
  // already read, when that paper has another open question of the same subject and chapter.
  for (const b of pools) {
    const have = () => kept.filter((q) => q.subject === b.subject && (!b.chapter || q.chapter === b.chapter)).length;
    for (const it of b.items) {
      if (have() >= b.need) break;
      if (taken.has(it.question_id) || !results.get(it.attempt_id)) continue;
      const r = results.get(it.attempt_id);
      const q = questionOf(it, (r.questions || []).find((x: any) => String(x?.id) === it.question_id), r.rules);
      taken.add(it.question_id);
      if (q) kept.push(q);
    }
  }

  // Physics, Chemistry, Maths, as a JEE Main paper; inside a subject the order is random. Numbered 1 to N.
  const questions = SUBJECTS.flatMap((s) => shuffle(kept.filter((q) => q.subject === s))).map((q, i) => ({ ...q, number: i + 1 }));
  for (const q of questions) counted[q.subject]++;
  await loadMocks(); // the serial number counts every mock this account already has
  const n = nextNumber();
  const exams = [...new Set(questions.map((q) => q.exam))];
  const mock: Mock = {
    v: 1, id: uuid(), uid, n, title: `Offline Misfire #${n}`, made_at: Date.now(), exam: exams.length === 1 ? exams[0] : "Mixed", source: phone ? "phone" : "website",
    counts: counted, asked: { ...ask.counts }, minutes: minutesFor(counted, PER_QUESTION), questions, status: "ready", answers: {}, visited: [],
  };
  if (!totalOf(counted)) return { mock, short: wanted };
  await addMock(mock);
  return { mock, short: wanted.filter((s) => counted[s] < ask.counts[s]) };
}
