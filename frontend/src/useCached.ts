import { useCallback, useEffect, useRef, useState } from "react";
import { storage } from "@/src/utils/storage";

// Stale-while-revalidate: paint last known data instantly, refresh in background.
const memory = new Map<string, any>();

export function useCached<T>(key: string | null, fetcher: (signal: AbortSignal) => Promise<T>, persist = true): { data: T | null; error: string; loading: boolean; reload: () => void; dataKey: string | null } {
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
      // Network starts immediately; the persisted copy only paints if the network hasn't answered yet.
      let fresh = false;
      if (!memory.has(key) && persist) {
        storage.getItem<string | null>("cache." + key, null).then((raw) => {
          if (!raw || !alive || fresh) return;
          try {
            const v = JSON.parse(raw);
            setData(v);
            setLoading(false);
          } catch {}
        });
      }
      try {
        const v = await fetchRef.current(controller.signal);
        fresh = true;
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
  // A key change renders before the effect runs; never flash another exam/account's data.
  return { data: dataKey === key ? data : (key ? memory.get(key) ?? null : null), error: dataKey === key ? error : "", loading: dataKey === key ? loading : true, reload, dataKey };
}

export const invalidate = (prefix: string) => {
  for (const k of [...memory.keys()]) if (k.startsWith(prefix)) memory.delete(k);
};

// Warm the in-memory cache before the user navigates (no UI state involved).
export function prefetch<T>(key: string, fetcher: () => Promise<T>) {
  if (memory.has(key)) return;
  fetcher().then((v) => { memory.set(key, v); storage.setItem("cache." + key, JSON.stringify(v)); }).catch(() => {});
}
