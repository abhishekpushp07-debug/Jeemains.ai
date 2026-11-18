import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, LineChart, Line } from 'recharts';
import { Users } from 'lucide-react';
import { Block, Tile, mmss, pc, TIP, AXIS } from './parts';

const TARGETS = [['topper', 'Topper'], ['top10', 'Top 10%'], ['average', 'Class average']];

export function ComparePicker({ an, value, onChange }) {
  const leaders = an.class.leaders || [];
  return (
    <div className="a2-picker" data-testid="a2-compare-picker">
      <span>Kisse compare karna hai?</span>
      <div className="a2-pills">
        {TARGETS.map(([k, l]) => <button type="button" key={k} className={value === k ? 'on' : ''} aria-pressed={value === k} data-testid={'a2-compare-' + k} onClick={() => onChange(k)}>{l}</button>)}
      </div>
      {leaders.length > 0 && <select aria-label="Leaderboard se student chuno" data-testid="a2-compare-student" value={value.startsWith('user:') ? value : ''} onChange={e => e.target.value && onChange(e.target.value)}>
        <option value="">Leaderboard se chuno…</option>
        {leaders.map(l => <option key={l.handle} value={'user:' + l.handle}>#{l.rank} · {l.learner} · {l.score}</option>)}
      </select>}
    </div>
  );
}

const QUALITY = [['Perfect', t => t.perfect], ['Careless galti', t => t.wasted], ['Overtime', t => t.slow_correct + t.costly_overtime], ['Confused', t => t.confused], ['Concept gap', t => t.concept_gap]];
const HAS = { head: ['overview', 'potential', 'journey', 'qs'], subjects: ['overview', 'performance'], quality: ['quality'], pace: ['time'], difficulty: ['difficulty'], gap: ['overview', 'potential'] };

// You against a student or a group. Totals and averages only: the other student's answers never reach the browser.
export function CompareBody({ an, part }) {
  const c = an.compare;
  if (!c) return null;
  if (!c.available) return <div className="a2-later" data-testid="a2-compare-off"><Users size={22} /><div><strong>Compare abhi nahi khula</strong><p>{c.reason}</p></div></div>;
  const you = an.you, them = c.profile, mine = an.overview || {}, show = k => part === 'all' || HAS[k].includes(part);
  const theirs = Object.fromEntries(them.subjects.map(s => [s.name, s]));
  const chart = c.by_subject.map(s => ({ name: s.name, Aap: s.you, [c.label]: s.them }));
  const pace = you.pace && them.pace ? you.pace.map((v, i) => ({ at: i * 5, Aap: v, [c.label]: them.pace[i] })) : null;
  const top = c.by_subject.find(s => s.gap > 0);
  const hard = [...c.by_difficulty].filter(d => d.you != null && d.them != null).sort((a, b) => (b.them - b.you) - (a.them - a.you))[0];
  return <div className="a2-compare" data-testid="a2-compare">
    {show('head') && <Block id="compare-head" title={`Aap vs ${c.label}`} note="Sirf totals aur averages. Kisi doosre student ke jawab kabhi nahi dikhte.">
      <div className="a2-tiles four">
        <Tile id="compare-you" label="Aapka Score" value={you.score} sub={mine.rank ? `Rank #${mine.rank} · Percentile ${mine.percentile}` : `Accuracy ${pc(you.accuracy)}`} tone="brand" />
        <Tile id="compare-them" label={c.label} value={them.score} sub={c.rank ? `Rank #${c.rank} · Percentile ${c.percentile}` : `Accuracy ${pc(them.accuracy)}`} />
        <Tile id="compare-gap" label="Gap" value={Math.abs(c.gap)} sub={c.gap > 0 ? 'marks peeche ho' : c.gap < 0 ? 'marks aage ho' : 'barabar'} tone={c.gap > 0 ? 'bad' : 'good'} />
        <Tile id="compare-time" label="Time" value={mmss(you.time)} sub={`${c.label}: ${mmss(them.time)}`} />
      </div>
    </Block>}
    {show('gap') && (top || hard) && <Block id="compare-gap" title="Gap sabse bada kahan hai">
      <ul className="a2-gaps" data-testid="a2-compare-biggest">
        {top && <li>Subject: <b>{top.name}</b> mein {top.gap} marks ka gap (aap {top.you}, {c.label} {top.them}).</li>}
        {hard && hard.them > hard.you && <li>Difficulty: <b>{an.copy.levels[hard.level]}</b> sawaalon par Accuracy aap {pc(hard.you)}, {c.label} {pc(hard.them)}.</li>}
      </ul>
    </Block>}
    {show('subjects') && <Block id="compare-subjects" title="Subject-wise: aap vs woh">
      <div className="a2-chart" data-testid="a2-compare-subject-chart"><ResponsiveContainer width="100%" height={230}><BarChart data={chart} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" /><XAxis dataKey="name" tick={AXIS} /><YAxis tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Aap" fill="var(--a-brand)" radius={[4, 4, 0, 0]} /><Bar dataKey={c.label} fill="var(--a-warn)" radius={[4, 4, 0, 0]} />
      </BarChart></ResponsiveContainer></div>
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-subject-table">
        <thead><tr><th>Subject</th><th>Score</th><th>Attempted</th><th>Accuracy</th><th>Time</th></tr></thead>
        <tbody>{you.subjects.filter(s => theirs[s.name]).map(s => { const o = theirs[s.name]; return <tr key={s.name}><td>{s.name}</td><td>{s.score} <small>vs {o.score}</small></td><td>{s.attempted} <small>vs {o.attempted}</small></td><td>{pc(s.accuracy)} <small>vs {pc(o.accuracy)}</small></td><td>{mmss(s.time)} <small>vs {mmss(o.time)}</small></td></tr>; })}</tbody>
      </table></div>
    </Block>}
    {show('quality') && <Block id="compare-quality" title="Attempt Quality: aap vs woh">
      {you.tags && them.tags ? <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-quality-table">
        <thead><tr><th>Tag</th><th>Aap</th><th>{c.label}</th></tr></thead>
        <tbody>{QUALITY.map(([name, get]) => <tr key={name}><td>{name}</td><td>{get(you.tags)}</td><td>{Math.round(get(them.tags) * 10) / 10}</td></tr>)}</tbody>
      </table></div> : <p className="a2-empty" data-testid="a2-compare-quality-off">Dono taraf time record hone par hi Attempt Quality compare hoti hai.</p>}
    </Block>}
    {show('pace') && <Block id="compare-pace" title="Pace: aap vs woh" note="Paper ka kitna % time beeta, aur tab tak kitne jawab ho chuke the.">
      {pace ? <div className="a2-chart" data-testid="a2-compare-pace-chart"><ResponsiveContainer width="100%" height={230}><LineChart data={pace} margin={{ top: 8, right: 12, left: -22, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--line)" /><XAxis dataKey="at" tick={AXIS} unit="%" /><YAxis tick={AXIS} /><Tooltip {...TIP} /><Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="Aap" stroke="var(--a-brand)" strokeWidth={2.5} dot={false} /><Line type="monotone" dataKey={c.label} stroke="var(--a-warn)" strokeWidth={2.5} dot={false} strokeDasharray="6 4" />
      </LineChart></ResponsiveContainer></div> : <p className="a2-empty">Is paper par Pace curve uplabdh nahi hai.</p>}
    </Block>}
    {show('difficulty') && <Block id="compare-difficulty" title="Difficulty par Accuracy: aap vs woh">
      <div className="a2-scroll"><table className="a2-table" data-testid="a2-compare-difficulty-table">
        <thead><tr><th>Level</th><th>Aap</th><th>{c.label}</th></tr></thead>
        <tbody>{c.by_difficulty.map(d => <tr key={d.level}><td>{an.copy.levels[d.level]}</td><td>{pc(d.you)}</td><td>{pc(d.them)}</td></tr>)}</tbody>
      </table></div>
    </Block>}
  </div>;
}
