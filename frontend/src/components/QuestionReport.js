import React, {createContext, useContext, useEffect, useState} from 'react';
import {Flag, CheckCircle2, Loader2} from 'lucide-react';
import {api, post} from '../lib/api';
import {Button} from './ui/button';
import {Input} from './ui/input';
import {Select, SelectTrigger, SelectValue, SelectContent, SelectItem} from './ui/select';

const Reports = createContext(null);
export const QuestionReportsProvider = ({attemptId,children}) => {
 const [items,setItems]=useState({});
 useEffect(()=>{let live=true;setItems({});api(`/attempts/${attemptId}/question-reports`).then(rows=>{if(live)setItems(old=>({...Object.fromEntries(rows.map(r=>[r.question_id,r])),...old}))}).catch(()=>{});return()=>{live=false}},[attemptId]);
 const remember=receipt=>setItems(old=>({...old,[receipt.question_id]:receipt}));
 return <Reports.Provider value={{items,remember}}>{children}</Reports.Provider>;
};

export const QuestionReport = ({attemptId,questionId,number,context='attempt'}) => {
 const shared=useContext(Reports), receipt=shared?.items[questionId];
 const [open,setOpen]=useState(false),[note,setNote]=useState(''),[category,setCategory]=useState(context==='solutions'?'solution':'question'),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const prefix=`${context}-report-${number}`;
 async function send(e){e.preventDefault();setBusy(true);setError('');try{const r=await post(`/attempts/${attemptId}/questions/${questionId}/report-wrong`,{category,context,note});shared?.remember(r);setOpen(false)}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <div className="question-report" data-testid={prefix+'-strip'}>
  {receipt?<span role="status" data-testid={prefix+'-ack'}><CheckCircle2 size={14}/> Report received · {receipt.status==='resolved'?'reviewed':'under review'}</span>:<Button variant="link" className="question-report-trigger" data-testid={prefix+'-open'} aria-expanded={open} onClick={()=>setOpen(v=>!v)}><Flag size={13}/> Report as wrong</Button>}
  {open&&!receipt&&<form onSubmit={send} className="question-report-form" data-testid={prefix+'-form'}><Select value={category} onValueChange={setCategory}><SelectTrigger aria-label="Issue type" data-testid={prefix+'-category'}><SelectValue/></SelectTrigger><SelectContent>{[['question','Question / options'],['display','Image / display'],...(context==='attempt'?[]:[['key','Answer key'],['solution','Explanation']])].map(([value,label])=><SelectItem value={value} key={value} data-testid={prefix+'-type-'+value}>{label}</SelectItem>)}</SelectContent></Select><Input aria-label="Optional issue note" maxLength={600} value={note} onChange={e=>setNote(e.target.value)} placeholder="What seems wrong? (optional)" data-testid={prefix+'-note'}/><Button type="submit" size="sm" disabled={busy} data-testid={prefix+'-send'}>{busy?<Loader2 size={14} className="spin"/>:'Send'}</Button><Button type="button" variant="ghost" size="sm" disabled={busy} onClick={()=>setOpen(false)} data-testid={prefix+'-cancel'}>Cancel</Button><small data-testid={prefix+'-help'}>For content review only—not “mark for review”. Your answers, score and timer are unchanged.</small></form>}
  {error&&<p className="warning-text" role="alert" data-testid={prefix+'-error'}>{error} Your report is not confirmed; retry Send.</p>}
 </div>;
};
