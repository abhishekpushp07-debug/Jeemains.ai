import { useCallback, useEffect, useRef, useState } from "react";
import { storage } from "@/src/utils/storage";
import { resources } from "@/src/resourceCache";

// Stale-while-revalidate: paint last known data instantly, refresh in background.
resources.setPersistence((key, raw, at) => {
  void Promise.resolve(storage.setItem("cache." + key, `{"v":2,"at":${at},"data":${raw}}`)).catch(() => {});
});

export function useCached<T>(key: string | null, fetcher: (signal: AbortSignal) => Promise<T>, persist = true): { data: T | null; error: string; loading: boolean; refreshing: boolean; reload: () => void; revalidate: () => void; dataKey: string | null } {
  const [data, setData] = useState<T | null>(key ? resources.peek<T>(key) : null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!data);
  const [refreshing, setRefreshing] = useState(false);
  const [tick, setTick] = useState(0);
  const [dataKey, setDataKey] = useState<string | null>(key);
  const fetchRef = useRef(fetcher);
  const forceNext = useRef(false);
  const aborts = useRef(0);
  fetchRef.current = fetcher;

  useEffect(() => {
    if (!key) return;
    const force = forceNext.current;
    forceNext.current = false;
    let alive = true;
    setError("");
    // Never show the previous key's data for a new key.
    const cached = resources.peek<T>(key);
    setData(cached);
    setDataKey(key);
    setLoading(cached === null);
    setRefreshing(force);
    (async () => {
      // Network starts immediately; the persisted copy only paints if the network hasn't answered yet.
      let fresh = false;
      if (cached === null && persist) {
        storage.getItem<string | null>("cache." + key, null).then((raw) => {
          if (!raw || !alive || fresh) return;
          try {
            const v = JSON.parse(raw);
            if (v?.v !== 2 || !Number.isFinite(v.at) || Date.now() - v.at > 10 * 60 * 1000) return;
            setData(v.data);
            setLoading(false);
          } catch {}
        });
      }
      let retry = false;
      try {
        const load = fetchRef.current; // bind this render's account/path before sharing the promise
        const v = await resources.request<T>(key, load, persist, force);
        fresh = true;
        aborts.current = 0;
        if (!alive) return;
        setData(v);
        setDataKey(key);
      } catch (e: any) {
        // A central reset (session restore, invalidation) cancelled the shared read while
        // this screen still needs it: ask again instead of leaving a skeleton forever.
        if (alive && e?.name === "AbortError" && aborts.current < 2) { aborts.current++; retry = true; }
        else if (alive && e?.name !== "AbortError") setError(e?.message || "Could not load. Retry.");
      } finally {
        if (alive && !retry) { setLoading(false); setRefreshing(false); }
        if (alive && retry) setTick((t) => t + 1);
      }
    })();
    return () => {
      alive = false;
      // Shared reads continue for another screen/prefetch; account resets and
      // explicit invalidation abort the shared request centrally.
    };
  }, [key, tick, persist]);

  const reload = useCallback(() => { forceNext.current = true; setTick((t) => t + 1); }, []);
  const revalidate = useCallback(() => { forceNext.current = false; setTick((t) => t + 1); }, []);
  // A key change renders before the effect runs; never flash another exam/account's data.
  const visible = key ? (dataKey === key ? data : resources.peek<T>(key)) : null;
  return { data: visible, error: dataKey === key ? error : "", loading: key ? (dataKey === key ? loading : visible === null) : false,
    refreshing: !!key && dataKey === key && refreshing, reload, revalidate, dataKey: key };
}

export const invalidate = (prefix: string) => resources.invalidate(prefix);

// Warm the in-memory cache before the user navigates (no UI state involved).
export function prefetch<T>(key: string, fetcher: (signal: AbortSignal) => Promise<T>, persist = true) { resources.prefetch(key, fetcher, persist); }
export const cancelPrefetch = (prefix: string) => resources.cancelPrefetch(prefix);
