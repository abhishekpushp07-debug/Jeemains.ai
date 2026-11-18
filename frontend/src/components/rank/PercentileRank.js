// Percentile se rank: NTA JEE Main percentile + category + PwD -> CRL, category / PwD rank, and the marks that percentile took on each paper type.
import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { CATEGORY_LABEL, CATS, ESTIMATE, fmt, fmtRange, invite, LEVEL, rank } from './rankApi';
import { Chip, Err, Field, Go, Notes, Panel, Problem, RankCard, Summary, WaButton } from './RankUi';
import { useShareLink } from '../mission/missionApi';

const SAVED = 'rank.pct.v1';
const load = () => { try { return { pct: '', category: 'GEN', pwd: false, ...JSON.parse(localStorage.getItem(SAVED) || '{}') }; } catch { return { pct: '', category: 'GEN', pwd: false }; } };

export function PercentileRank({ onColleges }) {
  const [form, setForm] = useState(load);
  const [open, setOpen] = useState(true), [query, setQuery] = useState(null), [res, setRes] = useState(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [problem, setProblem] = useState(''), [tries, setTries] = useState(0);
  const link = useShareLink();
  useEffect(() => {
    if (!query) return;
    let live = true;
    setBusy(true); setError('');
    rank.percentile(query).then(d => { if (live) setRes(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [query, tries]);
  const show = () => {
    const n = Number(String(form.pct).trim());
    if (!String(form.pct).trim() || !Number.isFinite(n) || n < 0 || n > 100) { setProblem('Percentile 0 se 100 ke beech daalo (jaise 97.4567).'); return; }
    setProblem('');
    try { localStorage.setItem(SAVED, JSON.stringify(form)); } catch {}
    setQuery({ percentile: n, category: form.category, pwd: form.pwd }); setOpen(false);
  };
  const summary = query ? [`${query.percentile} percentile`, CATEGORY_LABEL[query.category], query.pwd ? 'PwD' : null, 'JEE Main 2026'].filter(Boolean).join(' · ') : '';
  const r = res?.result;
  const text = r ? ['🎯 Mera JEELIVE.AI Rank · JEE Main 2026', r.summary, `Rank (CRL): ${fmtRange(r.crl)}`, ...(r.cat_rank ? [`${r.cat_rank.label}: ${fmtRange(r.cat_rank.range)}`] : []),
    '', 'Is percentile ke liye marks (lagbhag):', ...res.marks.map(m => `${LEVEL[m.level]} paper: ${m.marks} / 300`), '', ESTIMATE, '', invite(link)].join('\n') : '';
  return <>
    {open || !query ? <Panel form title="Your NTA percentile" testId="pr-input">
      <Field label="JEE Main percentile (scorecard se)" testId="pr-percentile-input" inputMode="decimal" placeholder="e.g. 97.4567" value={form.pct}
        onKeyDown={e => e.key === 'Enter' && show()} onChange={e => { setForm(f => ({ ...f, pct: e.target.value.replace(/[^0-9.]/g, '').slice(0, 10) })); setProblem(''); }} />
      <div className="rk-chips">{CATS.map(c => <Chip key={c} on={form.category === c} onClick={() => setForm(f => ({ ...f, category: c }))} testId={`pr-cat-${c}`}>{CATEGORY_LABEL[c]}</Chip>)}
        <Chip on={form.pwd} onClick={() => setForm(f => ({ ...f, pwd: !f.pwd }))} testId="pr-pwd">PwD</Chip></div>
      <small className="rk-dim">Percentile paper type par nahi badalta, isliye yahan Tough / Easy nahi chahiye.</small>
      <Problem text={problem} testId="pr-input-error" />
      <Go label="Rank dekho" busy={busy && !res} onClick={show} testId="pr-show" />
    </Panel> : <Summary text={summary} onEdit={() => setOpen(true)} testId="pr-input-collapsed" />}
    <Err error={error} retry={() => setTries(t => t + 1)} testId="pr-error" />
    {r && query ? <div className="rk-stack rk-reveal">
      <RankCard testId="pr-card" badge="JEE MAIN 2026" eyebrow="EXPECTED RANK · CRL" big={fmtRange(r.crl)} rule={`PERCENTILE  ${query.percentile}`}
        smalls={[r.cat_rank && { label: r.cat_rank.label, value: fmtRange(r.cat_rank.range), testId: 'pr-card-cat' }, r.pwd_rank && { label: r.pwd_rank.label, value: fmtRange(r.pwd_rank.range), testId: 'pr-card-pwd' }].filter(Boolean)}
        summary={r.summary} serial={fmt((r.crl[0] + r.crl[1]) / 2)} of={fmt(res.candidates)} />
      <Panel title="Is percentile ke liye marks" testId="pr-marks">
        <div className="rk-marks3">{res.marks.map(m => <div key={m.level} data-testid={`pr-marks-${m.level}`}><span className={'rk-tag lvl-' + m.level}>{LEVEL[m.level]}</span><b>{m.marks}</b><small>/ 300</small></div>)}</div>
        <small className="rk-dim">Tough shift mein kam marks par hi ye percentile aa jaata hai, Easy shift mein zyada marks lagte hain.</small>
      </Panel>
      <div className="rk-actions"><WaButton text={text} testId="pr-share" /></div>
      <Notes lines={res.notes} testId="pr-notes" />
      <button type="button" className="rk-outline" onClick={() => onColleges({ exam: 'jee', percentile: query.percentile, category: query.category, pwd: query.pwd })} data-testid="pr-colleges">
        Is percentile se colleges dekho<ArrowRight size={18} /></button>
    </div> : null}
  </>;
}
