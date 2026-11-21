import React,{useEffect,useRef,useState} from 'react';
import {UploadCloud,Loader2,FileText,X} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Field,plural} from './MasterShared';
import {mergePdfs,sendBook} from './uploadBook';
import {StorageNotice} from './StorageBadge';
import {BatchRows,newRows,runBatch} from './BatchUpload';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {toast} from 'sonner';

function PdfBox({label,hint,file,onPick,disabled,testId,required,multiple}){
 return <div className={'master-pdf-box'+(file?' has-file':'')} data-testid={testId}>
  <label htmlFor={testId+'-input'}><FileText size={20} aria-hidden="true"/><span><strong>{label}{required?'':' (optional)'}</strong><small>{file?`${file.name} · ${(file.size/1024/1024).toFixed(1)} MB`:hint}</small></span></label>
  <input id={testId+'-input'} type="file" accept="application/pdf,.pdf" multiple={multiple} disabled={disabled} onChange={e=>{const list=[...e.target.files];e.target.value='';onPick(multiple?list:list[0]||null);}} data-testid={testId+'-input'}/>
  {file&&!disabled&&<Button type="button" size="icon" variant="ghost" aria-label={'Remove '+label} onClick={()=>onPick(multiple?[]:null)} data-testid={testId+'-remove'}><X size={15}/></Button>}
 </div>;
}

export function UploadDialog({open,onClose,section,exam,replace,onStarted}){
 const [main,setMain]=useState(null),[key,setKey]=useState(null),[sols,setSols]=useState(null),[title,setTitle]=useState(''),[year,setYear]=useState(''),[rights,setRights]=useState(false),[subject,setSubject]=useState('');
 const [busy,setBusy]=useState(false),[msg,setMsg]=useState(''),[progress,setProgress]=useState(0),[batch,setBatch]=useState([]);const stopped=useRef(false);
 useEffect(()=>{if(open){setMain(null);setKey(null);setSols(null);setTitle('');setYear('');setRights(false);setSubject('');setMsg('');setProgress(0);setBatch([]);}},[open]);
 const chapters=section.layout==='chapters',pyq=section.kind==='pyq',many=batch.length>0;
 const count=replace==='all'?'every mock':replace?plural(replace.split(',').length,'mock'):'';
 function pickMain(list){
  const files=Array.isArray(list)?list:list?[list]:[];
  if(files.length>1){setMain(null);setBatch(newRows(files));return;}
  setBatch([]);setMain(files[0]||null);if(files[0]&&!title)setTitle(files[0].name.replace(/\.pdf$/i,''));
 }
 async function sendMany(){
  toast.dismiss('batch-paused');
  const r=await runBatch(batch,setBatch,{sectionId:section.id,subject:chapters?subject:'',pyq,stopped});
  if(r.failed||r.ok<batch.length){const n=batch.length,s=n===1?'':'s';if((r.paused||stopped.current)&&!r.failed)toast.info(`Paused: ${r.ok} of ${n} PDF${s} sent. Press Upload to send the rest.`,{id:'batch-paused'});else toast.error(`${r.ok} of ${n} PDF${s} sent. Press Upload again to send the rest.`);onStarted();return;}
  toast.success(`${r.ok} PDF${r.ok===1?'':'s'} uploaded. Each is read in the background, one after another.`);onStarted();onClose();
 }
 async function send(){setBusy(true);stopped.current=false;try{
  if(many){await sendMany();return;}
  const name=(title.trim()||main.name.replace(/\.pdf$/i,'')).slice(0,160);
  if(key||sols)setMsg('Joining your PDFs…');
  const file=await mergePdfs([main,key,sols].filter(Boolean),main.name);
  await sendBook({file,title:name,sectionId:section.id,replace,year:pyq?Number(year):null,subject:chapters?subject:'',stopped,onProgress:(m,p)=>{setMsg(m);setProgress(p);}});
  toast.success('Uploaded. Reading happens in the background; you can close this screen.');onStarted();onClose();
 }catch(e){toast.error(e.message);setMsg(e.message);}finally{setBusy(false);}}
 const ok=rights&&(many?(!pyq||batch.every(r=>r.state==='done'||/^\d{4}$/.test(r.year))):main&&(!pyq||/^\d{4}$/.test(year)));
 return <Dialog open={open} onOpenChange={v=>!v&&!busy&&onClose()}><DialogContent className="tejas-dialog admin-dialog master-dialog" data-testid="upload-dialog">
  <DialogTitle>Upload PDF to {section.name}</DialogTitle>
  <DialogDescription>{chapters?'Each chapter in the PDF becomes its own test, whatever its layout. If the chapter starts cannot be found, you mark them on the pages.':'The PDF can hold one mock or many; each printed mock becomes its own test.'} Every mock arrives as a Draft. No AI is used.</DialogDescription>
  {count&&<p className="admin-note warn" data-testid="upload-replace-note">Replacing {count}. The old ones stay Live until the new ones go Live, then move to your Library. Students keep their scores.</p>}
  {open&&<StorageNotice/>}
  <form className="admin-form" onSubmit={e=>{e.preventDefault();if(ok&&!busy)send();}}>
   <PdfBox label={many?`${batch.length} PDF${batch.length===1?'':'s'} chosen`:'Main PDF'} hint={replace?'Questions. If the answer key and solutions are inside it too, that is all you need. Up to 100 MB.':'Questions, up to 100 MB each. Choose several PDFs at once to send them one after another.'}
    file={main} onPick={pickMain} disabled={busy} testId="upload-main" required multiple={!replace}/>
   {many?<><BatchRows rows={batch} setRows={setBatch} pyq={pyq} busy={busy}/>{!busy&&<Button type="button" variant="ghost" size="sm" onClick={()=>setBatch([])} data-testid="upload-batch-clear">Clear all</Button>}</>:<>
    <div className="master-field-row">
     <PdfBox label="Answer key PDF" hint="Only if the key is a separate file." file={key} onPick={setKey} disabled={busy} testId="upload-key"/>
     <PdfBox label="Solutions PDF" hint="Only if solutions are a separate file." file={sols} onPick={setSols} disabled={busy} testId="upload-solutions"/>
    </div>
    <Field label="Name for your uploads list (private)" id="upload-title"><Input id="upload-title" value={title} maxLength={160} disabled={busy} onChange={e=>setTitle(e.target.value)} data-testid="upload-title"/></Field>
   </>}
   {many&&<p className="master-hint" data-testid="upload-batch-note">Each PDF must hold its own answer key. Names come from the file names{pyq?'; check the year of every paper':''}.</p>}
   {chapters&&<Field label="Subject of the chapters" id="upload-subject"><Select value={subject||'pdf'} onValueChange={v=>setSubject(v==='pdf'?'':v)} disabled={busy}><SelectTrigger id="upload-subject" data-testid="upload-subject"><SelectValue/></SelectTrigger><SelectContent>
    <SelectItem value="pdf" data-testid="upload-subject-pdf">Read it from the PDF (ask me if unclear)</SelectItem>
    {(exam?.subjects||[]).map(s=><SelectItem key={s} value={s} data-testid={'upload-subject-'+s.toLowerCase()}>All chapters are {s}</SelectItem>)}
   </SelectContent></Select></Field>}
   {pyq&&!many&&<Field label="Year of the paper" id="upload-year"><Input id="upload-year" inputMode="numeric" maxLength={4} value={year} disabled={busy} onChange={e=>setYear(e.target.value.replace(/\D/g,''))} placeholder="e.g. 2025" data-testid="upload-year"/></Field>}
   <label className="book-check"><input type="checkbox" checked={rights} disabled={busy} onChange={e=>setRights(e.target.checked)} data-testid="upload-rights"/><span>I have permission to show this content to students.</span></label>
   <p className="master-hint">A mock without an answer key cannot go Live. Solutions are optional: without them students see the answer key.</p>
   {msg&&!many&&<div className="admin-progress" role="status" data-testid="upload-progress"><progress value={progress} max={1}/><small>{msg}</small></div>}
   <div className="button-row">{busy?<Button type="button" variant="outline" onClick={()=>{stopped.current=true;}} data-testid="upload-pause">Pause</Button>:<Button type="button" variant="outline" onClick={onClose} disabled={busy} data-testid="upload-cancel">Cancel</Button>}<Button type="submit" disabled={!ok||busy} data-testid="upload-send">{busy?<Loader2 size={16} className="spin"/>:<UploadCloud size={16}/>}{many?(n=>`Upload ${n} PDF${n===1?'':'s'}`)(batch.filter(r=>r.state!=='done').length):'Upload'}</Button></div>
  </form>
 </DialogContent></Dialog>;
}
