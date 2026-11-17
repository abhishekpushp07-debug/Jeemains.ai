// Rank tab data: everything comes from our server (/api/rank), nothing is bundled in the app.
import { BACKEND } from "@/src/api/client";

export type Level = "tough" | "normal" | "easy";
export type Category = "GEN" | "EWS" | "OBC-NCL" | "SC" | "ST";
export type Segment = "all" | "NIT" | "IIIT" | "GFTI" | "DELHI";
export type Tag = "safe" | "likely" | "borderline";

export type FormBody = {
  marks?: number; percentile?: number; level: Level; category: Category;
  female: boolean; pwd: boolean; state: string | null; branches: string[];
};
export type Range = [number, number];
export type RankResult = {
  percentile: Range; crl: Range; from_marks: boolean; summary: string; spread?: string; paper?: string; check?: string;
  cat_rank?: { label: string; range: Range }; pwd_rank?: { label: string; range: Range }; delhi_note?: string;
};
export type Seat = {
  prog: number; inst: number; college: string; type: Exclude<Segment, "all">; branch: string; degree: string;
  close: number; round: string; rank_type: string; path: string; quota: string; gender: "N" | "F"; seat: "open" | "cat";
  tag?: Tag; gap?: string; y25?: number | null; y26?: number | null;
};
export type PredictOut = {
  result: RankResult; counts: Record<Segment, number>; reach?: Record<Segment, number>; segment: Segment; page: number; pages: number; total: number;
  items: Seat[]; near: Seat[]; note: string;
};
export type ChartLine = { pct: number; rank: number; marks: number };
export type Meta = {
  states: string[]; branches: string[]; categories: Category[]; chart: ChartLine[]; note: string; missing: string[];
  sources: { label: string; url: string }[]; y25_label: string; candidates: number;
  comedk: { groups: string[]; candidates: number; max_marks: number; rounds: string[]; notes: string[]; sources: { label: string; url: string }[] };
};
/** One round of one seat: closing (and JEE opening) rank, whether the student is inside it, the student's best (mine) and
 *  worst (hi) estimate compared, and for JAC Upgrade / Spot whether JAC never published the rank. */
export type Cell = { open?: number | null; close: number | null; in: boolean; mine?: number | null; hi?: number | null; unpublished?: boolean };
export type CollegeOut = {
  college: { id: number; name: string; short: string; type: Exclude<Segment, "all">; city: string; state: string };
  your_rank: { label: string; range: Range }; rounds: string[]; total: number; line: string | null; blocked: string | null; y25_label: string | null;
  rows: { prog: number; branch: string; degree: string; cells: Cell[]; first_in: string | null; y25: number | null }[];
  path: { quota: string; gender: "N" | "F"; seat: "open" | "cat" };
  options: { quota: { key: string; label: string }[]; gender: ("N" | "F")[]; seat: ("open" | "cat")[]; cat_label: string | null };
  official: string; official_csab: string | null;
};
export type CollegeReq = FormBody & { inst: number; prog?: number; quota?: string; gender?: "N" | "F"; seat?: "open" | "cat"; all?: boolean };

async function call<T>(path: string, body?: unknown): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  try {
    const res = await fetch(`${BACKEND}/api/rank${path}`, {
      method: body === undefined ? "GET" : "POST", signal: ctrl.signal,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const d = data?.detail;
      throw new Error(typeof d === "string" ? d : "Rank abhi load nahi hua. Retry dabao.");
    }
    return data as T;
  } catch (e: any) {
    if (e?.name === "AbortError") throw new Error("Network kamzor hai. Retry dabao.");
    throw e instanceof Error && e.message ? e : new Error("Network kamzor hai. Retry dabao.");
  } finally {
    clearTimeout(timer);
  }
}

export const getMeta = () => call<Meta>("/meta");
export const predict = (body: FormBody & { segment: Segment; page: number; page_size?: 20 | 25 }) => call<PredictOut>("/predict", body);
export const getCollege = (body: CollegeReq) => call<CollegeOut>("/college", body);

export type Campus = "all" | "Pilani" | "Goa" | "Hyderabad";
export type Degree = "all" | "BE" | "MSc" | "BPharm";
export type BitsatItem = {
  id: string; campus: Exclude<Campus, "all">; college: string; program: string; degree: Exclude<Degree, "all">;
  history: (number | null)[]; cutoff: number; last: number | null; tag: Tag | null; gap: number;
};
type Pick = { college: string; program: string; cutoff: number };
export type BitsatOut = {
  result: { score: number; max: number; cleared: number; total: number; cleared_all: number; total_all: number; best: Pick | null; target: (Pick & { gap: number }) | null };
  items: BitsatItem[]; near: BitsatItem[]; rest: BitsatItem[]; years: number[]; notes: string[]; source: string;
};
export const bitsat = (body: { score: number; campus: Campus; degree: Degree }) => call<BitsatOut>("/bitsat", body);

export type ComedkArea = "all" | "blr" | "other";
export type ComedkQuery = { marks?: number; rank?: number };
export type ComedkItem = {
  id: string; code: string; college: string; city: string; blr: boolean; course: string; cc: string; group: string;
  close: number; round: string; rounds: (number | null)[]; y25: number | null; seats: number | null; fee: number | null; tag?: Tag; gap?: string;
};
export type ComedkOut = {
  result: { rank: Range; mid: number; from_marks: boolean; candidates: number; in_reach: number; total: number; summary: string; spread?: string; check?: string };
  counts: Record<ComedkArea, number>; reach: Record<ComedkArea, number>; area: ComedkArea; page: number; pages: number; total: number;
  items: ComedkItem[]; near: ComedkItem[]; rounds: string[]; notes: string[];
};
export type ComedkCollegeReq = ComedkQuery & { branches?: string[]; code: string; course?: string; all?: boolean };
export type ComedkCollegeOut = {
  college: { code: string; name: string; short: string; city: string; blr: boolean }; your_rank: { label: string; range: Range };
  rounds: string[]; total: number; line: string; y25_label: string; official: string;
  rows: { cc: string; course: string; group: string; cells: Cell[]; close: number; round: string; first_in: string | null;
    y25: number | null; seats: number | null; fee: number | null; tag: Tag | null }[];
};
export const comedk = (body: ComedkQuery & { branches: string[]; area: ComedkArea; page: number }) => call<ComedkOut>("/comedk", body);
export const getComedkCollege = (body: ComedkCollegeReq) => call<ComedkCollegeOut>("/comedk/college", body);

/** Indian grouping: 107693 -> 1,07,693. */
export function fmt(n: number): string {
  const s = String(Math.round(n));
  if (s.length <= 3) return s;
  const head = s.slice(0, -3), tail = s.slice(-3);
  return head.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + tail;
}
export const fmtRange = (r: Range) => r[0] === r[1] ? fmt(r[0]) : `${fmt(r[0])} – ${fmt(r[1])}`;
