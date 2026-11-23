import React,{useEffect,useRef,useState} from 'react';
import {UploadCloud,Loader2,FileText,FolderOpen,X} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Field} from './MasterShared';
import {mergePdfs,sendBook} from './uploadBook';
import {StorageNotice} from './StorageBadge';
import {BatchRows,newRows,runBatch} from './BatchUpload';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {toast} from 'sonner';

// A plain "PDF chuniye" button opens the phone's or computer's file picker; tapping the text does the same.
function PdfBox({label,hint,file,onPick,disabled,testId,required,multiple}){
 const input=useRef(null);
 return <div className={'master-pdf-box'+(file?' has-file':'')} data-testid={testId}>
  <label htmlFor={testId+'-input'}><FileText size={20} aria-hidden="true"/><span><strong>{label}{required?'':' (zaroori nahi)'}</strong><small>{file?`${file.name} · ${(file.size/1024/1024).toFixed(1)} MB`:hint}</small></span></label>
  <input ref={input} id={testId+'-input'} className="master-pdf-input" type="file" accept="application/pdf,.pdf" multiple={multiple} disabled={disabled} onChange={e=>{const list=[...e.target.files];e.target.value='';onPick(multiple?list:list[0]||null);}} data-testid={testId+'-input'}/>
  <Button type="button" size="sm" variant={file?'outline':'default'} disabled={disabled} onClick={()=>input.current?.click()} data-testid={testId+'-pick'}><FolderOpen size={15}/>{file?'Badlo':'PDF chuniye'}</Button>
  {file&&!disabled&&<Button type="button" size="icon" variant="ghost" aria-label={label+' hatao'} onClick={()=>onPick(multiple?[]:null)} data-testid={testId+'-remove'}><X size={15}/></Button>}
 </div>;
}

export function UploadDialog({open,onClose,section,exam,replace,onStarted}){
 const [main,setMain]=useState(null),[key,setKey]=useState(null),[sols,setSols]=useState(null),[title,setTitle]=useState(''),[year,setYear]=useState(''),[rights,setRights]=useState(false),[subject,setSubject]=useState('');
 const [busy,setBusy]=useState(false),[msg,setMsg]=useState(''),[progress,setProgress]=useState(0),[batch,setBatch]=useState([]);const stopped=useRef(false);
 useEffect(()=>{if(open){setMain(null);setKey(null);setSols(null);setTitle('');setYear('');setRights(false);setSubject('');setMsg('');setProgress(0);setBatch([]);}},[open]);
 const chapters=section.layout==='chapters',pyq=section.kind==='pyq',many=batch.length>0;
 const count=replace==='all'?'har mock':replace?`${replace.split(',').length} mock`:'';
 function pickMain(list){
  const files=Array.isArray(list)?list:list?[list]:[];
  if(files.length>1){setMain(null);setBatch(newRows(files));return;}
  setBatch([]);setMain(files[0]||null);if(files[0]&&!title)setTitle(files[0].name.replace(/\.pdf$/i,''));
 }
 async function sendMany(){
  toast.dismiss('batch-paused');
  const r=await runBatch(batch,setBatch,{sectionId:section.id,subject:chapters?subject:'',pyq,stopped});
  if(r.failed||r.ok<batch.length){const n=batch.length;if((r.paused||stopped.current)&&!r.failed)toast.info(`Ruka: ${n} mein se ${r.ok} PDF gayi. Baaki bhejne ke liye Upload dabaiye.`,{id:'batch-paused'});else toast.error(`${n} mein se ${r.ok} PDF gayi. Baaki bhejne ke liye Upload phir dabaiye.`);onStarted();return;}
  toast.success(`${r.ok} PDF upload ho gayi. Har ek background mein, ek ke baad ek, padhi jayegi.`);onStarted();onClose();
 }
 async function send(){setBusy(true);stopped.current=false;try{
  if(many){await sendMany();return;}
  const name=(title.trim()||main.name.replace(/\.pdf$/i,'')).slice(0,160);
  if(key||sols)setMsg('Aapki PDF jodi ja rahi hain…');
  const file=await mergePdfs([main,key,sols].filter(Boolean),main.name);
  await sendBook({file,title:name,sectionId:section.id,replace,year:pyq?Number(year):null,subject:chapters?subject:'',stopped,onProgress:(m,p)=>{setMsg(m);setProgress(p);}});
  toast.success('Upload ho gaya. Padhai background mein hoti hai; yeh screen band kar sakte hain.');onStarted();onClose();
 }catch(e){toast.error(e.message);setMsg(e.message);}finally{setBusy(false);}}
 const ok=rights&&(many?(!pyq||batch.every(r=>r.state==='done'||/^\d{4}$/.test(r.year))):main&&(!pyq||/^\d{4}$/.test(year)));
 const left=batch.filter(r=>r.state!=='done').length;
 return <Dialog open={open} onOpenChange={v=>!v&&!busy&&onClose()}><DialogContent className="tejas-dialog admin-dialog master-dialog" data-testid="upload-dialog">
  <DialogTitle>{section.name} mein PDF upload karo</DialogTitle>
  <DialogDescription>{chapters?'PDF ka har chapter apna alag test banta hai, layout chahe jo ho. Agar chapter kahan shuru hote hain yeh na mile, toh aap pages par mark karenge.':'PDF mein ek mock ho ya kai; har chhapa hua mock apna alag test banta hai.'} Har mock Draft ki tarah aata hai. Koi AI nahi lagta.</DialogDescription>
  {count&&<p className="admin-note warn" data-testid="upload-replace-note">{count} badle ja rahe hain. Purane tab tak Live rahenge jab tak naye Live na ho jayein, phir woh Library mein chale jayenge. Students ke score rahenge.</p>}
  {open&&<StorageNotice/>}
  <form className="admin-form" onSubmit={e=>{e.preventDefault();if(ok&&!busy)send();}}>
   <PdfBox label={many?`${batch.length} PDF chuni`:'Main PDF'} hint={replace?'Sawaal. Agar answer key aur solutions bhi isi mein hain, toh bas yahi chahiye. 100 MB tak.':'Sawaal, har PDF 100 MB tak. Kai PDF ek saath chuniye, woh ek ke baad ek jayengi.'}
    file={main} onPick={pickMain} disabled={busy} testId="upload-main" required multiple={!replace}/>
   {many?<><BatchRows rows={batch} setRows={setBatch} pyq={pyq} busy={busy}/>{!busy&&<Button type="button" variant="ghost" size="sm" onClick={()=>setBatch([])} data-testid="upload-batch-clear">Sab hatao</Button>}</>:<>
    <div className="master-field-row">
     <PdfBox label="Answer key PDF" hint="Sirf tab, jab key alag file mein ho." file={key} onPick={setKey} disabled={busy} testId="upload-key"/>
     <PdfBox label="Solutions PDF" hint="Sirf tab, jab solutions alag file mein hon." file={sols} onPick={setSols} disabled={busy} testId="upload-solutions"/>
    </div>
    <Field label="Aapki uploads list ke liye naam (private)" id="upload-title"><Input id="upload-title" value={title} maxLength={160} disabled={busy} onChange={e=>setTitle(e.target.value)} data-testid="upload-title"/></Field>
   </>}
   {many&&<p className="master-hint" data-testid="upload-batch-note">Har PDF mein uski apni answer key honi chahiye. Naam file ke naam se aate hain{pyq?'; har paper ka saal check kijiye':''}.</p>}
   {chapters&&<Field label="Chapters ka subject" id="upload-subject"><Select value={subject||'pdf'} onValueChange={v=>setSubject(v==='pdf'?'':v)} disabled={busy}><SelectTrigger id="upload-subject" data-testid="upload-subject"><SelectValue/></SelectTrigger><SelectContent>
    <SelectItem value="pdf" data-testid="upload-subject-pdf">PDF se padho (saaf na ho toh mujhse poocho)</SelectItem>
    {(exam?.subjects||[]).map(s=><SelectItem key={s} value={s} data-testid={'upload-subject-'+s.toLowerCase()}>Saare chapter {s} ke hain</SelectItem>)}
   </SelectContent></Select></Field>}
   {pyq&&!many&&<Field label="Paper ka saal" id="upload-year"><Input id="upload-year" inputMode="numeric" maxLength={4} value={year} disabled={busy} onChange={e=>setYear(e.target.value.replace(/\D/g,''))} placeholder="jaise 2025" data-testid="upload-year"/></Field>}
   <label className="book-check"><input type="checkbox" checked={rights} disabled={busy} onChange={e=>setRights(e.target.checked)} data-testid="upload-rights"/><span>Mere paas yeh content students ko dikhane ki permission hai.</span></label>
   <p className="master-hint">Bina answer key wala mock Live nahi ho sakta. Solutions zaroori nahi: unke bina students ko answer key dikhti hai.</p>
   {msg&&!many&&<div className="admin-progress" role="status" data-testid="upload-progress"><progress value={progress} max={1}/><small>{msg}</small></div>}
   <div className="button-row">{busy?<Button type="button" variant="outline" onClick={()=>{stopped.current=true;}} data-testid="upload-pause">Roko</Button>:<Button type="button" variant="outline" onClick={onClose} disabled={busy} data-testid="upload-cancel">Cancel</Button>}<Button type="submit" disabled={!ok||busy} data-testid="upload-send">{busy?<Loader2 size={16} className="spin"/>:<UploadCloud size={16}/>}{many?`${left} PDF upload karo`:'Upload'}</Button></div>
  </form>
 </DialogContent></Dialog>;
}
