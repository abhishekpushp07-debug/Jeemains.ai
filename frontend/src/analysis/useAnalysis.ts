import { useCallback, useEffect, useState } from "react";
import { api } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { flushLeftover } from "./timeCapture";
import type { An } from "./format";

export type AnalysisState = { data: An | null; error: string; status: number; loading: boolean; offline: boolean; reload: () => void };

// One request opens the whole analysis. The last one opened stays readable without internet.
export function useAnalysis(id: string, userId: string | undefined, scoreVersion: string, enabled: boolean, compare: boolean, vs: string): AnalysisState {
  const [state, setState] = useState<{ data: An | null; error: string; status: number; loading: boolean; offline: boolean }>({ data: null, error: "", status: 0, loading: false, offline: false });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!enabled || !userId) return undefined;
    let stop = false, timer: ReturnType<typeof setTimeout> | undefined, tries = 0;
    const key = `analysis.last.${userId}`;
    const load = async () => {
      setState(s => ({ ...s, loading: true, error: "" }));
      try {
        if (!tries) await flushLeftover(userId, id);
        const q = `mode=${compare ? "comparative" : "personal"}&compare=${encodeURIComponent(vs)}&score_version=${encodeURIComponent(scoreVersion)}`;
        const data = await api<An>(`/attempts/${id}/analysis?${q}`);
        if (stop) return;
        setState({ data, error: "", status: 200, loading: false, offline: false });
        if (!compare && scoreVersion === "original") void storage.setItem(key, JSON.stringify({ id, data }));
        if (data.class?.state === "preparing" && ++tries < 6) timer = setTimeout(load, 2500);
      } catch (e: any) {
        if (stop || e?.name === "AbortError") return;
        // "Result abhi ban raha hai": the server asks to come back in a moment.
        if (e?.status === 409 && e.retryAfterMs && ++tries < 6) { timer = setTimeout(load, Math.max(2000, e.retryAfterMs)); return; }
        let saved: An | null = null;
        if (!e?.status) {
          try { const x = JSON.parse((await storage.getItem<string | null>(key, null)) || "null"); if (x?.id === id) saved = x.data; } catch {}
        }
        if (stop) return;
        setState(s => (saved ? { data: s.data || saved, error: "", status: 0, loading: false, offline: true }
          : { ...s, loading: false, error: e?.message || "Analysis nahi khul paaya. Dobara try karo.", status: e?.status || 0 }));
      }
    };
    void load();
    return () => { stop = true; clearTimeout(timer); };
  }, [id, userId, scoreVersion, enabled, compare, vs, tick]);
  const reload = useCallback(() => setTick(v => v + 1), []);
  return { ...state, reload };
}
