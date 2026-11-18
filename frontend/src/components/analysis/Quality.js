import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { Block, Tile, Later, QChips, TagChip, pick, TIP, AXIS } from './parts';
import { SpeedMap } from './charts';

const HEAD = ['perfect', 'wasted', 'overtime', 'confused', 'concept_gap'];
const HEAD_TONE = { perfect: 'good', wasted: 'bad', overtime: 'warn', confused: 'warn', concept_gap: 'bad' };
const BARS = [['Perfect', 'var(--a-good)'], ['Careless', 'var(--a-bad)'], ['Overtime', 'var(--a-warn)'], ['Confused', 'var(--a-info)'], ['Concept gap', 'var(--a-mute)']];
const ORDER = ['perfect', 'slow_correct', 'wasted', 'concept_gap', 'costly_overtime', 'confused', 'smart_skip', 'not_seen'];

function Headline({ an, onDrill }) {
  const q = an.quality, t = an.copy.tags, over = ['slow_correct', 'costly_overtime'];
  const ids = k => pick(an, x => (k === 'overtime' ? over.includes(x.tag) : x.tag === k));
  const name = k => (k === 'overtime' ? 'Overtime' : t[k][0]);
  const about = k => (k === 'overtime' ? 'Par time se kaafi zyada laga.' : t[k][1]);
  const from = q.par_from;
  return (
    <Block id="quality" kicker="HAR SAWAAL KO EK HI TAG" title="Aapke attempts kaise rahe" note={`${an.copy.time_label} Par time: ${from.solvers ? from.solvers + ' sawaal students ke data se, ' : ''}${from.standard || 0} sawaal paper standard se.`}>
      <div className="a2-tiles five">{HEAD.map(k => <Tile key={k} id={'quality-' + k} label={name(k)} value={q.headline[k]} sub={about(k)} tone={HEAD_TONE[k]} ids={ids(k)} onDrill={onDrill} />)}</div>
      <div className="a2-row wrap" data-testid="a2-quality-rest">
        {[...over, 'smart_skip', 'not_seen', 'no_score'].map(k => q.counts[k] > 0 && <button type="button" key={k} className="a2-chipbtn" title={t[k][1]} data-testid={'a2-quality-rest-' + k} onClick={() => onDrill(t[k][0], ids(k))}><TagChip tag={k} copy={an.copy} /> {q.counts[k]}</button>)}
      </div>
    </Block>
  );
}

function BySubject({ an }) {
  const data = an.quality.by_subject.map(s => ({ name: s.name, Perfect: s.counts.perfect, Careless: s.counts.wasted, Overtime: s.counts.slow_correct + s.counts.costly_overtime, Confused: s.counts.confused, 'Concept gap': s.counts.concept_gap }));
  return (
    <Block id="quality-subjects" kicker="SUBJECT × TAG" title="Kis subject mein kaisi galti">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-quality-table">
        <thead><tr><th>Subject</th>{BARS.map(b => <th key={b[0]}>{b[0]}</th>)}</tr></thead>
        <tbody>{data.map(r => <tr key={r.name}><td><b>{r.name}</b></td>{BARS.map(b => <td key={b[0]}>{r[b[0]]}</td>)}</tr>)}</tbody>
      </table></div>
      <div className="a2-chart" data-testid="a2-quality-chart"><ResponsiveContainer width="100%" height={240}><BarChart data={data} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" strokeDasharray="3 3" /><XAxis dataKey="name" tick={AXIS} /><YAxis allowDecimals={false} tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
        {BARS.map(b => <Bar key={b[0]} dataKey={b[0]} fill={b[1]} radius={[4, 4, 0, 0]} />)}
      </BarChart></ResponsiveContainer></div>
    </Block>
  );
}

export function Quality({ an, onDrill, onOpen }) {
  const q = an.quality, t = an.copy.tags;
  if (!q.available) return <Later id="quality" />;
  return <>
    <Headline an={an} onDrill={onDrill} />
    <Block id="speed-map" kicker="SPEED-ACCURACY MAP" title="Jaldbaazi ya der: galti kahan se aayi" note="Har dot ek sawaal hai. Baayein = jaldi, daayein = der. Beech ki line Par (ideal) time hai. Dot par tap karo, solution khulega.">
      <SpeedMap an={an} onOpen={onOpen} />
    </Block>
    {(q.painful.length > 0 || q.lucky.length > 0) && <div className={q.painful.length && q.lucky.length ? 'a2-duo' : 'a2-stack'}>
      {q.painful.length > 0 && <Block id="painful" kicker="DOHRA NUKSAAN" title="Painful sawaal" note="Galat bhi hue aur Par time se zyada bhi khaaya. Inka concept sabse pehle dekho.">
        <QChips id="painful" ids={q.painful} an={an} onOpen={onOpen} />
      </Block>}
      {q.lucky.length > 0 && <Block id="lucky" kicker="JALDI-SAHI" title="Kahin tukka to nahi tha?" note="Par ke 25% se bhi kam time mein sahi. Tukka tha to concept ek baar dekh lo.">
        <QChips id="lucky" ids={q.lucky} an={an} onOpen={onOpen} />
      </Block>}
    </div>}
    <BySubject an={an} />
    <details className="a2-defs" data-testid="a2-quality-defs">
      <summary>Tags ke matlab (rulebook)</summary>
      <dl>{ORDER.map(k => <div key={k}><dt><TagChip tag={k} copy={an.copy} /></dt><dd>{t[k][1]}</dd></div>)}</dl>
    </details>
  </>;
}
