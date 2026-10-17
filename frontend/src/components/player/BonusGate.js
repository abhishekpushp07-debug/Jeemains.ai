import React from 'react';
import {Lock,Unlock,Gift} from 'lucide-react';
import {Button} from '../ui/button';
import {Confirm} from '../Shared';

export const BonusGate=({rule,open,answered,pending,ended,online,onEnter,testId='player-bonus-gate'})=>{
 const total=rule.main_count,left=total-answered;
 if(open)return <div className="bonus-gate is-open" data-testid={testId+'-open'} role="status"><Lock size={16}/><span><strong>Bonus section · {rule.bonus_count} questions.</strong> Your {total} main answers are locked.</span></div>;
 if(left>0||pending)return <div className="bonus-gate is-waiting" data-testid={testId+'-waiting'}><Gift size={16}/><span>{left>0?<>Answer all {total} main questions to unlock {rule.bonus_count} bonus questions. <strong data-testid={testId+'-remaining'}>{left} left.</strong></>:'Saving your last answers… the bonus option appears once every answer is saved.'}</span></div>;
 return <div className="bonus-gate is-ready" data-testid={testId+'-ready'}><Unlock size={16}/><span>All {total} main questions answered.</span><Button className="btn btn-primary" disabled={ended||!online} onClick={onEnter} data-testid={testId+'-enter'}>Attempt Bonus Questions</Button></div>;
};

export const BonusConfirm=({open,onClose,onConfirm,busy,rule})=><Confirm open={open} onClose={onClose} title="Lock your main answers and open the bonus?" button="Lock answers & open bonus" busy={busy} onConfirm={onConfirm}>
 <div className="bonus-warning" data-testid="player-bonus-warning">
  <p><strong>This cannot be undone.</strong> All {rule.main_count} main answers will be locked. You will not be able to change, clear or review-edit them again.</p>
  <p>You then get {rule.bonus_count} bonus questions on the same timer, with the same marking: +3 correct, −1 wrong, 0 unanswered.</p>
  <p>If you are not sure about some main answers, cancel and review them first.</p>
 </div>
</Confirm>;
