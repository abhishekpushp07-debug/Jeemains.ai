// "Meri details" at the top of Rank: marks, percentile, rank and category, typed once (all optional).
// Closed: one baby pink bar with lights running round its dotted rim. Open: a small form per exam; Save fills every Rank tool.
import React, { useState } from 'react';
import { Pencil, Plus, User, X } from 'lucide-react';
import { CATEGORY_LABEL, CATS, fmt, getMeta, LEVEL, LEVELS } from './rankApi';
import { Chip, Field, Go, Problem, StateSelect, Switch } from './RankUi';
import { useRankData } from './rankStore';
import { clearProfile, problemOf, readScore, saveProfile, SCORE, typed, useRankProfile } from './profile';

const EXAMS = [{ key: 'jee', label: 'JEE Main' }, { key: 'bitsat', label: 'BITSAT' }, { key: 'comedk', label: 'COMEDK' }];

/** e.g. "JEE Main: 180 marks, 97.4 percentile · OBC-NCL · Bihar  |  BITSAT: 280". */
export function profileLine(p) {
  const j = p.jee, num = v => (readScore('jee', 'rank', v) === Number(v) ? fmt(Number(v)) : v);
  const jee = [[j.marks && `${j.marks} marks`, j.pct && `${j.pct} percentile`, j.rank && `rank ${num(j.rank)}`].filter(Boolean).join(', ') || null,
    CATEGORY_LABEL[j.category], j.female ? 'Female' : null, j.pwd ? 'PwD' : null, j.state].filter(Boolean).join(' · ');
  const comedk = [p.comedk.marks && `${p.comedk.marks} marks`, p.comedk.rank && `rank ${p.comedk.rank}`].filter(Boolean).join(', ');
  return [`JEE Main: ${jee}`, comedk ? `COMEDK: ${comedk}` : null, p.bitsat.score ? `BITSAT: ${p.bitsat.score}` : null].filter(Boolean).join('  |  ');
}

export function ProfileBar() {
  const profile = useRankProfile();
  const [open, setOpen] = useState(false), [saved, setSaved] = useState(false);
  if (open) return <ProfileForm start={profile} onClose={done => { setOpen(false); setSaved(done); }} />;
  const filled = profile.at > 0;
  return <button type="button" className="rk-profile" onClick={() => { setSaved(false); setOpen(true); }} data-testid="rank-profile"
    aria-label={filled ? `Meri details: ${profileLine(profile)}. Edit karo` : 'Add details'}>
    <i className="rk-profile-rim" aria-hidden="true" /><i className="rk-profile-glint" aria-hidden="true" />
    <span className="rk-profile-icon"><User size={17} strokeWidth={1.6} /></span>
    <span className="rk-profile-text">
      <b data-testid="rank-profile-title">{filled ? 'Meri details' : 'Add details'}</b>
      <small data-testid="rank-profile-summary">{filled ? profileLine(profile) : 'Marks, percentile, rank aur category. Har tool mein pehle se bhare milenge.'}</small>
      {saved ? <em data-testid="rank-profile-saved">Save ho gaya. Har tool mein bhar diya; kisi bhi tool mein alag se badal sakte ho.</em> : null}
    </span>
    <span className="rk-profile-edit" data-testid="rank-profile-edit">{filled ? <Pencil size={14} /> : <Plus size={14} />}{filled ? 'Edit' : 'Click'}</span>
  </button>;
}

function Box({ testId, exam, kind, value, onChange }) {
  const r = SCORE[exam][kind];
  return <Field label={r.label} testId={testId} inputMode={r.decimal ? 'decimal' : 'numeric'} placeholder={r.hint} value={value} onChange={e => onChange(typed(r, e.target.value))} />;
}

function ProfileForm({ start, onClose }) {
  const { data: meta } = useRankData(getMeta);
  const [p, setP] = useState(start), [exam, setExam] = useState('jee'), [problem, setProblem] = useState('');
  const jee = x => { setP(v => ({ ...v, jee: { ...v.jee, ...x } })); setProblem(''); };
  const comedk = x => { setP(v => ({ ...v, comedk: { ...v.comedk, ...x } })); setProblem(''); };
  const save = () => {
    const bad = problemOf(p);
    if (bad) { setExam(bad.exam); setProblem(bad.text); return; }
    saveProfile(p); onClose(true);
  };
  const many = [p.jee.marks, p.jee.pct, p.jee.rank].filter(Boolean).length > 1;
  return <section className="rk-panel is-form rk-profile-form" data-testid="rank-profile-form">
    <header className="rk-form-head"><span className="rk-form-icon"><User size={16} /></span><span className="rk-form-title"><small>MERI DETAILS</small><b>Ek baar bharo</b></span>
      <button type="button" className="rk-x" onClick={() => onClose(false)} aria-label="Meri details band karo" data-testid="rpf-close"><X size={18} /></button></header>
    <div className="rk-panel-body">
      <small className="rk-dim">Sab optional hai. Save karte hi ye har tool mein pehle se bhara milega; kisi bhi tool mein alag se badal sakte ho.</small>
      <Switch prefix="rpf-exam" value={exam} onChange={e => { setExam(e); setProblem(''); }} items={EXAMS} />
      {exam === 'jee' ? <>
        <div className="rk-three"><Box testId="rpf-jee-marks" exam="jee" kind="marks" value={p.jee.marks} onChange={v => jee({ marks: v })} />
          <Box testId="rpf-jee-percentile" exam="jee" kind="percentile" value={p.jee.pct} onChange={v => jee({ pct: v })} />
          <Box testId="rpf-jee-rank" exam="jee" kind="rank" value={p.jee.rank} onChange={v => jee({ rank: v })} /></div>
        <small className="rk-dim" data-testid="rpf-jee-note">{many ? 'Ek se zyada bhare hain: sabse pakka number chalega. Pehle Rank, phir Percentile, phir Marks.' : 'Jo pata hai wahi bharo, koi ek kaafi hai.'}</small>
        {p.jee.marks ? <div className="rk-row"><span className="rk-row-label">Paper</span>{LEVELS.map(l => <Chip key={l} tone={'lvl-' + l} on={p.jee.level === l} onClick={() => jee({ level: l })} testId={`rpf-level-${l}`}>{LEVEL[l]}</Chip>)}</div> : null}
        <div className="rk-chips">{CATS.map(c => <Chip key={c} on={p.jee.category === c} onClick={() => jee({ category: c })} testId={`rpf-cat-${c}`}>{CATEGORY_LABEL[c]}</Chip>)}</div>
        <div className="rk-chips"><Chip on={p.jee.female} onClick={() => jee({ female: !p.jee.female })} testId="rpf-female">Female</Chip>
          <Chip on={p.jee.pwd} onClick={() => jee({ pwd: !p.jee.pwd })} testId="rpf-pwd">PwD</Chip></div>
        <StateSelect states={meta?.states || []} value={p.jee.state} onChange={state => jee({ state })} testId="rpf-state" />
      </> : exam === 'comedk' ? <>
        <div className="rk-two"><Box testId="rpf-comedk-marks" exam="comedk" kind="marks" value={p.comedk.marks} onChange={v => comedk({ marks: v })} />
          <Box testId="rpf-comedk-rank" exam="comedk" kind="rank" value={p.comedk.rank} onChange={v => comedk({ rank: v })} /></div>
        <small className="rk-dim">COMEDK mein sabki ek hi merit list hai, isliye category nahi lagti. Dono bhare ho to Rank chalegi.</small>
      </> : <>
        <Box testId="rpf-bitsat-score" exam="bitsat" kind="marks" value={p.bitsat.score} onChange={v => { setP(x => ({ ...x, bitsat: { score: v } })); setProblem(''); }} />
        <small className="rk-dim">BITSAT mein sirf score chalta hai: percentile, rank aur category nahi lagte.</small>
      </>}
      <Problem text={problem} testId="rpf-error" />
      <Go label="Save karo" onClick={save} testId="rpf-save" />
      {start.at ? <button type="button" className="rk-link" onClick={() => { clearProfile(); onClose(false); }} data-testid="rpf-clear">Meri details hatao</button> : null}
    </div>
  </section>;
}
