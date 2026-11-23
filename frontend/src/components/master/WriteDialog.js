import React,{useEffect,useState} from 'react';
import {Loader2} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {post} from '../../lib/api';
import {Field} from './MasterShared';
import {toast} from 'sonner';

export function WriteDialog({open,onClose,section,exam,onCreated}){
 const d=section.defaults||{minutes:180,correct:4,wrong:-1};
 const [v,setV]=useState({}),[busy,setBusy]=useState(false);
 useEffect(()=>{if(open)setV({title:'',minutes:d.minutes,correct:d.correct,wrong:d.wrong,subject:exam.subjects[0]||'',chapter:'',year:'',exam_date:'',shift:''});},[open]);// eslint-disable-line react-hooks/exhaustive-deps
 const chapters=section.layout==='chapters',pyq=section.kind==='pyq',series=section.kind==='aits';
 const set=k=>e=>setV({...v,[k]:e.target?e.target.value:e});
 const ok=(v.title||'').trim().length>=2&&(!chapters||(v.subject&&v.chapter?.trim()))&&(!pyq||/^\d{4}$/.test(v.year||''));
 async function save(){setBusy(true);try{
  const r=await post(`/admin/master/types/${section.id}/written`,{title:v.title.trim(),...(series?{}:{minutes:Math.round(Number(v.minutes)),correct:Number(v.correct),wrong:Number(v.wrong)}),
   ...(chapters?{subject:v.subject,chapter:v.chapter.trim()}:{}),...(pyq?{year:Number(v.year),exam_date:v.exam_date,...(v.shift?{shift:Number(v.shift)}:{})}:{})});
  onCreated(r.id);
 }catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <Dialog open={open} onOpenChange={x=>!x&&onClose()}><DialogContent className="tejas-dialog admin-dialog master-dialog" data-testid="write-dialog">
  <DialogTitle>{section.name} mein mock likho</DialogTitle><DialogDescription>Yeh Draft ki tarah shuru hota hai. Sawaal ek-ek karke jodiye ya poora paper paste kijiye.</DialogDescription>
  <form className="admin-form" onSubmit={e=>{e.preventDefault();if(ok&&!busy)save();}}>
   <Field label={chapters?'Test ka naam':'Mock ka naam'} id="write-title"><Input id="write-title" value={v.title||''} maxLength={160} onChange={set('title')} placeholder={chapters?'jaise Laws of Motion · Test 1':'jaise Mock Test 12'} data-testid="write-title"/></Field>
   {chapters&&<div className="master-field-row">
    <Field label="Subject" id="write-subject"><Select value={v.subject} onValueChange={set('subject')}><SelectTrigger id="write-subject" data-testid="write-subject"><SelectValue/></SelectTrigger><SelectContent>{exam.subjects.map(s=><SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></Field>
    <Field label="Chapter" id="write-chapter"><Input id="write-chapter" value={v.chapter||''} maxLength={120} onChange={set('chapter')} data-testid="write-chapter"/></Field>
   </div>}
   {pyq&&<div className="master-field-row">
    <Field label="Saal" id="write-year"><Input id="write-year" inputMode="numeric" maxLength={4} value={v.year||''} onChange={e=>setV({...v,year:e.target.value.replace(/\D/g,'')})} data-testid="write-year"/></Field>
    <Field label="Exam ki date (zaroori nahi)" id="write-date"><Input id="write-date" type="date" value={v.exam_date||''} onChange={set('exam_date')} data-testid="write-date"/></Field>
    <Field label="Shift (zaroori nahi)" id="write-shift"><Input id="write-shift" inputMode="numeric" maxLength={1} value={v.shift||''} onChange={e=>setV({...v,shift:e.target.value.replace(/\D/g,'')})} data-testid="write-shift"/></Field>
   </div>}
   {series?<p className="master-hint">Series ke paper series ka time aur marks lete hain.</p>:<div className="master-field-row">
    <Field label="Time (minute)" id="write-minutes"><Input id="write-minutes" type="number" min={1} value={v.minutes??''} onChange={set('minutes')} data-testid="write-minutes"/></Field>
    <Field label="Sahi par marks" id="write-correct"><Input id="write-correct" type="number" step="0.25" value={v.correct??''} onChange={set('correct')} data-testid="write-correct"/></Field>
    <Field label="Galat par marks" id="write-wrong"><Input id="write-wrong" type="number" step="0.25" max={0} value={v.wrong??''} onChange={set('wrong')} data-testid="write-wrong"/></Field>
   </div>}
   <div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid="write-cancel">Cancel</Button><Button type="submit" disabled={!ok||busy} data-testid="write-create">{busy&&<Loader2 size={16} className="spin"/>}Likhna shuru karo</Button></div>
  </form>
 </DialogContent></Dialog>;
}
