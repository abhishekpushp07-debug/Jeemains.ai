// Cut off: pick ONE thing, a college or a branch, and read every round's 2026 cut-off (JEE Main, BITSAT, COMEDK).
// College -> all its branches; branch -> its most wanted college-branches. A score is optional: with it only the rows the
// student can reach stay, tagged Safe, Likely or Borderline. The app server works everything out (POST /api/rank/cutoff).
import React, { useEffect, useMemo, useState } from 'react';
import { ChevronRight, Search, X } from 'lucide-react';
import { CATEGORY_LABEL, CATS, getCutoffOptions, getMeta, rank } from './rankApi';
import { Chip, Err, Panel, RankSheet, StateSelect, Switch } from './RankUi';
import { useRankData } from './rankStore';
import { KEYS } from './profile';
import { CutoffList } from './CutoffList';

const PICK = { by: 'college', college: null, branch: null, kind: 'marks', text: '', score: null };
const DEFAULT = { exam: 'jee', level: 'normal', category: 'GEN', female: false, pwd: false, state: null, jee: PICK, comedk: PICK, bitsat: PICK };
const EXAMS = [{ key: 'jee', label: 'JEE Main' }, { key: 'bitsat', label: 'BITSAT' }, { key: 'comedk', label: 'COMEDK' }];
const COLLEGE = { tab: 'College se', pick: 'College chuno', hint: 'College ka naam ya shehar likho', none: 'Koi college nahi mila. Naam thoda chhota likh kar dekho.' };
const BRANCH = { tab: 'Branch se', pick: 'Branch chuno', hint: 'Branch likho, jaise CSE ya Mechanical', none: 'Koi branch nahi mili. Naam thoda chhota likh kar dekho.' };
const WORDS = { jee: { college: COLLEGE, branch: BRANCH }, comedk: { college: COLLEGE, branch: BRANCH },
  bitsat: { college: { tab: 'Campus se', pick: 'Campus chuno', hint: 'Pilani, Goa ya Hyderabad', none: 'Koi campus nahi mila.' },
    branch: { tab: 'Program se', pick: 'Program chuno', hint: 'Program likho, jaise Computer Science', none: 'Koi program nahi mila. Naam thoda chhota likh kar dekho.' } } };
const ABOUT = {
  jee: 'Category, gender aur home state se seat ka raasta badalta hai, isliye cutoff bhi. Home state se NIT ki Home-state seat aur JAC Delhi ki Delhi seat khulti hai.',
  comedk: 'Sirf GM (All India) seats. COMEDK mein category se cutoff nahi badalta.',
  bitsat: 'BITS round-wise cutoff publish nahi karta, isliye 2022 se 2026 tak ke final cutoff score dikhenge. Category se cutoff nahi badalta.',
};

function load() {
  try { const v = JSON.parse(localStorage.getItem(KEYS.cutoff) || '{}'); return { ...DEFAULT, ...v, jee: { ...PICK, ...v.jee }, comedk: { ...PICK, ...v.comedk }, bitsat: { ...PICK, ...v.bitsat } }; }
  catch { return DEFAULT; }
}

export function Cutoff() {
  const [st, setSt] = useState(load), [picking, setPicking] = useState(false);
  const { data: meta } = useRankData(getMeta);
  const lists = useRankData(getCutoffOptions);
  const patch = x => setSt(prev => { const next = { ...prev, ...x }; try { localStorage.setItem(KEYS.cutoff, JSON.stringify(next)); } catch {} return next; });
  const exam = st.exam, p = st[exam], w = WORDS[exam][p.by];
  const pick = x => patch({ [exam]: { ...p, ...x } });
  const options = lists.data?.[exam]?.[p.by === 'college' ? 'colleges' : 'branches'] || [];
  const chosen = options.find(o => o.key === (p.by === 'college' ? p.college : p.branch));
  const q = chosen ? { exam, by: p.by, key: chosen.key, ...p.score, ...(exam === 'jee' ? { level: st.level, category: st.category, female: st.female, pwd: st.pwd, state: st.state } : {}) } : null;
  const t = useCutoff(q);
  // While the next list loads the old one belongs to another choice: it is never shown under this one.
  const data = t.data && q && t.data.exam === exam && t.data.by === p.by && t.data.key === q.key ? t.data : null;
  return <>
    <Switch prefix="cut-exam" value={exam} onChange={e => patch({ exam: e })} items={EXAMS} />
    <Err error={lists.error} testId="cut-options-error" />
    <Panel form title="Kiska cut off dekhna hai?" testId="cut-form">
      <Switch prefix="cut-by" value={p.by} onChange={by => pick({ by })} items={[{ key: 'college', label: WORDS[exam].college.tab }, { key: 'branch', label: WORDS[exam].branch.tab }]} />
      <button type="button" className="rk-picker" onClick={() => setPicking(true)} disabled={!lists.data} data-testid="cut-pick">
        <span>{p.by === 'college' ? (exam === 'bitsat' ? 'Campus' : 'College') : exam === 'bitsat' ? 'Program' : 'Branch'}</span><b>{chosen?.title || w.pick}</b><ChevronRight size={16} /></button>
      {exam === 'jee' ? <>
        <div className="rk-chips">{CATS.map(c => <Chip key={c} on={st.category === c} onClick={() => patch({ category: c })} testId={`cut-cat-${c}`}>{CATEGORY_LABEL[c]}</Chip>)}</div>
        <div className="rk-chips"><Chip on={st.female} onClick={() => patch({ female: !st.female })} testId="cut-female">Female</Chip>
          <Chip on={st.pwd} onClick={() => patch({ pwd: !st.pwd })} testId="cut-pwd">PwD</Chip></div>
        <StateSelect states={meta?.states || []} value={st.state} onChange={state => patch({ state })} testId="cut-state" />
      </> : null}
      <small className="rk-dim">{ABOUT[exam]}</small>
    </Panel>
    <Err error={t.error} retry={t.retry} testId="cut-error" />
    {data && lists.data ? <CutoffList key={`${exam}-${p.by}-${data.key}`} data={data} busy={t.busy} pick={p} onPick={pick} kinds={lists.data[exam].score}
      level={st.level} onLevel={level => patch({ level })} query={q} />
      : q ? (t.error ? null : <div className="rk-loading" data-testid="cut-loading" />)
      : <p className="rk-dim" data-testid="cut-hint">{p.by === 'college' ? `${WORDS[exam].college.pick}: uski har branch ka har round ka cut off dikhega.` : `${WORDS[exam].branch.pick}: us branch ke top 100 college, har round ke cut off ke saath dikhenge.`} Phir apna score daal kar sirf wahi dekh sakte ho jahan aap eligible ho.</p>}
    <OptionSheet key={`${exam}-${p.by}`} open={picking} title={w.pick} options={options} hint={w.hint} none={w.none}
      onPick={k => { pick(p.by === 'college' ? { college: k } : { branch: k }); setPicking(false); }} onClose={() => setPicking(false)} />
  </>;
}

/** The answer for the current choice; a newer request always wins over an older one still on the way. */
function useCutoff(q) {
  const key = q ? JSON.stringify(q) : null;
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(''), [tries, setTries] = useState(0);
  useEffect(() => {
    if (!key) return;
    let live = true;
    setBusy(true); setError('');
    rank.cutoff(JSON.parse(key)).then(d => { if (live) setData(d); }).catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(false); });
    return () => { live = false; };
  }, [key, tries]);
  return { data, busy, error, retry: () => setTries(n => n + 1) };
}

const squash = t => String(t || '').toLowerCase().replace(/[.\-,()&/]/g, ' ').replace(/\s+/g, ' ');
function OptionSheet({ open, title, options, hint, none, onPick, onClose }) {
  const [text, setText] = useState('');
  const index = useMemo(() => options.map(o => { const h = squash(`${o.title} ${o.sub} ${o.find || ''}`); return [o, h + ' ' + h.replace(/ /g, '')]; }), [options]);
  const words = squash(text).trim().split(' ').filter(Boolean);
  const hits = index.filter(([, hay]) => words.every(w => hay.includes(w))).slice(0, 60).map(([o]) => o);
  return <RankSheet open={open} onClose={onClose} title={title} sub={`${options.length} mein se chuno`} testId="cut-pick-sheet">
    <label className="rk-search-box"><Search size={18} /><input value={text} onChange={e => setText(e.target.value)} placeholder={hint} aria-label={title} data-testid="cut-pick-sheet-input" />
      {text ? <button type="button" onClick={() => setText('')} aria-label="Clear" data-testid="cut-pick-sheet-clear"><X size={16} /></button> : null}</label>
    {hits.length ? <ul className="rk-search-list" role="listbox">{hits.map((o, i) => <li key={o.key}><button type="button" onClick={() => onPick(o.key)} data-testid={`cut-pick-sheet-hit-${i}`}>
      <b>{o.title}</b><small>{o.sub}</small></button></li>)}</ul> : <p className="rk-dim" data-testid="cut-pick-sheet-empty">{none}</p>}
  </RankSheet>;
}
