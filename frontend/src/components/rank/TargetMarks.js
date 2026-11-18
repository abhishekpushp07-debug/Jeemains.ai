// Target marks: pick a college -> how many marks each branch needs (2026 final closing; tough / normal / easy paper for JEE),
// round by round. JEE uses the student's category, gender, PwD and home state; COMEDK is GM; BITSAT shows cutoff and a safe score.
import React, { useEffect, useMemo, useState } from 'react';
import { Search, X } from 'lucide-react';
import { CATEGORY_LABEL, CATS, fmt, getColleges, getMeta, LEVEL, LEVELS, rank, rupees } from './rankApi';
import { CardActions, Chip, Err, Heading, Kind, Notes, Panel, PdfButton, StateSelect, Switch } from './RankUi';
import { bitsatDream, bitsatRowSaved, comedkRowDream, comedkRowSaved, getJeeProfile, jeeRowDream, jeeRowSaved, setJeeProfile, shortlist, useDreamToggle, useRankData } from './rankStore';

export function TargetMarks() {
  const [exam, setExam] = useState('jee');
  return <>
    <Switch prefix="tm-exam" value={exam} onChange={setExam} items={[{ key: 'jee', label: 'JEE Main' }, { key: 'comedk', label: 'COMEDK' }, { key: 'bitsat', label: 'BITSAT' }]} />
    <div className="rk-sub" hidden={exam !== 'jee'}><JeeTarget /></div>
    <div className="rk-sub" hidden={exam !== 'comedk'}><ComedkTarget /></div>
    <div className="rk-sub" hidden={exam !== 'bitsat'}><BitsatTarget /></div>
  </>;
}

/** Every typed word must match the college's short name, full name, city or a common alias; up to 20 matches. */
const ALIAS = { rvce: 'r v college', msrit: 'ramaiah', bmsce: 'b m s college', bmsit: 'b m s institute', dsce: 'dayananda sagar college', pesu: 'pes university', nmit: 'nitte meenakshi',
  nitk: 'surathkal', trichy: 'tiruchirappalli', mnnit: 'allahabad', vnit: 'nagpur', mnit: 'jaipur', manit: 'bhopal', svnit: 'surat', dtu: 'delhi technological', nsut: 'netaji subhas', iiitd: 'indraprastha' };
const squash = t => t.toLowerCase().replace(/[.\-,()]/g, ' ').replace(/\s+/g, ' ');
export function CollegeSearch({ items, onPick, testId, placeholder = 'College ka naam ya shehar (jaise NIT Trichy, Surathkal)' }) {
  const [q, setQ] = useState('');
  const index = useMemo(() => items.map(c => { const hay = squash(`${c.short} ${c.name} ${c.city || ''} ${c.state || ''}`); return [c, hay, hay.replace(/ /g, '')]; }), [items]);
  const hits = useMemo(() => {
    const words = squash(q).trim().split(' ').filter(Boolean);
    if (!words.length) return [];
    const ok = (hay, flat, w) => hay.includes(w) || flat.includes(w) || (ALIAS[w] && hay.includes(ALIAS[w]));
    return index.filter(([, hay, flat]) => words.every(w => ok(hay, flat, w))).slice(0, 20).map(([c]) => c);
  }, [q, index]);
  return <div className="rk-search" data-testid={testId}>
    <label className="rk-search-box"><Search size={18} /><input value={q} onChange={e => setQ(e.target.value)} placeholder={placeholder} aria-label="College dhoondo" data-testid={testId + '-input'} />
      {q ? <button type="button" onClick={() => setQ('')} aria-label="Clear" data-testid={testId + '-clear'}><X size={16} /></button> : null}</label>
    {hits.length ? <ul className="rk-search-list" role="listbox">{hits.map((c, i) => <li key={c.key}><button type="button" onClick={() => { onPick(c); setQ(''); }} data-testid={`${testId}-hit-${i}`}>
      <b>{c.short}</b><small>{c.name}{c.city ? ` · ${c.city}` : ''}</small>{c.type ? <Kind kind={c.type} /> : null}</button></li>)}</ul>
      : q.trim() ? <p className="rk-dim" data-testid={testId + '-empty'}>Is naam se koi college nahi mila.</p> : null}
  </div>;
}

const Chosen = ({ c, onClear, testId }) => <div className="rk-chosen" data-testid={testId}><div><b>{c.short}</b><small>{c.name}{c.city ? ` · ${c.city}` : ''}</small></div>
  <button type="button" className="rk-ghost" onClick={onClear} data-testid={testId + '-change'}>Badlo</button></div>;

function useTarget(load, key) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [tries, setTries] = useState(0);
  useEffect(() => {
    if (!key) return;
    let live = true;
    setData(null); setError('');
    load().then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [key, tries]); // eslint-disable-line react-hooks/exhaustive-deps
  return { data, error, retry: () => setTries(t => t + 1) };
}

function JeeTarget() {
  const { data: cols } = useRankData(getColleges);
  const { data: meta } = useRankData(getMeta);
  const [college, setCollege] = useState(null);
  const [profile, setProfile] = useState(getJeeProfile);
  const items = useMemo(() => (cols?.jee || []).map(c => ({ ...c, key: 'j' + c.inst })), [cols]);
  const key = college ? JSON.stringify([college.inst, profile]) : null;
  const t = useTarget(() => rank.targetJee({ inst: college.inst, ...profile }), key);
  const patch = p => setProfile(old => { const next = { ...old, ...p }; setJeeProfile(next); return next; });
  return <div className="rk-stack">
    <Panel form title="College chuno" testId="tm-jee-input">
      {college ? <Chosen c={college} onClear={() => setCollege(null)} testId="tm-jee-chosen" /> : <CollegeSearch items={items} onPick={setCollege} testId="tm-jee-search" />}
      <div className="rk-chips">{CATS.map(c => <Chip key={c} on={profile.category === c} onClick={() => patch({ category: c })} testId={`tm-cat-${c}`}>{CATEGORY_LABEL[c]}</Chip>)}</div>
      <div className="rk-chips"><Chip on={profile.female} onClick={() => patch({ female: !profile.female })} testId="tm-female">Female</Chip><Chip on={profile.pwd} onClick={() => patch({ pwd: !profile.pwd })} testId="tm-pwd">PwD</Chip></div>
      <StateSelect states={meta?.states || []} value={profile.state} onChange={state => patch({ state })} testId="tm-state" />
    </Panel>
    {!college ? <p className="rk-dim" data-testid="tm-jee-empty">NIT, IIIT, GFTI ya Delhi (DTU / NSUT / IIIT-D) ka koi bhi college chuno.</p> : null}
    <Err error={t.error} retry={t.retry} testId="tm-jee-error" />
    {college && !t.data && !t.error ? <div className="rk-loading" data-testid="tm-jee-loading" /> : null}
    {t.data ? <div className="rk-stack rk-reveal">
      <Heading title={`${t.data.college.short}: kitne marks chahiye`} sub={`${t.data.rows.length} branches · aapke liye sabse aasaan seat raasta`} />
      <div className="rk-list" data-testid="tm-jee-rows">{t.data.rows.map((r, i) => <JeeRow key={`${r.prog}-${r.path}`} college={t.data.college.short} r={r} testId={`tm-jee-row-${i}`} />)}</div>
      <div className="rk-actions"><PdfButton path="/target/jee" body={{ inst: college.inst, ...profile }} filename={`JEELIVE-target-${t.data.college.short}.pdf`} testId="tm-jee-pdf" />
        <a className="rk-ghost" href={t.data.official} target="_blank" rel="noopener noreferrer" data-testid="tm-jee-official">Official page</a></div>
      <Notes lines={t.data.notes} testId="tm-jee-notes" />
    </div> : null}
  </div>;
}

function Rounds({ cells, render, testId }) {
  const [open, setOpen] = useState(false);
  return <>
    <button type="button" className="rk-link" onClick={() => setOpen(o => !o)} aria-expanded={open} data-testid={testId + '-toggle'}>{open ? 'Rounds chhupao' : 'Har round ka target dekho'}</button>
    {open ? <div className="rk-table-wrap" data-testid={testId}><table className="rk-table"><thead><tr><th>Round</th><th>Closing</th><th>Marks</th></tr></thead>
      <tbody>{cells.map(c => <tr key={c.label}><th>{c.label}</th><td>{c.close ? fmt(c.close) : c.unpublished ? 'publish nahi' : '—'}</td><td>{render(c)}</td></tr>)}</tbody></table></div> : null}
  </>;
}

function JeeRow({ college, r, testId }) {
  const list = shortlist.useList();
  const saved = jeeRowSaved(college, r);
  const dream = useDreamToggle(`jee-${r.prog}`, async () => jeeRowDream(college, r));
  return <article className="rk-target" data-testid={testId}>
    <header><div><b>{r.branch}{r.degree ? ` (${r.degree})` : ''}</b><small>{r.path} · {r.rank_type}</small></div>
      <span className="rk-target-close"><small>{r.final.label} closing</small><b data-testid={testId + '-close'}>{fmt(r.final.close)}</b></span></header>
    <div className="rk-marks3">{LEVELS.map(l => <div key={l} className={l === 'normal' ? 'is-main' : ''} data-testid={`${testId}-${l}`}><span className={'rk-tag lvl-' + l}>{LEVEL[l]}</span><b>{r.final.marks[l]}</b><small>/ 300</small></div>)}</div>
    <p className="rk-target-meta">~{r.final.pct} percentile{r.seats ? ` · ${r.seats} seats` : ''}{r.y25 ? ` · 2025 final ${fmt(r.y25)}` : ''}</p>
    <Rounds cells={r.cells} testId={testId + '-rounds'} render={c => (c.marks ? `${c.marks.normal} (${c.marks.easy}–${c.marks.tough})` : '—')} />
    <CardActions testId={testId} compared={list.some(x => x.id === saved.id)} onCompare={() => shortlist.toggle(saved)} dream={dream} />
  </article>;
}

function ComedkTarget() {
  const { data: cols } = useRankData(getColleges);
  const [college, setCollege] = useState(null);
  const items = useMemo(() => (cols?.comedk || []).map(c => ({ ...c, key: 'c' + c.code })), [cols]);
  const t = useTarget(() => rank.targetComedk(college.code), college?.code);
  return <div className="rk-stack">
    <Panel form title="COMEDK college chuno" testId="tm-ck-input">
      {college ? <Chosen c={college} onClear={() => setCollege(null)} testId="tm-ck-chosen" /> : <CollegeSearch items={items} onPick={setCollege} testId="tm-ck-search" placeholder="College ka naam ya shehar (jaise RVCE, Bengaluru)" />}
    </Panel>
    <Err error={t.error} retry={t.retry} testId="tm-ck-error" />
    {college && !t.data && !t.error ? <div className="rk-loading" /> : null}
    {t.data ? <div className="rk-stack rk-reveal">
      <Heading title={`${t.data.college.short}: kitne marks chahiye`} sub={`${t.data.rows.length} courses · GM rank, 180 marks mein`} />
      <div className="rk-list" data-testid="tm-ck-rows">{t.data.rows.map((r, i) => <ComedkRow key={r.cc} code={college.code} college={t.data.college.short} r={r} testId={`tm-ck-row-${i}`} />)}</div>
      <div className="rk-actions"><PdfButton path="/target/comedk" body={{ code: college.code }} filename={`JEELIVE-target-${t.data.college.short}.pdf`} testId="tm-ck-pdf" /></div>
      <Notes lines={t.data.notes} testId="tm-ck-notes" />
    </div> : null}
  </div>;
}

function ComedkRow({ code, college, r, testId }) {
  const list = shortlist.useList();
  const saved = comedkRowSaved(code, college, r);
  const dream = useDreamToggle(`comedk-${code}|${r.cc}`, async () => comedkRowDream(code, college, r));
  return <article className="rk-target" data-testid={testId}>
    <header><div><b>{r.course}</b><small>{[r.fee ? `Fee ${rupees(r.fee)} / saal` : null, r.seats ? `${r.seats} seats` : null].filter(Boolean).join(' · ') || 'COMEDK 2026'}</small></div>
      <span className="rk-target-close"><small>{r.final.label} closing</small><b data-testid={testId + '-close'}>{fmt(r.final.close)}</b></span></header>
    <div className="rk-marks1"><b data-testid={testId + '-mid'}>{r.final.mid}</b><small>/ 180 marks chahiye</small><em>range {Math.min(...r.final.marks)}–{Math.max(...r.final.marks)}</em></div>
    {r.y25 ? <p className="rk-target-meta">2025 final closing {fmt(r.y25)}</p> : null}
    <Rounds cells={r.cells} testId={testId + '-rounds'} render={c => (c.mid != null ? `${c.mid}` : '—')} />
    <CardActions testId={testId} compared={list.some(x => x.id === saved.id)} onCompare={() => shortlist.toggle(saved)} dream={dream} />
  </article>;
}

const CAMPUS = [['all', 'Saare campus'], ['Pilani', 'Pilani'], ['Goa', 'Goa'], ['Hyderabad', 'Hyderabad']];
function BitsatTarget() {
  const [campus, setCampus] = useState('all');
  const t = useTarget(() => rank.targetBitsat(), 'bitsat');
  const rows = (t.data?.rows || []).filter(r => campus === 'all' || r.campus === campus);
  return <div className="rk-stack">
    <Panel form title="Campus chuno" testId="tm-bt-input"><div className="rk-chips">{CAMPUS.map(([k, l]) => <Chip key={k} on={campus === k} onClick={() => setCampus(k)} testId={`tm-bt-campus-${k}`}>{l}</Chip>)}</div></Panel>
    <Err error={t.error} retry={t.retry} testId="tm-bt-error" />
    {t.data ? <div className="rk-stack rk-reveal">
      <Heading title={`${rows.length} programs: kitne marks chahiye`} sub={t.data.source} />
      <div className="rk-list" data-testid="tm-bt-rows">{rows.map((r, i) => <BitsatRow key={r.id} r={r} years={t.data.years} testId={`tm-bt-row-${i}`} />)}</div>
      <div className="rk-actions"><PdfButton path="/target/bitsat" body={{ campus }} filename={`JEELIVE-target-BITSAT-${campus}.pdf`} testId="tm-bt-pdf" /></div>
      <Notes lines={t.data.notes} testId="tm-bt-notes" />
    </div> : !t.error ? <div className="rk-loading" /> : null}
  </div>;
}

function BitsatRow({ r, years, testId }) {
  const list = shortlist.useList();
  const saved = bitsatRowSaved(r);
  const dream = useDreamToggle(`bitsat-${r.id}`, async () => bitsatDream(r));
  return <article className="rk-target" data-testid={testId}>
    <header><div><b>{r.program}</b><small>{r.college}</small></div><span className="rk-target-close"><small>Cutoff 2026</small><b data-testid={testId + '-cutoff'}>{r.cutoff}</b></span></header>
    <div className="rk-marks1"><b>{r.safe}</b><small>/ 390 safe score</small><em>{years.map((y, i) => `${y}: ${r.history[i] ?? '—'}`).join(' · ')}</em></div>
    <CardActions testId={testId} compared={list.some(x => x.id === saved.id)} onCompare={() => shortlist.toggle(saved)} dream={dream} />
  </article>;
}
