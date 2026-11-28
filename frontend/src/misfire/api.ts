// Misfire: every wrong or skipped question of every finished paper, to be solved again. The same website answers as
// jeelive.ai's Misfire page (/my/misfire…), plus the list of finished papers of each test family for the paper-wise tabs.
import { api, post, registerAssetManifest } from "@/src/api/client";
import { noteStatus } from "./known";

export type MisfireStatus = "open" | "fixed";
export type MisfireItem = {
  id: string; attempt_id: string; question_id: string; title: string; exam?: string; subject: string; chapter?: string | null; number: number;
  outcome: "incorrect" | "skipped"; lost?: number | null; your_answer?: string | null; type: string; question: any; solution_count?: number;
  status: MisfireStatus; tries: number; last_correct?: boolean | null; at?: number; answer?: string; solution_text?: string;
};
export type MisfireSummary = { open: number; fixed: number; waiting: number; subjects: { name: string; open: number; fixed: number }[] };
export type MisfirePage = { items: MisfireItem[]; total: number; page: number; pages: number; waiting: number; chapters: { name: string; count: number }[] };
export type ChapterRow = { subject: string; chapter: string; papers: number; total: number; correct: number; wrong: number; skipped: number; lost: number; sahi: number; accuracy: number | null; trend: "up" | "down" | "same" | null };
export type ChapterReport = { papers: number; waiting: number; chapters: ChapterRow[]; subjects: ChapterRow[]; untagged: number };

/** Everything Misfire keeps for one account starts with this, so one call forgets it all. */
export const misfireKey = (uid: string) => `u.${uid}.misfire`;
export const getSummary = (signal?: AbortSignal) => api<MisfireSummary>("/my/misfire/summary", { signal });
// Every page the website answers also tells the phone which questions are understood (./known.ts, for Offline Misfire).
export const getPage = (status: MisfireStatus, subject: string, chapter: string, page: number, signal?: AbortSignal) =>
  api<MisfirePage>("/my/misfire?" + new URLSearchParams({ status, subject, chapter, page: String(page) }).toString(), { signal })
    .then((d) => { noteStatus(d?.items || []); return d; });
export const getChapters = (signal?: AbortSignal) => api<ChapterReport>("/my/chapters", { signal });
const act = (id: string, what: string) => `/my/misfire/${encodeURIComponent(id)}/${what}`;
export const tryAgain = (id: string, value: string) => post<{ correct: boolean; item: MisfireItem }>(act(id, "try"), { value });
export const markDone = (id: string) => post(act(id, "done"));
export const reopen = (id: string) => post(act(id, "reopen"));

/** The questions already marked "Samajh gaya" (newest 100), so a paper's own list can show them as done. */
export async function getFixedIds(signal?: AbortSignal) {
  const ids: string[] = [];
  for (let page = 1; page <= 5; page++) {
    const d = await getPage("fixed", "", "", page, signal);
    ids.push(...(d.items || []).map(i => i.id));
    if (page >= (d.pages || 1)) break;
  }
  return ids;
}

/** A wrong or skipped question of an opened result, in the shape of a Misfire item (its Misfire id is attempt:question). */
export function fromResult(r: any, q: any, fixed: boolean): MisfireItem {
  const rule = q.scoring || r.rules || {};
  return {
    id: `${r.id}:${q.id}`, attempt_id: r.id, question_id: q.id, title: r.title, exam: r.exam, subject: q.subject || q.section || "", chapter: q.topic || "",
    number: q.number, outcome: q.outcome, lost: Number(rule.correct ?? 0) - Number(q.marks ?? 0), your_answer: q.response || "", type: q.type, question: q,
    solution_count: Number(q.solution_asset_count) || 0, status: fixed ? "fixed" : "open", tries: 0, at: r.submitted_at,
  };
}

/** The row the picture loader needs for one Misfire question. */
export const pictureRow = (it: MisfireItem) => ({ ...(it.question || {}), id: it.question_id, solution_asset_count: it.solution_count ?? it.question?.solution_asset_count ?? 0 });
/** Lets these questions' pictures (and solutions) load. Questions of one paper are named together: naming a paper again
 *  with fewer questions lets go of the others. */
export function grantPictures(items: MisfireItem[]) {
  const by = new Map<string, any[]>();
  for (const it of items) by.set(it.attempt_id, [...(by.get(it.attempt_id) || []), pictureRow(it)]);
  for (const [attempt, rows] of by) registerAssetManifest(attempt, rows, true);
}

// ---- Paper-wise tabs: the finished papers of one test family, newest first.
export type Paper = { id: string; title: string; exam?: string; mode?: string; series_date?: string; started_at?: number; submitted_at?: number; summary?: any | null };
export type PaperPage = { items: Paper[]; pages: number };
export type Family = { key: string; label: string; exam: string; empty: string; load: (page: number, signal?: AbortSignal) => Promise<PaperPage> };

// A revision retry repeats questions of its own paper; its paper is already listed. An All India day has its own tab.
const own = (a: Paper) => a.mode !== "retry" && a.mode !== "preview" && !a.mode?.startsWith("series_");
const history = (slug: string, kind: string) => async (page: number, signal?: AbortSignal): Promise<PaperPage> => {
  const d = await api<any>(`/exam-navigation/${slug}/history?kind=${kind}&page=${page}`, { signal });
  return { items: (d.items || []).filter(own), pages: d.pages || 1 };
};
const series = async (page: number, signal?: AbortSignal): Promise<PaperPage> => {
  const d = await api<any>(`/series/all-india-jee/history?page=${page}`, { signal });
  return { items: d.items || [], pages: Math.max(1, Math.ceil((d.total || 0) / 20)) };
};
export const FAMILIES: Family[] = [
  { key: "aits", label: "AITS", exam: "jee-main", load: series, empty: "All India Series ka koi din do. Uske galat aur chhode sawaal yahan paper-wise aa jayenge." },
  { key: "jee-chapter", label: "JEE Chapter-wise", exam: "jee-main", load: history("jee-main", "chapter"), empty: "JEE ka koi chapter-wise test do. Uski galtiyan yahan aayengi." },
  { key: "jee-pyq", label: "JEE PYQ", exam: "jee-main", load: history("jee-main", "pyq"), empty: "JEE Main ka koi PYQ paper do. Uski galtiyan yahan aayengi." },
  { key: "bitsat-mock", label: "BITSAT Mocks", exam: "bitsat", load: history("bitsat", "mock"), empty: "BITSAT ka koi mock do. Uski galtiyan yahan aayengi." },
  { key: "bitsat-chapter", label: "BITSAT Chapter-wise", exam: "bitsat", load: history("bitsat", "chapter"), empty: "BITSAT ka koi chapter-wise test do. Uski galtiyan yahan aayengi." },
  { key: "comedk-mock", label: "COMEDK Mocks", exam: "comedk", load: history("comedk", "mock"), empty: "COMEDK ka koi mock do. Uski galtiyan yahan aayengi." },
];
