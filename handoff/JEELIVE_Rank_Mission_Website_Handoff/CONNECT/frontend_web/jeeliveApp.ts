// JEELIVE.AI website client for the app server's Rank, Mission and Dream college APIs.
// No dependencies: plain fetch + TypeScript types. Works in React, Next.js, Vite, or a plain <script type="module">.
//
//   import { createJeeliveApp } from "./jeeliveApp";
//   const app = createJeeliveApp();                       // talks to the website's own backend:  /api/rank/..., /api/mission/me
//   const meta = await app.rank.meta();
//   const out  = await app.rank.predict({ marks: 180, level: "normal", category: "GEN", female: false, pwd: false,
//                                         state: "Bihar", branches: [], segment: "all", page: 1 });
//   const me   = await app.mission.me();                  // signed-in student: { code, helped, week, link }
//
// Two ways to point it:
//   1. createJeeliveApp()                                  -> "/api" on the website (backend_fastapi/jeelive_app_connect.py mounted). Recommended.
//   2. createJeeliveApp({ baseUrl: "https://jeelive-mobile.emergent.host/api" })
//        -> the app server directly. Rank only, and only from a page served on an origin the app server allows
//           (today exactly https://jeelive.ai). Mission and Dream college need way 1.
//
// Every type below mirrors the app server's JSON one to one (see docs/03_RANK_API_REFERENCE.md).

// ------------------------------------------------------------------ types: shared
export type Level = "tough" | "normal" | "easy";
export type Category = "GEN" | "EWS" | "OBC-NCL" | "SC" | "ST";
export type Segment = "all" | "NIT" | "IIIT" | "GFTI" | "DELHI";
export type Tag = "safe" | "likely" | "borderline";
export type Exam = "jee" | "bitsat" | "comedk";
export type Range = [number, number];
export type Source = { label: string; url: string };

// ------------------------------------------------------------------ types: JEE Main
/** Send at least one of marks, percentile, rank (the scorecard's All India Rank). With several, the most exact wins:
 *  rank, then percentile, then marks. */
export type FormBody = {
  marks?: number; percentile?: number; rank?: number; level: Level; category: Category;
  female: boolean; pwd: boolean; state: string | null; branches: string[];
};
export type ScoreKind = "marks" | "percentile" | "rank";
export type RankResult = {
  percentile: Range; crl: Range; from_marks: boolean; source?: ScoreKind; summary: string; spread?: string; paper?: string; check?: string;
  cat_rank?: { label: string; range: Range }; pwd_rank?: { label: string; range: Range }; delhi_note?: string;
};
export type Seat = {
  prog: number; inst: number; college: string; type: Exclude<Segment, "all">; branch: string; degree: string;
  close: number; round: string; rank_type: string; path: string; quota: string; gender: "N" | "F"; seat: "open" | "cat";
  tag?: Tag; gap?: string; y25?: number | null; y26?: number | null;
};
export type PredictIn = FormBody & { segment: Segment; page: number; page_size?: 20 | 25 };
export type PredictOut = {
  result: RankResult; counts: Record<Segment, number>; reach: Record<Segment, number>; segment: Segment;
  page: number; pages: number; total: number; items: Seat[]; near: Seat[]; note: string;
};
export type ChartLine = { pct: number; rank: number; marks: number };
export type Meta = {
  states: string[]; branches: string[]; categories: Category[]; chart: ChartLine[]; note: string; missing: string[];
  sources: Source[]; y25_label: string; candidates: number;
  comedk: { groups: string[]; candidates: number; max_marks: number; rounds: string[]; notes: string[]; sources: Source[] };
};
/** One round of one seat. in = the student's best estimate is inside the closing rank; mine / hi = the student's best and
 *  worst estimate on that round's rank type; unpublished = JAC Delhi never published this round (Upgrade, Spot). */
export type Cell = { open?: number | null; close: number | null; in: boolean; mine?: number | null; hi?: number | null; unpublished?: boolean };
export type CollegeIn = FormBody & { inst: number; prog?: number; quota?: string; gender?: "N" | "F"; seat?: "open" | "cat"; all?: boolean };
export type CollegeOut = {
  college: { id: number; name: string; short: string; type: Exclude<Segment, "all">; city: string; state: string };
  your_rank: { label: string; range: Range }; rounds: string[]; total: number; line: string | null; blocked: string | null; y25_label: string | null;
  rows: { prog: number; branch: string; degree: string; cells: Cell[]; first_in: string | null; y25: number | null }[];
  path: { quota: string; gender: "N" | "F"; seat: "open" | "cat" };
  options: { quota: { key: string; label: string }[]; gender: ("N" | "F")[]; seat: ("open" | "cat")[]; cat_label: string | null };
  official: string; official_csab: string | null;
};

// ------------------------------------------------------------------ types: rank predictor / percentile
export type EstimateIn = { exam: "jee" | "comedk"; marks: number; level: Level; category: Category; pwd: boolean };
export type JeeEstimate = {
  exam: "jee"; result: RankResult; candidates: number; notes: string[];
  levels: { level: Level; percentile: Range; crl: Range; cat_rank?: { label: string; range: Range } | null; pwd_rank?: { label: string; range: Range } | null }[];
};
export type ComedkEstimate = {
  exam: "comedk"; rank: Range; mid: number; percentile: Range; candidates: number; summary: string; notes: string[];
  sources: (Source & { rank: number })[];
};
export type EstimateOut = JeeEstimate | ComedkEstimate;
export type PercentileIn = { percentile: number; category: Category; pwd: boolean };
export type PercentileOut = { result: RankResult; candidates: number; marks: { level: Level; marks: number }[]; notes: string[] };

// ------------------------------------------------------------------ types: BITSAT
export type Campus = "all" | "Pilani" | "Goa" | "Hyderabad";
export type Degree = "all" | "BE" | "MSc" | "BPharm";
export type BitsatItem = {
  id: string; campus: Exclude<Campus, "all">; college: string; program: string; degree: Exclude<Degree, "all">;
  history: (number | null)[]; cutoff: number; last: number | null; tag: Tag | null; gap: number;
};
type BitsatPick = { college: string; program: string; cutoff: number };
export type BitsatOut = {
  result: { score: number; max: number; cleared: number; total: number; cleared_all: number; total_all: number;
    best: BitsatPick | null; target: (BitsatPick & { gap: number }) | null };
  items: BitsatItem[]; near: BitsatItem[]; rest: BitsatItem[]; years: number[]; notes: string[]; source: string;
};

// ------------------------------------------------------------------ types: COMEDK
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
export type ComedkCollegeIn = ComedkQuery & { branches?: string[]; code: string; course?: string; all?: boolean };
export type ComedkCollegeOut = {
  college: { code: string; name: string; short: string; city: string; blr: boolean }; your_rank: { label: string; range: Range };
  rounds: string[]; total: number; line: string; y25_label: string; official: string;
  rows: { cc: string; course: string; group: string; cells: Cell[]; close: number; round: string; first_in: string | null;
    y25: number | null; seats: number | null; fee: number | null; tag: Tag | null }[];
};

// ------------------------------------------------------------------ types: target marks, college lists, compare
export type JeeProfile = { category: Category; female: boolean; pwd: boolean; state: string | null };
export type JeeCollege = { inst: number; short: string; name: string; type: Exclude<Segment, "all">; state: string; city: string };
export type ComedkCollege = { code: string; short: string; name: string; city: string };
export type BitsatCampus = { campus: Exclude<Campus, "all">; name: string; programs: number };
export type Colleges = { jee: JeeCollege[]; comedk: ComedkCollege[]; bitsat: BitsatCampus[] };
export type Marks3 = Record<Level, number>;
export type JeeTargetRow = {
  prog: number; branch: string; degree: string; group: string; path: string; quota: string; gender: "N" | "F"; rank_type: string;
  seats: number | null; y25: number | null;
  cells: { label: string; close: number | null; crl?: number; pct?: number; marks?: Marks3; unpublished?: boolean }[];
  final: { label: string; close: number; crl: number; pct: number; marks: Marks3 };
};
export type JeeTarget = { exam: "jee"; college: Omit<JeeCollege, "inst"> & { id: number }; rounds: string[]; rows: JeeTargetRow[]; official: string; notes: string[] };
export type ComedkTargetRow = {
  cc: string; course: string; group: string; fee: number | null; seats: number | null; y25: number | null;
  cells: { label: string; close: number | null; marks?: Range; mid?: number }[];
  final: { label: string; close: number; marks: Range; mid: number };
};
export type ComedkTarget = { exam: "comedk"; college: { code: string; name: string; short: string; city: string; blr: boolean }; rounds: string[]; rows: ComedkTargetRow[]; official: string; notes: string[] };
export type BitsatTarget = {
  exam: "bitsat"; years: number[]; max: number; source: string; notes: string[];
  rows: { id: string; campus: Exclude<Campus, "all">; college: string; program: string; degree: string; cutoff: number; history: number[]; safe: number }[];
};
/** A saved college-branch. JEE: id "jee-<prog>" plus prog, quota, gender and the readable path from the card.
 *  COMEDK: id "<code>|<cc>". BITSAT: id "<Campus>-<program key>", e.g. "Pilani-cs". */
export type CompareItem = { exam: Exam; id: string; prog?: number; quota?: string; gender?: "N" | "F"; path?: string };
export type CompareCol = {
  exam: Exam; id: string; missing?: boolean; title?: string; name?: string; place?: string; sub?: string; path?: string;
  rank_label?: string; rounds?: { label: string; close: number | null; crl?: boolean }[]; final?: { label: string; close: number } | null;
  prev?: { label: string; close: number | null } | null; seats?: number | null; seats_label?: string | null; fee?: number | null; fee_note?: string;
  higher_is_harder?: boolean;
};
export type CollegeRef = { exam: Exam; id: string };
export type CollegeSide = { branch: string; close: number; label: string; rank_label: string; marks: number; cs: boolean };
export type CollegeCol = {
  exam: Exam; id: string; missing?: boolean; title?: string; name?: string; place?: string; kind?: string;
  branches?: number; seats?: number | null; seats_label?: string | null; fee?: [number, number] | null; fee_note?: string | null;
  easiest?: CollegeSide | null; toughest?: CollegeSide | null; cs?: CollegeSide | null; cs_count?: number;
};

// ------------------------------------------------------------------ types: Cut off (NEW)
/** One college's branches, or one branch's 100 most wanted college-branches, with every round's 2026 cut-off.
 *  With a score only the rows the student can reach come back, each tagged Safe, Likely or Borderline. docs/11. */
export type CutoffExam = "jee" | "comedk" | "bitsat";
export type CutoffBy = "college" | "branch";
export type CutoffScore = { marks?: number; percentile?: number; rank?: number };
/** One line of a picker. Send `key` back exactly as received. Search over title + sub + find. */
export type CutoffOption = { key: string; title: string; sub: string; find?: string; kind?: string };
/** score = the kinds of score this exam accepts, in the order of the chips; marks = [lowest, highest] marks;
 *  levels = the Tough / Normal / Easy question applies; profile = category, gender, PwD and home state apply. */
export type CutoffOptions = { limit: number } & Record<CutoffExam, {
  name: string; score: ScoreKind[]; marks: [number, number]; levels: boolean; profile: boolean; colleges: CutoffOption[]; branches: CutoffOption[];
}>;
/** One round (BITSAT: one year) of one row. state is present only with a score: "in" = the student's whole range is
 *  inside (green), "edge" = only part of it, or a CSAB round (amber), "out" = not reached. na = the college has no such
 *  round (leave the box out). crl = this CSAB box is on CRL although the seat's own rank type is a category / PwD rank. */
export type CutoffCell = { label: string; close: number | null; state?: "in" | "edge" | "out"; na?: boolean; crl?: boolean };
export type CutoffRow = {
  id: string; college: string; place: string; kind: string; branch: string; path: string; rank_type: string; cells: CutoffCell[];
  final: { label: string; close: number }; prev: { label: string; close: number | null } | null; seats: number | null; fee: number | null;
  need: { marks: number; pct?: number; level?: Level }; tag: Tag | null; gap?: string;
  /** This year against last year, like for like (JEE: last JoSAA round, never CSAB). null = no last-year number. Print `label`. */
  trend: CutoffTrend | null;
  /** The row as one shortlist item: keep it as it is; `toCompareItem(save)` is what POST /rank/compare takes. */
  save: SavedRow;
};
/** dir "tough" = harder than last year (up arrow, red), "easy" = easier (down arrow, green), "same" = within 3 % (no arrow). */
export type CutoffTrend = { dir: "tough" | "easy" | "same"; prev: number; label: string };
/** id = "jee-262" | "comedk-E015|CS" | "bitsat-Pilani-cs": the same keys the College predictor saves under. */
export type SavedRow = { id: string; exam: Exam; title: string; sub: string; line: string; tag: Tag | null;
  jee?: { prog: number; quota: string; gender: "N" | "F"; path: string } };
/** A saved row as POST /rank/compare and the saved-list PDF take it. */
export const toCompareItem = (s: SavedRow): CompareItem =>
  s.exam === "jee" ? { exam: "jee", id: s.id, ...s.jee } : { exam: s.exam, id: s.id.replace(/^(comedk|bitsat)-/, "") };
export type CutoffYou = {
  source: ScoreKind; summary: string; line: string; percentile: Range | null; rank: { label: string; range: Range } | null;
  cat_rank?: { label: string; range: Range } | null; pwd_rank?: { label: string; range: Range } | null; check?: string | null;
  counts: Record<Tag, number>;
};
/** total = rows open to this student before the score filter; eligible = rows that passed it (null without a score);
 *  limit = 100 for a branch list, null for a college; metric "score" (BITSAT) = a bigger number is harder. */
export type CutoffOut = {
  exam: CutoffExam; by: CutoffBy; key: string; title: string; name: string; sub: string; kind: string | null; metric: "rank" | "score";
  columns: string[]; prev_label: string | null; rows: CutoffRow[]; total: number; eligible: number | null; limit: number | null;
  you: CutoffYou | null; near: CutoffRow[]; notes: string[]; official: string;
};
/** level, category, female, pwd and state are used by JEE Main only; leave them out for COMEDK and BITSAT. */
export type CutoffIn = { exam: CutoffExam; by: CutoffBy; key: string; level?: Level } & CutoffScore & Partial<JeeProfile>;

// ------------------------------------------------------------------ types: PDFs
export type PdfRequests = {
  "jee": FormBody & { segment: Segment };
  "comedk": ComedkQuery & { branches: string[]; area: ComedkArea };
  "bitsat": { score: number; campus: Campus; degree: Degree };
  "target/jee": JeeProfile & { inst: number };
  "target/comedk": { code: string };
  "target/bitsat": { campus: Campus };
  /** items = every saved college-branch, tags = its chance tag (or null), pick = indexes of the 2-3 shown side by side. */
  "saved": { items: CompareItem[]; tags: (Tag | null)[]; pick: number[] };
  /** The body that drew the Cut off list on screen, score included: the PDF is that same list. */
  "cutoff": CutoffIn;
};
export type Pdf = { name: string; blob: Blob };

// ------------------------------------------------------------------ types: Mission, Dream college
/** code = the student's 7-character link code; helped = friends who opened the link (all time); week = in the last 7 days;
 *  link = the full share link (added by the website connector). */
export type MissionStats = { code: string; helped: number; week: number; link?: string };
/** need = marks (on the exam's full-marks scale) the seat needs on a normal paper; range = [easy paper, tough paper]. */
export type Dream = { id: string; exam: Exam; college: string; branch: string; need: number; range?: Range; note: string; at: number };
export type Mock = { id: string; exam: Exam; score: number; max: number; raw: number; rawMax: number; title: string; at: number };
export type DreamState = { dreams: Dream[]; mocks: Mock[]; cheered: string[] };

// ------------------------------------------------------------------ client
export class JeeliveError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.name = "JeeliveError"; this.status = status; }
}
export type ClientOptions = { baseUrl?: string; fetch?: typeof fetch; timeoutMs?: number };

const RETRY = "Rank abhi load nahi hua. Retry dabao.";
const SLOW = "Network kamzor hai. Retry dabao.";

function messageOf(data: any, fallback: string): string {
  const d = data?.detail;
  if (typeof d === "string" && d) return d;                              // the server's own short Hinglish message
  if (Array.isArray(d) && typeof d[0]?.msg === "string") return d[0].msg; // a field failed validation (422)
  return fallback;
}

export function createJeeliveApp(options: ClientOptions = {}) {
  const base = (options.baseUrl ?? "/api").replace(/\/+$/, "");
  const doFetch: typeof fetch = options.fetch ?? ((input, init) => fetch(input, init));
  const timeoutMs = options.timeoutMs ?? 15000;

  async function send(path: string, init: RequestInit, ms: number): Promise<Response> {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), ms);
    try { return await doFetch(base + path, { ...init, signal: ctrl.signal }); }
    catch (e: any) { throw new JeeliveError(e?.name === "AbortError" ? SLOW : RETRY, 0); }
    finally { clearTimeout(timer); }
  }

  /** GET when body is undefined, else a JSON request (POST unless `method` says otherwise). `signedIn` sends the website's cookies. */
  async function call<T>(path: string, body?: unknown, o: { method?: string; signedIn?: boolean; fallback?: string } = {}): Promise<T> {
    const res = await send(path, {
      method: o.method ?? (body === undefined ? "GET" : "POST"),
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: o.signedIn ? "include" : "same-origin",
    }, timeoutMs);
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new JeeliveError(messageOf(data, o.fallback ?? RETRY), res.status);
    return data as T;
  }

  const rank = {
    /** States, branch groups, the 50-line percentile chart, notes and sources. Fetch once per visit. */
    meta: () => call<Meta>("/rank/meta"),
    /** Rank predictor: marks -> percentile and rank (JEE: all three paper types; COMEDK: three public analyses). */
    estimate: (body: EstimateIn) => call<EstimateOut>("/rank/estimate", body),
    /** NTA percentile -> CRL, category / PwD rank, and the marks it took on each paper type. Still served, but the app
     *  no longer has a screen for it: its tile became Cut off, and every JEE form now takes a percentile or a rank. */
    percentile: (body: PercentileIn) => call<PercentileOut>("/rank/percentile", body),
    /** College predictor, JEE Main: the Rank Card + up to 50 college-branches (25 a page) + 5 near misses. */
    predict: (body: PredictIn) => call<PredictOut>("/rank/predict", body),
    /** One JEE college opened from a card: every round's closing rank for its branches, on a chosen seat path. */
    college: (body: CollegeIn) => call<CollegeOut>("/rank/college", body),
    bitsat: (body: { score: number; campus: Campus; degree: Degree }) => call<BitsatOut>("/rank/bitsat", body),
    comedk: (body: ComedkQuery & { branches: string[]; area: ComedkArea; page: number }) => call<ComedkOut>("/rank/comedk", body),
    comedkCollege: (body: ComedkCollegeIn) => call<ComedkCollegeOut>("/rank/comedk/college", body),
    /** Search lists for Target marks and College compare. Fetch once per visit. */
    colleges: () => call<Colleges>("/rank/colleges"),
    targetJee: (body: JeeProfile & { inst: number }) => call<JeeTarget>("/rank/target/jee", body),
    targetComedk: (code: string) => call<ComedkTarget>("/rank/target/comedk", { code }),
    targetBitsat: () => call<BitsatTarget>("/rank/target/bitsat"),
    /** Branch vs branch: 1-3 saved college-branches side by side. */
    compare: (items: CompareItem[]) => call<{ items: CompareCol[]; notes: string[] }>("/rank/compare", { items }),
    /** College vs college: 1-3 whole colleges side by side, for the student's JEE profile. */
    compareColleges: (items: CollegeRef[], profile: JeeProfile) =>
      call<{ items: CollegeCol[]; notes: string[] }>("/rank/compare/colleges", { items, ...profile }),
    /** Cut off (NEW): the two pickers of every exam (colleges and branches). About 62 KB (11 KB compressed). Fetch once per visit. */
    cutoffOptions: () => call<CutoffOptions>("/rank/cutoff/options"),
    /** Cut off (NEW): every round's cut-off for one college's branches or one branch's top 100 colleges.
     *  Without a score: every row. With one: only Safe, Likely and Borderline rows, plus up to 3 nearest misses. */
    cutoff: (body: CutoffIn) => call<CutoffOut>("/rank/cutoff", body),
    /** A white A4 PDF drawn by the server (allow 30 s). `name` comes from the server, e.g. "JEELIVE-JEE-colleges-180-marks.pdf". */
    async pdf<K extends keyof PdfRequests>(kind: K, body: PdfRequests[K]): Promise<Pdf> {
      const fail = "PDF nahi bani. Network check karke dobara try karo.";
      const res = await send(`/rank/pdf/${kind}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }, 30000);
      if (!res.ok) throw new JeeliveError(messageOf(await res.json().catch(() => null), fail), res.status);
      const name = /filename="([^"]+)"/.exec(res.headers.get("content-disposition") ?? "")?.[1] ?? "JEELIVE-Rank.pdf";
      return { name, blob: await res.blob() };
    },
  };

  const account = { signedIn: true, fallback: "Abhi load nahi hua. Thodi der mein dobara try karo." };
  const mission = {
    /** The signed-in student's share link and impact. 401 = not signed in on the website. */
    me: () => call<MissionStats>("/mission/me", undefined, account),
  };
  const dream = {
    read: () => call<DreamState>("/dream", undefined, account),
    /** `dreams` = this device's list after its changes, `base` = ids of the account list those changes were made on. */
    save: (dreams: Dream[], base: string[]) => call<{ dreams: Dream[] }>("/dream/dreams", { dreams, base }, { ...account, method: "PUT" }),
    addMocks: (mocks: Mock[]) => call<{ ok: true }>("/dream/mocks", { mocks }, account),
    cheered: (ids: string[]) => call<{ ok: true }>("/dream/cheered", { ids }, account),
  };

  return { rank, mission, dream };
}

// ------------------------------------------------------------------ helpers the app's screens use (same output)
/** Indian grouping: 107693 -> "1,07,693". */
export function fmt(n: number): string {
  const s = String(Math.round(n));
  if (s.length <= 3) return s;
  return s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + s.slice(-3);
}
export const fmtRange = (r: Range) => (r[0] === r[1] ? fmt(r[0]) : `${fmt(r[0])} – ${fmt(r[1])}`);
export const fmtPct = (r: Range) => (r[0] === r[1] ? r[0].toFixed(2) : `${r[0].toFixed(2)} – ${r[1].toFixed(2)}`);

/** Saves a PDF (or any blob) from the browser. */
export function downloadBlob({ name, blob }: Pdf) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}

/** api.whatsapp.com directly: the wa.me redirect breaks some emoji in the message. */
export const whatsappUrl = (text: string) => "https://api.whatsapp.com/send?text=" + encodeURIComponent(text);

// Mission: the exact words and numbers of the app.
export const MISSION_SITE = "https://jeelive.ai";
/** The share link to show and send: the student's own link once known, the plain site before that. */
export const missionLink = (s?: MissionStats | null) => s?.link ?? MISSION_SITE;
/** The message under the Mission card picture (or alone, where a picture cannot be sent). */
export const missionCaption = (link: string) => [
  "🙏 Please share karo aur free education ko support karo!",
  "",
  "JEELIVE.AI: 100% free JEE Main, BITSAT & COMEDK prep. Abhishek Pushp ne ise AI ke saath, apne kharche par banaya hai.",
  "",
  "🧬 Har sawaal ka DNA 4,000+ PYQs analyse karke bana",
  "🎯 Target: har session 200+ marks ke sawaal isi Mock aur All India Test Series se",
  "⚡ Rapid Fire: revision ka competitive game",
  "🎓 Rank + College predictor: dream college kitni door?",
  "",
  `Abhi kholo 👉 ${link}`,
].join("\n");
/** Milestones on the Impact panel: the next one above the current count. */
const STEPS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
export const nextStep = (n: number) => STEPS.find(x => x > n) ?? Math.ceil((n + 1) / 10000) * 10000;
/** 12 -> "12", 1234 -> "1,234", 25300 -> "25k+". */
export const shortCount = (n: number) => (n < 10000 ? n.toLocaleString("en-IN") : `${Math.floor(n / 1000)}k+`);
/** "Rahul Kumar" -> "Rahul" for the thank-you line; "" when the name is a phone number. */
export const firstName = (name?: string) => {
  const w = (name || "").trim().split(/\s+/)[0] || "";
  return /\d/.test(w) ? "" : w.slice(0, 14);
};
