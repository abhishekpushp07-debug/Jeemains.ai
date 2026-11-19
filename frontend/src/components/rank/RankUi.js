// Shared pieces of the Rank page: jewel tool tiles, form panels in each tool's colour, chips, the dark metal Rank Card,
// college cards, round ladders, sheets, PDF and WhatsApp buttons.
import React, { createContext, useContext, useState } from 'react';
import { ArrowRight, Check, ChevronRight, ChevronUp, Download, Hand, Loader2, Pencil, Plus, Target, CheckCheck, BarChart3 } from 'lucide-react';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '../ui/sheet';
import { downloadPdf, fmt, TAG, KIND, shareWhatsApp } from './rankApi';

/** The open tool (name, icon): its form panel wears the tool's colour band. */
export const ToolCtx = createContext(null);

// The app's brilliant-cut diamond in side view: white facets, a few in the tile's own colour (currentColor), sparkles at the tips.
const FACETS = [['2,30 30,8 18,30', .5], ['30,8 34,30 18,30', .9], ['30,8 43.3,8 34,30', .35, 1], ['43.3,8 50,30 34,30', .75], ['43.3,8 56.7,8 50,30', .95],
  ['56.7,8 66,30 50,30', .4, 1], ['56.7,8 70,8 66,30', .8], ['70,8 82,30 66,30', .3], ['70,8 98,30 82,30', .6, 1], ['2,30 18,30 50,78', .3], ['18,30 34,30 50,78', .7, 1],
  ['34,30 50,30 50,78', .95], ['50,30 66,30 50,78', .5], ['66,30 82,30 50,78', .85, 1], ['82,30 98,30 50,78', .4]];
const star = (x, y, r) => `M${x} ${y - r}Q${x} ${y} ${x + r} ${y}Q${x} ${y} ${x} ${y + r}Q${x} ${y} ${x - r} ${y}Q${x} ${y} ${x} ${y - r}Z`;
// Drawn from fixed markup: the preview editor wraps dynamic JSX children in <span>, which an SVG would not draw.
const gemMarkup = sparkle => FACETS.map(([p, o, t]) => `<polygon points="${p}" fill="${t ? 'currentColor' : '#FFFFFF'}" fill-opacity="${o}" stroke="#FFFFFF" stroke-opacity=".75" stroke-width=".7" stroke-linejoin="round"/>`).join('')
  + (sparkle ? `<path d="${star(2, 30, 10)}" fill="#FFFFFF" class="rk-twinkle"/><path d="${star(86, 11, 6)}" fill="#FFFFFF" class="rk-twinkle b"/>` : '');
const GEM = { plain: { __html: gemMarkup(false) }, sparkle: { __html: gemMarkup(true) } };
export const Gem = ({ size = 46, className = '', sparkle }) => <svg className={'rk-gem ' + className} width={size} height={size * 0.8} viewBox="-8 -8 116 96" aria-hidden="true"
  dangerouslySetInnerHTML={sparkle ? GEM.sparkle : GEM.plain} />;

/** The same stone seen from above in hairlines: the quiet watermark of the black metal Rank Card. */
const at = (r, deg) => { const a = ((deg - 90) * Math.PI) / 180; return `${(100 + r * Math.cos(a)).toFixed(1)},${(100 + r * Math.sin(a)).toFixed(1)}`; };
const TABLE = Array.from({ length: 8 }, (_, k) => at(46, 22.5 + 45 * k)).join(' ');
const STAR = Array.from({ length: 16 }, (_, k) => at(k % 2 ? 46 : 72, 22.5 * k)).join(' ');
const RAYS = [...Array.from({ length: 8 }, (_, k) => `M${at(46, 22.5 + 45 * k)}L${at(96, 22.5 + 45 * k)}`),
  ...Array.from({ length: 8 }, (_, k) => `M${at(72, 45 * k)}L${at(96, 45 * k - 14)}M${at(72, 45 * k)}L${at(96, 45 * k + 14)}`)].join('');
const DiamondLine = () => <svg className="rk-card-watermark" viewBox="0 0 200 200" aria-hidden="true"><g fill="none" stroke="#FFFFFF" strokeOpacity=".09" strokeWidth=".8">
  <circle cx="100" cy="100" r="96" /><polygon points={STAR} /><polygon points={TABLE} /><path d={RAYS} /></g></svg>;
const DiamondMark = () => <svg width="20" height="16" viewBox="-6 -6 112 92" aria-hidden="true"><g fill="none" stroke="#EEF2F7" strokeOpacity=".85" strokeWidth="4" strokeLinejoin="round">
  <polygon points="30,8 70,8 98,30 50,78 2,30" /><path d="M2 30H98M30 8L18 30L50 78L34 30L43.3 8M70 8L82 30L50 78L66 30L56.7 8M34 30L50 8L66 30" /></g></svg>;
const Stars = () => <span className="rk-stars" aria-hidden="true"><svg width="15" height="15"><path d={star(7.5, 7.5, 7.5)} fill="#FFFFFF" /></svg><svg width="8" height="8"><path d={star(4, 4, 4)} fill="#FFFFFF" /></svg></span>;

export function Switch({ items, value, onChange, prefix }) {
  return <div className="rk-switch" role="tablist" data-testid={prefix}>
    {items.map(i => <button key={i.key} type="button" role="tab" aria-selected={value === i.key} className={value === i.key ? 'is-on' : ''}
      onClick={() => onChange(i.key)} data-testid={`${prefix}-${i.key}`}>{i.label}</button>)}
  </div>;
}

export const Chip = ({ on, onClick, children, testId, tone }) => <button type="button" aria-pressed={!!on} onClick={onClick}
  className={'rk-chip' + (on ? ' is-on' : '') + (tone ? ' tone-' + tone : '')} data-testid={testId}>{on && !tone ? <Check size={14} /> : null}{children}</button>;

/** A white panel; with `form` it is the open tool's form: framed in the tool's colour with a solid header band (tool icon, tool name, title). */
export function Panel({ title, form, right, testId, children }) {
  const tool = useContext(ToolCtx);
  const band = form && tool;
  return <section className={'rk-panel' + (form ? ' is-form' : '')} data-testid={testId}>
    {band ? <header className="rk-form-head" data-testid={testId ? testId + '-head' : undefined}><span className="rk-form-icon"><tool.Icon size={16} /></span>
      <span className="rk-form-title"><small>{tool.title.toUpperCase()}</small>{title ? <b>{title}</b> : null}</span>{right}</header>
      : title ? <header className="rk-panel-head"><h3><i aria-hidden="true" />{title}</h3>{right}</header> : null}
    <div className="rk-panel-body">{children}</div>
  </section>;
}

export const Field = ({ label, testId, ...p }) => <label className="rk-field"><span>{label}</span><input data-testid={testId} {...p} /></label>;

export const Go = ({ label, busy, onClick, testId }) => <button type="button" className="rk-go" onClick={onClick} disabled={busy} data-testid={testId}>
  {busy ? <Loader2 className="spin" size={18} /> : null}{label}<ArrowRight size={18} /></button>;

/** The score line after Show with a bright Edit pill in the tool's colour; the whole row reopens the form. */
export function Summary({ text, onEdit, testId }) {
  const tool = useContext(ToolCtx);
  return <button type="button" className="rk-summary" onClick={onEdit} aria-label={`${text}. Edit karke doosra number dekho`} data-testid={testId}>
    <i className="rk-summary-shine" aria-hidden="true" />
    {tool ? <span className="rk-summary-icon"><tool.Icon size={15} /></span> : null}
    <span className="rk-summary-text"><b>{text.replace(/-/g, '\u2011')}</b><small data-testid={testId + '-hint'}>Doosra number dekhna hai?</small></span>
    <span className="rk-summary-edit" data-testid={testId + '-edit'}><Pencil size={15} />Edit</span>
  </button>;
}

export const Problem = ({ text, testId }) => text ? <p className="rk-problem" role="alert" data-testid={testId}>{text}</p> : null;
export const Err = ({ error, retry, testId }) => error ? <div className="rk-error" role="alert" data-testid={testId}><span>{error}</span>{retry ? <button type="button" onClick={retry}>Retry</button> : null}</div> : null;
export const Notes = ({ lines, testId }) => <ul className="rk-notes" data-testid={testId}>{lines.filter(Boolean).map(l => <li key={l}>{l}</li>)}</ul>;
export const Tag = ({ tag }) => tag ? <span className={'rk-tag tag-' + tag}>{TAG[tag]}</span> : null;
export const Kind = ({ kind }) => <span className={'rk-tag kind-' + kind}>{KIND[kind] || kind}</span>;

/** The dark metal Rank Card: brand + badge, the big number, a hairline rule, small ranks and the summary with its № serial. */
export function RankCard({ testId, badge, eyebrow, big, caps, gem, rule, smalls = [], note, summary, serial, of, foot }) {
  return <article className="rk-card" data-testid={testId}>
    <DiamondLine />
    <i className="rk-card-sheen" aria-hidden="true" /><i className="rk-card-edge" aria-hidden="true" />
    <div className="rk-card-top"><span className="rk-card-brand"><DiamondMark />JEELIVE.AI</span><span className="rk-card-badge">{badge}</span></div>
    <small className="rk-eyebrow">{eyebrow}</small>
    <div className="rk-big-row"><strong className="rk-big" data-testid={testId + '-big'}>{big}</strong>{gem ? <Gem size={62} className="rk-card-gem" sparkle /> : <Stars />}</div>
    {caps ? <span className="rk-card-caps" data-testid={testId + '-caps'}>{caps}</span> : null}
    {rule ? <div className="rk-rule" data-testid={testId + '-rule'}><i /><span>{rule}</span></div> : null}
    {smalls.length ? <div className="rk-smalls">{smalls.map(s => <span key={s.label} className="rk-small" data-testid={s.testId}><small>{s.label.toUpperCase()}</small><b>{s.value}</b></span>)}</div> : null}
    {note ? <small className="rk-card-note">{note}</small> : null}
    <footer className="rk-card-foot">{foot || <>
      <div><small className="rk-eyebrow">YOUR SCORE</small><b data-testid={testId + '-summary'}>{summary.toUpperCase()}</b></div>
      {serial ? <div className="rk-serial" data-testid={testId + '-serial'}><small>№ </small><b>{serial}</b>{of ? <i> / {of}</i> : null}</div> : null}
    </>}</footer>
  </article>;
}

export function PdfButton({ path, body, filename, label = 'PDF download', testId }) {
  const [busy, setBusy] = useState(false), [err, setErr] = useState('');
  const go = async () => { setBusy(true); setErr(''); try { await downloadPdf(path, body, filename); } catch (e) { setErr(e.message); } finally { setBusy(false); } };
  return <span className="rk-pdf-wrap"><button type="button" className="rk-ghost" onClick={go} disabled={busy} data-testid={testId}>
    {busy ? <Loader2 className="spin" size={16} /> : <Download size={16} />}{label}</button>{err ? <small className="rk-problem">{err}</small> : null}</span>;
}

export const WaButton = ({ text, testId, label = 'WhatsApp par bhejo' }) => <button type="button" className="rk-wa" onClick={() => shareWhatsApp(text)} data-testid={testId}>
  <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.2 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.8s.7-2 .9-2.3c.3-.3.6-.3.8-.3h.6c.2 0 .4 0 .6.5l.9 2.1c.1.2.1.4 0 .6l-.4.6-.4.4c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.7-.1l.9-1.1c.2-.3.4-.2.7-.1l2 1c.3.1.5.2.5.3.1.2.1.6-.1 1.2Z" /></svg>{label}</button>;

/** One college as a card that reads like a button; "Add to Compare" and "Dream college" sit under it. */
export function CollegeCard({ testId, rank, edge, title, tags, sub, line, stats, note, teaser, viewed, pulse, open, onOpen, compared, onCompare, dream, children }) {
  return <div className={'rk-college' + (rank && rank <= 3 ? ` is-top wash-${rank}` : '')} data-testid={testId + '-wrap'}>
    <i className={'rk-college-edge edge-' + edge} />
    <button type="button" className="rk-college-main" onClick={onOpen} aria-expanded={open} data-testid={testId}>
      <span className="rk-college-head">
        {rank ? <span className={'rk-medal m' + Math.min(rank, 4)} data-testid={testId + '-medal'}>{rank}</span> : null}
        <span className="rk-college-text"><strong>{title}</strong>{tags ? <span className="rk-tags">{tags}</span> : null}<span className="rk-college-sub">{sub}</span>{line ? <small>{line}</small> : null}</span>
      </span>
      <span className="rk-stats">{stats.map(s => <span key={s.label} className="rk-stat" data-testid={s.testId}><small>{s.label}</small><b className={s.tone ? 'tone-' + s.tone : ''}>{s.value}</b>{s.sub ? <i>{s.sub}</i> : null}</span>)}</span>
      {note ? <span className="rk-college-gap" data-testid={testId + '-gap'}>{note}</span> : null}
      {children}
      <span className="rk-college-foot">
        <span className={'rk-teaser' + (viewed ? ' is-seen' : '')}>{viewed ? <Check size={15} /> : <BarChart3 size={15} />}{viewed ? `Dekha · ${teaser}` : teaser}</span>
        <span className={'rk-cta' + (pulse ? ' is-pulse' : '')} data-testid={testId + '-cta'}>{open ? 'Band karo' : 'Cutoff dekho'}{open ? <ChevronUp size={16} /> : <ChevronRight size={16} />}</span>
      </span>
    </button>
    <CardActions testId={testId} compared={compared} onCompare={onCompare} dream={dream} />
  </div>;
}

/** The app's 2025 → 2026 box (final round, same seat; a higher closing rank this year = easier); "Naya" when 2025 had no such seat. */
export function trendStat(y25, y26, testId) {
  if (!y25 || !y26) return { label: '2025 SE', value: 'Naya', sub: '2025 mein nahi tha', tone: 'soft', testId };
  const d = y26 - y25, same = Math.abs(d) < y25 * 0.03;
  return { label: '2025 SE', value: same ? '≈ Same' : d > 0 ? '▼ Aasaan' : '▲ Tough', sub: `${fmt(y25)} → ${fmt(y26)}`, tone: same ? 'soft' : d > 0 ? 'good' : 'bad', testId };
}

/** "Add to Compare" and "Dream college" under a card, with a one-line confirmation. */
export function CardActions({ testId, compared, onCompare, dream }) {
  const [cmpMsg, setCmpMsg] = useState(false);
  return <>
    <div className="rk-college-actions">
      <button type="button" className={'rk-act cmp' + (compared ? ' is-on' : '')} aria-pressed={compared} onClick={() => { setCmpMsg(!compared); onCompare(); }} data-testid={testId + '-compare'}>
        {compared ? <Check size={16} /> : <Plus size={16} />}{compared ? 'In Compare' : 'Add to Compare'}</button>
      {dream ? <button type="button" className={'rk-act dream' + (dream.on ? ' is-on' : '')} aria-pressed={dream.on} onClick={dream.toggle} disabled={dream.busy} data-testid={testId + '-dream'}>
        {dream.busy ? <Loader2 className="spin" size={16} /> : <Target size={16} />}{dream.on ? 'Dream ✓' : 'Dream college'}</button> : null}
    </div>
    {cmpMsg && compared ? <p className="rk-act-msg cmp" data-testid={testId + '-compare-msg'}>Compare mein juda. College compare tile mein 2–3 ko side by side dekho.</p> : null}
    {dream?.msg ? <p className="rk-act-msg dream" data-testid={testId + '-dream-msg'}>{dream.msg}</p> : null}
  </>;
}

export const TapHint = ({ testId, viewed, what = 'college' }) => <div className="rk-hint" data-testid={testId}>
  <span className="rk-hint-icon">{viewed ? <CheckCheck size={20} /> : <Hand size={20} />}</span>
  <span><b>{viewed ? `${viewed} ${what} dekhe, shabaash!` : `Kisi bhi ${what} card par tap karo`}</b>
    <small>{viewed ? 'Aur dekho. Sahi choice wahi jo poora data dekh kar ho.' : 'Har round ka cutoff, seats aur 2025 se trend: sab andar hai.'}</small></span>
</div>;

export const Heading = ({ title, sub }) => <div className="rk-heading"><b>{title}</b>{sub ? <small>{sub}</small> : null}</div>;

export function Pager({ page, pages, onPage, prefix }) {
  if (pages <= 1) return null;
  return <div className="rk-pager">{Array.from({ length: pages }, (_, i) => i + 1).map(p => <button key={p} type="button" className={p === page ? 'is-on' : ''}
    onClick={() => onPage(p)} data-testid={`${prefix}-page-${p}`}>Page {p}</button>)}</div>;
}

const SEEN = 'rank.cta.seen.v1';
/** The first card's button breathes until the student opens any college once (remembered in this browser). */
export function useCardViews() {
  const [seen, setSeen] = useState(() => { try { return !!localStorage.getItem(SEEN); } catch { return true; } });
  const [viewed, setViewed] = useState(() => new Set());
  const mark = id => { setViewed(v => (v.has(id) ? v : new Set(v).add(id))); if (!seen) { setSeen(true); try { localStorage.setItem(SEEN, '1'); } catch {} } };
  return { pulse: !seen && viewed.size === 0, viewed, mark };
}

export function RankSheet({ open, onClose, title, sub, testId, children }) {
  return <Sheet open={open} onOpenChange={v => { if (!v) onClose(); }}>
    <SheetContent side="right" className="rk-sheet" data-testid={testId}>
      <SheetHeader className="rk-sheet-head"><SheetTitle>{title}</SheetTitle>{sub ? <SheetDescription>{sub}</SheetDescription> : <SheetDescription className="sr-only">College details</SheetDescription>}</SheetHeader>
      <div className="rk-sheet-body">{children}</div>
    </SheetContent>
  </Sheet>;
}

/** Every round's closing rank as a red bar; the dark line and soft band are the student's rank (best to worst estimate). */
export function RoundLadder({ title, sub, rounds, cells, prev, quiet, testId }) {
  const closes = [...cells.map(c => c.close), prev?.close].filter(Boolean);
  const yours = quiet ? [] : cells.map(c => c.hi ?? c.mine ?? 0);
  const top = Math.max(1, ...closes, ...yours) * 1.04;
  const first = quiet ? null : cells.find(c => c.mine) ?? null;
  return <div className="rk-ladder" data-testid={testId}>
    <small className="rk-eyebrow red">ROUND-WISE CLOSING RANK</small><b>{title}</b>{sub ? <small>{sub}</small> : null}
    {rounds.map((rd, i) => <Rung key={rd} label={rd} cell={cells[i] ?? { close: null, in: false }} top={top} quiet={quiet} testId={`${testId}-${i}`} />)}
    {prev ? <><hr /><Rung label={prev.label} cell={{ close: prev.close, in: false, mine: first?.mine, hi: first?.hi }} top={top} past testId={`${testId}-prev`} /></> : null}
    {quiet ? null : <div className="rk-legend"><span><i className="mark" />kaali line = aapki rank</span><span><i className="bar" />laal patti = closing rank</span></div>}
  </div>;
}

function Rung({ label, cell, top, past, quiet, testId }) {
  const has = !!cell.close;
  const fill = has ? Math.max(0.04, cell.close / top) : 0;
  const mark = !quiet && cell.mine ? Math.min(1, cell.mine / top) : null;
  const band = mark !== null && cell.hi && cell.hi > cell.mine ? Math.min(1, cell.hi / top) - mark : 0;
  const state = !has || past || quiet ? null : (cell.hi != null ? cell.close >= cell.hi : cell.in) ? 'in' : cell.in ? 'maybe' : 'out';
  const empty = past ? '2025 mein is seat ka data nahi' : cell.unpublished ? 'JAC ne ye rank publish nahi ki' : 'is round mein allotment nahi';
  return <div className="rk-rung" data-testid={testId}>
    <span className="rk-rung-label">{label}</span>
    <span className="rk-rung-track"><i className={'fill' + (past ? ' past' : '')} style={{ width: fill * 100 + '%' }} />
      {has && band > 0 ? <i className="band" style={{ left: mark * 100 + '%', width: band * 100 + '%' }} /> : null}
      {has && mark !== null ? <i className="mark" style={{ left: mark * 100 + '%' }} data-testid={testId + '-mine'} /> : null}</span>
    <span className="rk-rung-value"><b data-testid={testId + '-close'}>{has ? fmt(cell.close) : '—'}</b>{cell.open ? <small>open {fmt(cell.open)}</small> : null}</span>
    <span className={'rk-rung-note ' + (state || 'none')}>{!has ? empty : state === 'in' ? '✓ aapki rank andar' : state === 'maybe' ? 'borderline · aapki range ke andar' : state === 'out' ? 'aapki rank bahar' : ''}</span>
  </div>;
}

/** Branches x rounds: green = the whole rank range is inside that round's closing rank, amber = only part of it. */
export function RoundTable({ rounds, rows, prevLabel, pick, onPick, prefix }) {
  return <div className="rk-table-wrap" data-testid={prefix + '-table'}><table className="rk-table">
    <thead><tr><th>Branch</th>{rounds.map(r => <th key={r}>{r}</th>)}{prevLabel ? <th className="prev">{prevLabel}</th> : null}</tr></thead>
    <tbody>{rows.map(r => <tr key={r.key} className={r.key === pick ? 'is-pick' : ''}>
      <th><button type="button" onClick={() => onPick(r.key === pick ? null : r.key)} data-testid={`${prefix}-branch-${r.key}`}>{r.name}</button></th>
      {r.cells.map((c, i) => { const part = c.in && c.hi != null && c.close && c.close < c.hi; return <td key={i} className={c.in ? (part ? 'part' : 'in') : ''}>{c.close ? fmt(c.close) : '—'}</td>; })}
      {prevLabel ? <td className="prev">{r.prev ? fmt(r.prev) : '—'}</td> : null}
    </tr>)}</tbody>
  </table></div>;
}

export function BranchPicker({ options, value, onChange, testId, allLabel = 'All branches' }) {
  const [open, setOpen] = useState(false);
  const label = value.length ? (value.length === 1 ? value[0] : `${value.length} branches`) : allLabel;
  const flip = b => onChange(value.includes(b) ? value.filter(x => x !== b) : [...value, b]);
  return <>
    <button type="button" className="rk-picker" onClick={() => setOpen(true)} data-testid={testId}><span>Branch</span><b>{label}</b><ChevronRight size={16} /></button>
    <RankSheet open={open} onClose={() => setOpen(false)} title="Branch chuno" sub="Kuch na chuno to saari branches." testId={testId + '-sheet'}>
      <div className="rk-chips"><Chip on={!value.length} onClick={() => onChange([])} testId={testId + '-all'}>{allLabel}</Chip>
        {options.map(b => <Chip key={b} on={value.includes(b)} onClick={() => flip(b)} testId={`${testId}-opt-${b.replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`}>{b}</Chip>)}</div>
      <Go label="Done" onClick={() => setOpen(false)} testId={testId + '-done'} />
    </RankSheet>
  </>;
}

export const StateSelect = ({ states, value, onChange, testId }) => <label className="rk-picker as-select"><span>Home state</span>
  <select value={value || ''} onChange={e => onChange(e.target.value || null)} data-testid={testId}><option value="">Chuno (zaroori nahi)</option>{states.map(s => <option key={s} value={s}>{s}</option>)}</select></label>;
