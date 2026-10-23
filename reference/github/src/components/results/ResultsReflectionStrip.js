import React, {useRef, useState} from 'react';
import {CheckCircle2, LockKeyhole} from 'lucide-react';
import {Button} from '../ui/button';
import {Label} from '../ui/label';
import {Textarea} from '../ui/textarea';
import {Select, SelectTrigger, SelectValue, SelectContent, SelectItem} from '../ui/select';
import {Checkbox} from '../ui/checkbox';
import {put} from '../../lib/api';

const steps = [['identified_error','I identified my error category'],['wrote_note','I wrote a short note'],['reviewed_solution','I reviewed the released solution'],['retry_planned','I have a plan to retry a similar question']];
const empty = {category:null,note:'',identified_error:false,wrote_note:false,reviewed_solution:false,retry_planned:false};
export const ResultsReflectionStrip = ({attemptId,question,scoreVersion,state,categories,assigned,confidence,excluded,solutionPending,onSaved}) => {
  const [draft,setDraft] = useState({...empty,...state});
  const [accepted,setAccepted] = useState(state);
  const [busy,setBusy] = useState(false), [error,setError] = useState(''), [saved,setSaved] = useState(false), [dirty,setDirty] = useState(false);
  const command = useRef(null);
  const n=question.number;
  function edit(key,value) { setDraft(d=>({...d,[key]:value}));command.current=null;setSaved(false);setDirty(true);setError(''); }
  async function reload() {
    setBusy(true);setError('');
    try { const result=await onSaved();const latest=result.review?.states?.[question.id];setAccepted(latest);setDraft({...empty,...latest});setDirty(false);setSaved(false);command.current=null; }
    catch(e){setError(e.message)}finally{setBusy(false)}
  }
  async function save() {
    if (busy) return;
    setBusy(true);setError('');command.current ||= crypto.randomUUID();
    try {
      const result=await put(`/attempts/${attemptId}/reviews/${question.id}`,{request_id:command.current,revision:(accepted?.revision||0)+1,score_version:scoreVersion,category:draft.category,note:draft.note,...Object.fromEntries(steps.map(([key])=>[key,draft[key]]))});
      setAccepted(result);setDraft({...empty,...result});setSaved(true);setDirty(false);command.current=null;
      try { await onSaved(); } catch { setError('Reflection saved, but analytics could not refresh. Reload the saved version to retry.'); }
    } catch(e){setError(e.message)} finally{setBusy(false)}
  }
  return <section className="reflection-panel" data-testid={'results-reflection-'+n}>
    <div className="import-section-label"><LockKeyhole size={15}/> YOUR PRIVATE REFLECTION</div>
    <div className="reflection-confidence"><span>Your confidence</span><strong data-testid={'results-question-confidence-value-'+n}>{confidence==null?'Not rated':`${Math.round(confidence*100)}%`}</strong>{excluded&&<small data-testid={'results-confidence-excluded-'+n}>Excluded from calibration: response changed after rating</small>}</div>
    <div className="reflection-form">
      <Label htmlFor={'reflection-category-'+n}>What went wrong? (optional)</Label>
      <Select value={draft.category||'unlabelled'} disabled={busy} onValueChange={v=>edit('category',v==='unlabelled'?null:v)}>
        <SelectTrigger id={'reflection-category-'+n} data-testid={'results-error-category-select-'+n}><SelectValue placeholder="Choose your own category"/></SelectTrigger>
        <SelectContent><SelectItem value="unlabelled" data-testid={'results-error-category-none-'+n}>No category selected</SelectItem>{Object.entries(categories||{}).map(([key,label])=><SelectItem key={key} value={key} data-testid={`results-error-category-${n}-${key}`}>{label}</SelectItem>)}</SelectContent>
      </Select>
      <Label htmlFor={'reflection-note-'+n}>Notes (optional)</Label>
      <Textarea id={'reflection-note-'+n} data-testid={'results-error-notes-textarea-'+n} value={draft.note} maxLength={500} disabled={busy} onChange={e=>edit('note',e.target.value)} placeholder="What will you do differently next time?"/>
      <small className="import-fineprint" data-testid={'results-note-length-'+n}>{draft.note.length}/500 · Private to this phone profile; phone ownership is not verified</small>
    </div>
    {assigned&&<div className="mistake-checklist" data-testid={'results-mistake-review-card-'+n}>
      <h4>Mistake review</h4><p className="import-fineprint">Four explicit steps—not a mastery score. Select a category and write a note before confirming those steps.</p>
      {steps.map(([key,label])=><label key={key} htmlFor={`${key}-${n}`} className="review-check-row"><Checkbox id={`${key}-${n}`} data-testid={`results-mistake-${n}-${key}`} checked={draft[key]} disabled={busy||(key==='reviewed_solution'&&solutionPending)||(key==='identified_error'&&!draft.category&&!draft[key])||(key==='wrote_note'&&!draft.note.trim()&&!draft[key])} onCheckedChange={v=>edit(key,v===true)}/><span>{key==='reviewed_solution'&&question.solution_kind==='answer_key_only'?'I reviewed the supplied answer key':label}</span></label>)}
      {accepted?.completed&&!dirty&&<p className="review-completed" data-testid={'results-mistake-review-complete-'+n}><CheckCircle2 size={16}/> Saved checklist completed</p>}
    </div>}
    {error&&<p role="alert" className="import-error" data-testid={'reflection-save-error-'+n}>{error} Your edits are still here.</p>}
    <div className="reflection-actions">
      <Button variant="outline" onClick={save} disabled={busy||(draft.reviewed_solution&&solutionPending)} data-testid={'results-reflection-save-'+n}>{busy?'Saving…':'Save reflection'}</Button>
      {error&&<Button variant="ghost" disabled={busy} onClick={reload} data-testid={'reflection-reload-'+n}>Reload saved version</Button>}
      <span className="import-fineprint" role="status" data-testid={'results-reflection-status-'+n}>{saved?'Saved to your profile. Marks unchanged.':dirty?'Unsaved changes · save before leaving.':'No cause is assigned automatically.'}</span>
    </div>
  </section>;
};
