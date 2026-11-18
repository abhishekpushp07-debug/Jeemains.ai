import React from 'react';
import { CheckCircle2, XCircle, MinusCircle, Zap, Hourglass, HelpCircle, SkipForward, EyeOff, Ban, Brain, Clock3 } from 'lucide-react';

export const mmss = s => (s == null ? '—' : `${Math.floor(Math.round(s) / 60)}m ${String(Math.round(s) % 60).padStart(2, '0')}s`);
export const pc = v => (v == null ? '—' : v + '%');
export const slug = v => String(v).toLowerCase().replace(/[^a-z0-9]+/g, '-');
export const pick = (an, test) => an.questions.filter(test).map(q => q.id);
export const RESULT = { correct: 'Sahi', incorrect: 'Galat', skipped: 'Chhoda', dropped: 'Dropped', bonus: 'Bonus' };
export const OUT_ICON = { correct: CheckCircle2, incorrect: XCircle, skipped: MinusCircle, dropped: Ban, bonus: CheckCircle2 };
export const OUT_TONE = { correct: 'good', incorrect: 'bad', skipped: 'mute', dropped: 'mute', bonus: 'good' };
export const TAG = {
  perfect: ['good', CheckCircle2], slow_correct: ['warn', Hourglass], wasted: ['bad', Zap], concept_gap: ['bad', Brain], costly_overtime: ['bad', Clock3],
  confused: ['warn', HelpCircle], smart_skip: ['info', SkipForward], not_seen: ['mute', EyeOff], no_score: ['mute', Ban],
};
export const TIP = { contentStyle: { background: 'var(--surface-card)', border: '1px solid var(--line)', borderRadius: 10, color: 'var(--ink)', fontSize: 12 }, cursor: { fill: 'var(--a-track)' } };
export const AXIS = { fontSize: 11, fill: 'var(--text-muted)' };

export const Block = ({ id, title, note, action, children }) => (
  <section className="a2-block" data-testid={'a2-block-' + id}>
    <header><div><h3>{title}</h3>{note && <p>{note}</p>}</div>{action}</header>
    {children}
  </section>
);

export const Tile = ({ id, label, value, sub, tone = '', ids, onDrill }) => {
  const body = <><span>{label}</span><strong data-testid={'a2-tile-' + id + '-value'}>{value}</strong>{sub ? <small>{sub}</small> : null}</>;
  return ids?.length && onDrill
    ? <button type="button" className={'a2-tile tap tone-' + tone} data-testid={'a2-tile-' + id} onClick={() => onDrill(label, ids)}>{body}<em>Sawaal dekho</em></button>
    : <div className={'a2-tile tone-' + tone} data-testid={'a2-tile-' + id}>{body}</div>;
};

export const TagChip = ({ tag, copy }) => {
  if (!tag) return <span className="a2-tag tone-mute">—</span>;
  const [tone, Icon] = TAG[tag];
  return <span className={'a2-tag tone-' + tone} title={copy.tags[tag][1]}><Icon size={12} aria-hidden="true" />{copy.tags[tag][0]}</span>;
};

export const Later = ({ id }) => (
  <div className="a2-later" data-testid={'a2-later-' + id}>
    <Clock3 size={22} />
    <div><strong>Agle mock se shuru hoga</strong><p>Is attempt mein har sawaal ka time record nahi hua tha. Agla mock doge to yeh hissa apne aap bhar jaayega.</p></div>
  </div>
);

export const Pills = ({ id, value, onChange, items }) => (
  <div className="a2-pills" role="tablist" data-testid={'a2-pills-' + id}>
    {items.map(([key, label]) => (
      <button type="button" role="tab" key={key} aria-selected={value === key} className={value === key ? 'on' : ''} data-testid={`a2-pill-${id}-${slug(key)}`} onClick={() => onChange(key)}>{label}</button>
    ))}
  </div>
);
