import { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { flushLeftover } from '../../lib/timeCapture';

// One request opens the whole analysis. The last one opened stays readable without internet.
export function useAnalysis(id, userId, scoreVersion, enabled, compare, vs) {
  const [state, setState] = useState({ data: null, error: '', loading: false, offline: false });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!enabled) return undefined;
    let stop = false, timer, tries = 0;
    const key = `tejas-analysis-last-${userId}`;
    const load = async () => {
      setState(s => ({ ...s, loading: true, error: '' }));
      try {
        if (!tries) await flushLeftover(userId, id);
        const q = new URLSearchParams({ mode: compare ? 'comparative' : 'personal', compare: vs, score_version: scoreVersion });
        const data = await api(`/attempts/${id}/analysis?${q}`);
        if (stop) return;
        setState({ data, error: '', loading: false, offline: false });
        if (!compare && scoreVersion === 'original') try { localStorage.setItem(key, JSON.stringify({ id, data })); } catch {}
        if (data.class?.state === 'preparing' && ++tries < 6) timer = setTimeout(load, 2500);
      } catch (e) {
        if (stop) return;
        let saved = null;
        try { const x = JSON.parse(localStorage.getItem(key) || 'null'); if (x?.id === id) saved = x.data; } catch {}
        setState(s => (saved && !e.status ? { data: s.data || saved, error: '', loading: false, offline: true } : { ...s, loading: false, error: e.message }));
      }
    };
    load();
    return () => { stop = true; clearTimeout(timer); };
  }, [id, userId, scoreVersion, enabled, compare, vs, tick]);
  return { ...state, reload: () => setTick(v => v + 1) };
}
