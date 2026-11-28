// Analytics for the app's search boxes (src/jlTracker.ts): one search_performed for each search that settles, plus
// search_zero_results when nothing came back. Only the place (`area`) and how many were found are sent, never the words.
import { useEffect, useRef } from "react";
import { track } from "@/src/jlTracker";

/** `count` = what the search found for `query` (null while it is still looking). A search counts once it has stood
 *  still for a moment, so typing a word letter by letter is one search, not one per letter. */
export function useSearchTrack(area: string, query: string, count: number | null | undefined) {
  const last = useRef("");
  useEffect(() => {
    const q = query.trim();
    if (!q || count == null || last.current === q) return;
    const t = setTimeout(() => {
      last.current = q;
      track("search_performed", { area, results: count });
      if (!count) track("search_zero_results", { area });
    }, 800);
    return () => clearTimeout(t);
  }, [area, query, count]);
}
