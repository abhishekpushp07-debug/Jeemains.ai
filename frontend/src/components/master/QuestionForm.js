import React,{useRef,useState} from 'react';
import {ImagePlus,X,Loader2,Trash2,Save} from 'lucide-react';
import {api,put} from '../../lib/api';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Textarea} from '../ui/textarea';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {PrivateBookImage} from '../books/BookShared';
import {MathText} from '../QuestionContent';
import {Field} from './MasterShared';
import {toast} from 'sonner';

const LETTERS=['A','B','C','D'];
const blank=subject=>({subject,chapter:'',text:'',image:'',type:'mcq',options:LETTERS.map(()=>({text:'',image:''})),answer:'',solution:'',solution_image:''});

function Photo({mockId,value,onChange,label,testId}){
 const ref=useRef(null),[busy,setBusy]=useState(false);
 async function send(file){if(!file)return;setBusy(true);try{const form=new FormData();form.append('file',file);const r=await api(`/admin/master/written/${mockId}/images`,{method:'POST',body:form});onChange(r.id);}catch(e){toast.error(e.message);}finally{setBusy(false);ref.current.value='';}}
 return <div className="master-photo" data-testid={testId}>
  {value?<><PrivateBookImage path={`/admin/master/written/${mockId}/images/${value}`} alt={label} testId={testId+'-img'}/><Button type="button" size="icon" variant="ghost" aria-label={'Remove '+label} onClick={()=>onChange('')} data-testid={testId+'-remove'}><X size={15}/></Button></>
   :<Button type="button" size="sm" variant="outline" disabled={busy} onClick={()=>ref.current.click()} data-testid={testId+'-add'}>{busy?<Loader2 size={15} className="spin"/>:<ImagePlus size={15}/>}{label}</Button>}
  <input ref={ref} type="file" hidden accept="image/png,image/jpeg,image/webp" onChange={e=>send(e.target.files[0])} data-testid={testId+'-input'}/>
 </div>;
}

export function QuestionForm({mock,question,subjects,onSaved,onDelete,disabled}){
 const start=question?.input?{...blank(''),...question.input,options:LETTERS.map((_,i)=>question.input.options?.[i]||{text:'',image:''})}:blank(mock.chapter_subject||subjects[0]||'');
 const [v,setV]=useState(start),[busy,setBusy]=useState(false);
 const set=(k,x)=>setV(p=>({...p,[k]:x}));
 const setOpt=(i,k,x)=>setV(p=>({...p,options:p.options.map((o,j)=>j===i?{...o,[k]:x}:o)}));
 const mcq=v.type==='mcq',filled=v.options.filter(o=>o.text.trim()||o.image);
 const ok=v.subject&&(v.text.trim()||v.image)&&(mcq?filled.length>=2&&LETTERS.slice(0,filled.length).includes(v.answer):/^[+-]?\d{1,20}$/.test(v.answer.trim()));
 async function save(){setBusy(true);try{
  const options=mcq?v.options.slice(0,Math.max(2,v.options.findLastIndex(o=>o.text.trim()||o.image)+1)):[];
  const r=await put(`/admin/master/written/${mock.id}/questions`,{...v,id:question?.id||'',answer:v.answer.trim(),options});
  toast.success(r.message);onSaved(r);if(!question)setV(blank(v.subject));
 }catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <form className="admin-panel master-qform" onSubmit={e=>{e.preventDefault();if(ok&&!busy)save();}} data-testid="question-form">
  <div className="admin-panel-head"><h2>{question?`Question ${question.number}`:'New question'}</h2>{question&&onDelete&&<Button type="button" variant="ghost" size="sm" disabled={busy||disabled} onClick={onDelete} data-testid="question-delete"><Trash2 size={15}/>Delete</Button>}</div>
  {question?.flag&&<p className="admin-note warn" data-testid="question-flag">{question.flag} Check every field, then save.</p>}
  <div className="master-field-row">
   <Field label="Subject" id="q-subject"><Select value={v.subject} onValueChange={x=>set('subject',x)}><SelectTrigger id="q-subject" data-testid="question-subject"><SelectValue placeholder="Choose"/></SelectTrigger><SelectContent>{[...new Set([...subjects,v.subject].filter(Boolean))].map(s=><SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></Field>
   {mock.test_kind==='chapter'&&<Field label="Topic (optional)" id="q-chapter"><Input id="q-chapter" value={v.chapter} maxLength={120} onChange={e=>set('chapter',e.target.value)} data-testid="question-chapter"/></Field>}
  </div>
  <Field label="Question (maths between $ signs, e.g. $x^2$)" id="q-text"><Textarea id="q-text" rows={5} value={v.text} maxLength={20000} onChange={e=>set('text',e.target.value)} data-testid="question-text"/></Field>
  {v.text.includes('$')&&<div className="master-preview" data-testid="question-preview"><MathText text={v.text}/></div>}
  <Photo mockId={mock.id} value={v.image} onChange={x=>set('image',x)} label="Question photo" testId="question-photo"/>
  <fieldset className="master-answer-type"><legend>Answer type</legend>{[['mcq','Options'],['integer','Numerical']].map(([k,l])=><button type="button" key={k} className={'admin-pill'+(v.type===k?' is-picked':'')} aria-pressed={v.type===k} onClick={()=>setV(p=>({...p,type:k,answer:''}))} data-testid={'question-type-'+k}>{l}</button>)}</fieldset>
  {mcq?<div className="master-options">{v.options.map((o,i)=><div key={i} className={'master-option'+(v.answer===LETTERS[i]?' is-correct':'')} data-testid={'question-option-'+LETTERS[i]}>
    <button type="button" className="master-option-letter" aria-pressed={v.answer===LETTERS[i]} aria-label={'Option '+LETTERS[i]+' is correct'} onClick={()=>set('answer',LETTERS[i])} data-testid={'question-correct-'+LETTERS[i]}>{LETTERS[i]}</button>
    <Input value={o.text} maxLength={4000} placeholder={'Option '+LETTERS[i]} onChange={e=>setOpt(i,'text',e.target.value)} data-testid={'question-option-text-'+LETTERS[i]}/>
    <Photo mockId={mock.id} value={o.image} onChange={x=>setOpt(i,'image',x)} label="Photo" testId={'question-option-photo-'+LETTERS[i]}/>
   </div>)}<small className="master-hint">Tap a letter to mark the correct option{v.answer?`: ${v.answer}`:''}.</small></div>
   :<Field label="Correct answer (whole number)" id="q-answer"><Input id="q-answer" inputMode="numeric" value={v.answer} maxLength={20} onChange={e=>set('answer',e.target.value)} placeholder="e.g. 12" data-testid="question-answer"/></Field>}
  <Field label="Solution (optional)" id="q-solution"><Textarea id="q-solution" rows={3} value={v.solution} maxLength={20000} onChange={e=>set('solution',e.target.value)} data-testid="question-solution"/></Field>
  <Photo mockId={mock.id} value={v.solution_image} onChange={x=>set('solution_image',x)} label="Solution photo" testId="question-solution-photo"/>
  <div className="button-row"><Button type="submit" disabled={!ok||busy||disabled} data-testid="question-save">{busy?<Loader2 size={16} className="spin"/>:<Save size={16}/>}{question?'Save':'Save & next'}</Button></div>
 </form>;
}
