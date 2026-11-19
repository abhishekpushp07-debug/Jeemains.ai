import React, { useState } from 'react';
import { Flag, Check, X, Minus } from 'lucide-react';
import { Block, Tile, Later, QChips, Key, TAG, OUT_TONE, RESULT, mmss, index } from './parts';
import { explain } from './explain';

const nth = n => (n === 2 ? '2nd' : n === 3 ? '3rd' : n + 'th');
const CHANGE = [['w2r', 'Galat se sahi', 'good'], ['r2w', 'Sahi se galat', 'bad'], ['w2w', 'Galat se galat', 'warn'], ['cleared', 'Jawab hataya', 'mute']];
const MARK = { correct: Check, incorrect: X };

function Changes({ an, onOpen, about }) {
  const c = an.habits?.changes;
  if (!c?.total) return null;
  const g = { ...c.groups, cleared: [...c.groups.r2s, ...c.groups.w2s] };
  return (
    <Block id="changes" kicker="JAWAB BADALNA" title={`${c.total} baar jawab badla`} info={about} note={`Is badlav se net ${c.marks > 0 ? '+' : ''}${c.marks} marks. ${c.marks < 0 ? 'Pehla jawab zyada sahi tha: bina pakke kaaran ke mat badlo.' : c.marks > 0 ? 'Dobara check karna kaam aaya.' : ''}`}>
      <div className="a2-changes" data-testid="a2-answer-changes">
        {CHANGE.map(([k, label, tone]) => g[k].length > 0 && (
          <div key={k} className={'a2-change tone-' + tone}><span>{label}<b>{g[k].length}</b></span><QChips id={'change-' + k} ids={g[k]} an={an} onOpen={onOpen} max={12} /></div>
        ))}
      </div>
    </Block>
  );
}

function Chips({ an, onOpen, about }) {
  const j = an.journey, byId = index(an), groups = {};
  const [tags, setTags] = useState(true);
  j.visits.forEach(v => { const i = Math.floor(v.a / j.block); (groups[i] = groups[i] || []).push(v); });
  const keys = Object.keys(groups).map(Number).sort((a, b) => a - b);
  return (
    <Block id="journey-chips" kicker="AAPKA RAASTA" title="Har visit, time ke hisaab se" info={about} note="Ek chip = ek baar sawaal khola. Gol nishaan = us sawaal ka result. Chhota number = kaun si baar. B→C = jawab badla. Time block par tap karke band ya khol sakte ho."
      action={<button type="button" className="a2-chipbtn" aria-pressed={tags} data-testid="a2-journey-tags-toggle" onClick={() => setTags(!tags)}>{tags ? 'Tag ka rang chhupao' : 'Tag ka rang dikhao'}</button>}>
      <div data-testid="a2-journey-legend">
        <Key items={[['✓ Sahi', 'good'], ['✕ Galat', 'bad'], ['– Jawab nahi', 'mute']]} />
        {tags && <Key items={[['Kinara aur chhota icon = tag. Perfect', 'good'], ['Careless / Concept gap / Mehnga overtime', 'bad'], ['Slow-correct / Confused', 'warn'], ['Smart skip', 'info']]} />}
      </div>
      {keys.map((i, at) => {
        const answered = groups[i].filter(v => v.set && v.set !== 'Clear').length;
        return (
          <details key={i} className="a2-jfold" open={keys.length <= 6 || at < 3} data-testid={'a2-block-journey-' + i}>
            <summary>{Math.round((i * j.block) / 60)}–{Math.round(((i + 1) * j.block) / 60)} min <small>{groups[i].length} visits · {answered} baar jawab diya ya badla</small></summary>
            <div className="a2-journey">{groups[i].map((v, k) => {
              const q = byId[v.q], tone = tags && q?.tag ? TAG[q.tag][0] : 'plain', Res = MARK[q?.outcome] || Minus, Tag = tags && q?.tag ? TAG[q.tag][1] : null;
              return <button type="button" key={k} className={'a2-visit tone-' + tone} title={q ? `${RESULT[q.outcome]}${q.tag ? ' · ' + an.copy.tags[q.tag][0] : ''}` : ''} data-testid={`a2-visit-${i}-${k}`} onClick={() => onOpen(v.q)}>
                {q && <i className={'res tone-' + OUT_TONE[q.outcome]} aria-label={RESULT[q.outcome]}><Res size={10} strokeWidth={3.2} aria-hidden="true" /></i>}<b>Q{v.n}</b>{v.v > 1 && <sup>{nth(v.v)}</sup>}<small>{mmss(v.d)}</small>{Tag && <Tag size={11} aria-hidden="true" />}{v.mark && <Flag size={11} aria-label="Marked for review" />}{v.set && <em>{v.set}</em>}
              </button>;
            })}</div>
          </details>
        );
      })}
    </Block>
  );
}

export function Journey({ an, onOpen }) {
  const j = an.journey, h = an.habits || {}, X = explain(an);
  if (!j.available) return <><Later id="journey" /><Changes an={an} onOpen={onOpen} about={X.changes} /></>;
  const s = j.summary, first = j.first_block;
  return <>
    <Block id="journey" kicker="QUESTION JOURNEY" title="Aap paper mein kaise chale" info={X.journey}>
      <p className="a2-lead" data-testid="a2-journey-summary">{s.total} mein se {s.visited} sawaal dekhe, {s.revisits} baar wapas gaye, {s.thrice} sawaal 3 ya zyada baar dekhe.</p>
      <div className="a2-tiles four">
        <Tile id="j-visited" label="Sawaal dekhe" value={`${s.visited} / ${s.total}`} tone="info" />
        <Tile id="j-revisits" label="Wapas gaye" value={s.revisits} />
        <Tile id="j-streak" label="Lagaataar sahi" value={h.streaks?.correct ?? '—'} sub="sabse lambi streak" tone="good" info={X.streak} />
        <Tile id="j-wstreak" label="Lagaataar galat" value={h.streaks?.incorrect ?? '—'} sub="sabse lambi streak" tone="bad" info={X.streak} />
      </div>
      <p className="a2-foot" data-testid="a2-journey-order">Subject order: <b>{j.order.join(' → ') || '—'}</b>.{first ? ` Pehle ${first.minutes} min mein ${first.answered} jawab (${first.correct} sahi, ${first.incorrect} galat).` : ''}</p>
    </Block>
    <Changes an={an} onOpen={onOpen} about={X.changes} />
    <Chips an={an} onOpen={onOpen} about={X.journey} />
  </>;
}
