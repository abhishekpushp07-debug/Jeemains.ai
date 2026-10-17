import React,{useCallback,useEffect,useState} from 'react';
import {ScanSearch,CheckCircle2,AlertTriangle,RotateCcw,Sparkles} from 'lucide-react';
import {api,post,API} from '../../lib/api';
import {ErrorBox} from '../Shared';
import {Skeleton} from '../ui/skeleton';
import {Button} from '../ui/button';
import {Textarea} from '../ui/textarea';
import {MathText} from '../QuestionContent';

const FILTERS=[['open','Needs review'],['key_confirmed','Key verified'],['key_wrong','Key flagged wrong'],['all','All']];
const LABEL={key_confirmed:'Key verified · AI re-solving with verified key',key_wrong:'Key flagged wrong · students see AI solution with a note'};

const Item=({x,onAct,busy})=>{
 const [note,setNote]=useState(x.review?.note||''),[open,setOpen]=useState(false);
 const tid=`ai-review-${x.set_id.slice(0,8)}-${x.number}`;
 return <li className="ai-review-item" data-testid={tid}>
  <div className="ai-review-top">
   <div><strong>{x.set_title} · Q{x.number}</strong><span className="import-fineprint">{x.kind} · {x.exam} · {x.subject}</span></div>
   <div className="ai-review-keys"><span data-testid={tid+'-key'}>PDF key <b>{x.key}</b></span><span className="ai" data-testid={tid+'-ai'}>AI answer <b>{x.ai_answer||'—'}</b></span></div>
  </div>
  {x.review&&<p className="ai-review-status" data-testid={tid+'-status'}>{LABEL[x.review.status]}{x.review.note?` — “${x.review.note}”`:''}</p>}
  <div className="ai-review-body">
   <div className="ai-review-images">{Array.from({length:Math.min(x.image_count,3)}).map((_,i)=><img key={i} alt={`Question ${x.number} source region ${i+1}`} loading="lazy" src={`${API}/studio/sets/${x.set_id}/questions/${x.question_id}/asset/question/${i}`}/>)}</div>
   <div className="ai-review-why"><strong><Sparkles size={13}/> Why the AI disagrees</strong><MathText text={x.insight}/>
    <button type="button" className="ai-review-toggle" onClick={()=>setOpen(!open)} data-testid={tid+'-steps-toggle'}>{open?'Hide':'Show'} AI steps ({x.steps.length})</button>
    {open&&<ol className="ai-review-steps">{x.steps.map((s,i)=><li key={i}><b><MathText text={s.title}/></b> <MathText text={s.explanation}/></li>)}</ol>}
   </div>
  </div>
  <Textarea value={note} onChange={e=>setNote(e.target.value)} maxLength={600} placeholder="Optional note (what you checked)" data-testid={tid+'-note'}/>
  <div className="ai-review-actions">
   <Button className="btn btn-primary" disabled={busy} onClick={()=>onAct(x,'key_confirmed',note)} data-testid={tid+'-confirm'}><CheckCircle2 size={15}/> PDF key is correct</Button>
   <Button variant="outline" disabled={busy} onClick={()=>onAct(x,'key_wrong',note)} data-testid={tid+'-wrong'}><AlertTriangle size={15}/> Key looks wrong</Button>
   {x.review&&<Button variant="ghost" disabled={busy} onClick={()=>onAct(x,'reopen','')} data-testid={tid+'-reopen'}><RotateCcw size={15}/> Reopen</Button>}
  </div>
 </li>;
};

export const AiReviewPanel=()=>{
 const [filter,setFilter]=useState('open'),[data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const load=useCallback(()=>{api('/studio/ai-review?state='+filter).then(setData).catch(e=>setError(e.message))},[filter]);
 useEffect(()=>{setData(null);load()},[load]);
 const act=async(x,action,note)=>{setBusy(true);setError('');try{await post(`/studio/ai-review/${x.set_id}/${x.question_id}`,{action,note});load()}catch(e){setError(e.message)}finally{setBusy(false)}};
 const p=data?.progress;
 return <section className="import-card ai-review-panel" data-testid="studio-ai-review-panel">
  <span className="import-section-label"><ScanSearch size={17}/> AI ANSWER REVIEW</span>
  <h2>Questions where the AI disagrees with the PDF key</h2>
  <p className="import-muted">gpt-6-astra solves every uploaded question in the backend as soon as it is saved, and stores the solution on the question. Students only read saved solutions. A solution that disagrees with the key is hidden from students until you review it.</p>
  {p&&<div className="chapter-fixed-rules" data-testid="studio-ai-progress"><span><Sparkles size={15}/> {p.ready} / {p.total} questions solved</span><span>{p.disagree} disagreements</span>{p.failed>0&&<span>{p.failed} retrying</span>}</div>}
  <div className="ai-review-filters" role="tablist">{FILTERS.map(([v,l])=><button key={v} type="button" role="tab" aria-selected={filter===v} className={filter===v?'active':''} onClick={()=>setFilter(v)} data-testid={'ai-review-filter-'+v}>{l}{data?.counts&&v!=='all'?` (${data.counts[v]||0})`:''}</button>)}</div>
  <ErrorBox error={error}/>
  {!data?<Skeleton className="h-32"/>:data.items.length===0?<p className="import-fineprint" data-testid="ai-review-empty">Nothing here. {filter==='open'?'Every saved AI solution so far agrees with the key, or has been reviewed.':''}</p>:
   <ul className="ai-review-list">{data.items.map(x=><Item key={x.set_id+x.question_id} x={x} onAct={act} busy={busy}/>)}</ul>}
  <p className="import-fineprint">“PDF key is correct” re-solves the question with your verification so students get a matching worked solution. “Key looks wrong” shows students the AI solution with a correction note; scores change only through an official correction.</p>
 </section>;
};
