import React,{useState} from 'react';
import {Link} from 'react-router-dom';
import {CheckCircle2,XCircle,Loader2,RotateCcw,BookOpen} from 'lucide-react';
import {post} from '../../lib/api';
import {PrivateBookImage} from '../books/BookShared';

const OUT={incorrect:['Galat','bad'],skipped:['Chhoda tha','warn']};
const asset=(m,kind,i)=>`/attempts/${m.attempt_id}/questions/${m.question_id}/asset/${kind}/${i}`;
const label=(q,k,i)=>q.source_option_labels&&typeof q.source_option_labels==='object'?q.source_option_labels[k]||k:q.source_option_labels?String(i+1):k;

function Question({m}){
 const q=m.question||{},typed=m.type==='mcq'?[]:Object.entries(q.options||{}).filter(([,t])=>t);
 return <div className="mf-question">
  {Array.from({length:q.asset_count||0},(_,i)=><PrivateBookImage key={i} path={asset(m,'question',i)} alt={`${m.subject} sawaal ${m.number}`} testId={`misfire-img-${m.id}-${i}`}/>)}
  {!q.asset_count&&q.text&&<p className="mf-text" data-testid={'misfire-text-'+m.id}>{q.text}</p>}
  {typed.length>0&&<ul className="mf-typed">{typed.map(([k,t])=><li key={k}><b>{k}</b>{t}</li>)}</ul>}
 </div>;
}

function Answer({m,value,setValue,busy}){
 const q=m.question||{},keys=Object.keys(q.options||{});
 if(m.type==='mcq'&&keys.length)return <div className="mf-options" role="radiogroup" aria-label="Apna jawab chuno">{keys.map((k,i)=><button type="button" key={k} role="radio" aria-checked={value===k}
  className={'mf-option'+(value===k?' is-on':'')} disabled={busy} onClick={()=>setValue(k)} data-testid={`misfire-option-${m.id}-${k}`}><b>{label(q,k,i)}</b>{q.options[k]?<span>{q.options[k]}</span>:null}</button>)}</div>;
 return <input className="mf-input" inputMode={m.type==='integer'?'numeric':'decimal'} value={value} maxLength={40} disabled={busy} placeholder="Apna jawab likho" onChange={e=>setValue(e.target.value)} data-testid={'misfire-input-'+m.id}/>;
}

function Solution({m}){
 return <div className="mf-solution" data-testid={'misfire-solution-'+m.id}>
  {Array.from({length:m.solution_count||0},(_,i)=><PrivateBookImage key={i} path={asset(m,'solution',i)} alt={`${m.subject} solution ${m.number}`} testId={`misfire-sol-${m.id}-${i}`}/>)}
  {m.solution_text&&<p className="mf-text">{m.solution_text}</p>}
  {!m.solution_count&&!m.solution_text&&<p className="mf-muted">Is sawaal ka likha hua solution nahi hai; upar sahi jawab diya hai.</p>}
 </div>;
}

export function MisfireItem({m:start,onChanged}){
 const [m,setM]=useState(start),[value,setValue]=useState(''),[busy,setBusy]=useState(false),[result,setResult]=useState(null),[open,setOpen]=useState(false),[error,setError]=useState('');
 const id=encodeURIComponent(m.id),[word,tone]=OUT[m.outcome]||['Galat','bad'];
 async function act(fn){setBusy(true);setError('');try{await fn();}catch(e){setError(e.message);}finally{setBusy(false);}}
 const check=()=>act(async()=>{const r=await post(`/my/misfire/${id}/try`,{value:String(value).trim()});setM(r.item);setResult(r.correct?'right':'wrong');});
 const done=()=>act(async()=>{await post(`/my/misfire/${id}/done`,{});onChanged(m.id);});
 const reopen=()=>act(async()=>{await post(`/my/misfire/${id}/reopen`,{});onChanged(m.id);});
 return <article className="mf-item" data-testid={'misfire-item-'+m.id}>
  <header className="mf-head"><span className={'mf-tag '+tone}>{word}</span><strong>{m.subject}{m.chapter?' · '+m.chapter:''}</strong>
   <small>Q{m.number} · {m.title}{m.lost?` · ${m.lost} marks gaye`:''}</small></header>
  <Question m={m}/>
  <p className="mf-muted" data-testid={'misfire-paper-answer-'+m.id}>Paper mein aapka jawab: {m.your_answer||'chhoda tha'}</p>
  {m.status==='fixed'?<div className="mf-actions"><span className="mf-good"><CheckCircle2 size={16}/>Samajh gaya</span>
   <button type="button" className="mf-btn ghost" disabled={busy} onClick={reopen} data-testid={'misfire-reopen-'+m.id}><RotateCcw size={15}/>Wapas list mein</button></div>
  :<>
   <Answer m={m} value={value} setValue={v=>{setValue(v);setResult(null);}} busy={busy||result==='right'}/>
   <div className="mf-actions">
    {result!=='right'&&<button type="button" className="mf-btn" disabled={busy||!String(value).trim()} onClick={check} data-testid={'misfire-check-'+m.id}>{busy?<Loader2 size={15} className="spin"/>:null}Check karo</button>}
    {result==='right'&&<><span className="mf-good" role="status" data-testid={'misfire-right-'+m.id}><CheckCircle2 size={16}/>Sahi!</span>
     <button type="button" className="mf-btn" disabled={busy} onClick={done} data-testid={'misfire-done-'+m.id}>Samajh gaya</button></>}
    {result==='wrong'&&<span className="mf-bad" role="status" data-testid={'misfire-wrong-'+m.id}><XCircle size={16}/>Galat. Sahi jawab: {m.answer}</span>}
    {m.tries>0&&<button type="button" className="mf-btn ghost" onClick={()=>setOpen(v=>!v)} data-testid={'misfire-show-solution-'+m.id}><BookOpen size={15}/>{open?'Solution chhupao':'Solution dekho'}</button>}
    <Link className="mf-link" to={`/results/${m.attempt_id}?view=solutions&question=${m.question_id}`} data-testid={'misfire-open-paper-'+m.id}>Paper ka result</Link>
   </div>
   {open&&m.tries>0&&<Solution m={m}/>}
  </>}
  {error&&<p className="mf-bad" role="alert" data-testid={'misfire-error-'+m.id}>{error}</p>}
 </article>;
}
