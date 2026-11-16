import React,{useEffect,useState} from 'react';
import {Loader2,Trash2} from 'lucide-react';
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription,DialogFooter} from '../ui/dialog';
import {Button} from '../ui/button';

const plural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;

// Says exactly what leaves for good before anything is deleted.
export function DeleteDialog({target,onClose,onConfirm,busy}){
 const [sure,setSure]=useState(false);
 useEffect(()=>{setSure(false);},[target]);
 const tests=target?.tests||[],uploads=target?.uploads||[];
 const attempts=tests.reduce((n,t)=>n+(t.attempts||0),0);
 const what=[tests.length?plural(tests.length,'test'):'',uploads.length?plural(uploads.length,'upload'):''].filter(Boolean).join(' and ');
 return <Dialog open={!!target} onOpenChange={o=>{if(!o&&!busy)onClose();}}>
  <DialogContent className="library-delete-dialog" data-testid="library-delete-dialog">
   <DialogHeader><DialogTitle>Delete {what} for good?</DialogTitle><DialogDescription>{tests.length===1&&!uploads.length?tests[0].title:uploads.length===1&&!tests.length?uploads[0].title:'They leave the Library and the server.'}</DialogDescription></DialogHeader>
   <ul className="library-restore-facts" data-testid="library-delete-facts">
    <li className="is-danger">This cannot be undone. Restore will no longer be possible.</li>
    {attempts>0&&<li data-testid="library-delete-attempts">{plural(attempts,'student attempt')} keep{attempts===1?'s':''} the score line. Students can no longer open those questions or solutions.</li>}
    {tests.length>0&&<li>The PDF a test came from is deleted too once no other test uses it.</li>}
    {uploads.length>0&&<li>Every Library test made from {uploads.length===1?'this upload':'these uploads'} is deleted with it.</li>}
    <li>Want a copy? Close this and use Download all as ZIP first.</li>
   </ul>
   <label className="book-check library-delete-sure"><input type="checkbox" checked={sure} onChange={e=>setSure(e.target.checked)} disabled={busy} data-testid="library-delete-sure"/><span>I understand. Delete {what} for good.</span></label>
   <DialogFooter><Button variant="outline" onClick={onClose} disabled={busy} data-testid="library-delete-cancel">Cancel</Button><Button variant="destructive" onClick={onConfirm} disabled={busy||!sure} data-testid="library-delete-confirm">{busy?<Loader2 size={16} className="spin"/>:<Trash2 size={16}/>}Delete for good</Button></DialogFooter>
  </DialogContent>
 </Dialog>;
}
