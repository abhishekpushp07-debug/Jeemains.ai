// The app's Dream College Meter (DreamMeter.tsx): one exam's dream seats against the student's full mocks. A shining
// purple header around a deep black body; the last mock and its change since the one before; the progress chart; then
// one card per dream (royal blue / teal, each with a diamond) with the marks it needs and how far the last mock is.
// A reached dream can be shown to friends as a black metal "Dream unlocked" picture with the student's own link.
import React, { useEffect, useRef, useState } from 'react';
import { toBlob } from 'html-to-image';
import { ArrowRight, ChevronRight, CircleAlert, Loader2, PlusCircle, Target, X } from 'lucide-react';
import { useAuth } from '../../lib/auth';
import { sendCard } from '../mission/MissionCard';
import { useShareLink } from '../mission/missionApi';
import { EXAM_LABEL } from './rankApi';
import { Gem, RankCard } from './RankUi';
import { dreamsOf, FULL, MAX_DREAMS, mocksOf, removeDream, useDreams } from './rankStore';
import '../../rank.css';
import '../../dream.css';

export const LINE_COLORS = ['#9DB6FF', '#5EF0D6', '#FFC94D', '#FF8FC7', '#C6F36B'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const day = at => { const d = new Date(at); return `${d.getDate()} ${MONTHS[d.getMonth()]}`; };
const r1 = v => Math.round(v * 10) / 10;
const ESTIMATE = '2026 cutoff par estimate, guarantee nahi.';

/** The mocks the chart draws, oldest first: the newest `max`, or on a result screen those up to that mock. */
export const seriesOf = (mocks, mockId, max = 30) => {
  const at = mockId ? mocks.findIndex(m => m.id === mockId) : 0;
  return at < 0 ? [] : mocks.slice(at, at + max).reverse();
};

/** Marks gained per mock over the last (up to 5) mocks: the slope of a least-squares line; null with fewer than 2. */
export function speedOf(series) {
  const s = series.slice(-5);
  if (s.length < 2) return null;
  const mx = (s.length - 1) / 2, my = s.reduce((a, m) => a + m.score, 0) / s.length;
  let num = 0, den = 0;
  s.forEach((m, i) => { num += (i - mx) * (m.score - my); den += (i - mx) ** 2; });
  return num / den;
}

function etaOf(gap, speed) {
  if (gap === null) return null;
  if (gap <= 0) return '🎉 Target marks pahunch gaye! Ab har mock mein isse upar raho, seat pakki karo.';
  if (speed === null) return 'Ek aur full mock do, phir dikhega kitne mock mein pahunchoge.';
  const s = r1(speed), k = speed >= 1 ? Math.ceil(gap / speed) : Infinity;
  if (k <= 30) return `Is raftaar (+${s}/mock) se ~${k} mock mein pahunchoge.`;
  const why = s > 0 ? `Raftaar dheemi (+${s}/mock)` : s < 0 ? 'Score gir raha hai' : 'Score ruka hai';
  return `${why}. 10 mock mein pahunchne ke liye har mock +${Math.ceil(gap / 10)} chahiye.`;
}

export function DreamMeter({ exam, testId, mockId, editable, limit, onAdd, onMore, chart }) {
  const s = useDreams();
  const dreams = dreamsOf(s, exam).slice().sort((a, b) => a.need - b.need);
  const mocks = mocksOf(s, exam);
  const at = mockId ? mocks.findIndex(m => m.id === mockId) : 0;
  const last = at >= 0 ? mocks[at] : undefined, prev = at >= 0 ? mocks[at + 1] : undefined;
  const shown = limit ? dreams.slice(0, limit) : dreams;
  const series = seriesOf(mocks, mockId, chart === 'compact' ? 8 : 30);
  const speed = speedOf(series);
  return <section className="dm" data-testid={testId}>
    <header className="dm-head"><i className="dm-shine" aria-hidden="true" /><span className="dm-target"><Target size={22} /></span>
      <div><small>DREAM COLLEGE METER · {EXAM_LABEL[exam].toUpperCase()}</small><h3>Kitne marks door?</h3></div>
      <b data-testid={testId + '-count'}>{dreams.length}/{MAX_DREAMS}</b></header>
    <div className="dm-body">
      {s.notice ? <p className="dm-notice" role="alert" data-testid={testId + '-notice'}><CircleAlert size={16} />{s.notice}</p> : null}
      {last ? <LastMock exam={exam} last={last} prev={prev} here={!!mockId} testId={testId} />
        : <p className="dm-soft" data-testid={testId + '-nomock'}>Pehla full {EXAM_LABEL[exam]} mock do. Har mock ke baad yahan dikhega har dream college kitne marks door hai.</p>}
      {chart && series.length ? <ProgressChart exam={exam} series={series} dreams={shown} compact={chart === 'compact'} here={!!mockId} testId={testId + '-chart'} /> : null}
      {dreams.length === 0 ? <div className="dm-empty" data-testid={testId + '-empty'}>
        <b>Apne {MAX_DREAMS} dream college + branch chuno</b>
        <p>College predictor mein kisi bhi college card par 🎯 Dream college dabao. Har mock ke baad yahan dikhega kitne marks door ho.</p>
        {onAdd ? <button type="button" className="dm-cta" onClick={onAdd} data-testid={testId + '-add'}>Dream college chuno<ArrowRight size={18} /></button> : null}
      </div> : shown.map((d, i) => <DreamRow key={d.id} d={d} i={i} mock={last} testId={`${testId}-row-${i}`} editable={editable}
        eta={chart ? etaOf(last ? d.need - last.score : null, speed) : null} />)}
      {limit && dreams.length > limit && onMore ? <button type="button" className="dm-more" onClick={onMore} data-testid={testId + '-more'}>Sab {dreams.length} dream dekho<ChevronRight size={16} /></button> : null}
      {dreams.length > 0 && dreams.length < MAX_DREAMS && onAdd ? <button type="button" className="dm-more" onClick={onAdd} data-testid={testId + '-add-more'}>
        <PlusCircle size={16} />{MAX_DREAMS - dreams.length} aur dream jodo</button> : null}
      {dreams.length ? <small className="dm-foot">Marks normal paper ke hisaab se, 2026 cutoff par estimate. Guarantee nahi.</small> : null}
    </div>
  </section>;
}

function LastMock({ exam, last, prev, here, testId }) {
  const d = prev ? r1(last.score - prev.score) : null;
  return <div className="dm-mock" data-testid={testId + '-mock'}>
    <div><small>{here ? 'IS MOCK MEIN' : 'LAST MOCK'}</small>
      <p className="dm-score"><b data-testid={testId + '-score'}>{last.score}</b><em className="dm-of"> / {Math.max(FULL[exam], last.rawMax)}</em></p>
      <span className="dm-mock-title">{last.title}{last.rawMax < FULL[exam] ? ` · ${last.raw}/${last.rawMax} ko ${FULL[exam]} par scale kiya`
        : last.rawMax > FULL[exam] ? ` · ${last.rawMax} marks ka paper (bonus sawal ke saath)` : ''}</span></div>
    {d !== null ? <div className={'dm-delta' + (d > 0 ? ' up' : d < 0 ? ' down' : '')} data-testid={testId + '-delta'}>
      <b>{d > 0 ? `▲ ${d}` : d < 0 ? `▼ ${-d}` : '= 0'}</b><small>pichhle mock se</small></div> : null}
  </div>;
}

function DreamRow({ d, i, mock, testId, editable, eta }) {
  const score = mock?.score;
  const gap = score === undefined ? null : r1(d.need - score);
  const done = gap !== null && gap <= 0;
  const sharer = useDreamShare(done ? d : undefined, mock);
  const fill = score === undefined ? 0 : Math.max(4, Math.min(100, (score / Math.max(1, d.need)) * 100));
  return <div className={`dm-row tone-${i % 2}${done ? ' is-done' : ''}`} data-testid={testId}>
    <Gem size={30} className="dm-gem" sparkle />
    <div className="dm-row-top">
      <span className="dm-num" style={{ borderColor: LINE_COLORS[i % LINE_COLORS.length] }}>{i + 1}</span>
      <div className="dm-row-text"><b>{d.college}</b><small>{d.branch}</small></div>
      {gap === null ? <div className="dm-right"><strong data-testid={testId + '-need'}>{r1(d.need)}</strong><em>TARGET</em></div>
        : done ? <div className="dm-right is-done"><span data-testid={testId + '-reached'}>✓ Pahunch mein</span><em>{gap < 0 ? `+${-gap} upar` : 'Bilkul target par'}</em></div>
          : <div className="dm-right is-gap"><strong data-testid={testId + '-gap'}>{gap}</strong><em>MARKS DOOR</em></div>}
      {editable ? <button type="button" className="dm-remove" onClick={() => removeDream(d.id)} aria-label={`${d.college} dream se hatao`} data-testid={testId + '-remove'}><X size={16} /></button> : null}
    </div>
    <div className="dm-track" aria-hidden="true"><i style={{ width: `${fill}%` }} /></div>
    <small className="dm-note">Target {r1(d.need)}{d.range ? ` (${r1(d.range[0])}–${r1(d.range[1])})` : ''} / {FULL[d.exam]} · {d.note}</small>
    {eta ? <small className="dm-eta" data-testid={testId + '-eta'}>{eta}</small> : null}
    {done ? <button type="button" className="dm-share" onClick={sharer.share} disabled={sharer.busy} aria-label={`${d.college} dream card WhatsApp par bhejo`} data-testid={testId + '-share'}>
      {sharer.busy ? <Loader2 className="spin" size={15} /> : null}Dost ko dikhao</button> : null}
    {sharer.note ? <small className="dm-share-note" data-testid={testId + '-share-note'}>{sharer.note}</small> : null}
    {sharer.card}
  </div>;
}

/** Caption = what was crossed + the invite with the student's own link; the plain-text fallback adds the estimate note. */
function dreamText(d, mock, link) {
  const over = Math.round(mock.score - d.need);
  const head = [`🎯 Dream unlocked! Mock mein ${d.college} · ${d.branch} ka target cross kar liya.`,
    `Score ${mock.score}/${FULL[d.exam]} · Target ${r1(d.need)}${over > 0 ? ` · +${over} marks upar` : ''}`];
  const invite = `Tum bhi apna dream set karo 👉 ${link}`;
  return { caption: [...head, '', invite].join('\n'), fallback: [...head, '', ESTIMATE, '', invite].join('\n') };
}

function useDreamShare(d, mock) {
  const { user } = useAuth();
  const link = useShareLink();
  const ref = useRef(null);
  const [busy, setBusy] = useState(false), [drawing, setDrawing] = useState(false), [note, setNote] = useState('');
  const share = async () => {
    if (busy || !d || !mock) return;
    setBusy(true); setNote(''); setDrawing(true);
    await new Promise(r => setTimeout(r, 150));
    try {
      const node = ref.current;
      const blob = node ? await toBlob(node, { pixelRatio: 1080 / node.offsetWidth, cacheBust: true }).catch(() => null) : null;
      const file = blob ? new File([blob], 'JEELIVE-Dream-Unlocked.png', { type: 'image/png' }) : null;
      const text = dreamText(d, mock, link);
      const out = await sendCard(file, true, file ? text.caption : text.fallback);
      setNote(out.shared ? out.note : '');
    } catch { setNote('Share nahi ho paya. Ek baar phir try karo.'); }
    finally { setBusy(false); setDrawing(false); }
  };
  const name = user?.display_name || (/\d/.test(user?.name || '') ? '' : user?.name) || 'JEE aspirant';
  const over = d && mock ? Math.round(mock.score - d.need) : 0;
  const card = drawing && d && mock ? <div className="dm-offscreen" aria-hidden="true"><div ref={ref}>
    <RankCard testId="dream-share-card" badge="DREAM UNLOCKED ✓" eyebrow={`${EXAM_LABEL[d.exam].toUpperCase()} · DREAM COLLEGE`} big={d.college} caps={d.branch} gem
      rule={over > 0 ? `TARGET CROSS · +${over} MARKS UPAR` : 'TARGET CROSS · BILKUL TARGET PAR'}
      smalls={[{ label: 'Mock score', value: `${mock.score} / ${FULL[d.exam]}` }, { label: 'Target', value: `${r1(d.need)}` }]} note={ESTIMATE}
      foot={<><div className="dm-card-foot"><small className="rk-eyebrow">STUDENT</small><b className="dm-card-name">{name}</b></div>
        <div className="dm-card-foot"><small className="rk-eyebrow">MOCK</small><em className="dm-card-mock">{mock.title}</em></div></>} />
  </div></div> : null;
  return { card, share, busy, note };
}

function useWidth() {
  const ref = useRef(null);
  const [w, setW] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

/** Y axis: round steps (10/20/25/50/100) with a little room above the highest target and below the lowest score. */
function scaleOf(values) {
  const min = Math.min(...values), max = Math.max(...values);
  const step = [10, 20, 25, 50, 100].find(s => Math.max(40, max - min) / s <= 5) ?? 100;
  let lo = Math.floor((min - step * 0.15) / step) * step;
  if (min >= 0 && lo < 0) lo = 0;
  return { lo, hi: Math.ceil((max + step * 0.15) / step) * step, step };
}

const L = 34, R = 46, TOP = 14, BOT = 22, GAP = 15;

function ProgressChart({ exam, series, dreams, compact, here, testId }) {
  const [ref, w] = useWidth();
  const [sel, setSel] = useState(null);
  const n = series.length;
  if (!n) return null;
  const at = sel !== null && sel < n ? sel : n - 1;
  const H = compact ? 136 : 192, plotW = Math.max(1, w - L - R), plotH = H - TOP - BOT, base = TOP + plotH;
  const { lo, hi, step } = scaleOf([...series.map(m => m.score), ...dreams.map(d => d.need)]);
  const x = i => L + (n === 1 ? plotW / 2 : (i * plotW) / (n - 1));
  const y = v => TOP + ((hi - v) / Math.max(1, hi - lo)) * plotH;
  const scores = series.map(m => m.score), last = scores[n - 1];
  const best = Math.max(...scores), avg = Math.round(scores.slice(-3).reduce((a, b) => a + b, 0) / Math.min(3, n));
  const sp = (v => (v === null ? null : r1(v)))(speedOf(series));
  const line = series.map((m, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(m.score).toFixed(1)}`).join('');
  const ticks = [];
  for (let v = lo; v <= hi; v += step) ticks.push(v);
  const labels = dreams.map((d, i) => ({ d, i, at: y(d.need) })).sort((a, b) => a.at - b.at);
  labels.forEach((l, k) => { if (k) l.at = Math.max(l.at, labels[k - 1].at + GAP); });
  const shift = Math.max(0, (labels[labels.length - 1]?.at ?? 0) - base);
  labels.forEach(l => { l.at = Math.max(TOP - 6, l.at - shift); });
  const m = series[at], px = x(at), half = n === 1 ? plotW / 2 : plotW / (2 * (n - 1));
  const gid = `${testId}-area`, f = v => v.toFixed(1);
  // One fixed markup string: the preview editor wraps dynamic JSX children in <span>, which an SVG would not draw.
  const markup = [
    `<defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A855F7" stop-opacity=".45"/><stop offset="1" stop-color="#A855F7" stop-opacity="0"/></linearGradient></defs>`,
    ...ticks.map(v => `<line x1="${L}" x2="${f(L + plotW)}" y1="${f(y(v))}" y2="${f(y(v))}" class="grid"/><text x="${L - 6}" y="${f(y(v) + 3.5)}" text-anchor="end" class="tick">${v}</text>`),
    ...dreams.map((d, i) => `<line x1="${L}" x2="${f(L + plotW)}" y1="${f(y(d.need))}" y2="${f(y(d.need))}" stroke="${LINE_COLORS[i % LINE_COLORS.length]}" stroke-width="1.6"${last >= d.need ? '' : ' stroke-dasharray="6 4"'}/>`),
    `<line x1="${f(px)}" x2="${f(px)}" y1="${TOP}" y2="${f(base)}" class="cursor"/>`,
    n > 1 ? `<path d="${line}L${f(x(n - 1))} ${f(base)}L${f(x(0))} ${f(base)}Z" fill="url(#${gid})"/><path d="${line}" class="glow"/><path d="${line}" class="line"/>` : '',
    ...series.map((s, i) => `<circle cx="${f(x(i))}" cy="${f(y(s.score))}" r="${i === at ? 6 : 3.4}" class="${i === at ? 'dot on' : 'dot'}"/>`),
    ...labels.map(l => { const c = LINE_COLORS[l.i % LINE_COLORS.length]; return `<g data-testid="${testId}-target-${l.i}" transform="translate(${f(L + plotW + 5)} ${f(l.at)})"><circle cx="7" cy="0" r="7" fill="${c}"/>`
      + `<text x="7" y="3" text-anchor="middle" class="tnum">${l.i + 1}</text><text x="17" y="3.5" fill="${c}" class="tval">${last >= l.d.need ? '✓' : r1(l.d.need)}</text></g>`; }),
    `<text x="${L}" y="${H - 4}" class="tick">${day(series[0].at)}</text>`,
    n > 1 ? `<text x="${f(w - R)}" y="${H - 4}" text-anchor="end" class="tick">${day(series[n - 1].at)}</text>` : '',
  ].join('');
  return <div className="dm-chart" data-testid={testId}>
    <small className="dm-eyebrow">PROGRESS · {n} FULL MOCK{n > 1 ? 'S' : ''}</small>
    <div className="dm-stats">
      <ChartStat label="BEST" value={best} testId={testId + '-best'} />
      <ChartStat label="AVG" value={avg} sub={n >= 3 ? 'last 3' : 'sab mock'} testId={testId + '-avg'} />
      <ChartStat label="RAFTAAR" value={sp === null ? '—' : `${sp > 0 ? '+' : ''}${sp}`} sub={sp === null ? '2 mock do' : 'per mock'}
        tone={sp === null ? 'muted' : sp > 0 ? 'up' : sp < 0 ? 'down' : ''} testId={testId + '-speed'} />
    </div>
    <div className="dm-tip" data-testid={testId + '-tip'}>
      <p className="dm-tip-score"><b>{m.score}</b><em className="dm-of small"> / {Math.max(FULL[exam], m.rawMax)}</em></p>
      <div className="dm-tip-text"><em className="dm-tip-title">{m.title}</em><small>{day(m.at)}{at === n - 1 ? (here ? ' · is mock' : ' · last mock') : ` · mock ${at + 1} / ${n}`}</small></div>
      {here && at === n - 1 ? <em className="dm-here">IS MOCK</em> : null}
    </div>
    <div ref={ref} className="dm-plot" style={{ height: H }}>
      {w ? <svg width={w} height={H} role="img" aria-label={`${n} full mock. Last ${last}, best ${best}${sp !== null ? `, har mock mein ${sp} marks ki raftaar` : ''}.`}
        dangerouslySetInnerHTML={{ __html: markup }} data-testid={testId + '-svg'} /> : null}
      {w ? series.map((s, i) => <button key={s.id} type="button" className="dm-zone" style={{ left: x(i) - half, width: half * 2, height: H }}
        aria-label={`${s.title}: ${s.score} marks, ${day(s.at)}`} aria-pressed={i === at} onClick={() => setSel(i)} data-testid={`${testId}-point-${i}`} />) : null}
    </div>
    <small className="dm-soft">{n === 1 ? 'Ek aur full mock do, tab progress ki line banegi.' : 'Kisi bhi point par tap karke us mock ka score dekho. Dotted line = dream ka target, number = neeche wala card.'}</small>
  </div>;
}

const ChartStat = ({ label, value, sub, tone = '', testId }) => <div className="dm-stat"><small>{label}</small><b className={tone} data-testid={testId}>{value}</b>{sub ? <i>{sub}</i> : null}</div>;
