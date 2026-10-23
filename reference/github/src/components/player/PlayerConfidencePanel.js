import React, {useEffect, useState} from 'react';
import {ChevronDown} from 'lucide-react';
import {Collapsible, CollapsibleTrigger, CollapsibleContent} from '../ui/collapsible';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Label} from '../ui/label';

export const PlayerConfidencePanel = ({questionId, preference, observation, changed, answerChosen, disabled, onSave, online}) => {
  const [open, setOpen] = useState(false);
  const [choice, setChoice] = useState(preference == null ? '' : String(preference * 100));
  useEffect(() => { setChoice(preference == null ? '' : String(preference * 100)); }, [preference]);
  const locked = disabled || !!observation || answerChosen;
  const value = observation ? observation.probability : preference;
  const valid = choice.trim() !== '' && Number.isFinite(Number(choice)) && Number(choice) >= 0 && Number(choice) <= 100;
  return <Collapsible open={open} onOpenChange={setOpen} className="confidence-panel" data-testid="player-confidence-panel">
    <CollapsibleTrigger asChild><Button variant="ghost" className="confidence-trigger" data-testid="player-confidence-collapsible-toggle">
      <span>Add confidence <small>(optional)</small></span>
      <span data-testid="player-confidence-collapsible-summary">{value == null ? 'Not rated' : `${Math.round(value * 100)}%`}<ChevronDown size={15}/></span>
    </Button></CollapsibleTrigger>
    <CollapsibleContent className="confidence-content">
      <p data-testid="player-confidence-help">Before choosing your first answer, optionally estimate how likely it is correct. It never changes your marks or blocks your attempt.</p>
      <Label htmlFor={'confidence-'+questionId}>Your estimate · 0–100%</Label>
      <Input id={'confidence-'+questionId} type="number" min="0" max="100" step="1" value={choice} disabled={locked} onChange={e=>setChoice(e.target.value)} placeholder="No estimate selected" aria-invalid={choice !== '' && !valid} data-testid="player-confidence-value"/>
      {choice !== '' && !valid && <p role="alert" data-testid="player-confidence-invalid">Enter a number between 0 and 100.</p>}
      <div className="confidence-actions">
        <Button variant="outline" disabled={locked || !valid} onClick={()=>onSave(questionId, Number(choice)/100)} data-testid="player-confidence-save-button">Save confidence</Button>
        <Button variant="ghost" disabled={locked || value == null} onClick={()=>{setChoice('');onSave(questionId,null)}} data-testid="player-confidence-clear-button">Clear</Button>
      </div>
      <p className="import-fineprint" role="status" data-testid="player-confidence-save-state">
        {observation ? 'Your first response is saved; its original rating is locked.' : answerChosen ? 'An answer is already selected. Confidence cannot be added retrospectively.' : value == null ? 'No rating saved. You can continue normally.' : `Saved on this device${online ? '' : ' · offline'}. Sent with your first answer, without an extra request.`}
      </p>
      {changed && <p className="import-fineprint" data-testid="player-confidence-excluded-note">Excluded from calibration: your response changed after rating, even if changed back.</p>}
    </CollapsibleContent>
  </Collapsible>;
};
