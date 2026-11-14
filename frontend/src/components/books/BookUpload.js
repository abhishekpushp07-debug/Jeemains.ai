import React,{useRef,useState} from 'react';
import {UploadCloud,Pause} from 'lucide-react';
import {Button} from '../ui/button';
import {post,fetchWithSession} from '../../lib/api';
import {BookField,BookError} from './BookShared';

const sha=async data=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),v=>v.toString(16).padStart(2,'0')).join('');

export function BookUpload({sectionId,onOpen}){
 const [file,setFile]=useState(null),[title,setTitle]=useState(''),[rights,setRights]=useState(false);
 const [busy,setBusy]=useState(false),[sent,setSent]=useState(0),[message,setMessage]=useState(''),[error,setError]=useState('');const stopped=useRef(false);
 async function upload(e){e.preventDefault();setError('');if(!file||!rights)return;stopped.current=false;setBusy(true);setSent(0);
  try{if(file.size>100*1024*1024)throw new Error('Choose a PDF within 100 MB.');setMessage('Checking file identity…');
   const hash=await sha(await file.arrayBuffer());
   const book=await post('/admin/books',{filename:file.name,title:title.trim()||file.name.replace(/\.pdf$/i,''),sha256:hash,size:file.size,rights_confirmed:true,section_id:sectionId});
   if(book.state!=='uploading'){onOpen(book.id);return;}
   const existing=new Set(book.received_parts);let done=book.received_parts.reduce((n,i)=>n+Math.min(book.chunk_size,file.size-i*book.chunk_size),0);setSent(done);
   for(let i=0;i<Math.ceil(file.size/book.chunk_size);i++){if(stopped.current){setMessage('Transfer paused. Choose this same PDF again and press Upload to resume completed parts.');return;}if(existing.has(i))continue;
    setMessage(`Transferring part ${i+1} of ${Math.ceil(file.size/book.chunk_size)}…`);
    const chunk=file.slice(i*book.chunk_size,(i+1)*book.chunk_size);
    const partHash=await sha(await chunk.arrayBuffer());
    let r=null,tries=0;
    for(;;){tries+=1;
     try{r=await fetchWithSession(`/admin/books/${book.id}/parts/${i}?sha256=${partHash}`,{method:'PUT',headers:{'Content-Type':'application/octet-stream'},body:chunk});}catch{r=null;}
     if(r&&(r.ok||(r.status<500&&r.status!==408&&r.status!==429)))break;
     if(tries>=4||stopped.current)break;
     setMessage(`Connection problem on part ${i+1}. Retrying (${tries} of 3)…`);await new Promise(done=>setTimeout(done,1500*tries));
    }
    if((!r||!r.ok)&&stopped.current){setMessage('Transfer paused. Choose this same PDF again and press Upload to resume completed parts.');return;}
    if(!r||!r.ok){const d=r?await r.json().catch(()=>({})):{};throw new Error(d.error?.message||d.detail||'Transfer interrupted. Retry the same file; completed parts are saved.');}
    done+=Math.min(book.chunk_size,file.size-i*book.chunk_size);setSent(done);
   }
   await post(`/admin/books/${book.id}/complete`);onOpen(book.id);
  }catch(e){setError(e.message);}finally{setBusy(false);}
 }
 return <form className="book-upload" onSubmit={upload} data-testid="book-upload-form"><div className="book-upload-heading"><UploadCloud size={28}/><div><h2>One book. Separate mocks.</h2><p>Up to 100 MB per PDF · no page or mock limit. Uncertain content stays private.</p></div></div>
  <BookField label="Combined PDF book" id="book-file" type="file" accept="application/pdf,.pdf" disabled={busy} required onChange={e=>{const f=e.target.files[0];setFile(f||null);if(f)setTitle(f.name.replace(/\.pdf$/i,''));}}/>
  <BookField label="Book title (private, for your uploads list)" id="book-title" value={title} maxLength={160} required disabled={busy} onChange={e=>setTitle(e.target.value)}/>
  <p className="book-note" data-testid="book-duplicate-notice">Uploading the same PDF again opens its existing upload. Students see each mock by its printed name, not the book title.</p>
  <label className="book-check"><input type="checkbox" data-testid="book-rights" checked={rights} disabled={busy} onChange={e=>setRights(e.target.checked)}/><span>I have permission to upload and share these questions, explanations and student reports.</span></label>
  <p className="book-note" data-testid="book-no-automatic-ai">Nothing goes live on its own: you publish ready mocks after reading. Upload never authorises paid AI reading or explanations.</p>
  <BookError error={error}/>{message&&<p role="status" data-testid="book-transfer-message">{message}</p>}{file&&(busy||sent>0)&&<div data-testid="book-transfer-progress"><progress value={sent} max={file.size}/><span>{(sent/1024/1024).toFixed(1)} / {(file.size/1024/1024).toFixed(1)} MB received</span></div>}
  <div className="book-actions"><Button type="submit" disabled={busy||!file||!rights} data-testid="upload-book"><UploadCloud size={16}/>{busy?'Transferring…':'Upload'}</Button>{busy&&<Button type="button" variant="outline" data-testid="pause-book-transfer" onClick={()=>{stopped.current=true;}}><Pause size={16}/>Pause transfer</Button>}</div>
 </form>;
}
