import React, { useEffect, useState } from 'react';
import { Search, Users } from 'lucide-react';
import { api } from '../../lib/api';
import { Block, mmss, pc } from './parts';

const seen = new Map();

// This paper's leaderboard, kept for a minute so the picker and the board share one request.
export function useBoard(id, q = '') {
  const key = id + '|' + q;
  const [d, setD] = useState(() => seen.get(key)?.d || null);
  useEffect(() => {
    const hit = seen.get(key);
    if (hit && Date.now() - hit.at < 60000) { setD(hit.d); return undefined; }
    let live = true;
    const t = setTimeout(() => api(`/attempts/${id}/leaderboard${q ? '?q=' + encodeURIComponent(q) : ''}`)
      .then(x => { seen.set(key, { d: x, at: Date.now() }); if (live) setD(x); })
      .catch(() => live && setD({ state: 'error', rows: [], around: [], found: [] })), q ? 350 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [id, q, key]);
  return d;
}

function Rows({ rows, value, onPick, testId }) {
  return (
    <div className="a2-scroll"><table className="a2-table" data-testid={testId}>
      <thead><tr><th>Rank</th><th>Student</th><th>Score</th><th>Attempted</th><th>Accuracy</th><th>Time</th><th /></tr></thead>
      <tbody>{rows.map(r => (
        <tr key={r.handle} className={r.is_you ? 'you' : ''} data-testid={'a2-board-row-' + r.handle}>
          <td><b>#{r.rank}</b></td><td>{r.is_you ? <b>Aap</b> : r.name}</td><td><b>{r.score}</b></td><td>{r.attempted}</td><td>{pc(r.accuracy)}</td><td>{mmss(r.time)}</td>
          <td>{!r.is_you && <button type="button" className={'a2-chipbtn' + (value === 'user:' + r.handle ? ' on' : '')} data-testid={'a2-board-compare-' + r.handle} onClick={() => onPick('user:' + r.handle)}>Compare</button>}</td>
        </tr>
      ))}</tbody>
    </table></div>
  );
}

export function Leaderboard({ id, value, onPick }) {
  const [q, setQ] = useState('');
  const d = useBoard(id, q.trim());
  if (!d || d.state !== 'ready') return null;
  const rows = q.trim() ? d.found : d.rows.slice(0, 10);
  return (
    <Block id="leaderboard" kicker={`${d.n} STUDENTS`} title="Is paper ka leaderboard" note="Kisi bhi student se Compare karo. Sirf naam, Score aur totals dikhte hain; kisi ke jawab kabhi nahi."
      action={<label className="a2-search"><Search size={14} aria-hidden="true" /><input value={q} onChange={e => setQ(e.target.value.slice(0, 20))} placeholder="Naam ya Rank" aria-label="Leaderboard mein dhoondo" data-testid="a2-board-search" /></label>}>
      {rows.length ? <Rows rows={rows} value={value} onPick={onPick} testId="a2-board-top" /> : <p className="a2-empty" data-testid="a2-board-none">Is naam ya Rank ka koi student nahi mila.</p>}
      {!q.trim() && d.around.length > 0 && !d.rows.slice(0, 10).some(r => r.is_you) && <>
        <h4 className="a2-subhead"><Users size={15} aria-hidden="true" /> Aapke aas-paas</h4>
        <Rows rows={d.around} value={value} onPick={onPick} testId="a2-board-around" />
      </>}
    </Block>
  );
}
