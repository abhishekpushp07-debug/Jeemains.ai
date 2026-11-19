import React from 'react';
import { ArrowRight, Crown } from 'lucide-react';
import { Block, Tile, Meter, Locked, Key, mmss, pc, pick, slug, r1, signed } from './parts';
import { ScoreRing, Histogram, QGrid, Split, SubjectVs } from './charts';
import { Learnings } from './Learnings';
import { explain } from './explain';

export const RANK_NOTE = {
  sealed: 'Rank sabka time khatam hone par aayega', preparing: 'Class ka data ban raha hai…', staff: 'Staff attempt par Rank nahi banta',
  original_only: 'Rank sirf original Score par banta hai', none: 'Is test par Rank nahi banta', ready: 'Rank jald aayega',
};
const GO = { overview: 'Overview', performance: 'Performance', potential: 'Score Potential', quality: 'Attempt Quality', time: 'Time', difficulty: 'Difficulty', journey: 'Question Journey', qs: 'Qs by Qs' };

function Hero({ an, onDrill, go, toBoard, X }) {
  const o = an.overview, v = o.verdict, by = t => pick(an, q => q.outcome === t), p = an.paper;
  return (
    <Block id="score" className="feature-dark a2-feature" kicker={`${p.count} SAWAAL · ${p.minutes ? p.minutes + ' MIN' : 'UNTIMED'} · +${p.marks.correct} / ${p.marks.wrong}`} title="Aapka Score" info={X.score}>
      <div className="a2-hero">
        <ScoreRing score={o.score} maximum={o.maximum} percentage={o.percentage} />
        <div className="a2-hero-side">
          {v && (
            <button type="button" className={'a2-verdict tone-' + v.tone} data-testid="a2-verdict" onClick={() => go(v.section)}>
              <p>{v.text}</p><span>{GO[v.section]} mein poora hisaab <ArrowRight size={14} /></span>
            </button>
          )}
          <div className="a2-tiles four">
            <Tile id="rank" label="Rank" value={o.rank ? '#' + o.rank : '—'} sub={o.rank ? `${o.of} students mein` : RANK_NOTE[an.class.state]} tone="brand" onTap={o.rank && toBoard ? toBoard : null} tap="Leaderboard dekho →" info={X.rank} />
            <Tile id="percentile" label="Percentile" value={o.percentile ?? '—'} sub={o.rank ? 'is paper par' : 'Rank ke saath aayega'} info={X.percentile} />
            <Tile id="accuracy" label="Accuracy" value={pc(o.accuracy)} sub={`${o.correct} sahi / ${o.attempted} attempted`} tone={o.accuracy >= 75 ? 'good' : o.accuracy < 50 ? 'bad' : 'warn'} info={X.accuracy} />
            <Tile id="time" label="Time" value={mmss(o.time_used)} sub={o.time_on_screen != null ? 'Sawaalon par ' + mmss(o.time_on_screen) : 'paper mein laga'} info={X.time} />
          </div>
        </div>
      </div>
      <div className="a2-tiles four">
        <Tile id="attempted" label="Attempted" value={o.attempted} ids={pick(an, q => ['correct', 'incorrect'].includes(q.outcome))} onDrill={onDrill} info={X.attempted} />
        <Tile id="correct" label="Sahi" value={o.correct} tone="good" ids={by('correct')} onDrill={onDrill} />
        <Tile id="incorrect" label="Galat" value={o.incorrect} tone="bad" ids={by('incorrect')} onDrill={onDrill} />
        <Tile id="skipped" label="Chhode" value={o.skipped} tone="mute" ids={by('skipped')} onDrill={onDrill} />
      </div>
    </Block>
  );
}

function Ledger({ led, X }) {
  const chips = [['earned', 'Kamaye', '+' + led.earned, 'good'], ['negative', 'Negative mein kate', led.negative ? '−' + led.negative : 0, 'bad'],
    ['left_wrong', 'Galat jawab mein reh gaye', led.left_wrong, 'warn'], ['left_skipped', 'Chhode mein reh gaye', led.left_skipped, 'mute'], ['net', 'Net Score', led.net, 'brand']];
  return (
    <Block id="ledger" kicker="MARKS KA HISAAB" title="Har mark kahan gaya" info={X.ledger} note={`Paper ${led.maximum} marks ka tha. Kitne kamaye, kitne kate aur kitne mez par reh gaye.`}>
      <div className="a2-ledger">
        {chips.map(([k, label, value, tone]) => <div key={k} className={'a2-ledger-chip tone-' + tone} data-testid={'a2-ledger-' + k}><span>{label}</span><strong>{value}</strong></div>)}
      </div>
      <Split testId="a2-ledger-bar" label="Kamaye, galat mein aur chhode mein reh gaye marks" parts={[['Kamaye', led.earned, 'good'], ['Galat mein', led.left_wrong, 'bad'], ['Chhode mein', led.left_skipped, 'mute']]} />
      <Key items={[[`Kamaye ${led.earned}`, 'good'], [`Galat mein reh gaye ${led.left_wrong}`, 'bad'], [`Chhode mein reh gaye ${led.left_skipped}`, 'mute']]} />
      <p className="a2-foot" data-testid="a2-ledger-no-negative">Agar ek bhi galat jawab na hota (sirf chhod dete), to Score <b>{led.no_negative}</b> hota. Negative ne <b>{led.negative}</b> marks khaaye.</p>
    </Block>
  );
}

function Standing({ an, X }) {
  const o = an.overview, d = o.distribution, k = an.class;
  if (!d) {
    const text = k.state === 'ready' ? `Abhi sirf ${k.n} student ne yeh paper diya hai. Doosra student aate hi yeh chart khul jaayega.` : RANK_NOTE[k.state] + '. Tab tak baaki saara analysis aapke apne data se taiyaar hai.';
    return <Locked id="standing" title="Class mein aap kahan ho" text={text} />;
  }
  const above = k.above;
  return (
    <Block id="standing" kicker={`${d.n} STUDENTS NE YEH PAPER DIYA`} title="Class mein aap kahan khade ho" info={X.standing} note="Har column ek Score range hai. Laal column mein aap ho.">
      <Histogram dist={d} />
      <div className="a2-facts">
        <span>Class average <b>{d.average}</b></span><span>Median <b>{d.median}</b></span><span>Top Score <b>{d.top}</b></span>
        <span>Aap <b>{o.score}</b> ({o.score >= d.average ? `average se ${r1(o.score - d.average)} upar` : `average se ${r1(d.average - o.score)} neeche`})</span>
      </div>
      {above && <p className="a2-above" data-testid="a2-above">Aapse theek upar: <b>{above.name}</b> ({above.score} marks). Sirf <b>{r1(above.score - o.score)}</b> {r1(above.score - o.score) === 1 ? 'mark' : 'marks'} aur, aur Rank ek upar.</p>}
      {!above && o.rank === 1 && <p className="a2-above" data-testid="a2-topper"><Crown size={16} className="a2-gold" aria-hidden="true" /> Aap is paper ke <b>topper</b> ho: {o.of} students mein sabse upar. Ab apna hi Score todna hai.</p>}
    </Block>
  );
}

function VsClass({ an, X }) {
  const mine = Object.fromEntries(an.overview.subjects.map(s => [s.name, s]));
  const rows = (an.overview.class_subjects || []).filter(r => mine[r.name]).map(r => ({ ...r, you: mine[r.name].score }));
  if (!rows.length) return null;
  const wide = rows.some(r => r.average != null);
  return (
    <Block id="vs-class" kicker={`${an.class.n} STUDENTS MEIN`} title="Har subject mein aap vs class" info={X.vs_class}
      note={wide ? 'Aapka Score, class ka average, Top 10% ka average aur Topper ka Score.' : `Abhi sirf Topper dikh raha hai. Class average aur Top 10% kam se kam ${an.class.min_finishers} students par khulte hain.`}>
      <SubjectVs rows={rows} />
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-subject-vs-table">
        <thead><tr><th>Subject</th><th>Aap</th>{wide && <th>Class average</th>}{wide && <th>Top 10%</th>}<th>Topper</th>{wide && <th>Average se</th>}</tr></thead>
        <tbody>{rows.map(r => {
          const gap = wide ? r1(r.you - r.average) : 0;
          return <tr key={r.name}><td><b>{r.name}</b></td><td><b>{r.you}</b></td>{wide && <td>{r.average}</td>}{wide && <td>{r.top10}</td>}<td>{r.topper}</td>{wide && <td className={gap < 0 ? 'bad' : 'good'}>{signed(gap)}</td>}</tr>;
        })}</tbody>
      </table></div>
    </Block>
  );
}

function Subjects({ an, onDrill }) {
  return (
    <Block id="subjects" kicker="SUBJECT-WISE" title="Har subject ek nazar mein" note="Card par tap karo: us subject ke galat aur chhode sawaal khulenge.">
      <div className="a2-cards">
        {an.overview.subjects.map(g => {
          const ids = pick(an, q => q.subject === g.name && q.outcome !== 'correct');
          return (
            <button type="button" className="a2-card" key={g.name} data-testid={'a2-subject-' + slug(g.name)} onClick={() => onDrill(`${g.name}: galat + chhode`, ids)}>
              <h4>{g.name}</h4><strong>{g.score}<small> / {g.maximum}</small></strong>
              <Meter value={Math.max(0, g.score)} max={g.maximum} tone="brand" />
              <p><b className="good">{g.correct} sahi</b> · <b className="bad">{g.incorrect} galat</b> · {g.skipped} chhode</p>
              <p>Accuracy {pc(g.accuracy)}{g.time != null ? ' · Time ' + mmss(g.time) : ''}</p>
            </button>
          );
        })}
      </div>
    </Block>
  );
}

function NextThree({ an, onDrill, go, X }) {
  const items = an.overview.next3;
  return (
    <Block id="next3" kicker="SIRF AAPKE DATA SE · KOI AI NAHI" title="Agle mock ke liye 3 kaam" info={X.next3} note="Jahan sabse zyada marks daav par hain, wahi pehle.">
      {items.length ? <ol className="a2-next">
        {items.map((x, i) => (
          <li key={x.key} data-testid={'a2-next-' + x.key}>
            <span className="a2-next-no">{i + 1}</span>
            <div><h4>{x.title} <b>+{x.marks} marks</b></h4><p>{x.detail}</p>
              <div className="a2-row">
                {x.questions.length > 0 && <button type="button" className="a2-link" data-testid={'a2-next-questions-' + x.key} onClick={() => onDrill(x.title, x.questions)}>{x.questions.length} sawaal dekho</button>}
                <button type="button" className="a2-link" data-testid={'a2-next-open-' + x.key} onClick={() => go(x.section === 'questions' ? 'qs' : x.section)}>Poora hisaab <ArrowRight size={13} /></button>
              </div>
            </div>
          </li>
        ))}
      </ol> : <p className="a2-empty" data-testid="a2-next-empty">Is attempt mein koi bada sudhaar ka point nahi mila. Ab naye sawaal try karo.</p>}
    </Block>
  );
}

export function Overview({ an, id, onDrill, onOpen, go, board, toBoard }) {
  const X = explain(an);
  return <>
    <Hero an={an} onDrill={onDrill} go={go} toBoard={toBoard} X={X} />
    <Ledger led={an.overview.ledger} X={X} />
    <NextThree an={an} onDrill={onDrill} go={go} X={X} />
    <Standing an={an} X={X} />
    {board}
    <VsClass an={an} X={X} />
    <Block id="grid" kicker="HAR SAWAAL EK NAZAR MEIN" title="Question map" note="Hara = sahi, laal = galat, dhundhla = chhoda. Kisi bhi number par tap karo, solution khulega.">
      <QGrid an={an} onOpen={onOpen} />
      <Key items={[['Sahi', 'good'], ['Galat', 'bad'], ['Chhoda', 'mute'], ['Marked for review', 'warn']]} />
    </Block>
    <Subjects an={an} onDrill={onDrill} />
    <Learnings key={an.attempt_id} id={id} an={an} />
  </>;
}
