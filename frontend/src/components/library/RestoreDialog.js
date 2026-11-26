import React from 'react';
import {Loader2,RotateCcw} from 'lucide-react';
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription,DialogFooter} from '../ui/dialog';
import {Button} from '../ui/button';

const plural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;

// Says in plain words what students will see after the restore, before anything changes.
export function RestoreDialog({tests,onClose,onConfirm,busy}){
 const list=tests||[],live=list.filter(t=>t.state==='live'||t.state==='ended').length,series=list.filter(t=>t.series_date).length;
 return <Dialog open={!!tests} onOpenChange={o=>{if(!o&&!busy)onClose();}}>
  <DialogContent data-testid="library-restore-confirm-dialog">
   <DialogHeader><DialogTitle>Restore {plural(list.length,'test')}?</DialogTitle><DialogDescription>Each test goes back to the exam and mock type it came from.</DialogDescription></DialogHeader>
   <ul className="library-restore-facts" data-testid="library-restore-facts">
    {live>0&&<li className="is-live" data-testid="library-restore-live">{plural(live,'test')} {live===1?'was':'were'} Live. Students see {live===1?'it':'them'} again as soon as {live===1?'its':'their'} pictures are proven in storage; a test without pictures is back right away. If a picture is not proven, that test stays Off and its row says why.</li>}
    {list.length-live>0&&<li data-testid="library-restore-quiet">{plural(list.length-live,'test')} come{list.length-live===1?'s':''} back as {list.length-live===1?'it was':'they were'} (Draft, Off or Scheduled). Students do not see {list.length-live===1?'it':'them'} until you make {list.length-live===1?'it':'them'} Live.</li>}
    {series>0&&<li data-testid="library-restore-series">{plural(series,'All India paper')} go{series===1?'es':''} back on {series===1?'its':'their'} day if that day is still free; otherwise without a day.</li>}
    <li>Students' old scores stay as they are.</li>
   </ul>
   <DialogFooter><Button variant="outline" onClick={onClose} disabled={busy} data-testid="library-restore-cancel">Cancel</Button><Button onClick={onConfirm} disabled={busy} data-testid="library-restore-confirm">{busy?<Loader2 size={16} className="spin"/>:<RotateCcw size={16}/>}Restore {plural(list.length,'test')}</Button></DialogFooter>
  </DialogContent>
 </Dialog>;
}
