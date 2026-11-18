import React from 'react';
import { Zap, ShieldAlert, Timer, Dices } from 'lucide-react';
import { Block, Tile, QChips, r1 } from './parts';
import { Waterfall } from './charts';

const STEP = {
  careless: ['Careless galti theek', Zap, 'Jo sawaal Par time ke aadhe se kam mein galat hue. Aaram se padhte to sahi + negative wapas.'],
  guard: ['Mushkil par risk nahi', ShieldAlert, 'Jo Tough sawaal class mein bhi 25% se kam bane aur aapse galat hue. Chhod dete to negative bachta.'],
  reinvest: ['Atka time wapas', Timer, 'Jahan time laga par marks nahi bane, woh time chhode hue Easy sawaalon ko dete. Aapki apni accuracy se hisaab.'],
};
const AT = { current: 'Abhi', realistic: 'Realistic target', maximum: 'Maximum potential' };

function Steps({ an, p, onDrill, onOpen }) {
  return (
    <Block id="potential-steps" kicker="HAR STEP KE PEECHE KE SAWAAL" title="Kahan se kitne marks">
      <div className="a2-steps">
        {p.steps.map(s => {
          const [name, Icon, about] = STEP[s.key];
          return (
            <article key={s.key} className="a2-step-card" data-testid={'a2-potential-step-' + s.key}>
              <header><Icon size={18} aria-hidden="true" /><h4>{name}</h4><strong>+{s.marks}</strong></header>
              <p>{about}{s.key === 'reinvest' && s.minutes ? ` Atka time: ${s.minutes} min.` : ''}</p>
              {s.questions.length > 0 ? <>
                <QChips id={'potential-' + s.key} ids={s.questions} an={an} onOpen={onOpen} max={18} />
                <button type="button" className="a2-link" data-testid={'a2-potential-questions-' + s.key} onClick={() => onDrill(name, s.questions)}>{s.questions.length} sawaal ki list</button>
              </> : <p className="a2-empty">Is step mein koi sawaal nahi. Badhiya!</p>}
            </article>
          );
        })}
      </div>
    </Block>
  );
}

export function Potential({ an, onDrill, onOpen }) {
  const p = an.potential, ranked = p.at.filter(x => x.rank), g = p.guess;
  return <>
    <Block id="potential" kicker="SEEDHA HISAAB · KOI ANDAAZA NAHI" title="Yahan se marks bach sakte the" note="Realistic target = Careless + Risk poora, aur atke time ka aadha. Maximum = teeno poore.">
      {!p.available && <p className="a2-empty" data-testid="a2-potential-partial">Is attempt mein time record nahi hua, isliye Careless aur Time wale step 0 hain. Agle mock se poore dikhenge.</p>}
      <div className="a2-tiles three">
        <Tile id="potential-current" label="Abhi ka Score" value={<span data-testid="a2-potential-current">{p.current}</span>} sub={`${p.paper_maximum} mein se`} />
        <Tile id="potential-realistic" label="Realistic target" value={<span data-testid="a2-potential-realistic">{p.realistic}</span>} sub={`+${r1(p.realistic - p.current)} marks, sirf aadatein badal kar`} tone="good" />
        <Tile id="potential-maximum" label="Maximum potential" value={<span data-testid="a2-potential-maximum">{p.maximum}</span>} sub={`+${r1(p.maximum - p.current)} marks`} tone="good" />
      </div>
      <Waterfall p={p} />
    </Block>
    <Steps an={an} p={p} onDrill={onDrill} onOpen={onOpen} />
    {ranked.length > 0 && <Block id="potential-rank" kicker="ISI PAPER KE STUDENTS SE" title="Itne marks par Rank lagbhag">
      <div className="a2-tiles three">{ranked.map(x => <Tile key={x.key} id={'at-' + x.key} label={`${AT[x.key]} · ${x.score} marks`} value={'#' + x.rank} sub={`${x.of} mein · Percentile ${x.percentile}`} tone={x.key === 'current' ? '' : 'good'} />)}</div>
    </Block>}
    <Block id="guess" kicker="NEGATIVE MARKING" title="Guess ka niyam">
      <div className="a2-guess" data-testid="a2-guess">
        <Dices size={26} aria-hidden="true" />
        <div>
          <p>Is paper mein sahi par <b>+{g.pos}</b> aur galat par <b>{g.neg}</b>. Jawab tabhi do jab <b>{g.break_even}% se zyada</b> yakeen ho.</p>
          <p>4 option mein se ek bhi pakka hata sako to guess faydemand hai. Bilkul andhere mein chhodna behtar hai.</p>
          <p className="a2-muted">Bina kisi galat jawab ke (sirf chhod kar) aapka Score <b>{p.no_negative}</b> hota.</p>
        </div>
      </div>
    </Block>
  </>;
}
