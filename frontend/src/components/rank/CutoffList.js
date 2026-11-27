// The Cut off answer: heading, the optional score box ("sirf eligible dikhao"), then one card per row with every round's
// cut-off in small boxes (green = the student's rank is inside that round, amber = on the edge), 25 at a time, and the nearest misses.
import React, { useState } from 'react';
import { ArrowDown, ArrowUp, Check, Plus } from 'lucide-react';
import { fmt, fmtRange, KIND, LEVEL, LEVELS, TAG } from './rankApi';
import { Chip, Field, Go, Heading, Notes, PdfButton, Problem, Tag } from './RankUi';
import { shortlist } from './rankStore';
import { readScore, SCORE, typed } from './profile';

const PAGE = 25;
const KIND_LABEL = { marks: 'Marks', percentile: 'Percentile', rank: 'Rank' };
const WHAT = { jee: { college: 'branches', branch: 'college-branch' }, comedk: { college: 'courses', branch: 'college-course' }, bitsat: { college: 'programs', branch: 'campus' } };

export function CutoffList({ data, busy, pick, onPick, kinds, level, onLevel, query }) {
  const [editing, setEditing] = useState(false), [problem, setProblem] = useState(''), [shown, setShown] = useState(PAGE);
  const you = data.you, rule = SCORE[data.exam][pick.kind] || SCORE[data.exam].marks, what = WHAT[data.exam][data.by];
  const count = you ? `${data.eligible} / ${data.total} ${what} eligible${data.rows.length < (data.eligible ?? 0) ? ` · top ${data.rows.length} dikh rahe` : ''}`
    : data.limit && data.total > data.limit ? `Top ${data.limit} of ${data.total} ${what} · sabse zyada demand wale pehle`
    : `${data.total} ${what} · ${data.metric === 'score' ? '5 saal ke cutoff score' : 'har round ki closing rank'}`;
  const apply = () => {
    const v = readScore(data.exam, pick.kind, pick.text);
    if (typeof v !== 'number') { setProblem(v ?? 'Pehle apna score daalo.'); return; }
    setProblem(''); setEditing(false); setShown(PAGE); onPick({ score: { [pick.kind]: v } });
  };
  const showAll = () => { setEditing(false); setProblem(''); setShown(PAGE); onPick({ score: null }); };
  return <div className="rk-stack rk-reveal" data-testid="cut-list">
    <section className="rk-panel rk-cut-head" data-testid="cut-head">
      <header className="rk-panel-head"><h3><i aria-hidden="true" />{data.title}</h3>{busy ? <small className="rk-dim">…</small> : data.kind && KIND[data.kind] ? <span className={'rk-tag kind-' + data.kind}>{KIND[data.kind]}</span> : null}</header>
      <div className="rk-panel-body">
        <small className="rk-dim">{data.sub}</small>
        <b className="rk-cut-count" data-testid="cut-count">{count}</b>
        {you && !editing ? <div className="rk-cut-box" data-testid="cut-you">
          <small className="rk-eyebrow">AAPKA SCORE</small>
          <b data-testid="cut-you-line">{you.line}</b>
          {[you.cat_rank, you.pwd_rank].filter(Boolean).map(x => <small key={x.label} className="rk-dim">{x.label}: {fmtRange(x.range)}</small>)}
          <div className="rk-chips">{['safe', 'likely', 'borderline'].map(c => <span key={c} className={'rk-tag tag-' + c} data-testid={`cut-count-${c}`}>{TAG[c]} {you.counts[c]}</span>)}</div>
          <small className="rk-dim" data-testid="cut-you-key">{data.metric === 'score' ? 'Hara box = 2026 ka cutoff aap clear karte ho. Peela = kinare par, pakka nahi.' : 'Hara box = us round mein aap andar. Peela = kinare par, pakka nahi.'}</small>
          {you.check ? <small className="rk-cut-check" data-testid="cut-you-check">{you.check}</small> : null}
          <div className="rk-two"><button type="button" className="rk-ghost" onClick={() => setEditing(true)} data-testid="cut-edit">Score badlo</button>
            <button type="button" className="rk-ghost" onClick={showAll} data-testid="cut-clear">Sab cutoffs dikhao</button></div>
        </div> : <div className="rk-cut-box" data-testid="cut-score">
          <b>Sirf wahi dekhna hai jahan aap eligible ho?</b>
          <small className="rk-dim">Apna score daalo (optional). Sirf Safe, Likely aur Borderline options bachenge.</small>
          {kinds.length > 1 ? <div className="rk-chips">{kinds.map(k => <Chip key={k} on={pick.kind === k} onClick={() => { if (k !== pick.kind) onPick({ kind: k, text: '' }); setProblem(''); }} testId={`cut-kind-${k}`}>{KIND_LABEL[k]}</Chip>)}</div> : null}
          <Field label={rule.label} testId="cut-score-input" inputMode={rule.decimal ? 'decimal' : 'numeric'} placeholder={rule.hint} value={pick.text}
            onKeyDown={e => e.key === 'Enter' && apply()} onChange={e => { onPick({ text: typed(rule, e.target.value) }); setProblem(''); }} />
          {data.exam === 'jee' && pick.kind === 'marks' ? <div className="rk-row"><span className="rk-row-label">Paper</span>
            {LEVELS.map(l => <Chip key={l} tone={'lvl-' + l} on={level === l} onClick={() => onLevel(l)} testId={`cut-level-${l}`}>{LEVEL[l]}</Chip>)}</div> : null}
          <Problem text={problem} testId="cut-score-error" />
          <Go label="Eligible dikhao" busy={busy && !!pick.score} onClick={apply} testId="cut-apply" />
          {pick.score ? <button type="button" className="rk-link" onClick={showAll} data-testid="cut-clear">Sab cutoffs dikhao</button> : null}
        </div>}
        {data.rows.length ? <div className="rk-actions"><PdfButton path="/cutoff" body={query} filename={`JEELIVE-cutoff-${data.title}.pdf`} label={you ? 'Eligible list ki PDF' : 'Cut off list ki PDF'} testId="cut-pdf" /></div> : null}
      </div>
    </section>
    {data.rows.length === 0 ? <p className="rk-dim" data-testid="cut-empty">{you ? `Is score par yahan 2026 mein koi option eligible nahi tha.${data.near.length ? ' Neeche dekho, kitna door ho.' : ''}` : 'Aapki category, gender aur home state ke liye yahan 2026 ki koi seat nahi thi.'}</p> : null}
    <div className="rk-list">{data.rows.slice(0, shown).map((r, i) => <Row key={r.id} r={r} by={data.by} metric={data.metric} n={i + 1} testId={`cut-row-${i}`} />)}</div>
    {data.rows.length > shown ? <button type="button" className="rk-outline" onClick={() => setShown(shown + PAGE)} data-testid="cut-more">Aur dikhao ({data.rows.length - shown} baaki)</button> : null}
    {data.near.length ? <><Heading title="Bas thoda sa door" sub="Thoda aur, aur ye bhi aapke" />
      <div className="rk-list" data-testid="cut-near">{data.near.map((r, i) => <Row key={r.id} r={r} by={data.by} metric={data.metric} testId={`cut-near-${i}`} near />)}</div></> : null}
    <Notes lines={data.notes} testId="cut-notes" />
  </div>;
}

/** One college-branch: who and where, every round in small boxes, then the final line, trend and Compare. */
function Row({ r, by, metric, n, testId, near }) {
  const saved = shortlist.useList().some(s => s.id === r.save.id);
  // A round the college does not have (JAC Delhi stops at R4) is left out; last year's final closes the set.
  const boxes = [...r.cells.filter(c => !c.na), ...(r.prev ? [{ label: r.prev.label, close: r.prev.close, past: true }] : [])];
  const need = r.need?.level ? `≈ ${r.need.marks}+ marks (${LEVEL[r.need.level]} paper)` : r.need ? `≈ ${r.need.marks}+ marks / 180` : null;
  const final = metric === 'score' ? `${r.final.label} cutoff: ${r.final.close} / 390`
    : [`Closing ${r.final.label}: ${fmt(r.final.close)} ${r.rank_type}`, need, r.seats ? `${r.seats} seats` : null, r.fee ? `₹${fmt(r.fee)} / saal` : null].filter(Boolean).join(' · ');
  return <article className={'rk-cut-row' + (near ? ' is-near' : '')} data-testid={testId}>
    <i className={'rk-college-edge edge-' + (r.tag || (near ? 'near' : 'none'))} />
    <header>{n ? <span className="rk-cut-n">{n}</span> : null}
      <div><b data-testid={testId + '-title'}>{by === 'college' ? r.branch : r.college}</b>{by === 'branch' ? <span>{r.branch}</span> : null}<small>{by === 'branch' ? `${r.place} · ${r.path}` : r.path}</small></div>
      <Tag tag={r.tag} /></header>
    <div className="rk-rounds">{boxes.map(c => <span key={c.label} className={'rk-round' + (c.past ? ' is-past' : '') + (c.state === 'in' ? ' is-in' : c.state === 'edge' ? ' is-edge' : '')}
      aria-label={`${c.label}: ${c.close ? fmt(c.close) : 'nahi'}${c.state === 'in' ? ', aap andar' : c.state === 'edge' ? ', kinare par' : ''}`}>
      <small>{c.label}{c.crl && c.close ? ' · CRL' : ''}</small><b>{c.close ? fmt(c.close) : '—'}</b></span>)}</div>
    <p className="rk-cut-final" data-testid={testId + '-final'}>{final}</p>
    {r.gap ? <p className="rk-college-gap" data-testid={testId + '-gap'}>{r.gap}</p> : null}
    <footer>{r.trend ? <span className={'rk-cut-trend t-' + r.trend.dir} data-testid={testId + '-trend'}>{r.trend.dir === 'tough' ? <ArrowUp size={13} /> : r.trend.dir === 'easy' ? <ArrowDown size={13} /> : null}{r.trend.label}</span> : <span />}
      <button type="button" className={'rk-act cmp' + (saved ? ' is-on' : '')} aria-pressed={saved} onClick={() => shortlist.toggle(r.save)} data-testid={testId + '-save'}>
        {saved ? <Check size={15} /> : <Plus size={15} />}{saved ? 'Compare mein' : 'Compare'}</button></footer>
  </article>;
}
