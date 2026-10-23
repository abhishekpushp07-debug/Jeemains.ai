import { useCallback, useEffect, useRef, useState } from "react";
import { storage } from "@/src/utils/storage";

// Stale-while-revalidate: paint last known data instantly, refresh in background.
const memory = new Map<string, any>();

export function useCached<T>(key: string | null, fetcher: (signal: AbortSignal) => Promise<T>, persist = true) {
  const [data, setData] = useState<T | null>(key ? memory.get(key) ?? null : null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!data);
  const [tick, setTick] = useState(0);
  const [dataKey, setDataKey] = useState<string | null>(key);
  const fetchRef = useRef(fetcher);
  fetchRef.current = fetcher;

  useEffect(() => {
    if (!key) return;
    const controller = new AbortController();
    let alive = true;
    setError("");
    // Never show the previous key's data for a new key.
    setData(memory.get(key) ?? null);
    setDataKey(key);
    setLoading(!memory.has(key));
    (async () => {
      if (!memory.has(key) && persist) {
        const raw = await storage.getItem<string | null>("cache." + key, null);
        if (raw && alive) {
          try {
            const v = JSON.parse(raw);
            memory.set(key, v);
            setData(v);
            setLoading(false);
          } catch {}
        }
      } else if (memory.has(key)) {
        setData(memory.get(key));
        setLoading(false);
      }
      try {
        const v = await fetchRef.current(controller.signal);
        if (!alive) return;
        memory.set(key, v);
        setData(v);
        setDataKey(key);
        if (persist) storage.setItem("cache." + key, JSON.stringify(v));
      } catch (e: any) {
        if (alive && e?.name !== "AbortError") setError(e?.message || "Could not load. Retry.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
      controller.abort();
    };
  }, [key, tick, persist]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, error, loading, reload, dataKey };
}

export const invalidate = (prefix: string) => {
  for (const k of [...memory.keys()]) if (k.startsWith(prefix)) memory.delete(k);
};
