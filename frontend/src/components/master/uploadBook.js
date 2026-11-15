import {PDFDocument} from 'pdf-lib';
import {api,post,fetchWithSession} from '../../lib/api';

const sha=async data=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),v=>v.toString(16).padStart(2,'0')).join('');
const LIMIT=100*1024*1024;

// Answer key and solutions PDFs are appended after the questions, so the reader sees one book.
export async function mergePdfs(files,name){
 if(files.length===1)return files[0];
 const out=await PDFDocument.create();
 for(const f of files){
  const doc=await PDFDocument.load(await f.arrayBuffer(),{ignoreEncryption:true});
  (await out.copyPages(doc,doc.getPageIndices())).forEach(p=>out.addPage(p));
 }
 const merged=new File([await out.save()],name,{type:'application/pdf'});
 if(merged.size>LIMIT)throw new Error('Together these PDFs are over 100 MB. Upload a smaller set.');
 return merged;
}

export async function sendBook({file,title,sectionId,replace,year,onProgress,stopped}){
 if(file.size>LIMIT)throw new Error('Choose a PDF within 100 MB.');
 onProgress('Checking the file…',0);
 const book=await post('/admin/books',{filename:file.name,title,sha256:await sha(await file.arrayBuffer()),size:file.size,rights_confirmed:true,section_id:sectionId,
  ...(year?{year}:{}),...(replace==='all'?{replace_all:true}:replace?{replace_ids:replace.split(',')}:{})});
 if(book.state!=='uploading')return book.id;
 const have=new Set(book.received_parts),total=Math.ceil(file.size/book.chunk_size);let sent=0;
 for(let i=0;i<total;i++){
  if(stopped?.current)throw new Error('Paused. Choose the same PDF again to continue from where it stopped.');
  const size=Math.min(book.chunk_size,file.size-i*book.chunk_size);
  if(have.has(i)){sent+=size;continue;}
  onProgress(`Sending part ${i+1} of ${total}…`,sent/file.size);
  const chunk=file.slice(i*book.chunk_size,(i+1)*book.chunk_size),hash=await sha(await chunk.arrayBuffer());
  let r=null;
  for(let tries=1;tries<=4;tries++){
   try{r=await fetchWithSession(`/admin/books/${book.id}/parts/${i}?sha256=${hash}`,{method:'PUT',headers:{'Content-Type':'application/octet-stream'},body:chunk});}catch{r=null;}
   if(r&&(r.ok||(r.status<500&&r.status!==408&&r.status!==429)))break;
   onProgress(`Connection problem on part ${i+1}. Retrying (${tries} of 3)…`,sent/file.size);
   await new Promise(done=>setTimeout(done,1500*tries));
  }
  if(!r||!r.ok){const d=r?await r.json().catch(()=>({})):{};throw new Error(d.error?.message||d.detail||'Sending stopped. Choose the same PDF again; parts already sent are kept.');}
  sent+=size;
 }
 onProgress('Sent. Reading starts now.',1);
 await post(`/admin/books/${book.id}/complete`);
 return book.id;
}

export async function sendChapterBook({file,sectionId,replace}){
 const form=new FormData();
 form.append('request_id',crypto.randomUUID());form.append('section_id',sectionId);form.append('file',file);
 if(replace)form.append('replace',replace);
 return api('/studio/chapter-books',{method:'POST',body:form});
}
