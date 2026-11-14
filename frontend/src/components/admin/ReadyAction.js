import React,{useState} from 'react';
import {Link} from 'react-router-dom';
import {ChevronDown,Send,CalendarClock,ExternalLink,Loader2} from 'lucide-react';
import {Popover,PopoverTrigger,PopoverContent} from '../ui/popover';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {post} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {toast} from 'sonner';

export function ReadyAction({item,onDone,label='Ready',testId}){
 const [open,setOpen]=useState(false),[at,setAt]=useState(''),[busy,setBusy]=useState(false);
 const id=testId||'ready-action-'+item.id;
 async function publish(release){setBusy(true);try{const r=await post('/admin/publish-ready',{items:[{kind:item.kind,id:item.id}],...(release?{release_at:release}:{})});invalidateCatalog();toast.success(r.message);(r.notes||[]).forEach(n=>toast.message(n));setOpen(false);onDone?.();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <Popover open={open} onOpenChange={setOpen}>
  <PopoverTrigger asChild><button type="button" className="admin-chip tone-ready admin-chip-button" aria-label={`${label}: publish ${item.title}`} data-testid={id}><i aria-hidden="true"/>{label}<ChevronDown size={13} aria-hidden="true"/></button></PopoverTrigger>
  <PopoverContent className="admin-popover" align="end" data-testid={id+'-menu'}>
   <strong>{item.kind==='chapter_book'?'All chapters of '+item.title:item.title}</strong>
   {item.kind==='import'?<><p>Paper uploads open as a live exam at the time you choose on their page.</p><Button asChild size="sm"><Link to={'/studio/imports/'+item.id} data-testid={id+'-open'}><ExternalLink size={15}/>Choose its live time</Link></Button></>:<>
    <Button size="sm" disabled={busy} onClick={()=>publish(null)} data-testid={id+'-now'}>{busy?<Loader2 size={15} className="spin"/>:<Send size={15}/>}Publish now</Button>
    {item.kind!=='chapter_book'&&<div className="admin-popover-row"><Input type="datetime-local" aria-label="Publish at (your local time)" value={at} onChange={e=>setAt(e.target.value)} data-testid={id+'-at'}/><Button size="sm" variant="outline" disabled={busy||!at} onClick={()=>publish(new Date(at).getTime()/1000)} data-testid={id+'-schedule'}><CalendarClock size={15}/>Schedule</Button></div>}
    <small>Students see it in its section from then on. You can switch it off or move it to the Library later.</small></>}
  </PopoverContent>
 </Popover>;
}
