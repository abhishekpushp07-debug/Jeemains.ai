import React,{useEffect,useState} from 'react';
import {Smartphone,Copy,Share2,ExternalLink,Link2Off,RefreshCw} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {toast} from 'sonner';

export const previewWhen=s=>new Date(s*1000).toLocaleString(undefined,{day:'numeric',month:'short',hour:'numeric',minute:'2-digit'});

function LinkBox({url,title}){
 async function copy(){try{await navigator.clipboard.writeText(url);toast.success('Link copied. Send it to your phone.');}catch{toast.error('Copy did not work. Select the link and copy it.');}}
 return <div className="admin-preview-link" data-testid="preview-link-box">
  <Input readOnly value={url} onFocus={e=>e.target.select()} aria-label="Preview link" data-testid="preview-link-url"/>
  <div className="admin-actions">
   <Button onClick={copy} data-testid="preview-link-copy"><Copy size={16}/>Copy link</Button>
   {navigator.share&&<Button variant="outline" onClick={()=>navigator.share({title,url}).catch(()=>{})} data-testid="preview-link-share"><Share2 size={16}/>Share</Button>}
   <Button asChild variant="ghost"><a href={url} target="_blank" rel="noreferrer" data-testid="preview-link-open"><ExternalLink size={16}/>Open</a></Button>
  </div>
 </div>;
}

export function PreviewLink({section,exam}){
 const [open,setOpen]=useState(false),[status,setStatus]=useState(null),[url,setUrl]=useState(''),[busy,setBusy]=useState(false);
 const path=`/admin/catalog/sections/${section.id}/preview-link`;
 useEffect(()=>{setUrl('');},[section.id]);
 useEffect(()=>{if(!open){return;}setStatus(null);api(path).then(setStatus).catch(e=>toast.error(e.message));},[open,path]);
 async function run(fn){setBusy(true);try{await fn();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 const make=()=>run(async()=>{const r=await post(path);setUrl(`${window.location.origin}/preview/s/${r.token}`);setStatus({active:true,expires_at:r.expires_at});toast.success('Preview link ready. Open it on your phone.');});
 const stop=()=>run(async()=>{await api(path,{method:'DELETE'});setUrl('');setStatus({active:false});toast.success('Preview link turned off. It no longer opens.');});
 return <>
  <Button variant="outline" onClick={()=>setOpen(true)} data-testid="admin-section-preview-link"><Smartphone size={16}/>Phone preview link</Button>
  <Dialog open={open} onOpenChange={setOpen}>
   <DialogContent className="admin-dialog" data-testid="preview-link-dialog">
    <DialogTitle>Phone preview link</DialogTitle>
    <DialogDescription>See {exam.name} › {section.name} the way students will, including tests that are not live yet. Anyone with the link sees only test names, order and status. They cannot open or attempt a test. The link works for 7 days.</DialogDescription>
    {!status?<p className="admin-note" data-testid="preview-link-loading">Checking this section's link…</p>:url?<LinkBox url={url} title={`${exam.name} › ${section.name} preview`}/>:
     <p className="admin-note" data-testid="preview-link-status">{status.active?`A link is on until ${previewWhen(status.expires_at)}. For safety it is shown only once. Make a new link to copy it again; the old link then stops working.`:'No preview link is on for this section.'}</p>}
    {status?.active&&url&&<p className="admin-note" data-testid="preview-link-expiry">Works until {previewWhen(status.expires_at)}.</p>}
    <div className="admin-actions">
     <Button disabled={busy||!status} onClick={make} variant={url?'outline':'default'} data-testid="preview-link-create">{status?.active?<><RefreshCw size={16}/>Make a new link</>:<><Smartphone size={16}/>Create link</>}</Button>
     {status?.active&&<Button variant="ghost" disabled={busy} onClick={stop} data-testid="preview-link-revoke"><Link2Off size={16}/>Turn off link</Button>}
    </div>
   </DialogContent>
  </Dialog>
 </>;
}
