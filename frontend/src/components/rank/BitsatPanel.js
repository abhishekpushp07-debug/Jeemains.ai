// BITSAT college predictor: score out of 390 (+ campus, degree) -> every BITS program cleared, the ones a few marks away,
// and each program's cutoff over the years.
import React, { useEffect, useState } from 'react';
import { ESTIMATE, invite, rank } from './rankApi';
import { Chip, CollegeCard, Err, Field, Go, Heading, Notes, Panel, PdfButton, Problem, RankCard, Summary, Tag, TapHint, useCardViews, WaButton } from './RankUi';
import { bitsatDream, bitsatSaved, shortlist, useDreamToggle } from './rankStore';
import { useShareLink } from '../mission/missionApi';

const SAVED = 'rank.bitsat.v1';
const DEF = { score: '', campus: 'all', degree: 'all' };
const CAMPUS = [['all', 'Saare campus'], ['Pilani', 'Pilani'], ['Goa', 'Goa'], ['Hyderabad', 'Hyderabad']];
const DEGREE = [['all', 'Saari degree'], ['BE', 'B.E.'], ['MSc', 'M.Sc.'], ['BPharm', 'B.Pharm']];
const load = () => { try { return { ...DEF, ...JSON.parse(localStorage.getItem(SAVED) || '{}') }; } catch { return DEF; } };

export function BitsatPanel() {
  const [form, setForm] = useState(load);
  const [open, setOpen] = useState(true), [query, setQuery] = useState(null);
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [problem, setProblem] = useState(''), [tries, setTries] = useState(0);
  const [rest, setRest] = useState(false), [openId, setOpenId] = useState(null);
  const views = useCardViews();
  const link = useShareLink();
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError('');
    rank.bitsat(query).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [query, tries]);
  const run = f => {
    const raw = String(f.score).trim(), n = Number(raw);
    if (!raw || !Number.isInteger(n) || n < -130 || n > 390) { setProblem('Score −130 se 390 ke beech poore ank mein daalo.'); return; }
    setProblem('');
    try { localStorage.setItem(SAVED, JSON.stringify(f)); } catch {}
    setQuery({ score: n, campus: f.campus, degree: f.degree }); setOpen(false);
  };
  const res = data?.result;
  const share = res ? ['🎓 Mera JEELIVE.AI BITSAT Predictor · 2026', `${res.score} / ${res.max} score · ${res.cleared} / ${res.total} programs clear`,
    ...data.items.slice(0, 5).map((b, i) => `${i + 1}. ${b.college} · ${b.program} (cutoff ${b.cutoff})`), '', ESTIMATE, '', invite(link)].join('\n') : '';
  const card = (b, i, prefix, first) => <BitsatCard key={prefix + b.id} b={b} n={prefix === 'bt-item' ? i + 1 : null} years={data.years} testId={`${prefix}-${i}`} views={views} first={first}
    open={openId === b.id} onOpen={() => { views.mark(b.id); setOpenId(o => (o === b.id ? null : b.id)); }} />;
  return <>
    {open || !query ? <Panel form title="Your BITSAT score" testId="bt-input">
      <Field label="Score (out of 390)" testId="bt-score-input" inputMode="numeric" placeholder="e.g. 280" value={form.score} onKeyDown={e => e.key === 'Enter' && run(form)}
        onChange={e => { setForm(f => ({ ...f, score: e.target.value.replace(/[^0-9-]/g, '').slice(0, 4) })); setProblem(''); }} />
      <div className="rk-chips">{CAMPUS.map(([k, l]) => <Chip key={k} on={form.campus === k} onClick={() => setForm(f => ({ ...f, campus: k }))} testId={`bt-campus-${k}`}>{l}</Chip>)}</div>
      <div className="rk-chips">{DEGREE.map(([k, l]) => <Chip key={k} on={form.degree === k} onClick={() => setForm(f => ({ ...f, degree: k }))} testId={`bt-degree-${k}`}>{l}</Chip>)}</div>
      <small className="rk-dim">BITSAT 2026: 130 sawaal, +3 / −1, poore 390 marks.</small>
      <Problem text={problem} testId="bt-input-error" />
      <Go label="Programs dekho" busy={busy && !data} onClick={() => run(form)} testId="bt-show" />
    </Panel> : <Summary text={`${query.score} / 390 · ${CAMPUS.find(c => c[0] === query.campus)[1]} · ${DEGREE.find(d => d[0] === query.degree)[1]}`} onEdit={() => setOpen(true)} testId="bt-input-collapsed" />}
    <Err error={error} retry={() => setTries(t => t + 1)} testId="bt-error" />
    {res && query ? <div className="rk-stack rk-reveal">
      <RankCard testId="bt-card" badge="BITSAT 2026" eyebrow="PROGRAMS CLEAR" big={`${res.cleared} / ${res.total}`} rule={`SCORE  ${res.score} / ${res.max}`}
        smalls={[res.best && { label: 'Sabse achha', value: `${res.best.college.replace('BITS ', '')} · ${res.best.program}`, testId: 'bt-card-best' },
          res.target && { label: 'Agla target', value: `${res.target.program} · +${res.target.gap}`, testId: 'bt-card-target' }].filter(Boolean)}
        summary={`${res.score} / ${res.max} · ${res.cleared_all} / ${res.total_all} programs (saare campus)`} />
      <Heading title={data.items.length ? `${data.items.length} programs clear` : 'Is score par abhi koi program clear nahi'} sub={data.source} />
      {data.items.length ? <TapHint testId="bt-hint" viewed={views.viewed.size} what="program" /> : null}
      <div className="rk-list" data-testid="bt-list">{data.items.map((b, i) => card(b, i, 'bt-item', i === 0))}</div>
      {data.near?.length ? <><Heading title="Bas thoda door" sub="In programs tak kuch marks aur." /><div className="rk-list" data-testid="bt-near">{data.near.map((b, i) => card(b, i, 'bt-near'))}</div></> : null}
      {data.rest?.length ? <><button type="button" className="rk-outline" onClick={() => setRest(v => !v)} data-testid="bt-rest-toggle">{rest ? 'Baaki programs chhupao' : `Baaki programs dekho (${data.rest.length})`}</button>
        {rest ? <div className="rk-list" data-testid="bt-rest">{data.rest.map((b, i) => card(b, i, 'bt-rest'))}</div> : null}</> : null}
      <div className="rk-actions"><PdfButton path="/bitsat" body={query} filename="JEELIVE-BITSAT.pdf" testId="bt-pdf" /><WaButton text={share} testId="bt-share" /></div>
      <Notes lines={[...data.notes, ESTIMATE]} testId="bt-notes" />
    </div> : null}
  </>;
}

function BitsatCard({ b, n, years, testId, views, first, open, onOpen }) {
  const list = shortlist.useList();
  const saved = bitsatSaved(b);
  const dream = useDreamToggle(`bitsat-${b.id}`, () => bitsatDream(b));
  const top = Math.max(...b.history.filter(Boolean), b.cutoff, 1);
  return <CollegeCard testId={testId} rank={n} edge={b.campus === 'Pilani' ? 'NIT' : b.campus === 'Goa' ? 'IIIT' : 'GFTI'} title={b.college} tags={<Tag tag={b.tag} />} sub={b.program}
    line={b.gap >= 0 ? `Cutoff se ${b.gap} marks upar` : `${-b.gap} marks aur chahiye`}
    stats={[{ label: 'Cutoff 2026', value: `${b.cutoff}`, sub: '/ 390', testId: testId + '-cutoff' }, b.last ? { label: 'Pichhla saal', value: String(b.last) } : null].filter(Boolean)}
    teaser="Saalon ka cutoff" viewed={views.viewed.has(b.id)} pulse={views.pulse && first} open={open} onOpen={onOpen}
    compared={list.some(x => x.id === saved.id)} onCompare={() => shortlist.toggle(saved)} dream={dream}>
    {open ? <span className="rk-history" data-testid={testId + '-history'}>{years.map((y, i) => <span key={y}><i style={{ height: `${Math.max(6, ((b.history[i] || 0) / top) * 100)}%` }} />
      <b>{b.history[i] ?? '—'}</b><small>{y}</small></span>)}</span> : null}
  </CollegeCard>;
}
