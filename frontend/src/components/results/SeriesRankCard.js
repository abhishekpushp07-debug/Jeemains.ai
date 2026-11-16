import React, { useEffect, useState } from 'react';
import { Trophy, Clock3 } from 'lucide-react';
import { api } from '../../lib/api';

const ist = n => new Date(n * 1000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', timeStyle: 'short' }).toUpperCase() + ' IST';

// The day's All India rank: score and solutions are already open; the rank waits for the day to close.
export function SeriesRankCard({ id }) {
  const [d, setD] = useState(null);
  useEffect(() => {
    let stop = false;
    api('/attempts/' + id + '/series-rank').then(x => { if (!stop) setD(x); }).catch(() => {});
    return () => { stop = true; };
  }, [id]);
  if (!d || d.state === 'unavailable') return null;
  return <section className={'series-rank-card state-' + d.state} data-testid="series-rank-card">
    <span className="series-rank-icon">{d.state === 'ready' ? <Trophy size={26} /> : <Clock3 size={26} />}</span>
    <div>
      <span className="series-kicker">ALL INDIA RANK · TODAY’S PAPER</span>
      {d.state === 'ready' && <><h2 data-testid="series-rank-value">#{d.rank} <small>of {d.total}</small></h2><p data-testid="series-rank-top">Top {d.top_percent}% of every live attempt today.</p></>}
      {d.state === 'sealed' && <><h2 data-testid="series-rank-sealed">Your rank arrives at {ist(d.release_at)}</h2><p>Score and solutions are ready below. The rank waits until every student’s time is up, so it is fair for all.</p></>}
      {d.state === 'preparing' && <h2 data-testid="series-rank-preparing">Preparing your rank…</h2>}
    </div>
  </section>;
}
