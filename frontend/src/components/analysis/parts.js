import React from 'react';
import { CheckCircle2, Zap, Hourglass, HelpCircle, SkipForward, EyeOff, Ban, Brain, Clock3, Lock, Info as InfoIcon } from 'lucide-react';
import { Popover, PopoverTrigger, PopoverContent } from '../ui/popover';

export const mmss = s => (s == null ? '—' : `${Math.floor(Math.round(s) / 60)}m ${String(Math.round(s) % 60).padStart(2, '0')}s`);
export const pc = v => (v == null ? '—' : v + '%');
export const r1 = v => Math.round((v || 0) * 10) / 10;
export const signed = v => (v > 0 ? '+' + v : String(v));
export const slug = v => String(v).toLowerCase().replace(/[^a-z0-9]+/g, '-');
export const pick = (an, test) => an.questions.filter(test).map(q => q.id);
export const index = an => Object.fromEntries(an.questions.map(q => [q.id, q]));
export const RESULT = { correct: 'Sahi', incorrect: 'Galat', skipped: 'Chhoda', dropped: 'Dropped', bonus: 'Bonus' };
export const OUT_TONE = { correct: 'good', incorrect: 'bad', skipped: 'mute', dropped: 'mute', bonus: 'good' };
export const TAG = {
  perfect: ['good', CheckCircle2], slow_correct: ['warn', Hourglass], wasted: ['bad', Zap], concept_gap: ['bad', Brain], costly_overtime: ['bad', Clock3],
  confused: ['warn', HelpCircle], smart_skip: ['info', SkipForward], not_seen: ['mute', EyeOff], no_score: ['mute', Ban],
};
export const TIP = {
  contentStyle: { background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 12, color: 'var(--ink)', fontSize: 12, boxShadow: '0 8px 24px rgb(0 0 0 / .35)' },
  labelStyle: { color: 'var(--ink)', fontWeight: 700 }, itemStyle: { color: 'var(--ink)' }, cursor: { fill: 'var(--a-hover)' },
};
export const AXIS = { fontSize: 11, fill: 'var(--text-muted)' };
export const GRID = { vertical: false, stroke: 'var(--line)', strokeDasharray: '3 3' };
export const LEGEND = { wrapperStyle: { fontSize: 12 }, itemSorter: null };

// (i): what a number means and how it was counted.
export const Info = ({ id, title, text }) => (
  <Popover>
    <PopoverTrigger asChild><button type="button" className="a2-info" aria-label={`${title}: yeh kaise bana`} data-testid={'a2-info-' + id} onClick={e => e.stopPropagation()}><InfoIcon size={15} aria-hidden="true" /></button></PopoverTrigger>
    <PopoverContent className="a2-info-pop" align="end" data-testid={'a2-info-pop-' + id}><b>{title}</b><p>{text}</p></PopoverContent>
  </Popover>
);

export const Block = ({ id, kicker, title, note, action, info, children, className = '' }) => (
  <section className={'a2-block ' + className} data-testid={'a2-block-' + id}>
    <header><div>{kicker && <span className="a2-kicker">{kicker}</span>}<h3>{title}</h3>{note && <p>{note}</p>}</div>
      {(action || info) && <div className={'a2-head-act' + (action ? '' : ' solo')}>{action}{info && <Info id={'block-' + id} title={title} text={info} />}</div>}
    </header>
    {children}
  </section>
);

export const Tile = ({ id, label, value, sub, tone = '', ids, onDrill, onTap, tap = 'Sawaal dekho →', info }) => {
  const body = <><span className="a2-tile-label">{label}</span><strong className="a2-tile-value" data-testid={'a2-tile-' + id + '-value'}>{value}</strong>{sub ? <small className="a2-tile-sub">{sub}</small> : null}</>;
  const act = onTap || (ids?.length && onDrill ? () => onDrill(label, ids) : null);
  const tile = act
    ? <button type="button" className={'a2-tile tap tone-' + tone} data-testid={'a2-tile-' + id} onClick={act}>{body}<em>{tap}</em></button>
    : <div className={'a2-tile tone-' + tone} data-testid={'a2-tile-' + id}>{body}</div>;
  return info ? <div className="a2-tile-box">{tile}<Info id={id} title={label} text={info} /></div> : tile;
};

export const TagChip = ({ tag, copy }) => {
  if (!tag) return <span className="a2-tag tone-mute">—</span>;
  const [tone, Icon] = TAG[tag];
  return <span className={'a2-tag tone-' + tone} title={copy.tags[tag][1]}><Icon size={12} aria-hidden="true" />{copy.tags[tag][0]}</span>;
};

export const Locked = ({ id, title, text, icon: Icon = Lock, testId }) => (
  <div className="a2-later" data-testid={testId || 'a2-locked-' + id}>
    <Icon size={22} aria-hidden="true" />
    <div><strong>{title}</strong><p>{text}</p></div>
  </div>
);

export const Later = ({ id }) => (
  <Locked id={id} testId={'a2-later-' + id} icon={Clock3} title="Agle mock se shuru hoga"
    text="Is attempt mein har sawaal ka time record nahi hua tha. Agla mock doge to yeh hissa apne aap bhar jaayega." />
);

export const Pills = ({ id, value, onChange, items }) => (
  <div className="a2-pills" role="tablist" data-testid={'a2-pills-' + id}>
    {items.map(([key, label]) => (
      <button type="button" role="tab" key={key} aria-selected={value === key} className={value === key ? 'on' : ''} data-testid={`a2-pill-${id}-${slug(key)}`} onClick={() => onChange(key)}>{label}</button>
    ))}
  </div>
);

export const Meter = ({ value, max = 100, tone = 'brand', label, testId }) => (
  <div className={'a2-meter tone-' + tone} role="img" aria-label={label || `${value} / ${max}`} data-testid={testId}>
    <i style={{ width: Math.max(0, Math.min(100, (100 * (value || 0)) / (max || 1))) + '%' }} />
  </div>
);

export const Key = ({ items }) => (
  <div className="a2-key">{items.map(([label, tone]) => <span key={label}><i className={'tone-' + tone} />{label}</span>)}</div>
);

export function QChips({ id, ids, an, onOpen, max = 40 }) {
  const by = index(an);
  const rows = ids.map(i => by[i]).filter(Boolean);
  if (!rows.length) return <p className="a2-empty">Koi sawaal nahi.</p>;
  return (
    <div className="a2-qchips" data-testid={'a2-qchips-' + id}>
      {rows.slice(0, max).map(q => (
        <button type="button" key={q.id} className={'a2-qchip tone-' + OUT_TONE[q.outcome]} title={`Q${q.number} · ${q.subject} · ${RESULT[q.outcome]}`}
          data-testid={`a2-qchip-${id}-${q.number}`} onClick={() => onOpen(q.id)}>Q{q.number}</button>
      ))}
      {rows.length > max && <span className="a2-more">+{rows.length - max} aur</span>}
    </div>
  );
}
