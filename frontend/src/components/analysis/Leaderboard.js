import React, { useEffect, useState } from 'react';
import { Search, Users, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../../lib/api';
import { DisplayName } from '../DisplayName';
import { Block, mmss, pc } from './parts';

const seen = new Map();

// This paper's leaderboard, kept for a minute so the picker and the board share one request.
export function useBoard(id, q = '', tick = 0) {
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
  }, [id, q, key, tick]);
  return d;
}

function Rows({ rows, value, onPick, testId }) {
  return (
    <div className="a2-scroll"><table className="a2-table" data-testid={testId}>
      <thead><tr><th>Rank</th><th>Student</th><th>Score</th><th>Attempted</th><th>Accuracy</th><th>Time</th><th /></tr></thead>
      <tbody>{rows.map(r => (
        <tr key={r.handle} className={r.is_you ? 'you' : ''} data-testid={'a2-board-row-' + r.handle}>
          <td><b>#{r.rank}</b></td><td>{r.is_you ? <b>Aap{r.named ? ' · ' + r.name : ''}</b> : r.name}</td><td><b>{r.score}</b></td><td>{r.attempted}</td><td>{pc(r.accuracy)}</td><td>{mmss(r.time)}</td>
          <td>{!r.is_you && <button type="button" className={'a2-chipbtn' + (value === 'user:' + r.handle ? ' on' : '')} data-testid={'a2-board-compare-' + r.handle} onClick={() => onPick('user:' + r.handle)}>Compare</button>}</td>
        </tr>
      ))}</tbody>
    </table></div>
  );
}

// Top 10 (or all 50), the students around you, search by name or Rank, and Compare on every row. Names and totals only.
export function Leaderboard({ id, value, onPick }) {
  const [q, setQ] = useState('');
  const [all, setAll] = useState(false);
  const [tick, setTick] = useState(0);
  const term = q.trim();
  const d = useBoard(id, term, tick);
  if (!d || d.state !== 'ready') return null;
  const rows = term ? d.found : all ? d.rows : d.rows.slice(0, 10);
  const More = all ? ChevronUp : ChevronDown;
  return (
    <Block id="leaderboard" kicker={`${d.n} STUDENTS · HAR STUDENT KA PEHLA ATTEMPT`} title="Is paper ka leaderboard" note="Kisi bhi student par Compare dabao: aap vs woh khul jaayega. Sirf naam, Score aur totals dikhte hain; kisi ke jawab ya phone number kabhi nahi."
      action={<label className="a2-search"><Search size={14} aria-hidden="true" /><input value={q} onChange={e => setQ(e.target.value.slice(0, 20))} placeholder="Naam ya Rank" aria-label="Leaderboard mein dhoondo" data-testid="a2-board-search" /></label>}>
      {d.you && !d.you.named && (
        <div className="a2-name-ask" data-testid="a2-board-name-ask">
          <p>Leaderboard par aap abhi <b>{d.you.name}</b> dikh rahe ho. Apna naam likh do, sab aapko pehchaan lenge.</p>
          <DisplayName onSaved={() => { seen.clear(); setTick(v => v + 1); }} />
        </div>
      )}
      {rows.length ? <Rows rows={rows} value={value} onPick={onPick} testId="a2-board-top" /> : <p className="a2-empty" data-testid="a2-board-none">Is naam ya Rank ka koi student nahi mila.</p>}
      {!term && d.rows.length > 10 && <button type="button" className="a2-chipbtn a2-more-btn" aria-expanded={all} data-testid="a2-board-more" onClick={() => setAll(!all)}><More size={14} aria-hidden="true" /> {all ? 'Sirf top 10 dikhao' : `Top ${d.rows.length} dikhao`}</button>}
      {!term && d.around.length > 0 && !rows.some(r => r.is_you) && <>
        <h4 className="a2-subhead"><Users size={15} aria-hidden="true" /> Aapke aas-paas</h4>
        <Rows rows={d.around} value={value} onPick={onPick} testId="a2-board-around" />
      </>}
    </Block>
  );
}
