import { api, post, uuid } from "./client";
import { storage } from "@/src/utils/storage";
import { invalidate } from "@/src/useCached";
import { checkReadiness } from "./readiness";

export type PyqAttempt = { id: string; status: string; resumable?: boolean; result_available?: boolean };
export type PyqPaper = {
  id: string; year: number; exam_date: string; shift: string | number;
  count: number; minutes: number; maximum: number; title?: string;
  attempt: PyqAttempt | null; latest_result_id: string | null; attempt_count: number;
  live_enabled?: boolean;
};
export type PyqCatalogue = { items: PyqPaper[]; years: number[]; total: number; source_note?: string; server_now?: number };
export type PaperState = "new" | "active" | "completed" | "grading" | "expired" | "unavailable";

export async function getPyqCatalogue(signal?: AbortSignal): Promise<PyqCatalogue> {
  const data = await api<PyqCatalogue>("/pyq/jee-main", { signal });
  if (!data || !Array.isArray(data.items) || !Array.isArray(data.years) || !Number.isInteger(data.total) || data.total < 0 ||
    data.years.some((y) => !Number.isInteger(y)) || data.items.some((p) => !p.id || !Number.isInteger(p.year) ||
      !/^\d{4}-\d{2}-\d{2}$/.test(p.exam_date) || p.shift == null || !Number.isFinite(p.count) || !Number.isFinite(p.minutes) || !Number.isFinite(p.maximum))) {
    throw new Error("The paper list could not be read. Please refresh to get the latest published papers.");
  }
  return data;
}

export function paperState(p: PyqPaper): PaperState {
  // live_enabled gates scheduled import/chapter events upstream, NOT ordinary PYQs.
  // A paper returned by the student catalogue is available subject to server checks.
  if (p.count <= 0) return "unavailable";
  if (!p.attempt) return p.latest_result_id ? "completed" : "new";
  if (!p.attempt.id) return "unavailable";
  if (p.attempt.status === "active" || p.attempt.resumable) return "active";
  if (p.attempt.status === "completed") return "completed";
  if (p.attempt.status === "grading" || p.attempt.status === "embargoed") return "grading";
  if (p.attempt.status === "expired") return "expired";
  return "unavailable";
}

export function resultId(p: PyqPaper): string | null {
  return p.latest_result_id || ((["completed", "expired"].includes(p.attempt?.status || "") || p.attempt?.result_available === true) ? p.attempt!.id : null);
}

export function paperDate(date: string): string {
  const d = new Date(date + "T12:00:00Z");
  return Number.isNaN(d.getTime()) ? date : d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

export function sortPapers(items: PyqPaper[]) {
  return [...items].sort((a, b) => b.year - a.year || a.exam_date.localeCompare(b.exam_date) || String(a.shift).localeCompare(String(b.shift), undefined, { numeric: true }));
}

type StartIntent = { key: string; priorResult: string | null };
type OpenedAttempt = { id: string; status: string };
const pending = new Map<string, Promise<OpenedAttempt>>();

export async function resumePyq(paper: PyqPaper): Promise<OpenedAttempt> {
  if (!paper.attempt?.id) throw new Error("The saved attempt could not be found. Refresh the list.");
  const attempt = await api<OpenedAttempt>(`/attempts/${encodeURIComponent(paper.attempt.id)}`);
  if (!attempt?.id || !attempt.status) throw new Error("Could not confirm the saved attempt. Please retry.");
  return attempt; // Expired/sealed attempts go to their result; never POST a new start.
}

async function begin(uid: string, paper: PyqPaper, checkedAt = 0): Promise<OpenedAttempt> {
  const storageKey = `pyq.start.${uid}.${paper.id}`;
  // Recheck authoritative status before a cached card can start a duplicate attempt.
  const detail = await api<{ attempt?: PyqAttempt }>(`/my/sets/${encodeURIComponent(paper.id)}`);
  // GET details + preflight/start enforce the backend's actual permission contract.
  // Do not infer availability from unrelated live-event metadata.
  if (detail.attempt?.id && (detail.attempt.status === "active" || detail.attempt.resumable)) {
    await storage.removeItem(storageKey);
    return detail.attempt;
  }
  const rawIntent = await storage.getItem<string | null>(storageKey, null);
  let previous: StartIntent | null = null;
  try { previous = rawIntent ? JSON.parse(rawIntent) : null; } catch { /* Server status above still prevents resuming as a new attempt. */ }
  const priorResult = paper.latest_result_id || (paper.attempt?.status === "completed" ? paper.attempt.id : null);
  const intent = previous?.key && previous.priorResult === priorResult ? previous : { key: uuid(), priorResult };
  if (!await storage.setItem(storageKey, JSON.stringify(intent))) throw new Error("Phone storage is unavailable. Free some space and retry so your start can be recovered safely.");
  if (!checkedAt || Date.now() - checkedAt > 60000) await checkReadiness(paper.id);
  const attempt = await post<OpenedAttempt>(`/sets/${encodeURIComponent(paper.id)}/start`, {
    start_key: intent.key, device_checked: true, preview: false,
  });
  if (!attempt?.id || !attempt.status) throw new Error("The start could not be confirmed. Retry safely; your start request is saved.");
  await storage.removeItem(storageKey);
  invalidate(`u.${uid}.`);
  return attempt;
}

export function openPyq(uid: string, paper: PyqPaper, checkedAt = 0): Promise<OpenedAttempt> {
  const key = `${uid}.${paper.id}`;
  const existing = pending.get(key);
  if (existing) return existing;
  const operation = begin(uid, paper, checkedAt).finally(() => pending.delete(key));
  pending.set(key, operation);
  return operation;
}