// COMEDK college predictor: marks or rank (+ course groups) -> expected rank and every Karnataka seat in reach, Bengaluru or not.
import React, { useEffect, useState } from 'react';
import { ESTIMATE, fmt, fmtRange, getMeta, invite, rank } from './rankApi';
import { BranchPicker, CollegeCard, Err, Field, Go, Heading, Notes, Pager, Panel, PdfButton, Problem, RankCard, Summary, Switch, Tag, TapHint, trendStat, useCardViews, WaButton } from './RankUi';
import { comedkDream, comedkSaved, shortlist, useDreamToggle, useRankData } from './rankStore';
import { ComedkCollegeSheet } from './CollegeSheets';
import { useShareLink } from '../mission/missionApi';

const SAVED = 'rank.comedk.v1';
const DEF = { mode: 'marks', marks: '', rank: '', branches: [] };
const AREAS = [['all', 'All'], ['blr', 'Bengaluru'], ['other', 'Baaki Karnataka']];
const load = () => { try { return { ...DEF, ...JSON.parse(localStorage.getItem(SAVED) || '{}') }; } catch { return DEF; } };
function toBody(f) {
  const raw = String(f.mode === 'marks' ? f.marks : f.rank).trim(), n = Number(raw);
  if (!raw) return f.mode === 'marks' ? 'Marks daalo.' : 'Rank daalo.';
  if (f.mode === 'marks') return Number.isInteger(n) && n >= 0 && n <= 180 ? { marks: n, branches: f.branches } : 'Marks 0 se 180 ke beech daalo.';
  return Number.isInteger(n) && n >= 1 && n <= 200000 ? { rank: n, branches: f.branches } : 'Rank 1 se 2,00,000 ke beech daalo.';
}

export function ComedkPanel({ handover }) {
  const { data: meta } = useRankData(getMeta);
  const [form, setForm] = useState(load);
  const [open, setOpen] = useState(true), [query, setQuery] = useState(null), [area, setArea] = useState('all'), [page, setPage] = useState(1);
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [problem, setProblem] = useState(''), [tries, setTries] = useState(0);
  const [sheet, setSheet] = useState(null);
  const views = useCardViews();
  const link = useShareLink();
  const run = f => {
    const q = toBody(f);
    if (typeof q === 'string') { setProblem(q); setOpen(true); return; }
    setProblem('');
    try { localStorage.setItem(SAVED, JSON.stringify(f)); } catch {}
    setQuery(q); setArea('all'); setPage(1); setOpen(false);
  };
  useEffect(() => {
    if (!handover?.marks && handover?.marks !== 0) return;
    const f = { ...load(), mode: 'marks', marks: String(handover.marks) };
    setForm(f); run(f);
  }, [handover]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError('');
    rank.comedk({ ...query, area, page }).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [query, area, page, tries]);
  const patch = p => { setForm(f => ({ ...f, ...p })); setProblem(''); };
  const r = data?.result;
  const share = r ? ['🎓 Mera JEELIVE.AI College Predictor · COMEDK 2026', r.summary, `Expected rank: ${fmtRange(r.rank)}`, '',
    ...data.items.slice(0, 5).map((c, i) => `${i + 1}. ${c.college} · ${c.course} (closing ${fmt(c.close)})`), '', ESTIMATE, '', invite(link)].join('\n') : '';
  const summary = query ? [query.marks != null ? `${query.marks} / 180 marks` : `Rank ${fmt(query.rank)}`, query.branches.length ? `${query.branches.length} course group` : 'Saare courses', 'COMEDK 2026'].join(' · ') : '';
  return <>
    {open || !query ? <Panel form title="Your COMEDK score" testId="ck-input">
      <Switch prefix="ck-mode" value={form.mode} onChange={mode => patch({ mode })} items={[{ key: 'marks', label: 'Marks se' }, { key: 'rank', label: 'Rank se' }]} />
      {form.mode === 'marks'
        ? <Field label="Marks (out of 180)" testId="ck-marks-input" inputMode="numeric" placeholder="e.g. 110" value={form.marks} onKeyDown={e => e.key === 'Enter' && run(form)} onChange={e => patch({ marks: e.target.value.replace(/\D/g, '').slice(0, 3) })} />
        : <Field label="COMEDK rank" testId="ck-rank-input" inputMode="numeric" placeholder="e.g. 8500" value={form.rank} onKeyDown={e => e.key === 'Enter' && run(form)} onChange={e => patch({ rank: e.target.value.replace(/\D/g, '').slice(0, 6) })} />}
      <BranchPicker options={meta?.comedk?.groups || []} value={form.branches} onChange={branches => patch({ branches })} testId="ck-branches" allLabel="Saare courses" />
      <Problem text={problem} testId="ck-input-error" />
      <Go label="Colleges dekho" busy={busy && !data} onClick={() => run(form)} testId="ck-show" />
    </Panel> : <Summary text={summary} onEdit={() => setOpen(true)} testId="ck-input-collapsed" />}
    <Err error={error} retry={() => setTries(t => t + 1)} testId="ck-error" />
    {r && query ? <div className="rk-stack rk-reveal">
      <RankCard testId="ck-card" badge="COMEDK 2026" eyebrow="EXPECTED RANK" big={fmtRange(r.rank)} rule={`${r.in_reach} / ${r.total} SEATS PAHUNCH MEIN`} summary={r.summary} serial={fmt(r.mid)} of={fmt(r.candidates)} />
      <div className="rk-segs" role="tablist">{AREAS.map(([k, l]) => <button key={k} type="button" role="tab" aria-selected={area === k} className={'rk-seg' + (area === k ? ' is-on' : '')}
        onClick={() => { setArea(k); setPage(1); }} data-testid={`ck-area-${k}`}>{l}<b>{fmt(data.reach?.[k] ?? data.counts?.[k] ?? 0)}</b></button>)}</div>
      <Heading title={data.total ? `${fmt(data.reach?.[area] ?? data.total)} seats aapki pahunch mein` : 'Is filter mein koi seat pahunch mein nahi'}
        sub={[data.total && (data.reach?.[area] ?? 0) > data.total ? `Sabse achhi ${data.total} yahan, best pehle.` : null, 'Closing rank = 2026 ke aakhri round tak, GM seats.'].filter(Boolean).join(' ')} />
      {data.items.length ? <TapHint testId="ck-hint" viewed={views.viewed.size} /> : null}
      <div className="rk-list" data-testid="ck-list">{data.items.map((c, i) => <ComedkCard key={c.id} c={c} n={(page - 1) * 25 + i + 1} first={i === 0} testId={`ck-seat-${(page - 1) * 25 + i}`} views={views}
        onOpen={() => setSheet({ ...query, code: c.code, course: c.cc })} />)}</div>
      <Pager page={page} pages={data.pages} onPage={p => { setPage(p); requestAnimationFrame(() => document.querySelector('[data-testid="ck-list"]')?.scrollIntoView({ behavior: 'smooth', block: 'start' })); }} prefix="ck" />
      {data.near?.length ? <><Heading title="Thoda aur mehnat, aur ye bhi" sub="Ye seats aapki rank se thoda pehle band hui." />
        <div className="rk-list" data-testid="ck-near">{data.near.map((c, i) => <ComedkCard key={'n' + c.id} c={c} testId={`ck-near-${i}`} views={views} onOpen={() => setSheet({ ...query, code: c.code, course: c.cc })} />)}</div></> : null}
      <div className="rk-actions"><PdfButton path="/comedk" body={{ ...query, area }} filename="JEELIVE-COMEDK-colleges.pdf" testId="ck-pdf" /><WaButton text={share} testId="ck-share" /></div>
      <Notes lines={[r.spread, r.check, ...data.notes]} testId="ck-notes" />
    </div> : null}
    {sheet ? <ComedkCollegeSheet req={sheet} onClose={() => setSheet(null)} /> : null}
  </>;
}

/** ₹2,85,000 → "₹2.85 L" so the fee fits its stat box. */
const lakh = fee => (fee >= 100000 ? `₹${(fee / 100000).toFixed(2)} L` : `₹${fmt(fee)}`);

function ComedkCard({ c, n, first, testId, views, onOpen }) {
  const list = shortlist.useList();
  const saved = comedkSaved(c);
  const dream = useDreamToggle(`comedk-${c.code}|${c.cc}`, () => comedkDream(c));
  return <CollegeCard testId={testId} rank={n} edge={c.tag || (c.gap ? 'near' : 'none')} title={c.college} tags={<Tag tag={c.tag} />}
    sub={c.course} line={`${c.city ? `${c.city} · ` : ''}GM (All India)`} note={c.gap}
    stats={[{ label: 'CLOSING', value: fmt(c.close), sub: `${c.round} · 2026`, testId: testId + '-close' }, trendStat(c.y25, c.close, testId + '-trend'),
      { label: 'FEE / SAAL', value: c.fee ? lakh(c.fee) : '—', sub: c.seats ? `${c.seats} GM seats` : 'seats —' }]}
    teaser="Har round ka cutoff · fee · seats" viewed={views.viewed.has(c.id)} pulse={views.pulse && first} open={false} onOpen={() => { views.mark(c.id); onOpen(); }}
    compared={list.some(x => x.id === saved.id)} onCompare={() => shortlist.toggle(saved)} dream={dream} />;
}
