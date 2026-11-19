// Home: the student's Dream College Meter (first exam with dreams, two rows, last 8 mocks), or an invitation to pick them.
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import { DreamMeter } from '../rank/DreamMeter';
import { EXAMS, dreamsOf, useDreams } from '../rank/rankStore';
import '../../celebrate.css';

export function HomeDream() {
  const s = useDreams();
  const navigate = useNavigate();
  if (!s.loaded) return null;
  const exam = EXAMS.find(e => dreamsOf(s, e).length) || null;
  if (!exam) return <Link to="/rank?tool=college" className="home-dream-cta" data-testid="home-dream-cta">
    <span className="cb-icon"><Sparkles size={22} /></span>
    <span><b>Apna dream college chuno</b><small>Har full mock ke baad dekho ki aap kitne marks door ho.</small></span><ArrowRight size={18} />
  </Link>;
  return <div className="home-dream" data-testid="home-dream">
    <DreamMeter exam={exam} testId="home-dream-meter" limit={2} chart="compact" onMore={() => navigate('/rank?tool=dream')} onAdd={() => navigate('/rank?tool=college')} />
  </div>;
}
