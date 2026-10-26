import { useCallback, useEffect, useMemo, useSyncExternalStore } from "react";
import { useFocusEffect } from "expo-router";
import { privateAssets } from "@/src/api/client";

export type PaperQuestion = { id: string; number?: number; subject?: string; asset_count?: number; solution_asset_count?: number; bonus?: boolean };
export const subjectOf = (q?: PaperQuestion) => q?.subject?.trim() || "Uncategorised";
export const subjectId = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
export const availableQuestions = <T extends PaperQuestion>(rows: T[], bonusUnlocked: boolean) => rows.filter(q => !q.bonus || bonusUnlocked);
export const resultIsReleased = (status: number, result?: { summary?: unknown; status?: string } | null) => status === 200 && !!result?.summary && result.status !== "embargoed";
export function imagePaths(id: string, q: PaperQuestion, kind: "question" | "solution", version = "original") {
  const count = kind === "question" ? q.asset_count : q.solution_asset_count;
  return Array.from({ length: Math.max(0, Number(count) || 0) }, (_, i) =>
    `/attempts/${encodeURIComponent(id)}/questions/${encodeURIComponent(q.id)}/asset/${kind}/${i}${version !== "original" ? `?score_version=${encodeURIComponent(version)}` : ""}`);
}
export function prioritizedPaths(id: string, rows: PaperQuestion[], selected: string | undefined, solutions: boolean, version = "original") {
  const current = rows.find(q => q.id === selected) || rows[0];
  const order = [...rows].sort((a, b) => {
    const rank = (q: PaperQuestion) => q.id === current?.id ? 0 : subjectOf(q) === subjectOf(current) ? 1 : 2;
    return rank(a) - rank(b);
  });
  return order.flatMap(q => [...imagePaths(id, q, "question", version), ...(solutions ? imagePaths(id, q, "solution", version) : [])]);
}
export function usePaperAssets(id: string, rows: PaperQuestion[], selected?: string, solutions = false, version = "original", enabled = true) {
  const paths = useMemo(() => prioritizedPaths(id, rows, selected, solutions, version), [id, rows, selected, solutions, version]);
  const revision = useSyncExternalStore(privateAssets.subscribe, privateAssets.snapshot, privateAssets.snapshot);
  useFocusEffect(useCallback(() => { if (enabled) privateAssets.selectGroup(id); }, [id, enabled]));
  useEffect(() => {
    if (!enabled || !rows.length || !privateAssets.isGroup(id)) return;
    privateAssets.preload(paths);
  }, [id, rows.length, paths, enabled, revision]);
  useEffect(() => {
    if (!enabled || !rows.length || !privateAssets.isGroup(id)) return;
    // Promote every current crop above the background queue. No solution access
    // exists here until the caller has a released200 result payload.
    const current = rows.find(q => q.id === selected) || rows[0];
    const focus = [...imagePaths(id, current, "question", version), ...(solutions ? imagePaths(id, current, "solution", version) : [])];
    privateAssets.pin(focus);
    focus.forEach(path => { void privateAssets.get(path, 100).catch(() => {}); });
  }, [id, rows, selected, solutions, version, enabled]);
  const retry = useCallback(() => privateAssets.retry(paths), [paths]);
  return { ...privateAssets.progress(enabled ? paths : []), retry };
}