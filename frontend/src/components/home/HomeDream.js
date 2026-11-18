// Home: the student's dream colleges against the latest full mock, or an invitation to pick them.
import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import { DreamMeter } from '../rank/DreamPanel';
import { EXAMS, FULL, dreamsOf, mocksOf, useDreams } from '../rank/rankStore';
import '../../rank.css';
import '../../celebrate.css';

export function HomeDream() {
  const s = useDreams();
  if (!s.loaded) return null;
  const exam = EXAMS.find(e => dreamsOf(s, e).length) || null;
  if (!exam) return <Link to="/rank?tool=target" className="home-dream-cta" data-testid="home-dream-cta">
    <span className="cb-icon"><Sparkles size={22} /></span>
    <span><b>Apna dream college chuno</b><small>Har full mock ke baad dekho ki aap kitne marks door ho.</small></span><ArrowRight size={18} />
  </Link>;
  const latest = mocksOf(s, exam)[0];
  return <section className="cb-dreams" data-testid="home-dream">
    {dreamsOf(s, exam).slice(0, 2).map((d, i) => <DreamMeter key={d.id} dream={d} score={latest?.score ?? null} max={FULL[exam]} testId={`home-dream-${i}`} />)}
    <Link to="/rank?tool=dream" className="home-dream-all" data-testid="home-dream-all">Saare dream college<ArrowRight size={16} /></Link>
  </section>;
}
