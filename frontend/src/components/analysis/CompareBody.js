import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, LineChart, Line } from 'recharts';
import { Users, Crown } from 'lucide-react';
import { Block, Tile, mmss, pc, TIP, LEGEND, AXIS, GRID } from './parts';
import { useBoard } from './Leaderboard';
import { explain } from './explain';

const TARGETS = [['topper', 'Topper'], ['top10', 'Top 10%'], ['average', 'Class average']];

export function ComparePicker({ id, value, onChange, above }) {
  const d = useBoard(id);
  const seen = new Set();
  const people = d?.state === 'ready' ? [...d.rows, ...d.around].filter(r => !r.is_you && !seen.has(r.handle) && seen.add(r.handle)) : [];
  const next = above?.handle ? 'user:' + above.handle : null;
  return (
    <div className="a2-picker" data-testid="a2-compare-picker">
      <span>Kisse compare karna hai?</span>
      <div className="a2-pills">
        {TARGETS.map(([k, l]) => <button type="button" key={k} className={value === k ? 'on' : ''} aria-pressed={value === k} data-testid={'a2-compare-' + k} onClick={() => onChange(k)}>{l}</button>)}
        {next && <button type="button" className={value === next ? 'on' : ''} aria-pressed={value === next} data-testid="a2-compare-above" onClick={() => onChange(next)}>Aapse ek Rank upar</button>}
      </div>
      {people.length > 0 && <select aria-label="Leaderboard se student chuno" data-testid="a2-compare-student" value={value.startsWith('user:') ? value : ''} onChange={e => e.target.value && onChange(e.target.value)}>
        <option value="">Leaderboard se student chuno…</option>
        {people.map(l => <option key={l.handle} value={'user:' + l.handle}>#{l.rank} · {l.name} · {l.score}</option>)}
      </select>}
    </div>
  );
}

const QUALITY = [['Perfect', t => t.perfect], ['Careless galti', t => t.wasted], ['Overtime', t => t.slow_correct + t.costly_overtime], ['Confused', t => t.confused], ['Concept gap', t => t.concept_gap]];
const HAS = { head: ['overview', 'potential', 'journey', 'qs'], subjects: ['overview', 'performance'], quality: ['quality'], pace: ['time'], subtime: ['time'], walk: ['journey'], difficulty: ['difficulty'], gap: ['overview', 'potential', 'performance'] };
const round = v => Math.round(v * 10) / 10;

function Gap({ c, an, about }) {
  const top = c.by_subject.find(s => s.gap > 0);
  const hard = [...c.by_difficulty].filter(d => d.you != null && d.them != null).sort((a, b) => (b.them - b.you) - (a.them - a.you))[0];
  const t = c.split_total || { volume: 0, quality: 0 };
  return (
    <Block id="compare-gap" kicker="GAP KA HISAAB" title="Gap sabse bada kahan hai" info={about} note="Volume = unhone zyada sawaal attempt kiye. Quality = har attempt par unke marks zyada bane (kam galat jawab).">
      <ul className="a2-gaps" data-testid="a2-compare-biggest">
        {top && <li>Subject: <b>{top.name}</b> mein {top.gap} marks ka gap (aap {top.you}, {c.label} {top.them}).</li>}
        {hard && hard.them > hard.you && <li>Difficulty: <b>{an.copy.levels[hard.level]}</b> sawaalon par Accuracy aap {pc(hard.you)}, {c.label} {pc(hard.them)}.</li>}
        {c.gap > 0 && <li>Kul gap {c.gap} marks: <b>{round(t.volume)}</b> kam attempt se, <b>{round(t.quality)}</b> galat jawab (kam Accuracy) se.</li>}
        {c.gap <= 0 && <li>Is compare mein aap {c.gap < 0 ? `${-c.gap} marks aage ho` : 'barabar ho'}.</li>}
      </ul>
      {c.split?.length > 0 && <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-split">
        <thead><tr><th>Subject</th><th>Kam attempt se</th><th>Galat jawab se</th><th>Kya karein</th></tr></thead>
        <tbody>{c.split.map(s => <tr key={s.name}><td><b>{s.name}</b></td><td>{s.volume}</td><td>{s.quality}</td><td>{s.volume <= 0 && s.quality <= 0 ? 'Aap aage ho' : s.volume > s.quality ? 'Zyada sawaal attempt karo' : 'Accuracy badhao'}</td></tr>)}</tbody>
      </table></div>}
    </Block>
  );
}

// You against a student or a group. Totals and averages only: the other student's answers never reach the browser.
export function CompareBody({ an, part }) {
  const c = an.compare;
  if (!c) return null;
  if (!c.available) return <div className="a2-later" data-testid="a2-compare-off"><Users size={22} /><div><strong>Compare abhi nahi khula</strong><p>{c.reason}</p></div></div>;
  const you = an.you, them = c.profile, mine = an.overview || {}, show = k => part === 'all' || HAS[k].includes(part), X = explain(an);
  const theirs = Object.fromEntries(them.subjects.map(s => [s.name, s]));
  const chart = c.by_subject.map(s => ({ name: s.name, Aap: s.you, [c.label]: s.them }));
  const pace = you.pace && them.pace ? you.pace.map((v, i) => ({ at: i * 5, Aap: v, [c.label]: them.pace[i] })) : null;
  const both = you.subjects.filter(s => theirs[s.name]);
  const timed = both.some(s => s.time != null && theirs[s.name].time != null);
  const spent = both.map(s => ({ name: s.name, Aap: round((s.time || 0) / 60), [c.label]: round((theirs[s.name].time || 0) / 60) }));
  const self = c.kind === 'topper' && mine.rank === 1 && c.gap === 0;
  return <div className="a2-compare" data-testid="a2-compare">
    {self && <p className="a2-above" data-testid="a2-compare-self"><Crown size={16} className="a2-gold" aria-hidden="true" /> Aap khud is paper ke topper ho, isliye yeh compare aapka apne hi saath hai. Upar se Top 10% ya Class average chuno.</p>}
    {show('head') && <Block id="compare-head" kicker="COMPARATIVE" title={`Aap vs ${c.label}`} note={`Sirf totals aur averages. Kisi doosre student ke jawab kabhi nahi dikhte.${c.n > 1 ? ` ${c.n} students ka hisaab.` : ''}`}>
      <div className="a2-tiles four">
        <Tile id="compare-you" label="Aapka Score" value={you.score} sub={mine.rank ? `Rank #${mine.rank} · Percentile ${mine.percentile}` : `Accuracy ${pc(you.accuracy)}`} tone="brand" />
        <Tile id="compare-them" label={c.label} value={them.score} sub={c.rank ? `Rank #${c.rank} · Percentile ${c.percentile}` : `Accuracy ${pc(them.accuracy)}`} tone="warn" />
        <Tile id="compare-gap" label="Gap" value={Math.abs(c.gap)} sub={c.gap > 0 ? 'marks peeche ho' : c.gap < 0 ? 'marks aage ho' : 'barabar'} tone={c.gap > 0 ? 'bad' : 'good'} />
        <Tile id="compare-time" label="Time" value={mmss(you.time)} sub={`${c.label}: ${mmss(them.time)}`} />
      </div>
    </Block>}
    {show('gap') && <Gap c={c} an={an} about={X.gap} />}
    {show('subjects') && <Block id="compare-subjects" kicker="SUBJECT-WISE" title="Subject-wise: aap vs woh">
      <div className="a2-chart" data-testid="a2-compare-subject-chart"><ResponsiveContainer width="100%" height={230}><BarChart data={chart} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} /><YAxis tick={AXIS} /><Tooltip {...TIP} /><Legend {...LEGEND} />
        <Bar dataKey="Aap" fill="var(--a-fill)" radius={[5, 5, 0, 0]} /><Bar dataKey={c.label} fill="var(--a-warn)" radius={[5, 5, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-subject-table">
        <thead><tr><th>Subject</th><th>Score</th><th>Attempted</th><th>Accuracy</th><th>Time</th></tr></thead>
        <tbody>{both.map(s => { const o = theirs[s.name]; return <tr key={s.name}><td><b>{s.name}</b></td><td>{s.score} <small>vs {o.score}</small></td><td>{s.attempted} <small>vs {o.attempted}</small></td><td>{pc(s.accuracy)} <small>vs {pc(o.accuracy)}</small></td><td>{mmss(s.time)} <small>vs {mmss(o.time)}</small></td></tr>; })}</tbody>
      </table></div>
    </Block>}
    {show('quality') && <Block id="compare-quality" kicker="ATTEMPT QUALITY" title="Attempt Quality: aap vs woh">
      {you.tags && them.tags ? <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-quality-table">
        <thead><tr><th>Tag</th><th>Aap</th><th>{c.label}</th></tr></thead>
        <tbody>{QUALITY.map(([name, get]) => <tr key={name}><td><b>{name}</b></td><td>{get(you.tags)}</td><td>{round(get(them.tags))}</td></tr>)}</tbody>
      </table></div> : <p className="a2-empty" data-testid="a2-compare-quality-off">Dono taraf time record hone par hi Attempt Quality compare hoti hai.</p>}
    </Block>}
    {show('subtime') && <Block id="compare-subject-time" kicker="TIME" title="Har subject par laga time: aap vs woh" note="Sawaalon par screen time, minute mein.">
      {timed ? <div className="a2-chart" data-testid="a2-compare-time-chart"><ResponsiveContainer width="100%" height={220}><BarChart data={spent} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid {...GRID} /><XAxis dataKey="name" tick={AXIS} /><YAxis tick={AXIS} unit="m" /><Tooltip {...TIP} /><Legend {...LEGEND} />
        <Bar dataKey="Aap" fill="var(--a-fill)" radius={[5, 5, 0, 0]} /><Bar dataKey={c.label} fill="var(--a-warn)" radius={[5, 5, 0, 0]} />
      </BarChart></ResponsiveContainer></div> : <p className="a2-empty" data-testid="a2-compare-time-off">Dono taraf time record hone par hi subject ka time compare hota hai.</p>}
    </Block>}
    {show('pace') && <Block id="compare-pace" kicker="PACE" title="Pace: aap vs woh" note="Paper ka kitna % time beeta, aur tab tak kitne jawab ho chuke the.">
      {pace ? <div className="a2-chart" data-testid="a2-compare-pace-chart"><ResponsiveContainer width="100%" height={230}><LineChart data={pace} margin={{ top: 8, right: 12, left: -22, bottom: 0 }}>
        <CartesianGrid {...GRID} /><XAxis dataKey="at" tick={AXIS} unit="%" /><YAxis tick={AXIS} /><Tooltip {...TIP} /><Legend {...LEGEND} />
        <Line type="monotone" dataKey="Aap" stroke="var(--a-fill)" strokeWidth={2.6} dot={false} /><Line type="monotone" dataKey={c.label} stroke="var(--a-warn)" strokeWidth={2.6} dot={false} strokeDasharray="6 4" />
      </LineChart></ResponsiveContainer></div> : <p className="a2-empty">Is paper par Pace curve uplabdh nahi hai.</p>}
    </Block>}
    {show('walk') && <Block id="compare-journey" kicker="QUESTION JOURNEY" title="Raasta: aap vs woh" note="Kitne sawaal khole aur kitni baar kisi sawaal par wapas aaye.">
      {you.journey && them.journey ? <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-journey-table">
        <thead><tr><th /><th>Aap</th><th>{c.label}</th></tr></thead>
        <tbody>
          <tr><td><b>Sawaal dekhe</b></td><td>{you.journey.visited}</td><td>{them.journey.visited}</td></tr>
          <tr><td><b>Wapas gaye</b></td><td>{you.journey.revisits}</td><td>{them.journey.revisits}</td></tr>
          <tr><td><b>Attempt kiye</b></td><td>{you.attempted}</td><td>{them.attempted}</td></tr>
        </tbody>
      </table></div> : <p className="a2-empty" data-testid="a2-compare-journey-off">Dono taraf time record hone par hi raasta compare hota hai.</p>}
    </Block>}
    {show('difficulty') && <Block id="compare-difficulty" kicker="DIFFICULTY" title="Difficulty par Accuracy: aap vs woh">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-difficulty-table">
        <thead><tr><th>Level</th><th>Aap</th><th>{c.label}</th></tr></thead>
        <tbody>{c.by_difficulty.map(d => <tr key={d.level}><td><b>{an.copy.levels[d.level]}</b></td><td>{pc(d.you)}</td><td>{pc(d.them)}</td></tr>)}</tbody>
      </table></div>
    </Block>}
  </div>;
}
