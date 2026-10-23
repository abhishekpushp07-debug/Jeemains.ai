import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

// Live peer statistics and pre-generated AI solutions for one completed attempt.
export function useResultExtras(id, enabled, suppliedOnly = false) {
  const [cohort, setCohort] = useState(null);
  const [solutions, setSolutions] = useState(null);
  useEffect(() => {
    if (!enabled) return undefined;
    let stop = false, timer, tries = 0;
    const loadCohort = async () => {
      try {
        const c = await api('/attempts/' + id + '/cohort');
        if (stop) return;
        setCohort(c);
        if (c.state === 'preparing' && ++tries < 8) timer = setTimeout(loadCohort, 2500);
      } catch (e) { if (!stop) setCohort({ state: 'error', reason: e.message }); }
    };
    loadCohort();
    if (suppliedOnly) {
      setSolutions({ items: [], ready: 0, total: 0 });
    } else {
      api('/attempts/' + id + '/ai-solutions').then((d) => { if (!stop) setSolutions(d); }).catch(() => { if (!stop) setSolutions({ items: [], ready: 0, total: 0 }); });
    }
    return () => { stop = true; clearTimeout(timer); };
  }, [id, enabled, suppliedOnly]);
  const peer = {};
  (cohort?.questions || []).forEach((q) => { peer[q.id] = q; });
  const ai = {};
  (solutions?.items || []).forEach((x) => { ai[x.question_id] = x; });
  return { cohort, solutions, peer, ai };
}
