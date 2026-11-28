// Student Choice: the student chooses chapters of the JEE Main chapter-wise questions jeelive.ai already has, and takes
// them their own way. A chapter here IS a chapter-wise test of the website; its id is that test's id.
// Today: each ticked chapter's whole test, one after another. When the website can make a paper of chosen questions
// (bank.pick) or a random mock (bank.random), those ways open by themselves: the bank says which are open.
// The bank (subjects, chapters, a chapter's questions WITHOUT options) is read from our own server (backend/choice.py,
// for signed-in students); a paper is made by jeelive.ai (POST /choice/papers, the student's own request) and is then
// an ordinary paper: started, solved, marked and analysed like every other one.
import { ApiError, BACKEND, api, clearRapidAccess, post, rapidAccess } from "@/src/api/client";
import { cataloguePath } from "@/src/api/examCatalog";

export const SUBJECTS = ["Physics", "Chemistry", "Mathematics"] as const;
export type Subject = typeof SUBJECTS[number];
export const SHORT: Record<Subject, string> = { Physics: "Physics", Chemistry: "Chemistry", Mathematics: "Maths" };
/** The chapter's whole test on the website (the chapter-wise test, under the chapter's own id): `page` = the page of
 *  the subject's chapter-wise list it is on, where the student's own attempt of it is read. */
export type ChapterTest = { page: number; minutes: number | null; correct: number; wrong: number; marks: number };
export type Chapter = { id: string; n: number | null; title: string; count: number; mcq: number; integer: number; test?: ChapterTest | null };
/** `ready: false` = there is no chapter to choose from (nothing else is sent then). `pick` = questions can be chosen
 *  and one paper made of them; `random` = a random mock can be made. Both need the website: false until it can. */
export type Bank = {
  ready: boolean; sample?: boolean; pick?: boolean; random?: boolean; exam?: string; max_questions: number; max_per_subject: number | null;
  minutes: Record<Subject, number>; marks: { correct: number; wrong: number }; subjects: { name: Subject; chapters: Chapter[] }[];
  /** The website makes Misfire Mocks (door C, mode "misfire"): Misfire's "Mock" tab opens (src/misfire/web.ts). */
  misfire?: boolean;
};
/** A question's picture, sized in print points (the picture file holds more pixels). */
export type Stem = { url: string; w: number | null; h: number | null };
/** A question as it is listed: its words or its pictures. Never its options, answer or solution. */
export type Question = { id: string; n: number | null; type: "mcq" | "integer"; text: string; stem: Stem[] };
export type ChapterQuestions = { id: string; title: string; subject: string; total: number; items: Question[] };

async function get<T>(path: string, uid: string, signal: AbortSignal, again = true): Promise<T> {
  const token = await rapidAccess(uid);
  let res: Response;
  try {
    res = await fetch(`${BACKEND}/api/choice${path}`, { signal, headers: { Accept: "application/json", Authorization: `Bearer ${token}` } });
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    throw new ApiError("Connection interrupted. Please try again.", 0);
  }
  if (res.status === 401 && again) {
    const body = await res.json().catch(() => null);
    // The website wants a fresh session: the usual session check renews it. Otherwise our own pass has run out.
    if (body?.code === "website_session") await api("/auth/session").catch(() => null);
    else clearRapidAccess();
    return get<T>(path, uid, signal, false);
  }
  if (!res.ok) throw new ApiError(res.status === 404 ? "Is chapter ke sawaal abhi yahan nahi khul paaye. Doosra chapter chuno, ya thodi der mein dobara dekho." : res.status === 401 ? "Please sign in again." : "Sawaal abhi load nahi ho paaye. Dobara try karo.", res.status);
  return res.json();
}
export const getBank = (uid: string) => (signal: AbortSignal) => get<Bank>("/bank", uid, signal);
export const getChapter = (uid: string, id: string) => (signal: AbortSignal) => get<ChapterQuestions>("/chapters/" + id, uid, signal);

/** The student's own attempt of a chapter's test, as the chapter-wise list gives it (null = not started). */
export type Attempt = { id: string; status?: string; resumable?: boolean; result_available?: boolean };
export type TestPage = { subject: Subject; page: number };
/** The student's attempts of the chapter tests on these pages of the chapter-wise list, by test id. Their own request,
 *  the same one the chapter-wise screen makes. */
export const getAttempts = (pages: TestPage[]) => async (signal: AbortSignal) => {
  const lists = await Promise.all(pages.map(p => api<{ items?: { id?: string; attempt?: Attempt | null }[] }>(cataloguePath("jee-main", "chapters", "", p.subject, "", p.page), { signal })));
  const out: Record<string, Attempt | null> = {};
  for (const list of lists) for (const row of list?.items || []) if (row?.id) out[row.id] = row.attempt || null;
  return out;
};

export type Counts = Record<Subject, number>;
export const NONE: Counts = { Physics: 0, Chemistry: 0, Mathematics: 0 };
export const totalOf = (c: Counts) => c.Physics + c.Chemistry + c.Mathematics;
/** The time a paper gets: every question brings its subject's minutes (Maths 3.2, Physics 2.4, Chemistry 1.6, so
 *  25 + 25 + 25 questions get 180 minutes); the sum is rounded up to a whole minute. */
export const minutesFor = (c: Counts, per: Record<Subject, number>) => Math.ceil(Math.round(SUBJECTS.reduce((sum, s) => sum + c[s] * per[s], 0) * 1e4) / 1e4);
/** Each subject's share of a paper's time in whole minutes that add up to exactly the paper's time (`minutesFor`):
 *  every subject first gets its whole minutes, then the minutes left over go to the subjects with the largest remainders
 *  (rounding each subject up on its own could add up to a minute or two more than the paper's time). */
export function splitMinutes(c: Counts, per: Record<Subject, number>): Counts {
  const exact = Object.fromEntries(SUBJECTS.map(s => [s, Math.round(c[s] * per[s] * 1e4) / 1e4])) as Counts;
  const out = Object.fromEntries(SUBJECTS.map(s => [s, Math.floor(exact[s])])) as Counts;
  let left = minutesFor(c, per) - totalOf(out);
  for (const s of [...SUBJECTS].sort((a, b) => (exact[b] - Math.floor(exact[b])) - (exact[a] - Math.floor(exact[a])))) {
    if (left > 0 && exact[s] > Math.floor(exact[s])) { out[s] += 1; left -= 1; }
  }
  return out;
}

/** A whole chapter test's time by the owner's rule: what its questions bring, three hours at most. The website sets the
 *  real time; this is what the app compares it with (the same rule: chapter_test_minutes in backend/choice.py). */
export const TEST_MAX_MINUTES = 180;
export const testMinutes = (subject: Subject, count: number, per: Record<Subject, number>) => Math.min(TEST_MAX_MINUTES, minutesFor({ ...NONE, [subject]: count }, per));
/** A random mock of `n` questions, split like a JEE Main paper: equally over the subjects the bank has; a question or two
 *  left over go to the first subjects (Physics, then Chemistry). */
export function splitOf(n: number, subjects: readonly Subject[]): Counts {
  const out = { ...NONE };
  subjects.forEach((s, i) => { out[s] = Math.floor(n / subjects.length) + (i < n % subjects.length ? 1 : 0); });
  return out;
}
/** "1 hr 12 min", "45 min" */
export const timeLabel = (minutes: number) => (minutes >= 60 ? `${Math.floor(minutes / 60)} hr${minutes % 60 ? ` ${minutes % 60} min` : ""}` : `${minutes} min`);

export type PaperAsk = { mode: "pick"; question_ids: string[] } | { mode: "random"; count: number }
  // A Misfire Mock (src/misfire/web.ts): how many of each subject from the student's open Misfire, and the chapters where only some were ticked.
  | { mode: "misfire"; counts: Counts; chapters?: Partial<Record<Subject, string[]>> };
/** The website's answer to door C: the paper's id and, for a Misfire Mock, its name and number, how many questions
 *  were asked and given, and its minutes (unchecked here: the caller reads what it needs). */
export type MadePaper = { set_id: string; title?: unknown; number?: unknown; asked?: unknown; given?: unknown; minutes?: unknown };
/** Asks jeelive.ai to make the paper; `key` = the same for every retry of this one request, so it is never made twice. */
export async function askPaper(ask: PaperAsk, key: string): Promise<MadePaper> {
  let made: { set_id?: unknown } | null;
  try {
    made = await post<{ set_id?: unknown }>("/choice/papers", { exam: "jee-main", request_key: key, ...ask });
  } catch (e: any) {
    // The website does not make these papers yet.
    if (e instanceof ApiError && (e.status === 404 || e.status === 405)) throw new ApiError("Paper banana abhi jeelive.ai se jud raha hai. Thodi der mein yeh khul jayega; aapke chune sawaal yahin rahenge.", e.status);
    throw e;
  }
  if (typeof made?.set_id !== "string" || !/^[A-Za-z0-9_-]{6,80}$/.test(made.set_id)) throw new ApiError("Paper ban nahi paaya. Dobara try karo.", 502);
  return made as MadePaper;
}
/** The paper's id: its page (/set/<id>) starts it like any other paper. */
export const makePaper = async (ask: PaperAsk, key: string): Promise<string> => (await askPaper(ask, key)).set_id;
