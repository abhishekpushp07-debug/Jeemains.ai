import { useCallback, useMemo, useState } from "react";
import { useCached } from "@/src/useCached";

type Page<T> = { items: T[]; pages?: number };
/** A list that arrives a page at a time: the first page paints at once from the phone's copy and is checked again,
 *  "Aur dikhao" adds the next one. Later pages belong to the first page they followed: a fresh first page drops them. */
export function usePaged<T, P extends Page<T> = Page<T>>(key: string | null, load: (page: number, signal?: AbortSignal) => Promise<P>) {
  const first = useCached<P>(key, signal => load(1, signal));
  const [extra, setExtra] = useState<{ base: P | null; items: T[]; page: number }>({ base: null, items: [], page: 1 });
  const [busy, setBusy] = useState(false);
  const [moreError, setMoreError] = useState("");
  const base = first.data;
  const mine = !!base && extra.base === base;
  const page = mine ? extra.page : 1;
  const items = useMemo<T[]>(() => (base ? [...(base.items || []), ...(mine ? extra.items : [])] : []), [base, mine, extra.items]);
  const more = useCallback(async () => {
    if (!base || busy) return;
    setBusy(true); setMoreError("");
    try {
      const next = await load(page + 1);
      setExtra(old => ({ base, items: [...(old.base === base ? old.items : []), ...(next.items || [])], page: page + 1 }));
    } catch (e: any) { setMoreError(e?.message || "Load nahi hua. Dobara try karo."); }
    finally { setBusy(false); }
  }, [base, busy, page, load]);
  return { first: base, items, hasMore: page < (base?.pages || 1), more, busy, moreError, error: first.error, loading: first.loading, refreshing: first.refreshing, reload: first.reload, revalidate: first.revalidate };
}
