import { api } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { istDate } from "@/src/navigation";
import type { SeriesTone } from "@/src/theme";

export type Slot = { day: number; date: string; state: string; ready: boolean; set_id: string | null; title: string; can_start: boolean; opens_at: number; last_start_at: number; closes_at: number };
export type Series = { id: string; title: string; first_date: string; last_date: string; total: number; today: string; server_now: number; slots: Slot[]; today_slot?: Slot | null };
export type StreakDay = { day: number; date: string; state: "completed" | "pending" | "in_progress" | "missed" | "today" | "upcoming"; attempt_id?: string | null };
export type Milestone = { days: number; title: string; subtitle?: string; earned: boolean };
export type Streak = { stage: "prelaunch" | "live" | "finished"; first_date?: string; completed_count: number; current_streak: number; best_streak: number; total_days: number; today_state?: string; days?: StreakDay[]; milestones?: Milestone[] };
export type SeriesAttempt = { id: string; title: string; mode: string; series_date?: string; status: string; resumable?: boolean; remaining_seconds?: number; summary?: { score: number; maximum: number } | null };
export type SeriesHistory = { items: SeriesAttempt[]; total: number };

export type DayInfo = {
  day: number; date: string; slot: Slot; tone: SeriesTone; label: string; isToday: boolean;
  live?: SeriesAttempt; practice?: SeriesAttempt;
};

// Up to 100 attempts: enough for every live day plus archive practice in one view.
async function fetchHistory(signal: AbortSignal): Promise<SeriesHistory> {
  const first = await api<SeriesHistory>("/series/all-india-jee/history?page=1", { signal });
  const items = [...(first.items || [])];
  for (let page = 2; items.length < (first.total || 0) && page <= 5; page++) {
    const next = await api<SeriesHistory>(`/series/all-india-jee/history?page=${page}`, { signal });
    if (!next.items?.length) break;
    items.push(...next.items);
  }
  return { ...first, items };
}

const fetchSeries = (signal: AbortSignal) => api<Series>("/series/all-india-jee", { signal });

/** How many days the series runs, exactly as the website sets it (0 while it loads). Never a number baked into the app. */
export const seriesDays = (s?: Series | null) => s?.total || s?.slots?.length || 0;
/** The same count for screens that don't load the whole series (shares the cached schedule). */
export const useSeriesDays = () => seriesDays(useCached<Series>("series", fetchSeries).data);

export function useSeriesData(uid?: string, historyAlways = true) {
  const series = useCached<Series>("series", fetchSeries);
  const streak = useCached<Streak>(uid ? `u.${uid}.streak` : null, (signal) => api("/series/all-india-jee/streak", { signal }));
  const started = !!series.data && series.data.today >= series.data.first_date;
  const history = useCached<SeriesHistory>(uid && (historyAlways || started) ? `u.${uid}.serieshist` : null, fetchHistory);
  const days = series.data ? buildDays(series.data, streak.data, history.data) : [];
  const reload = () => { series.reload(); streak.reload(); history.reload(); };
  return { series, streak, history, days, reload };
}

export function buildDays(s: Series, streak?: Streak | null, history?: SeriesHistory | null): DayInfo[] {
  const byDate = new Map((streak?.days || []).map(d => [d.date, d]));
  const items = history?.items || [];
  return s.slots.map(slot => {
    const live = items.find(a => a.mode === "series_live" && a.series_date === slot.date);
    const practice = items.find(a => a.mode === "series_practice" && a.series_date === slot.date);
    const isToday = slot.date === s.today;
    const state = byDate.get(slot.date)?.state;
    let tone: SeriesTone, label: string;
    if (state === "completed" || state === "pending" || (!state && live && !live.resumable)) { tone = "done"; label = "Completed"; }
    else if (state === "in_progress" || (isToday && live?.resumable)) { tone = "today"; label = "In progress"; }
    else if (isToday) { tone = "today"; label = !slot.ready ? "Awaiting paper" : slot.state === "start_closed" ? "Starts closed" : slot.state === "ended" ? "Day ended" : "Live today"; }
    else if (state === "missed" || slot.date < s.today) { tone = "missed"; label = slot.can_start ? "Missed · practise" : "Missed"; }
    else { tone = "upcoming"; label = "Upcoming"; }
    return { day: slot.day, date: slot.date, slot, tone, label, isToday, live, practice };
  });
}

/** Released live results only, in day order, for the score trend. */
export function scorePoints(days: DayInfo[]) {
  return days.filter(d => d.live?.summary && !d.live.resumable).map(d => ({ day: d.day, score: d.live!.summary!.score, maximum: d.live!.summary!.maximum, id: d.live!.id }));
}

export const skippedCount = (days: DayInfo[]) => days.filter(d => d.tone === "missed").length;

export type SeriesAction = { label: string; to: string; testID: string; icon?: "arrow-right" | "play" | "chart-box-outline" | "calendar-clock" | "archive-outline" | "lock-clock" };

/** One state-driven primary action for a series day (live day uses the live attempt). */
export function dayAction(d: DayInfo): SeriesAction | null {
  const { slot, live, practice } = d;
  if (live) {
    if (live.resumable) return { label: d.isToday ? "Resume live attempt" : "Resume", to: `/attempt/${live.id}`, testID: `series-resume-${d.day}`, icon: "play" };
    if (live.summary) return { label: d.isToday ? "Open live result" : "View result", to: `/result/${live.id}`, testID: `series-resume-${d.day}`, icon: "chart-box-outline" };
    if (live.status === "embargoed") return null;
    return { label: "Open live result", to: `/result/${live.id}`, testID: `series-resume-${d.day}`, icon: "chart-box-outline" };
  }
  if (practice?.resumable) return { label: "Resume practice", to: `/attempt/${practice.id}`, testID: `series-practice-resume-${d.day}`, icon: "play" };
  if (slot.can_start && slot.set_id) return { label: slot.state === "archive" ? "Practise this paper" : "Check device & start", to: `/set/${slot.set_id}`, testID: `series-start-${d.day}`, icon: "arrow-right" };
  return null;
}

/** Human note for days without an action. */
export function dayNote(d: DayInfo) {
  const { slot, live } = d;
  if (live && !live.resumable && !live.summary) return live.status === "embargoed" ? "Results at 11:59 PM IST" : "Preparing your result";
  if (!slot.ready && slot.state === "upcoming") return `Opens ${istDate(slot.date)} · 12:01 AM IST`;
  if (!slot.ready) return "Paper not available yet. Only published papers can be started.";
  if (slot.state === "upcoming") return `Opens ${istDate(slot.date)} · 12:01 AM IST`;
  if (slot.state === "start_closed") return "New starts closed at 8:59 PM. Existing attempts keep their timer.";
  if (slot.state === "ended") return "Results released. Archive opens at midnight.";
  return "75 questions · 180 minutes · +4 / −1";
}

export function countdown(toUnix: number, nowMs = Date.now()) {
  const s = Math.max(0, Math.floor(toUnix - nowMs / 1000));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h ? `${h}h ${m}m` : `${m}m`;
}
