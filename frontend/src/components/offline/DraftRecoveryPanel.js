import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { HardDriveDownload, Download, ArrowRight } from 'lucide-react';
import { Button } from '../ui/button';
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction } from '../ui/alert-dialog';
import { profileDrafts, discardProfileDraft } from '../../lib/drafts';
import { toast } from 'sonner';

export const DraftRecoveryPanel = ({ userId, attemptId }) => {
  const [revision, setRevision] = useState(0); const [selected,setSelected]=useState(null);
  const drafts = profileDrafts(userId).filter(d => !attemptId || d.attemptId === attemptId);
  function exportDraft(d) {
    const blob=new Blob([JSON.stringify({attempt_id:d.attemptId,local_only:true,warning:'These drafts are not proof of accepted or scored answers.',answers:d.answers,meta:d.meta},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='jeelive-ai-local-draft-'+d.attemptId+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <section className="import-card draft-recovery" data-testid="draft-recovery-list" data-revision={revision}><div className="import-section-label"><HardDriveDownload size={18}/> SAVED ON THIS DEVICE</div><h2>Local drafts stay separate from your score.</h2><p className="import-muted">Only server-acknowledged responses count. Reopening a still-active attempt can sync drafts; expired drafts remain here for reference and cannot change a sealed result.</p>
    {!drafts.length ? <p className="import-fineprint mt-4" data-testid="draft-recovery-empty">No pending drafts for {attemptId?'this attempt':'this profile'} on this device.</p> : <div className="space-y-4 mt-5" data-testid="draft-recovery-banner">{drafts.map((d,i)=><article className="draft-row" key={d.key} data-testid={'draft-recovery-row-'+i}><strong>{d.meta.title || 'Saved practice attempt'}</strong><p>{d.corrupt?'A local draft could not be read safely. It has not been deleted.':`${d.count} unacknowledged response(s)`}</p><small>{d.meta.updated_at?new Date(d.meta.updated_at).toLocaleString():'Local save time unavailable'} · {d.attemptId}</small><div className="flex flex-wrap gap-2 mt-3"><Button asChild variant="outline"><Link to={'/attempts/'+d.attemptId} data-testid={'draft-recovery-resume-'+i}>Open attempt<ArrowRight size={15}/></Link></Button><Button variant="outline" disabled={d.corrupt} data-testid={'draft-recovery-export-'+i} onClick={()=>exportDraft(d)}><Download size={15}/> Export draft</Button><Button variant="ghost" data-testid={'draft-recovery-discard-'+i} onClick={()=>setSelected(d)}>Discard local draft</Button></div></article>)}</div>}
    <AlertDialog open={!!selected} onOpenChange={open=>!open&&setSelected(null)}><AlertDialogContent data-testid="draft-discard-dialog"><AlertDialogHeader><AlertDialogTitle>Discard this local draft?</AlertDialogTitle><AlertDialogDescription>This removes only the selected attempt's unacknowledged draft from this device. Saved server answers and other profiles are unchanged. Export first if you want a copy.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel data-testid="draft-discard-cancel">Keep draft</AlertDialogCancel><AlertDialogAction data-testid="draft-discard-confirm" onClick={()=>{try{discardProfileDraft(selected);setRevision(x=>x+1);setSelected(null)}catch{toast.error('Browser storage could not be updated. Draft retained.')}}}>Discard this draft</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
  </section>;
};
