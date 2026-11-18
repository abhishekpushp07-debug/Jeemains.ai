// Rank predictor (first tile): JEE Main or COMEDK marks -> expected percentile and rank. JEE shows all three paper types side by side;
// COMEDK shows what each public analysis says. "Is score se colleges dekho" carries the score into the College predictor.
import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { CATEGORY_LABEL, CATS, ESTIMATE, fmt, fmtPct, fmtRange, invite, LEVEL, LEVELS, rank } from './rankApi';
import { Chip, Err, Field, Go, Notes, Panel, Problem, RankCard, Summary, Switch, WaButton } from './RankUi';
import { useShareLink } from '../mission/missionApi';

const SAVED = 'rank.estimate.v1';
const DEFAULT = { exam: 'jee', jee: '', comedk: '', level: 'normal', category: 'GEN', pwd: false };
const MAX = { jee: 300, comedk: 180 };
const load = () => { try { return { ...DEFAULT, ...JSON.parse(localStorage.getItem(SAVED) || '{}') }; } catch { return DEFAULT; } };

function toQuery(f) {
  const raw = String(f.exam === 'jee' ? f.jee : f.comedk).trim(), n = Number(raw), min = f.exam === 'jee' ? -75 : 0;
  if (!raw) return 'Marks daalo.';
  if (!Number.isInteger(n) || n < min || n > MAX[f.exam]) return `Marks ${min === 0 ? '0' : '−75'} se ${MAX[f.exam]} ke beech poore ank mein daalo.`;
  return { exam: f.exam, marks: n, level: f.level, category: f.category, pwd: f.pwd };
}
const summaryOf = q => (q.exam === 'jee'
  ? [`${q.marks} / 300 marks`, `${LEVEL[q.level]} paper`, CATEGORY_LABEL[q.category], q.pwd ? 'PwD' : null, 'JEE Main 2026'].filter(Boolean).join(' · ')
  : `${q.marks} / 180 marks · COMEDK 2026`);

export function RankPredictor({ onColleges }) {
  const [form, setForm] = useState(load);
  const [open, setOpen] = useState(true);
  const [queries, setQueries] = useState({});
  const [results, setResults] = useState({});
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [problem, setProblem] = useState(''), [tries, setTries] = useState(0);
  const query = queries[form.exam] ?? null;
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError('');
    rank.estimate(query).then(d => { if (live) setResults(r => ({ ...r, [query.exam]: d })); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [query, tries]);
  const patch = p => { setForm(f => ({ ...f, ...p })); setProblem(''); };
  const run = f => {
    const q = toQuery(f);
    if (typeof q === 'string') { setProblem(q); return; }
    try { localStorage.setItem(SAVED, JSON.stringify(f)); } catch {}
    setQueries(m => ({ ...m, [q.exam]: q })); setOpen(false);
  };
  const shown = results[form.exam]?.exam === form.exam && query ? results[form.exam] : null;
  return <>
    <Switch prefix="rp-exam" value={form.exam} onChange={exam => { patch({ exam }); setOpen(!queries[exam]); setError(''); }} items={[{ key: 'jee', label: 'JEE Main' }, { key: 'comedk', label: 'COMEDK' }]} />
    {open || !query ? <Panel form title="Your marks" testId="rp-input">
      <Field label={`Marks (out of ${MAX[form.exam]})`} testId="rp-marks-input" inputMode="numeric" placeholder={form.exam === 'jee' ? 'e.g. 180' : 'e.g. 110'}
        value={form.exam === 'jee' ? form.jee : form.comedk} onKeyDown={e => e.key === 'Enter' && run(form)}
        onChange={e => patch(form.exam === 'jee' ? { jee: e.target.value.replace(/[^0-9-]/g, '').slice(0, 4) } : { comedk: e.target.value.replace(/[^0-9]/g, '').slice(0, 3) })} />
      {form.exam === 'jee' ? <>
        <div className="rk-row"><span className="rk-row-label">Paper</span>{LEVELS.map(l => <Chip key={l} tone={'lvl-' + l} on={form.level === l} onClick={() => patch({ level: l })} testId={`rp-level-${l}`}>{LEVEL[l]}</Chip>)}</div>
        <small className="rk-dim">Paper type = aapki shift ka paper kaisa tha (pata na ho to Normal rakho).</small>
        <div className="rk-chips">{CATS.map(c => <Chip key={c} on={form.category === c} onClick={() => patch({ category: c })} testId={`rp-cat-${c}`}>{CATEGORY_LABEL[c]}</Chip>)}
          <Chip on={form.pwd} onClick={() => patch({ pwd: !form.pwd })} testId="rp-pwd">PwD</Chip></div>
      </> : <small className="rk-dim">COMEDK UGET 2026: 180 sawaal, +1 / 0. Sabki ek hi merit list, isliye category aur paper type nahi lagte.</small>}
      <Problem text={problem} testId="rp-input-error" />
      <Go label="Predict rank" busy={busy && !shown} onClick={() => run(form)} testId="rp-show" />
    </Panel> : <Summary text={summaryOf(query)} onEdit={() => setOpen(true)} testId="rp-input-collapsed" />}
    <Err error={error} retry={() => setTries(t => t + 1)} testId="rp-error" />
    {shown ? <>
      {shown.exam === 'jee' ? <JeeEstimate data={shown} level={query.level} busy={busy} onLevel={level => { const f = { ...form, level }; setForm(f); run(f); }} />
        : <ComedkEstimate data={shown} />}
      <button type="button" className="rk-outline" onClick={() => onColleges(query)} data-testid="rp-colleges">Is score se colleges dekho<ArrowRight size={18} /></button>
    </> : null}
  </>;
}

function JeeEstimate({ data, level, onLevel, busy }) {
  const link = useShareLink();
  const r = data.result;
  const text = ['🎯 Mera JEELIVE.AI Rank Predictor · JEE Main 2026', r.summary, `Rank (CRL): ${fmtRange(r.crl)}`, `Percentile: ${fmtPct(r.percentile)}`,
    ...data.levels.map(l => `${LEVEL[l.level]}: ${fmtPct(l.percentile)} percentile · rank ${fmtRange(l.crl)}`), '', ESTIMATE, '', invite(link)].join('\n');
  return <div className="rk-stack rk-reveal">
    <RankCard testId="rp-card" badge="JEE MAIN 2026" eyebrow="EXPECTED PERCENTILE" big={fmtPct(r.percentile)} rule={`RANK (CRL)  ${fmtRange(r.crl)}`}
      smalls={[r.cat_rank && { label: r.cat_rank.label, value: fmtRange(r.cat_rank.range), testId: 'rp-card-cat' }, r.pwd_rank && { label: r.pwd_rank.label, value: fmtRange(r.pwd_rank.range), testId: 'rp-card-pwd' }].filter(Boolean)}
      summary={r.summary} serial={fmt((r.crl[0] + r.crl[1]) / 2)} of={fmt(data.candidates)} />
    <Panel title="Paper type ke hisaab se" testId="rp-levels" right={busy ? <small className="rk-dim">…</small> : null}>
      <div className="rk-levels">{data.levels.map(l => <button key={l.level} type="button" className={'rk-level' + (l.level === level ? ' is-on' : '')} aria-pressed={l.level === level}
        onClick={() => onLevel(l.level)} data-testid={`rp-levels-${l.level}`}>
        <span className={'rk-tag lvl-' + l.level}>{LEVEL[l.level]}</span>{l.level === level ? <em>aapka paper</em> : null}
        <span className="rk-level-vals"><b>{fmtPct(l.percentile)}</b><small>percentile</small></span>
        <span className="rk-level-vals"><b>{fmtRange(l.crl)}</b><small>rank (CRL)</small></span>
        {[l.cat_rank, l.pwd_rank].filter(Boolean).map(x => <small key={x.label} className="rk-dim">{x.label}: {fmtRange(x.range)}</small>)}
      </button>)}</div>
      <small className="rk-dim">Same marks par shift ka paper tough tha to percentile zyada aata hai. Kisi bhi paper par tap karo, card us paper ke hisaab se badal jayega.</small>
    </Panel>
    <div className="rk-actions"><WaButton text={text} testId="rp-share" /></div>
    <Notes lines={[r.spread, ...data.notes]} testId="rp-notes" />
  </div>;
}

function ComedkEstimate({ data }) {
  const link = useShareLink();
  const text = ['🎯 Mera JEELIVE.AI Rank Predictor · COMEDK 2026', data.summary, `Expected rank: ${fmtRange(data.rank)}`, `Percentile: lagbhag ${fmtPct(data.percentile)}`, '', ESTIMATE, '', invite(link)].join('\n');
  return <div className="rk-stack rk-reveal">
    <RankCard testId="rp-card" badge="COMEDK 2026" eyebrow="EXPECTED RANK" big={fmtRange(data.rank)} rule={`PERCENTILE  ${fmtPct(data.percentile)}`}
      summary={data.summary} serial={fmt(data.mid)} of={fmt(data.candidates)} />
    <Panel title="3 analyses kya kehte hain" testId="rp-sources">
      {data.sources.map((s, i) => <div key={s.label} className="rk-source" data-testid={`rp-sources-${i}`}><span>{s.label}</span><b>{fmt(s.rank)}</b></div>)}
      <small className="rk-dim">Beech wala andaaza (№ {fmt(data.mid)}) card par hai; range = sabse achha se sabse kharab andaaza.</small>
    </Panel>
    <div className="rk-actions"><WaButton text={text} testId="rp-share" /></div>
    <Notes lines={data.notes} testId="rp-notes" />
  </div>;
}
