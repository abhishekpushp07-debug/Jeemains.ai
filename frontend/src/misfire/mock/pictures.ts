// A mock's pictures: its questions come from several papers, and each picture is asked for under its own paper, so
// each paper's questions of this mock are named to the picture loader under that paper (as Misfire's solve screen does).
import { useCallback, useLayoutEffect, useMemo } from "react";
import { useFocusEffect } from "expo-router";
import { useAuth } from "@/src/auth";
import { privateAssets, registerAssetManifest } from "@/src/api/client";
import { trustKept } from "@/src/assets/assetGrants";
import { imagePaths, questionPaths } from "@/src/assets/paperAssets";
import type { MockQ } from "./store";

export const picturesOf = (q: MockQ, solutions = false) => [...questionPaths(q.attempt_id, q), ...(solutions ? imagePaths(q.attempt_id, q, "solution") : [])];

/** Lets the mock's pictures load: the one in view first, the next two and the one before it after it, the rest quietly
 *  behind. `solutions`: only once the mock is over. */
export function useMockPictures(questions: MockQ[], current?: string, solutions = false) {
  const groups = useMemo(() => {
    const by = new Map<string, MockQ[]>();
    for (const q of questions) by.set(q.attempt_id, [...(by.get(q.attempt_id) || []), q]);
    return by;
  }, [questions]);
  // Behind the offline door (no session): the pictures kept on this phone are the pictures, as a kept result's are
  // (app/offline/result.tsx); nothing can be asked of the server.
  const signedIn = !!useAuth().user;
  useLayoutEffect(() => {
    for (const [attempt, rows] of groups) { registerAssetManifest(attempt, rows, solutions); if (!signedIn) trustKept(attempt); }
  }, [groups, solutions, signedIn]);
  useFocusEffect(useCallback(() => {
    if (!questions.length) return;
    privateAssets.selectGroup("misfire-mock");
    const i = Math.max(0, questions.findIndex((q) => q.id === current));
    const focus = picturesOf(questions[i], solutions);
    const around = [questions[i + 1], questions[i + 2], questions[i - 1]].filter(Boolean).flatMap((q) => picturesOf(q, solutions));
    privateAssets.pin(focus, around);
    focus.forEach((p) => { void privateAssets.get(p, 100).catch(() => {}); });
    around.forEach((p) => { void privateAssets.get(p, 80).catch(() => {}); });
    privateAssets.preload(questions.flatMap((q) => picturesOf(q, solutions)));
  }, [questions, current, solutions]));
}
