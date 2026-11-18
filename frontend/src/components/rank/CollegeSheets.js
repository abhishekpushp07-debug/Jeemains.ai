// College detail sheets: the tapped branch's closing rank in every round as a ladder, then branches x rounds,
// seat-path switches (JEE) and the official pages.
import React, { useEffect, useState } from 'react';
import { ExternalLink, Loader2 } from 'lucide-react';
import { fmtRange, KIND, rank, rupees } from './rankApi';
import { Chip, Err, RankSheet, RoundLadder, RoundTable } from './RankUi';

export const ladderLine = (name, rounds, cells) => {
  const i = cells.findIndex(c => c.in);
  return i < 0 ? `${name}: 2026 ke kisi round mein aapki rank andar nahi aayi.` : `${name}: ${rounds[i]} se aapki rank andar aati hai.`;
};
const Loading = ({ testId }) => <div className="rk-loading" data-testid={testId}><Loader2 className="spin" size={22} /></div>;
const Official = ({ href, label, testId }) => <a className="rk-official" href={href} target="_blank" rel="noopener noreferrer" data-testid={testId}>{label}<ExternalLink size={14} /></a>;

export function JeeCollegeSheet({ req, onClose }) {
  const [path, setPath] = useState({ quota: req.quota, gender: req.gender, seat: req.seat });
  const [all, setAll] = useState(false), [pick, setPick] = useState(req.prog ?? null);
  const [data, setData] = useState(null), [error, setError] = useState(''), [tries, setTries] = useState(0);
  useEffect(() => {
    let live = true;
    setError('');
    rank.college({ ...req, ...path, all }).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [req, path, all, tries]);
  const chosen = data?.rows.find(r => r.prog === pick) ?? null;
  return <RankSheet open onClose={onClose} title={data?.college.short ?? 'College'} sub={data ? `${data.college.name} · ${data.college.city}, ${data.college.state}` : null} testId="cp-college">
    {!data && !error ? <Loading testId="cp-college-loading" /> : null}
    <Err error={error} retry={() => setTries(t => t + 1)} testId="cp-college-error" />
    {data ? <>
      <div className="rk-sheet-meta"><span className={'rk-tag kind-' + data.college.type}>{KIND[data.college.type]}</span>
        <b data-testid="cp-college-yourrank">Aapki {data.your_rank.label}: {fmtRange(data.your_rank.range)}</b></div>
      <div className="rk-chips">{data.options.quota.map(q => <Chip key={q.key} on={data.path.quota === q.key} onClick={() => setPath(p => ({ ...p, quota: q.key }))} testId={`cp-college-quota-${q.key}`}>{q.label}</Chip>)}</div>
      {data.options.gender.length > 1 || data.options.seat.length > 1 ? <div className="rk-chips">
        {data.options.gender.length > 1 ? data.options.gender.map(g => <Chip key={g} on={data.path.gender === g} onClick={() => setPath(p => ({ ...p, gender: g }))} testId={`cp-college-gender-${g}`}>{g === 'F' ? 'Female-only' : 'Gender-neutral'}</Chip>) : null}
        {data.options.seat.length > 1 ? data.options.seat.map(s => <Chip key={s} on={data.path.seat === s} onClick={() => setPath(p => ({ ...p, seat: s }))} testId={`cp-college-seat-${s}`}>{s === 'open' ? 'Open' : data.options.cat_label ?? 'Category'}</Chip>) : null}
      </div> : null}
      {data.line ? <p className={'rk-line' + (data.blocked ? ' is-bad' : '')} data-testid="cp-college-line">{chosen && !data.blocked ? ladderLine(chosen.branch, data.rounds, chosen.cells) : data.line}</p> : null}
      {chosen ? <RoundLadder testId="cp-college-ladder" title={`${chosen.branch}${chosen.degree ? ` (${chosen.degree})` : ''}`} rounds={data.rounds} cells={chosen.cells}
        quiet={!!data.blocked} prev={data.y25_label ? { label: data.y25_label, close: chosen.y25 } : null} /> : null}
      {data.rows.length === 0 ? <p className="rk-dim">Is raaste par 2026 mein koi seat nahi thi.</p>
        : <RoundTable prefix="cp-college" rounds={data.rounds} prevLabel={data.y25_label} pick={pick} onPick={setPick}
          rows={data.rows.map(r => ({ key: r.prog, name: `${r.branch}${r.degree ? ` (${r.degree})` : ''}`, cells: r.cells, prev: r.y25 }))} />}
      <small className="rk-dim">Kisi bhi branch par tap karo, uska har round upar dikhega. Hara = aapki poori rank range andar, peela = range ka sirf kuch hissa. {data.official_csab ? 'CSAB rounds mein CRL dekhi jaati hai.' : 'Upgrade aur Spot round ki rank JAC ne publish nahi ki.'}</small>
      {!all && data.total > data.rows.length ? <button type="button" className="rk-outline" onClick={() => setAll(true)} data-testid="cp-college-all">Saari branches dikhao ({data.total})</button> : null}
      <div className="rk-officials"><Official href={data.official} label={`Official page (${data.official_csab ? 'JoSAA' : 'JAC Delhi'})`} testId="cp-college-official" />
        {data.official_csab ? <Official href={data.official_csab} label="CSAB Special official page" testId="cp-college-official-csab" /> : null}</div>
    </> : null}
  </RankSheet>;
}

export function ComedkCollegeSheet({ req, onClose }) {
  const [all, setAll] = useState(false), [pick, setPick] = useState(req.course ?? null);
  const [data, setData] = useState(null), [error, setError] = useState(''), [tries, setTries] = useState(0);
  useEffect(() => {
    let live = true;
    setError('');
    rank.comedkCollege({ ...req, all }).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [req, all, tries]);
  const chosen = data?.rows.find(r => r.cc === pick) ?? null;
  return <RankSheet open onClose={onClose} title={data?.college.short ?? 'College'} sub={data ? `${data.college.name} · ${data.college.city}` : null} testId="ck-college">
    {!data && !error ? <Loading testId="ck-college-loading" /> : null}
    <Err error={error} retry={() => setTries(t => t + 1)} testId="ck-college-error" />
    {data ? <>
      <div className="rk-sheet-meta">{data.college.blr ? <span className="rk-tag kind-NIT">Bengaluru</span> : null}<b data-testid="ck-college-yourrank">Aapki {data.your_rank.label}: {fmtRange(data.your_rank.range)}</b></div>
      <p className="rk-line" data-testid="ck-college-line">{chosen ? ladderLine(chosen.course, data.rounds, chosen.cells) : data.line}</p>
      {chosen ? <>
        <RoundLadder testId="ck-college-ladder" title={chosen.course} sub={[chosen.seats ? `${chosen.seats} seats` : null, chosen.fee ? `Fee ${rupees(chosen.fee)} / saal` : null].filter(Boolean).join(' · ')}
          rounds={data.rounds} cells={chosen.cells} prev={data.y25_label ? { label: data.y25_label, close: chosen.y25 } : null} />
      </> : null}
      <RoundTable prefix="ck-college" rounds={data.rounds} prevLabel={data.y25_label} pick={pick} onPick={setPick}
        rows={data.rows.map(r => ({ key: r.cc, name: r.course, cells: r.cells, prev: r.y25 }))} />
      <small className="rk-dim">Kisi bhi course par tap karo, uska har round upar dikhega. Rank GM (general merit) ki hai.</small>
      {!all && data.total > data.rows.length ? <button type="button" className="rk-outline" onClick={() => setAll(true)} data-testid="ck-college-all">Saare courses dikhao ({data.total})</button> : null}
      <div className="rk-officials"><Official href={data.official} label="COMEDK official page" testId="ck-college-official" /></div>
    </> : null}
  </RankSheet>;
}
