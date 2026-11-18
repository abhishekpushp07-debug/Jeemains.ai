// College compare: "Colleges" puts 2-3 whole colleges side by side (branches, seats, fee, easiest / toughest / CS seat);
// "Branches" compares 2-3 saved branch seats round by round. Both lists stay in this browser.
import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Trash2 } from 'lucide-react';
import { fmt, getColleges, rank, rupees } from './rankApi';
import { Chip, Err, Go, Heading, Notes, Panel, PdfButton, Switch } from './RankUi';
import { compareColleges, getJeeProfile, savedPdfBody, shortlist, toCompareItem, useRankData } from './rankStore';
import { CollegeSearch } from './TargetMarks';

export function Compare({ onTool }) {
  const [mode, setMode] = useState('colleges');
  return <>
    <Switch prefix="cmp-mode" value={mode} onChange={setMode} items={[{ key: 'colleges', label: 'College vs college' }, { key: 'branches', label: 'Saved branches' }]} />
    <div className="rk-sub" hidden={mode !== 'colleges'}><CollegesCompare /></div>
    <div className="rk-sub" hidden={mode !== 'branches'}><BranchesCompare onTool={onTool} /></div>
  </>;
}

/** Keeps up to 3 ticked ids that still exist in the list; starts with the first ones. */
function usePick(list) {
  const [pick, setPick] = useState(() => list.slice(0, 3).map(i => i.id));
  useEffect(() => { setPick(p => { const kept = p.filter(id => list.some(i => i.id === id)); return kept.length ? kept : list.slice(0, 3).map(i => i.id); }); }, [list]);
  const flip = id => setPick(p => (p.includes(id) ? p.filter(x => x !== id) : p.length >= 3 ? p : [...p, id]));
  return [pick, flip];
}

function useCompare(fn) {
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const run = async () => { setBusy(true); setError(''); try { setData(await fn()); } catch (e) { setError(e.message); } finally { setBusy(false); } };
  return { data, busy, error, run, clear: () => setData(null) };
}

const PickList = ({ list, pick, flip, onRemove, prefix }) => <ul className="rk-picklist" data-testid={prefix + '-list'}>{list.map((s, i) => <li key={s.id} className={pick.includes(s.id) ? 'is-on' : ''}>
  <button type="button" className="rk-pick" aria-pressed={pick.includes(s.id)} onClick={() => flip(s.id)} data-testid={`${prefix}-pick-${i}`}>
    <i className="rk-check" aria-hidden="true" /><span><b>{s.title}</b><small>{s.sub}</small>{s.line ? <em>{s.line}</em> : null}</span></button>
  <button type="button" className="rk-remove" onClick={() => onRemove(s.id)} aria-label={`${s.title} hatao`} data-testid={`${prefix}-remove-${i}`}><Trash2 size={16} /></button>
</li>)}</ul>;

function Table({ cols, rows, testId }) {
  return <div className="rk-table-wrap" data-testid={testId}><table className="rk-table rk-compare">
    <thead><tr><th />{cols.map((c, i) => <th key={i} data-testid={`${testId}-col-${i}`}><b>{c.missing ? 'Data nahi mila' : c.title}</b>{c.name ? <small>{c.name}</small> : null}</th>)}</tr></thead>
    <tbody>{rows.map(([label, get]) => <tr key={label}><th>{label}</th>{cols.map((c, i) => <td key={i}>{c.missing ? '—' : get(c) ?? '—'}</td>)}</tr>)}</tbody>
  </table></div>;
}

const side = s => (s ? <span className="rk-cell"><b>{s.branch}</b><small>{s.marks} marks · {s.label} {fmt(s.close)} {s.rank_label}</small></span> : null);
const fee = c => (c.fee ? <span className="rk-cell"><b>{Array.isArray(c.fee) ? (c.fee[0] === c.fee[1] ? rupees(c.fee[0]) : `${rupees(c.fee[0])} – ${rupees(c.fee[1])}`) : rupees(c.fee)}</b>{c.fee_note ? <small>{c.fee_note}</small> : null}</span> : null);
const COLLEGE_ROWS = [
  ['Kahan', c => c.place], ['Type', c => c.kind], ['Branches', c => c.branches], ['Seats', c => (c.seats ? <span className="rk-cell"><b>{fmt(c.seats)}</b><small>{c.seats_label}</small></span> : null)],
  ['Fee / saal', fee], ['Sabse aasaan branch', c => side(c.easiest)], ['Sabse mushkil branch', c => side(c.toughest)],
  ['Computer Science', c => (c.cs ? <span className="rk-cell"><b>{c.cs.marks} marks</b><small>{c.cs.branch}{c.cs_count > 1 ? ` · ${c.cs_count} CS seats` : ''}</small></span> : 'CS branch nahi')],
];
const BRANCH_ROWS = [
  ['Kahan', c => c.place], ['Branch', c => c.sub], ['Seat raasta', c => c.path],
  ['Final closing', c => (c.final ? <span className="rk-cell"><b>{fmt(c.final.close)}</b><small>{c.final.label}{c.rank_label ? ` · ${c.rank_label}` : ''}</small></span> : null)],
  ['Round by round', c => (c.rounds?.length ? <span className="rk-cell rounds">{c.rounds.map(r => <small key={r.label}>{r.label}: <b>{r.close ? fmt(r.close) : '—'}</b></small>)}</span> : null)],
  ['Pichhla saal', c => (c.prev ? `${c.prev.label}: ${c.prev.close ? fmt(c.prev.close) : '—'}` : null)],
  ['Seats', c => (c.seats ? `${fmt(c.seats)}${c.seats_label ? ` · ${c.seats_label}` : ''}` : null)], ['Fee / saal', fee],
];

const EXAMS = [['jee', 'JEE Main'], ['comedk', 'COMEDK'], ['bitsat', 'BITSAT']];
function CollegesCompare() {
  const { data: cols } = useRankData(getColleges);
  const list = compareColleges.useList();
  const [exam, setExam] = useState('jee');
  const [pick, flip] = usePick(list);
  const items = useMemo(() => {
    if (!cols) return [];
    if (exam === 'jee') return cols.jee.map(c => ({ key: 'j' + c.inst, cid: String(c.inst), ...c }));
    if (exam === 'comedk') return cols.comedk.map(c => ({ key: 'c' + c.code, cid: c.code, ...c }));
    return cols.bitsat.map(c => ({ key: 'b' + c.campus, cid: c.campus, short: c.name, name: `${c.programs} programs`, city: c.campus }));
  }, [cols, exam]);
  const add = c => { const id = `${exam}-${c.cid}`; if (!list.some(x => x.id === id)) compareColleges.toggle({ id, exam, cid: c.cid, title: c.short, sub: `${EXAMS.find(e => e[0] === exam)[1]} · ${c.name}` }); };
  const chosen = list.filter(s => pick.includes(s.id));
  const cmp = useCompare(() => rank.compareColleges(chosen.map(s => ({ exam: s.exam, id: s.cid })), getJeeProfile()));
  return <div className="rk-stack">
    <Panel form title="College jodo" testId="cmp-col-input">
      <div className="rk-chips">{EXAMS.map(([k, l]) => <Chip key={k} on={exam === k} onClick={() => setExam(k)} testId={`cmp-col-exam-${k}`}>{l}</Chip>)}</div>
      <CollegeSearch items={items} onPick={add} testId="cmp-col-search" />
    </Panel>
    {list.length ? <>
      <Heading title={`${list.length} college list mein`} sub="2 ya 3 par tick karo, phir Compare dabao." />
      <PickList list={list} pick={pick} flip={flip} onRemove={id => { compareColleges.remove(id); cmp.clear(); }} prefix="cmp-col" />
      <Go label={chosen.length < 2 ? '2 ya 3 college chuno' : `${chosen.length} college compare karo`} busy={cmp.busy} onClick={() => chosen.length >= 2 && cmp.run()} testId="cmp-col-run" />
    </> : <p className="rk-empty" data-testid="cmp-col-empty">Upar se 2–3 college jodo. JEE college ke marks aapki category aur state ke hisaab se aate hain (College predictor ya Target marks mein jo chuna).</p>}
    <Err error={cmp.error} retry={cmp.run} testId="cmp-col-error" />
    {cmp.data ? <div className="rk-stack rk-reveal"><Table cols={cmp.data.items} rows={COLLEGE_ROWS} testId="cmp-col-table" /><Notes lines={cmp.data.notes} testId="cmp-col-notes" /></div> : null}
  </div>;
}

function BranchesCompare({ onTool }) {
  const list = shortlist.useList();
  const [pick, flip] = usePick(list);
  const chosen = list.filter(s => pick.includes(s.id));
  const cmp = useCompare(() => rank.compare(chosen.map(toCompareItem)));
  if (!list.length) return <div className="rk-empty" data-testid="cmp-br-empty"><p>Abhi koi branch save nahi. College predictor ya Target marks mein kisi bhi card par <b>Add to Compare</b> dabao.</p>
    <button type="button" className="rk-outline" onClick={() => onTool('college')} data-testid="cmp-br-go">College predictor kholo<ArrowRight size={18} /></button></div>;
  return <div className="rk-stack">
    <Heading title={`${list.length} saved branches`} sub="2 ya 3 par tick karo, phir Compare dabao." />
    <PickList list={list} pick={pick} flip={flip} onRemove={id => { shortlist.remove(id); cmp.clear(); }} prefix="cmp-br" />
    <Go label={chosen.length < 2 ? '2 ya 3 branch chuno' : `${chosen.length} branch compare karo`} busy={cmp.busy} onClick={() => chosen.length >= 2 && cmp.run()} testId="cmp-br-run" />
    <Err error={cmp.error} retry={cmp.run} testId="cmp-br-error" />
    {cmp.data ? <div className="rk-stack rk-reveal"><Table cols={cmp.data.items} rows={BRANCH_ROWS} testId="cmp-br-table" /><Notes lines={cmp.data.notes} testId="cmp-br-notes" /></div> : null}
    <div className="rk-actions"><PdfButton path="/saved" body={savedPdfBody(list, pick)} filename={`JEELIVE-saved-colleges-${list.length}.pdf`} label="Saari list ka PDF" testId="cmp-br-pdf" /></div>
  </div>;
}
