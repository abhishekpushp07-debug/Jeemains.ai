// College predictor (JEE Main · BITSAT · COMEDK). JEE: marks or percentile + profile -> rank card, every seat in reach
// by NIT / IIIT / GFTI / Delhi, near misses, and a college sheet with every round's closing rank.
import React, { useEffect, useState } from 'react';
import { CATEGORY_LABEL, CATS, ESTIMATE, fmt, fmtPct, fmtRange, getMeta, invite, LEVEL, LEVELS, rank, SEGMENTS } from './rankApi';
import { BranchPicker, Chip, CollegeCard, Err, Field, Go, Heading, Kind, Notes, Pager, Panel, PdfButton, Problem, RankCard, StateSelect, Summary, Switch, Tag, TapHint, trendStat, useCardViews, WaButton } from './RankUi';
import { jeeDream, jeeSaved, setJeeProfile, shortlist, useDreamToggle, useRankData } from './rankStore';
import { JeeCollegeSheet } from './CollegeSheets';
import { BitsatPanel } from './BitsatPanel';
import { ComedkPanel } from './ComedkPanel';
import { useShareLink } from '../mission/missionApi';

export function CollegePredictor({ handover }) {
  const [exam, setExam] = useState(handover?.exam || 'jee');
  useEffect(() => { if (handover) setExam(handover.exam); }, [handover]);
  return <>
    <Switch prefix="cp-exam" value={exam} onChange={setExam} items={[{ key: 'jee', label: 'JEE Main' }, { key: 'bitsat', label: 'BITSAT' }, { key: 'comedk', label: 'COMEDK' }]} />
    <div className="rk-sub" hidden={exam !== 'jee'}><JeeColleges handover={handover?.exam === 'jee' ? handover : null} /></div>
    <div className="rk-sub" hidden={exam !== 'bitsat'}><BitsatPanel /></div>
    <div className="rk-sub" hidden={exam !== 'comedk'}><ComedkPanel handover={handover?.exam === 'comedk' ? handover : null} /></div>
  </>;
}

const SAVED = 'rank.college.v1';
const DEF = { mode: 'marks', marks: '', pct: '', level: 'normal', category: 'GEN', female: false, pwd: false, state: null, branches: [] };
const load = () => { try { return { ...DEF, ...JSON.parse(localStorage.getItem(SAVED) || '{}') }; } catch { return DEF; } };
function toBody(f) {
  const profile = { level: f.level, category: f.category, female: f.female, pwd: f.pwd, state: f.state, branches: f.branches };
  if (f.mode === 'marks') {
    const raw = String(f.marks).trim(), n = Number(raw);
    if (!raw) return 'Marks daalo.';
    if (!Number.isInteger(n) || n < -75 || n > 300) return 'Marks −75 se 300 ke beech poore ank mein daalo.';
    return { marks: n, ...profile };
  }
  const raw = String(f.pct).trim(), n = Number(raw);
  if (!raw || !Number.isFinite(n) || n < 0 || n > 100) return 'Percentile 0 se 100 ke beech daalo (jaise 97.4567).';
  return { percentile: n, ...profile };
}
const summaryOf = q => [q.marks != null ? `${q.marks} / 300 marks · ${LEVEL[q.level]} paper` : `${q.percentile} percentile`, CATEGORY_LABEL[q.category],
  q.female ? 'Female' : null, q.pwd ? 'PwD' : null, q.state, q.branches.length ? `${q.branches.length} branch` : null].filter(Boolean).join(' · ');

function JeeColleges({ handover }) {
  const { data: meta } = useRankData(getMeta);
  const [form, setForm] = useState(load);
  const [open, setOpen] = useState(true), [query, setQuery] = useState(null);
  const [segment, setSegment] = useState('all'), [page, setPage] = useState(1);
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [problem, setProblem] = useState(''), [tries, setTries] = useState(0);
  const [sheet, setSheet] = useState(null), [chart, setChart] = useState(false);
  const views = useCardViews();
  const link = useShareLink();
  const run = f => {
    const q = toBody(f);
    if (typeof q === 'string') { setProblem(q); setOpen(true); return; }
    setProblem('');
    try { localStorage.setItem(SAVED, JSON.stringify(f)); } catch {}
    setJeeProfile({ category: q.category, female: q.female, pwd: q.pwd, state: q.state });
    setQuery(q); setSegment('all'); setPage(1); setOpen(false);
  };
  useEffect(() => {
    if (!handover) return;
    const f = { ...load(), ...(handover.marks != null ? { mode: 'marks', marks: String(handover.marks), level: handover.level || 'normal' } : { mode: 'pct', pct: String(handover.percentile) }),
      category: handover.category || 'GEN', pwd: !!handover.pwd };
    setForm(f); run(f);
  }, [handover]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError('');
    rank.predict({ ...query, segment, page }).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [query, segment, page, tries]);
  const patch = p => { setForm(f => ({ ...f, ...p })); setProblem(''); };
  const r = data?.result;
  const share = r ? ['🎓 Mera JEELIVE.AI College Predictor · JEE Main 2026', r.summary, `Rank (CRL): ${fmtRange(r.crl)}`, '',
    ...data.items.slice(0, 5).map((s, i) => `${i + 1}. ${s.college} · ${s.branch} (closing ${fmt(s.close)})`), '', ESTIMATE, '', invite(link)].join('\n') : '';
  return <>
    {open || !query ? <Panel form title="Your score" testId="cp-input">
      <Switch prefix="cp-mode" value={form.mode} onChange={mode => patch({ mode })} items={[{ key: 'marks', label: 'Marks se' }, { key: 'pct', label: 'Percentile se' }]} />
      {form.mode === 'marks'
        ? <Field label="Marks (out of 300)" testId="cp-marks-input" inputMode="numeric" placeholder="e.g. 180" value={form.marks} onKeyDown={e => e.key === 'Enter' && run(form)}
          onChange={e => patch({ marks: e.target.value.replace(/[^0-9-]/g, '').slice(0, 4) })} />
        : <Field label="NTA percentile" testId="cp-pct-input" inputMode="decimal" placeholder="e.g. 97.4567" value={form.pct} onKeyDown={e => e.key === 'Enter' && run(form)}
          onChange={e => patch({ pct: e.target.value.replace(/[^0-9.]/g, '').slice(0, 10) })} />}
      {form.mode === 'marks' ? <div className="rk-row"><span className="rk-row-label">Paper</span>{LEVELS.map(l => <Chip key={l} tone={'lvl-' + l} on={form.level === l} onClick={() => patch({ level: l })} testId={`cp-level-${l}`}>{LEVEL[l]}</Chip>)}</div> : null}
      <div className="rk-chips">{CATS.map(c => <Chip key={c} on={form.category === c} onClick={() => patch({ category: c })} testId={`cp-cat-${c}`}>{CATEGORY_LABEL[c]}</Chip>)}</div>
      <div className="rk-chips"><Chip on={form.female} onClick={() => patch({ female: !form.female })} testId="cp-female">Female</Chip><Chip on={form.pwd} onClick={() => patch({ pwd: !form.pwd })} testId="cp-pwd">PwD</Chip></div>
      <div className="rk-two">
        <StateSelect states={meta?.states || []} value={form.state} onChange={state => patch({ state })} testId="cp-state" />
        <BranchPicker options={meta?.branches || []} value={form.branches} onChange={branches => patch({ branches })} testId="cp-branches" />
      </div>
      <small className="rk-dim">Home state se NIT ki Home State seats aur state quota khulti hain.</small>
      <Problem text={problem} testId="cp-input-error" />
      <Go label="Colleges dekho" busy={busy && !data} onClick={() => run(form)} testId="cp-show" />
      {meta?.chart?.length ? <button type="button" className="rk-link" onClick={() => setChart(c => !c)} data-testid="cp-chart-toggle">{chart ? 'Percentile chart band karo' : 'Percentile → rank → marks chart dekho'}</button> : null}
      {chart && meta ? <PercentileChart lines={meta.chart} onPick={l => { const f = { ...form, mode: 'pct', pct: String(l.pct) }; setForm(f); run(f); setChart(false); }} /> : null}
    </Panel> : <Summary text={summaryOf(query)} onEdit={() => setOpen(true)} testId="cp-input-collapsed" />}
    <Err error={error} retry={() => setTries(t => t + 1)} testId="cp-error" />
    {r && query ? <div className="rk-stack rk-reveal">
      <RankCard testId="cp-card" badge="JEE MAIN 2026" eyebrow={r.from_marks ? 'EXPECTED PERCENTILE' : 'YOUR PERCENTILE'} big={fmtPct(r.percentile)} rule={`RANK (CRL)  ${fmtRange(r.crl)}`}
        smalls={[r.cat_rank && { label: r.cat_rank.label, value: fmtRange(r.cat_rank.range), testId: 'cp-card-cat' }, r.pwd_rank && { label: r.pwd_rank.label, value: fmtRange(r.pwd_rank.range), testId: 'cp-card-pwd' }].filter(Boolean)}
        summary={r.summary} serial={fmt((r.crl[0] + r.crl[1]) / 2)} of={meta ? fmt(meta.candidates) : null} />
      <div className="rk-segs" role="tablist">{SEGMENTS.map(([k, l]) => <button key={k} type="button" role="tab" aria-selected={segment === k} className={'rk-seg' + (segment === k ? ' is-on' : '')}
        onClick={() => { setSegment(k); setPage(1); }} data-testid={`cp-seg-${k}`}>{l}<b>{fmt(data.reach?.[k] ?? data.counts?.[k] ?? 0)}</b></button>)}</div>
      <Heading title={data.total ? `${fmt(data.reach?.[segment] ?? data.total)} seats aapki pahunch mein` : 'Is filter mein koi seat pahunch mein nahi'}
        sub={[data.total && (data.reach?.[segment] ?? 0) > data.total ? `Sabse achhi ${data.total} yahan, best pehle.` : null, data.note].filter(Boolean).join(' ')} />
      {data.items.length ? <TapHint testId="cp-hint" viewed={views.viewed.size} /> : null}
      <div className="rk-list" data-testid="cp-list">{data.items.map((s, i) => <SeatCard key={`${s.prog}-${s.path}`} s={s} n={(page - 1) * 25 + i + 1} y25={meta?.y25_label}
        testId={`cp-seat-${(page - 1) * 25 + i}`} views={views} first={i === 0} onOpen={() => setSheet({ ...query, inst: s.inst, prog: s.prog, quota: s.quota, gender: s.gender, seat: s.seat })} />)}</div>
      <Pager page={page} pages={data.pages} onPage={p => { setPage(p); requestAnimationFrame(() => document.querySelector('[data-testid="cp-list"]')?.scrollIntoView({ behavior: 'smooth', block: 'start' })); }} prefix="cp" />
      {data.near?.length ? <><Heading title="Thoda aur mehnat, aur ye bhi" sub="Ye seats aapki rank se thoda pehle band hui. Kuch marks aur, aur ye aapki." />
        <div className="rk-list" data-testid="cp-near">{data.near.map((s, i) => <SeatCard key={`n-${s.prog}-${s.path}`} s={s} y25={meta?.y25_label} testId={`cp-near-${i}`} views={views}
          onOpen={() => setSheet({ ...query, inst: s.inst, prog: s.prog, quota: s.quota, gender: s.gender, seat: s.seat })} />)}</div></> : null}
      <div className="rk-actions"><PdfButton path="/jee" body={{ ...query, segment }} filename="JEELIVE-JEE-colleges.pdf" testId="cp-pdf" /><WaButton text={share} testId="cp-share" /></div>
      <Notes lines={[r.spread, r.paper, r.check, r.delhi_note, ESTIMATE]} testId="cp-notes" />
    </div> : null}
    {sheet ? <JeeCollegeSheet req={sheet} onClose={() => setSheet(null)} /> : null}
  </>;
}

function SeatCard({ s, n, testId, views, first, onOpen }) {
  const list = shortlist.useList();
  const saved = jeeSaved(s);
  const dream = useDreamToggle(`jee-${s.prog}`, () => jeeDream(s));
  const key = `jee-${s.prog}-${s.path}`;
  return <CollegeCard testId={testId} rank={n} edge={s.tag || (s.gap ? 'near' : 'none')} title={s.college} tags={<><Kind kind={s.type} /><Tag tag={s.tag} /></>}
    sub={`${s.branch}${s.degree ? ` (${s.degree})` : ''}`} line={s.path} note={s.gap}
    stats={[{ label: 'CLOSING', value: fmt(s.close), sub: `${s.rank_type} · 2026`, testId: testId + '-close' }, { label: 'ROUND', value: s.round, sub: 'jahan seat mili' },
      trendStat(s.y25, s.y26, testId + '-trend')]}
    teaser="Har round ka cutoff + sab branches" viewed={views.viewed.has(key)} pulse={views.pulse && first} open={false} onOpen={() => { views.mark(key); onOpen(); }}
    compared={list.some(x => x.id === saved.id)} onCompare={() => shortlist.toggle(saved)} dream={dream} />;
}

function PercentileChart({ lines, onPick }) {
  return <div className="rk-table-wrap" data-testid="cp-chart"><table className="rk-table rk-chart">
    <thead><tr><th>Percentile</th><th>Rank (CRL)</th><th>Marks (normal)</th></tr></thead>
    <tbody>{lines.map(l => <tr key={l.pct}><th><button type="button" onClick={() => onPick(l)} data-testid={`cp-chart-${String(l.pct).replace('.', '-')}`}>{l.pct}</button></th><td>{fmt(l.rank)}</td><td>{l.marks}</td></tr>)}</tbody>
  </table><small className="rk-dim">Kisi bhi percentile par tap karo, uske colleges khul jayenge.</small></div>;
}
