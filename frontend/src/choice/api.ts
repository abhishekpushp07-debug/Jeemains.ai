// Student Choice: a paper the student makes of the chapters and questions they choose, or a random mock.
// The question bank (subjects, chapters, a chapter's questions WITHOUT options) is read from our own server
// (backend/choice.py, for signed-in students); the paper itself is made by jeelive.ai (POST /choice/papers, the student's
// own request) and is then an ordinary paper: started, solved, marked and analysed like every other one.
import { ApiError, BACKEND, api, clearRapidAccess, post, rapidAccess } from "@/src/api/client";

export const SUBJECTS = ["Physics", "Chemistry", "Mathematics"] as const;
export type Subject = typeof SUBJECTS[number];
export const SHORT: Record<Subject, string> = { Physics: "Physics", Chemistry: "Chemistry", Mathematics: "Maths" };
export type Chapter = { id: string; n: number | null; title: string; count: number; mcq: number; integer: number };
/** `ready: false` = the bank is not connected yet (nothing else is sent then). */
export type Bank = {
  ready: boolean; sample?: boolean; exam?: string; max_questions: number; max_per_subject: number | null;
  minutes: Record<Subject, number>; marks: { correct: number; wrong: number }; subjects: { name: Subject; chapters: Chapter[] }[];
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
  if (!res.ok) throw new ApiError(res.status === 404 ? "Is chapter mein chunne ke liye sawaal nahi hain." : res.status === 401 ? "Please sign in again." : "Sawaal abhi load nahi ho paaye. Dobara try karo.", res.status);
  return res.json();
}
export const getBank = (uid: string) => (signal: AbortSignal) => get<Bank>("/bank", uid, signal);
export const getChapter = (uid: string, id: string) => (signal: AbortSignal) => get<ChapterQuestions>("/chapters/" + id, uid, signal);

export type Counts = Record<Subject, number>;
export const NONE: Counts = { Physics: 0, Chemistry: 0, Mathematics: 0 };
export const totalOf = (c: Counts) => c.Physics + c.Chemistry + c.Mathematics;
/** The time a paper gets: every question brings its subject's minutes (Maths 3.2, Physics 2.4, Chemistry 1.6, so
 *  25 + 25 + 25 questions get 180 minutes); the sum is rounded up to a whole minute. */
export const minutesFor = (c: Counts, per: Record<Subject, number>) => Math.ceil(Math.round(SUBJECTS.reduce((sum, s) => sum + c[s] * per[s], 0) * 1e4) / 1e4);
/** A random mock of `n` questions, split like a JEE Main paper: equally over the subjects the bank has; a question or two
 *  left over go to the first subjects (Physics, then Chemistry). */
export function splitOf(n: number, subjects: readonly Subject[]): Counts {
  const out = { ...NONE };
  subjects.forEach((s, i) => { out[s] = Math.floor(n / subjects.length) + (i < n % subjects.length ? 1 : 0); });
  return out;
}
/** "1 hr 12 min", "45 min" */
export const timeLabel = (minutes: number) => (minutes >= 60 ? `${Math.floor(minutes / 60)} hr${minutes % 60 ? ` ${minutes % 60} min` : ""}` : `${minutes} min`);

export type PaperAsk = { mode: "pick"; question_ids: string[] } | { mode: "random"; count: number };
/** Asks jeelive.ai to make the paper; `key` = the same for every retry of this one request, so it is never made twice.
 *  Gives the paper's id: its page (/set/<id>) starts it like any other paper. */
export async function makePaper(ask: PaperAsk, key: string): Promise<string> {
  let made: { set_id?: unknown } | null;
  try {
    made = await post<{ set_id?: unknown }>("/choice/papers", { exam: "jee-main", request_key: key, ...ask });
  } catch (e: any) {
    // The website does not make these papers yet.
    if (e instanceof ApiError && (e.status === 404 || e.status === 405)) throw new ApiError("Paper banana abhi jeelive.ai se jud raha hai. Thodi der mein yeh khul jayega; aapke chune sawaal yahin rahenge.", e.status);
    throw e;
  }
  if (typeof made?.set_id !== "string" || !/^[A-Za-z0-9_-]{6,80}$/.test(made.set_id)) throw new ApiError("Paper ban nahi paaya. Dobara try karo.", 502);
  return made.set_id;
}
