import {PDFDocument} from 'pdf-lib';
import {api,post,fetchWithSession} from '../../lib/api';

const sha=async data=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),v=>v.toString(16).padStart(2,'0')).join('');
const LIMIT=100*1024*1024;
const TRIES=8;
const LANES=4;
const wait=ms=>new Promise(done=>setTimeout(done,ms));

// One part, with a time limit so a part lost on the way is sent again instead of waiting for ever.
async function putPart(path,chunk){
 const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),90000);
 try{return await fetchWithSession(path,{method:'PUT',headers:{'Content-Type':'application/octet-stream'},body:chunk,signal:ctl.signal});}
 catch{return null;}
 finally{clearTimeout(timer);}
}

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

export async function sendBook({file,title,sectionId,replace,year,subject,onProgress,stopped}){
 if(file.size>LIMIT)throw new Error('PDF 100 MB tak ki chuniye. Isse badi file server nahi lega.');
 onProgress('File check ho rahi hai…',0);
 const book=await post('/admin/books',{filename:file.name,title,sha256:await sha(await file.arrayBuffer()),size:file.size,rights_confirmed:true,section_id:sectionId,
  ...(year?{year}:{}),...(subject?{subject}:{}),...(replace==='all'?{replace_all:true}:replace?{replace_ids:replace.split(',')}:{})});
 if(book.state!=='uploading'){onProgress((book.message||'').startsWith('Same PDF chosen again')?'Wahi PDF dobara: save hue pages se aage chal rahe hain.':'Yeh PDF pehle se yahan hai. Uski progress khul rahi hai.',1);return book.id;}
 const total=Math.ceil(file.size/book.chunk_size),have=new Set(book.received_parts),size=i=>Math.min(book.chunk_size,file.size-i*book.chunk_size);
 const todo=[];let sent=0,done=have.size,failure=null;
 for(let i=0;i<total;i++){if(have.has(i))sent+=size(i);else todo.push(i);}
 const paused=()=>new Error('Ruka. Jahan ruka tha wahan se chalane ke liye wahi PDF dobara chuniye.');
 // Up to LANES parts travel at once (the server keeps each part on its own), so a long distance to the server costs far less time.
 async function sendOne(i){
  const chunk=file.slice(i*book.chunk_size,(i+1)*book.chunk_size),hash=await sha(await chunk.arrayBuffer());
  let r=null;
  for(let tries=1;tries<=TRIES;tries++){
   while(navigator.onLine===false&&!stopped?.current){onProgress(`Internet band hai. Wapas aane ka intezaar (${total} mein se ${done} hisse gaye)…`,sent/file.size);await wait(1500);}
   if(stopped?.current||failure)throw failure||paused();
   r=await putPart(`/admin/books/${book.id}/parts/${i}?sha256=${hash}`,chunk);
   if(r&&(r.ok||(r.status<500&&r.status!==408&&r.status!==429)))break;
   if(tries===TRIES)break;
   const delay=Math.min(30000,2000*2**(tries-1));
   onProgress(`${total} mein se hissa ${i+1} par connection toota. ${Math.round(delay/1000)} s mein phir koshish (${TRIES-1} mein se ${tries})…`,sent/file.size);
   await wait(delay);
  }
  if(!r||!r.ok){const d=r?await r.json().catch(()=>({})):{};throw new Error(d.error?.message||d.detail||`${total} mein se hisse ${i+1} par bhejna ruk gaya. Wahi PDF ke saath Upload phir dabaiye: jo ${done} hisse ja chuke hain woh rakhe gaye hain.`);}
  sent+=size(i);done+=1;onProgress(`Bhej rahe hain… ${total} mein se ${done} hisse`,sent/file.size);
 }
 async function lane(){
  while(todo.length&&!failure){
   if(stopped?.current){failure=failure||paused();break;}
   const i=todo.shift();
   try{await sendOne(i);}catch(e){failure=failure||e;}
  }
 }
 onProgress(`Bhej rahe hain… ${total} mein se ${done} hisse`,sent/file.size);
 await Promise.all(Array.from({length:Math.min(LANES,todo.length)},lane));
 if(failure)throw failure;
 onProgress('Chali gayi. Ab padhai shuru.',1);
 await post(`/admin/books/${book.id}/complete`);
 return book.id;
}

export async function sendChapterBook({file,sectionId,replace}){
 const form=new FormData();
 form.append('request_id',crypto.randomUUID());form.append('section_id',sectionId);form.append('file',file);
 if(replace)form.append('replace',replace);
 return api('/studio/chapter-books',{method:'POST',body:form});
}
