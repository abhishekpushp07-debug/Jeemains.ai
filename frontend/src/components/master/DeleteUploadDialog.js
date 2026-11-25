import React,{useEffect,useState} from 'react';
import {Loader2,Trash2} from 'lucide-react';
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription,DialogFooter} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {api,post} from '../../lib/api';
import {toast} from 'sonner';

const WHERE={supabase:'Original PDF Supabase se hategi.',emergent:'Original PDF Emergent mein hai: uska record hatega, file wahan rahegi (Emergent mein hatana hota hi nahi).',server:'Server par pade PDF ke hisse hatenge.'};

// Deletes for good an upload that never reached students. First what leaves, then what stays; nothing happens before DELETE is typed.
export function DeleteUploadDialog({target,onClose,onDone}){
 const [f,setF]=useState(null),[error,setError]=useState(''),[text,setText]=useState(''),[busy,setBusy]=useState(false);
 // An answer that arrives after another upload was picked is dropped: the box only ever counts the upload it names.
 useEffect(()=>{setF(null);setError('');setText('');if(!target)return;let live=true;api(`/admin/master/uploads/book/${target.id}/delete`).then(d=>{if(live)setF(d);}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[target]);
 async function run(){setBusy(true);try{const r=await post(`/admin/master/uploads/book/${target.id}/delete`,{confirm:'DELETE'});toast.success(r.message);onClose();onDone?.();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 const sure=text.trim()==='DELETE',blocked=error||(f&&!f.allowed?f.reason:'');
 return <Dialog open={!!target} onOpenChange={o=>{if(!o&&!busy)onClose();}}>
  <DialogContent className="library-delete-dialog upload-delete-dialog" data-testid="upload-delete-dialog">
   <DialogHeader><DialogTitle>Yeh upload hamesha ke liye delete karein?</DialogTitle><DialogDescription data-testid="upload-delete-title">{target?.title}</DialogDescription></DialogHeader>
   {!f&&!error&&<p className="admin-note" data-testid="upload-delete-loading"><Loader2 size={14} className="spin"/> Gin raha hai ki kya-kya hatega…</p>}
   {blocked&&<p className="admin-note error" role="alert" data-testid="upload-delete-blocked">{blocked}</p>}
   {f?.allowed&&<>
    <strong className="upload-delete-head">Kya hatega</strong>
    <ul className="library-restore-facts" data-testid="upload-delete-facts">
     <li className="is-danger">Yeh wapas nahi aa sakta.</li>
     <li data-testid="upload-delete-mocks">{f.mocks} Draft mock{f.fixed>0?` · inmein se ${f.fixed} mein aapke fix hain, woh bhi hatenge`:''}{f.in_library>0?` · ${f.in_library} Library mein hain`:''}</li>
     <li data-testid="upload-delete-pages">{f.pages} page ki padhai aur page ke nishaan</li>
     <li data-testid="upload-delete-original">{WHERE[f.original]}</li>
     {f.pictures.supabase>0&&<li data-testid="upload-delete-pictures">{f.pictures.supabase} pictures Supabase se</li>}
     {f.pictures.emergent>0&&<li data-testid="upload-delete-emergent">{f.pictures.emergent} pictures Emergent mein hain: unka record hatega, file wahan rahegi.</li>}
     <li>“Try as student” ki private copy aur is upload ke ruke hue kaam</li>
     {f.days>0&&<li data-testid="upload-delete-days">{f.days} din khali ho jayenge (jo is upload ke Draft ko diye the).</li>}
    </ul>
    <strong className="upload-delete-head">Kya nahi hatega</strong>
    <ul className="library-restore-facts" data-testid="upload-delete-kept">
     <li>Koi doosra upload, koi bana hua test, kisi student ka score, JEE Main PYQ.</li>
     {f.replaces&&<li>Jis purane mock ko yeh replace karne wala tha, woh jaisa hai waisa rahega.</li>}
     <li>Wahi PDF aap turant dobara upload kar sakte hain; woh naye sire se padhi jayegi.</li>
    </ul>
    <label className="upload-delete-type" htmlFor="upload-delete-input">Pakka karne ke liye DELETE likhiye
     <Input id="upload-delete-input" value={text} onChange={e=>setText(e.target.value)} autoComplete="off" autoCapitalize="characters" disabled={busy} placeholder="DELETE" data-testid="upload-delete-input"/></label>
   </>}
   <DialogFooter><Button variant="outline" onClick={onClose} disabled={busy} data-testid="upload-delete-cancel">{f?.allowed?'Cancel':'Band karo'}</Button>
    {f?.allowed&&<Button variant="destructive" onClick={run} disabled={busy||!sure} data-testid="upload-delete-confirm">{busy?<Loader2 size={16} className="spin"/>:<Trash2 size={16}/>}Hamesha ke liye delete karo</Button>}</DialogFooter>
  </DialogContent>
 </Dialog>;
}
