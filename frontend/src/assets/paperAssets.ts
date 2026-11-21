import { useCallback, useLayoutEffect, useMemo } from "react";
import { useFocusEffect } from "expo-router";
import { privateAssets, registerAssetManifest } from "@/src/api/client";
import { Piece, pieceLayout, piecesOf } from "./pieces";

export type PaperQuestion = { id: string; number?: number; subject?: string; asset_count?: number; solution_asset_count?: number; bonus?: boolean; pieces?: Piece[] | null; typed_options?: Record<string, string> | null };
export const subjectOf = (q?: PaperQuestion) => q?.subject?.trim() || "Uncategorised";
export const subjectId = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
export const availableQuestions = <T extends PaperQuestion>(rows: T[], bonusUnlocked: boolean) => rows.filter(q => !q.bonus || bonusUnlocked);
export const resultIsReleased = (status: number, result?: { summary?: unknown; status?: string } | null) => status === 200 && !!result?.summary && result.status !== "embargoed";
export function imagePaths(id: string, q: PaperQuestion, kind: "question" | "solution" | "piece", version = "original") {
  const count = kind === "piece" ? piecesOf(q)?.length : kind === "question" ? q.asset_count : q.solution_asset_count;
  return Array.from({ length: Math.max(0, Number(count) || 0) }, (_, i) =>
    `/attempts/${encodeURIComponent(id)}/questions/${encodeURIComponent(q.id)}/asset/${kind}/${i}${version !== "original" ? `?score_version=${encodeURIComponent(version)}` : ""}`);
}
/** The pictures a question is drawn from: its cut pieces when the website supplies them, otherwise the whole picture. */
export const questionPaths = (id: string, q: PaperQuestion, version = "original") => imagePaths(id, q, piecesOf(q) ? "piece" : "question", version);
export function prioritizedPaths(id: string, rows: PaperQuestion[], selected: string | undefined, solutions: boolean, version = "original") {
  const current = rows.find(q => q.id === selected) || rows[0];
  const order = [...rows].sort((a, b) => {
    const rank = (q: PaperQuestion) => q.id === current?.id ? 0 : subjectOf(q) === subjectOf(current) ? 1 : 2;
    return rank(a) - rank(b);
  });
  return order.flatMap(q => [...questionPaths(id, q, version), ...(solutions ? imagePaths(id, q, "solution", version) : [])]);
}
// The questions a student most likely opens next: the two after this one and the one before, in the same subject.
function neighbours(rows: PaperQuestion[], selected?: string) {
  const current = rows.find(q => q.id === selected) || rows[0];
  const subject = rows.filter(q => subjectOf(q) === subjectOf(current));
  const i = subject.indexOf(current);
  return [subject[i + 1], subject[i + 2], subject[i - 1]].filter(Boolean);
}
/** Drawn size of every neighbouring cut piece, so the warm-up decodes each picture at the size the screen will ask for. */
export function pieceWarmSizes(id: string, rows: PaperQuestion[], selected: string | undefined, width: number, zoom = 1, version = "original") {
  const sizes: Record<string, { width: number; height: number }> = {};
  for (const q of neighbours(rows, selected)) {
    const pieces = piecesOf(q);
    if (!pieces) continue;
    const scale = pieceLayout(pieces, q.typed_options, width, zoom);
    imagePaths(id, q, "piece", version).forEach((path, i) => {
      const k = pieces[i].part === "q" ? scale.stem : scale.option;
      sizes[path] = { width: pieces[i].w * k, height: pieces[i].h * k };
    });
  }
  return sizes;
}
export function usePaperAssets(id: string, rows: PaperQuestion[], selected?: string, solutions = false, version = "original", enabled = true) {
  const paths = useMemo(() => prioritizedPaths(id, rows, selected, solutions, version), [id, rows, selected, solutions, version]);
  const window = useMemo(() => {
    const around = neighbours(rows, selected);
    // Whole pictures are large (6 at most stay warm); a cut question is five small pieces.
    return around.flatMap(q => [...questionPaths(id, q, version), ...(solutions ? imagePaths(id, q, "solution", version) : [])]).slice(0, around.some(piecesOf) ? 18 : 6);
  }, [id, rows, selected, solutions, version]);
  useLayoutEffect(() => { if (enabled && rows.length) registerAssetManifest(id, rows, solutions, version); }, [id, rows, solutions, version, enabled]);
  useFocusEffect(useCallback(() => {
    if (!enabled || !rows.length) return;
    privateAssets.selectGroup(id);
    // Promote every current crop above the background queue. No solution access
    // exists here until the caller has a released200 result payload.
    const current = rows.find(q => q.id === selected) || rows[0];
    const focus = [...questionPaths(id, current, version), ...(solutions ? imagePaths(id, current, "solution", version) : [])];
    privateAssets.pin(focus, window);
    focus.forEach(path => { void privateAssets.get(path, 100).catch(() => {}); });
    window.forEach(path => { void privateAssets.get(path, 80).catch(() => {}); });
    privateAssets.preload(paths);
  }, [id, rows, selected, solutions, version, enabled, paths, window]));
  // No global progress subscription: downloading Q75 must not render Q1 again.
  return enabled ? window : [];
}