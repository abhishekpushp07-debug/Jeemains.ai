// Matched: the JEE Main questions that matched ours, shift by shift. Read from our own server (backend/matched.py), which
// is open to everyone: no sign-in, no account in the request.
import { ApiError, BACKEND } from "@/src/api/client";

export type Picture = { url: string; w: number | null; h: number | null };
/** One question as it was supplied: words (maths in $…$), options, pictures; and its solution when given: the place of the
 *  right option (from 0), the answer in words, the worked solution and its pictures. */
export type Side = { text: string; options: string[]; images: Picture[]; correct: number | null; answer: string; solution: string; solution_images: Picture[]; source?: string; tag?: string };
export type MatchedItem = { n: number | null; subject: string; chapter: string; jee: Side; ours: Side[] };
export type ShiftSummary = { id: string; day: string; shift: number; asked: number | null; matched: number; subjects: { name: string; n: number }[]; updated_at?: number };
export type MatchedIndex = { total: number; updated_at: number; shifts: ShiftSummary[] };
export type MatchedShift = ShiftSummary & { items: MatchedItem[] };

async function get<T>(path: string, signal: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BACKEND}/api/matched${path}`, { signal, headers: { Accept: "application/json" } });
  } catch (e: any) {
    if (e?.name === "AbortError") throw e;
    throw new ApiError("Connection interrupted. Please try again.", 0);
  }
  if (!res.ok) throw new ApiError(res.status === 404 ? "Yeh shift ab yahan nahi hai." : "Matched abhi load nahi ho paaya. Dobara try karo.", res.status);
  return res.json();
}
export const getIndex = (signal: AbortSignal) => get<MatchedIndex>("", signal);
export const getShift = (id: string) => (signal: AbortSignal) => get<MatchedShift>("/" + id, signal);

const at = (day: string) => new Date(day + "T12:00:00+05:30");
/** "Jan 2027" */
export const monthLabel = (day: string) => at(day).toLocaleDateString("en-IN", { month: "short", year: "numeric", timeZone: "Asia/Kolkata" });
/** "Mon, 25 Jan" */
export const dayLabel = (day: string) => at(day).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", timeZone: "Asia/Kolkata" });
/** "25 Jan" */
export const shortDay = (day: string) => at(day).toLocaleDateString("en-IN", { day: "numeric", month: "short", timeZone: "Asia/Kolkata" });
/** "18 of 75 matched", or "18 matched" when the paper's size was not given. */
export const countLine = (s: { matched: number; asked: number | null }) => (s.asked ? `${s.matched} of ${s.asked} matched` : `${s.matched} matched`);
export const SHORT: Record<string, string> = { Mathematics: "Maths" };
/** The year of the JEE Main the shift belongs to: "2027". */
export const yearOf = (day: string) => day.slice(0, 4);

export type MonthGroup = { key: string; label: string; matched: number; days: { day: string; shifts: ShiftSummary[] }[] };
/** Month, then day, then shift: the newest month and day first, a day's shifts in their own order (1, then 2). */
export function byMonth(shifts: ShiftSummary[]): MonthGroup[] {
  const months: MonthGroup[] = [];
  for (const s of [...shifts].sort((a, b) => (a.day === b.day ? a.shift - b.shift : a.day < b.day ? 1 : -1))) {
    const key = s.day.slice(0, 7);
    let month = months.find(m => m.key === key);
    if (!month) months.push(month = { key, label: monthLabel(s.day), matched: 0, days: [] });
    let day = month.days.find(d => d.day === s.day);
    if (!day) month.days.push(day = { day: s.day, shifts: [] });
    day.shifts.push(s);
    month.matched += s.matched;
  }
  return months;
}
