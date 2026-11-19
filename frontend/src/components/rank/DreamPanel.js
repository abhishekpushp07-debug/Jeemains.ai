// The Rank tab's Dream college tool: the exam switch (JEE Main / BITSAT / COMEDK with N/5) and the Dream College Meter
// for that exam, with remove buttons. Opens on the first exam that has dreams. Dreams live with the account on the app server.
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Lock } from 'lucide-react';
import { useAuth } from '../../lib/auth';
import { EXAM_LABEL } from './rankApi';
import { Panel, Switch } from './RankUi';
import { dreamsOf, EXAMS, MAX_DREAMS, useDreams } from './rankStore';
import { DreamMeter } from './DreamMeter';

export function DreamPanel({ onTool }) {
  const { user } = useAuth();
  const s = useDreams();
  const [exam, setExam] = useState(null);
  const first = EXAMS.find(e => dreamsOf(s, e).length) ?? null;
  useEffect(() => { if (exam === null && first) setExam(first); }, [exam, first]);
  if (!user) return <Panel testId="dream-signin"><div className="rk-locked"><Lock size={22} /><div><b>Dream college aapke account ke saath save hote hain</b>
    <p>Sign in karo, 5 dream college chuno, aur har full mock ke baad dekho ki aap kitne marks door ho.</p>
    <Link className="rk-go as-link" to="/login?next=%2Frank%3Ftool%3Ddream" data-testid="dream-signin-link">Sign in karo<ArrowRight size={18} /></Link></div></div></Panel>;
  const shown = exam ?? first ?? 'jee';
  return <div className="rk-stack" data-testid="dream-panel">
    <Switch prefix="dream-exam" value={shown} onChange={setExam} items={EXAMS.map(e => ({ key: e, label: `${EXAM_LABEL[e]} ${dreamsOf(s, e).length}/${MAX_DREAMS}` }))} />
    {s.loaded ? <DreamMeter exam={shown} testId="dream-meter" editable chart="full" onAdd={() => onTool('college')} /> : <div className="rk-loading" data-testid="dream-loading" />}
  </div>;
}
