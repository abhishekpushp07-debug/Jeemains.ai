import React,{useRef,useState} from 'react';
import {UploadCloud,Pause} from 'lucide-react';
import {Button} from '../ui/button';
import {post,fetchWithSession} from '../../lib/api';
import {BookField,BookError} from './BookShared';

export function BookUpload({onOpen}){
 const [file,setFile]=useState(null),[title,setTitle]=useState(''),[edition,setEdition]=useState(''),[rights,setRights]=useState(false),[auto,setAuto]=useState(true),[schedule,setSchedule]=useState(''),[competitive,setCompetitive]=useState(false),[closes,setCloses]=useState('');
 const [busy,setBusy]=useState(false),[sent,setSent]=useState(0),[message,setMessage]=useState(''),[error,setError]=useState('');const stopped=useRef(false);
 async function upload(e){e.preventDefault();setError('');if(!file||!rights)return;stopped.current=false;setBusy(true);setSent(0);
  try{if(file.size>100*1024*1024)throw new Error('Choose a PDF within 100 MB.');setMessage('Checking file identity…');
   const bytes=await file.arrayBuffer();const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
   const book=await post('/admin/books',{filename:file.name,title:title.trim()||file.name.replace(/\.pdf$/i,''),edition,sha256:hash,size:file.size,rights_confirmed:true,auto_publish:auto,release_at:schedule?new Date(schedule).getTime()/1000:null,competitive,closes_at:closes?new Date(closes).getTime()/1000:null});
   if(book.state!=='uploading'){onOpen(book.id);return;}
   const existing=new Set(book.received_parts);let done=book.received_parts.reduce((n,i)=>n+Math.min(book.chunk_size,file.size-i*book.chunk_size),0);setSent(done);
   for(let i=0;i<Math.ceil(file.size/book.chunk_size);i++){if(stopped.current){setMessage('Transfer paused. Reselect this same PDF and Upload Book to resume completed parts.');return;}if(existing.has(i))continue;
    setMessage(`Transferring part ${i+1} of ${Math.ceil(file.size/book.chunk_size)}…`);
    const chunk=file.slice(i*book.chunk_size,(i+1)*book.chunk_size);
    const partHash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await chunk.arrayBuffer())),v=>v.toString(16).padStart(2,'0')).join('');
    let r=null,tries=0;
    for(;;){tries+=1;
     try{r=await fetchWithSession(`/admin/books/${book.id}/parts/${i}?sha256=${partHash}`,{method:'PUT',headers:{'Content-Type':'application/octet-stream'},body:chunk});}catch{r=null;}
     if(r&&(r.ok||(r.status<500&&r.status!==408&&r.status!==429)))break;
     if(tries>=4||stopped.current)break;
     setMessage(`Connection problem on part ${i+1}. Retrying (${tries} of 3)…`);await new Promise(done=>setTimeout(done,1500*tries));
    }
    if((!r||!r.ok)&&stopped.current){setMessage('Transfer paused. Reselect this same PDF and Upload Book to resume completed parts.');return;}
    if(!r||!r.ok){const d=r?await r.json().catch(()=>({})):{};throw new Error(d.error?.message||d.detail||'Transfer interrupted. Retry the same file; completed parts are saved.');}
    done+=Math.min(book.chunk_size,file.size-i*book.chunk_size);setSent(done);
   }
   await post(`/admin/books/${book.id}/complete`);onOpen(book.id);
  }catch(e){setError(e.message);}finally{setBusy(false);}
 }
 return <form className="book-upload" onSubmit={upload} data-testid="book-upload-form"><div className="book-upload-heading"><UploadCloud size={28}/><div><h2>One book. Separate mocks.</h2><p>Up to 100 MB per PDF · no page or mock limit. Uncertain content stays private.</p></div></div>
  <BookField label="Combined PDF book" id="book-file" type="file" accept="application/pdf,.pdf" disabled={busy} required onChange={e=>{const f=e.target.files[0];setFile(f||null);if(f)setTitle(f.name.replace(/\.pdf$/i,''));}}/>
  <div className="book-form-grid"><BookField label="Series title" id="book-title" value={title} maxLength={160} required disabled={busy} onChange={e=>setTitle(e.target.value)}/><BookField label="Edition label (optional)" id="book-edition" value={edition} maxLength={80} disabled={busy} onChange={e=>setEdition(e.target.value)} /></div>
  <p className="book-note" data-testid="book-duplicate-notice">Identical PDF + edition opens the existing upload. Change the edition only for a deliberate separate import.</p>
  <label className="book-check"><input type="checkbox" data-testid="book-rights" checked={rights} disabled={busy} onChange={e=>setRights(e.target.checked)}/><span>I have permission to upload and share these questions, explanations and student reports.</span></label>
  <label className="book-check"><input type="checkbox" data-testid="book-auto-publish" checked={auto} disabled={busy} onChange={e=>setAuto(e.target.checked)}/><span>Automatically publish complete mocks after source checks pass</span></label>
  <details data-testid="book-schedule-options"><summary data-testid="book-schedule-toggle">Optional release schedule</summary><BookField label="Release at (your local time); empty means immediate" id="book-schedule" type="datetime-local" value={schedule} disabled={busy} onChange={e=>setSchedule(e.target.value)}/><label className="book-check"><input type="checkbox" data-testid="book-competitive" checked={competitive} disabled={busy} onChange={e=>setCompetitive(e.target.checked)}/><span>Competitive window: solutions stay locked until closing</span></label>{competitive&&<BookField label="Window closes (your local time)" id="book-closes" type="datetime-local" value={closes} required disabled={busy} onChange={e=>setCloses(e.target.value)}/>}</details>
  <p className="book-note" data-testid="book-no-automatic-ai">Upload never authorises paid AI reading or explanation generation. Each requires a separate allowance.</p>
  <BookError error={error}/>{message&&<p role="status" data-testid="book-transfer-message">{message}</p>}{file&&(busy||sent>0)&&<div data-testid="book-transfer-progress"><progress value={sent} max={file.size}/><span>{(sent/1024/1024).toFixed(1)} / {(file.size/1024/1024).toFixed(1)} MB received</span></div>}
  <div className="book-actions"><Button type="submit" disabled={busy||!file||!rights} data-testid="upload-book"><UploadCloud size={16}/>{busy?'Transferring…':'Upload Book'}</Button>{busy&&<Button type="button" variant="outline" data-testid="pause-book-transfer" onClick={()=>{stopped.current=true;}}><Pause size={16}/>Pause transfer</Button>}</div>
 </form>;
}
