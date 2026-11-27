import { api, ApiError } from "./client";
import { resources } from "@/src/resourceCache";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import { EXAMS } from "@/src/navigation";
import type { IconName } from "@/src/components/ui";

/** The website's own exam list and sections: whatever the owner adds, hides or reorders there shows here. */
export type ExamSection = { id: string; slug: string; name: string; description?: string; layout: "list" | "chapters"; kind?: string; hidden?: boolean; order?: number; live_count?: number };
export type CatalogExam = { slug: string; key: string; name: string; short?: string; subjects?: string[]; shown?: boolean; order?: number; sections?: ExamSection[] };

// Only used when the website can't be reached: the three exams the app has always had.
const BUILT_IN: CatalogExam[] = EXAMS.map(e => ({ slug: e.slug, key: e.name, name: e.name }));
const ICONS: Record<string, IconName> = { "jee-main": "atom-variant", bitsat: "school-outline", comedk: "office-building-outline" };
// A new exam borrows one of the app's existing icons (no per-exam artwork).
const SPARE: IconName[] = ["book-open-page-variant-outline", "file-document-multiple-outline", "bullseye-arrow", "star-outline", "flag-outline", "compass-outline"];
export const examIcon = (slug: string, index = 0): IconName => ICONS[slug] ?? SPARE[index % SPARE.length];

const byOrder = <T extends { order?: number }>(a: T, b: T) => (a.order ?? 99) - (b.order ?? 99);

export function useExams() {
  const { user } = useAuth();
  const res = useCached<{ items: CatalogExam[] }>(user ? `u.${user.id}.catalog.exams` : null, signal => api("/catalog/exams", { signal }));
  const live = res.data?.items?.filter(e => e?.slug && e.shown !== false).sort(byOrder);
  return { ...res, exams: live ?? (res.error ? BUILT_IN : null) };
}

const examKey = (uid: string, slug: string) => `u.${uid}.catalog.exam.${slug}`;
/** The exam's name without another request: what this phone last heard from the website, else the built-in name. */
export const cachedExamName = (uid?: string, slug?: string) =>
  (uid && slug ? resources.peek<CatalogExam>(examKey(uid, slug))?.name : "") || EXAMS.find(e => e.slug === slug)?.name || "";

export function useExam(slug?: string) {
  const { user } = useAuth();
  // The website answers 404 for an exam the owner has hidden: that means "not available", not a network problem.
  const res = useCached<CatalogExam>(user && slug ? examKey(user.id, slug) : null, signal => api<CatalogExam>(`/catalog/exams/${encodeURIComponent(slug!)}`, { signal })
    .catch(e => { if (e instanceof ApiError && e.status === 404) return { slug: slug!, key: "", name: "", shown: false }; throw e; }));
  const exam = res.data ? (res.data.shown === false ? null : res.data) : res.error ? BUILT_IN.find(e => e.slug === slug) ?? null : null;
  const sections = (exam?.sections || []).filter(s => s?.slug && !s.hidden).sort(byOrder);
  return { ...res, exam, sections };
}

/** Builtin sections are reached by kind alone (same request as before); a section the owner created is named.
 *  A named section is always asked for with kind=mocks: the website then answers with that section's own layout
 *  (checked against the live website: kind=mocks&section=chapters returns the chapter list; kind=chapters&section=mocks is refused). */
export const catalogueKind = (s: Pick<ExamSection, "layout">) => (s.layout === "chapters" ? "chapters" : "mocks");
export const sectionParam = (s: Pick<ExamSection, "slug" | "layout">) => (s.slug === catalogueKind(s) ? "" : s.slug);
export const cataloguePath = (slug: string, kind: string, section: string, subject: string, q: string, page: number, perPage = 0) =>
  `/exam-navigation/${slug}/catalogue?${new URLSearchParams({ kind, ...(section ? { section } : {}), subject, q, page: String(page), ...(perPage ? { per_page: String(perPage) } : {}) })}`;

/** One list whole, for a screen that regroups it on the phone (Class 11 / Class 12). Asked for with per_page=100: a
 *  website that honours it (its packet N1, 28 Nov 2026) answers in one page; one that does not gives 12 a page as
 *  before, and the first page says how many pages there are, so the others are asked for together. Either way the
 *  student sees the same list, grouped by the app's own Class 11 / Class 12 list (src/classLevel.ts). */
export async function catalogueAll(slug: string, kind: string, section: string, subject: string, q: string, signal?: AbortSignal) {
  const first = await api<any>(cataloguePath(slug, kind, section, subject, q, 1, 100), { signal });
  const pages = Math.min(Number(first?.pages) || 1, 10);
  if (pages <= 1) return first;
  const rest = await Promise.all(Array.from({ length: pages - 1 }, (_, i) => api<any>(cataloguePath(slug, kind, section, subject, q, i + 2, 100), { signal })));
  const ids = new Set<string>(); // a test published between two pages must not be listed twice
  const items = [first, ...rest].flatMap(p => p?.items || []).filter(s => s?.id && !ids.has(s.id) && ids.add(s.id));
  return { ...first, items, page: 1, pages: 1 };
}
