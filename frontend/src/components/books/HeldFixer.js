import React,{useEffect,useState} from 'react';
import {Loader2,CheckCircle2} from 'lucide-react';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {api,post} from '../../lib/api';
import {BookError,PrivateBookImage} from './BookShared';
import {plain} from '../master/MasterShared';
import {toast} from 'sonner';

const LETTERS=['A','B','C','D','E'];
const pagesIn=text=>[...new Set([...text.matchAll(/Page (\d+)/g)].map(m=>Number(m[1])))].slice(0,4);
const rulesIssue=text=>/rules|count|mechanic|marking|instructions|duration/i.test(text);

function Choice({value,options,onChange,testId}){
 return <div className="admin-choice-row" role="radiogroup">{options.map(([v,l])=><button type="button" role="radio" aria-checked={value===v} key={v} className={'admin-pill'+(value===v?' is-picked':'')} onClick={()=>onChange(v)} data-testid={`${testId}-${v}`}>{l}</button>)}</div>;
}

function QuestionCard({q,bookId,mockId,revision,onSaved,onOpenPage}){
 const tag='held-q-'+q.number;
 const [type,setType]=useState(q.type==='integer'?'integer':'mcq'),[options,setOptions]=useState(q.options.filter(x=>LETTERS.includes(x)).length>=2?q.options.filter(x=>LETTERS.includes(x)):['A','B','C','D']);
 const [answer,setAnswer]=useState(q.answer||''),[complete,setComplete]=useState(false),[keyOnly,setKeyOnly]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[done,setDone]=useState(false);
 const needsSolution=q.issues.some(x=>/original solution expected/i.test(x));
 const valid=complete&&answer.trim()&&(type==='integer'?/^[+-]?\d{1,20}$/.test(answer.trim()):options.length>=2&&options.includes(answer));
 function toggle(letter){setOptions(o=>o.includes(letter)?o.filter(x=>x!==letter):LETTERS.filter(x=>o.includes(x)||x===letter));}
 async function save(){setBusy(true);setError('');try{const r=await post(`/admin/books/${bookId}/mocks/${mockId}/fix`,{revision,question_id:q.id,response_type:type,option_labels:type==='mcq'?options:[],answer:answer.trim(),complete:true,key_only:keyOnly});toast.success(r.message);setDone(true);onSaved();}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <article className={'held-card'+(done?' is-done':'')} data-testid={tag}>
  <header className="held-card-head"><strong>{q.subject} · Q{q.number}</strong><span>Page {q.pages.join(', ')}</span>{done&&<span className="held-saved" data-testid={tag+'-saved'}><CheckCircle2 size={15}/>Saved · rechecking</span>}</header>
  <ul className="admin-reasons">{[...new Set(q.issues.map(plain))].map((x,i)=><li key={i}>{x}</li>)}</ul>
  <div className="held-crops">{Array.from({length:q.question_images},(_,i)=><PrivateBookImage key={i} path={`/admin/books/${bookId}/mocks/${mockId}/questions/${q.id}/asset/question/${i}`} alt={`${q.subject} question ${q.number}, part ${i+1}`} testId={`${tag}-img-${i}`}/>)}</div>
  {onOpenPage&&<div className="book-actions">{q.pages.map(n=><Button key={n} variant="outline" size="sm" onClick={()=>onOpenPage(n)} data-testid={`${tag}-page-${n}`}>Full page {n}</Button>)}{q.next_page&&<Button variant="outline" size="sm" onClick={()=>onOpenPage(q.next_page)} data-testid={`${tag}-next-page`}>Next page {q.next_page}</Button>}</div>}
  <div className="held-form">
   <fieldset><legend>1. Answer type</legend><Choice value={type} onChange={v=>{setType(v);setAnswer('');}} options={[['mcq','Options (MCQ)'],['integer','Numerical answer']]} testId={tag+'-type'}/></fieldset>
   {type==='mcq'&&<fieldset><legend>2. Options printed in the question</legend>{LETTERS.map(l=><label key={l} className="book-check held-option"><input type="checkbox" checked={options.includes(l)} onChange={()=>toggle(l)} data-testid={`${tag}-option-${l}`}/><span>{l}</span></label>)}</fieldset>}
   <fieldset><legend>{type==='mcq'?'3. Correct option':'2. Correct answer'}</legend>{type==='mcq'?<Choice value={answer} onChange={setAnswer} options={options.map(l=>[l,l])} testId={tag+'-answer'}/>:<Input value={answer} onChange={e=>setAnswer(e.target.value)} placeholder="e.g. 12" inputMode="numeric" className="held-number" data-testid={tag+'-answer-input'}/>}<small className="held-hint">{q.answer?`The book’s answer key says ${q.answer}.`:'No printed key was read for it yet.'}</small></fieldset>
   {needsSolution&&q.key_only_allowed&&<label className="book-check"><input type="checkbox" checked={keyOnly} onChange={e=>setKeyOnly(e.target.checked)} data-testid={tag+'-key-only'}/><span>The book has no worked solution for this question. Publish it with the answer key only.</span></label>}
   <label className="book-check"><input type="checkbox" checked={complete} onChange={e=>setComplete(e.target.checked)} data-testid={tag+'-complete'}/><span>I checked the picture: the whole question and all its options are shown. Nothing is cut off.</span></label>
   
   <BookError error={error}/>
   <Button disabled={busy||!valid||done} onClick={save} data-testid={tag+'-save'}>{busy?<Loader2 size={16} className="spin"/>:null}Save & recheck</Button>
  </div>
 </article>;
}

export function HeldFixer({bookId,mockId,onClose,onOpenPage,onOpenRules,onSaved}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0);
 useEffect(()=>{api(`/admin/books/${bookId}/mocks/${mockId}/problems`).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[bookId,mockId,reload]);
 function saved(){onSaved?.();setTimeout(()=>setReload(n=>n+1),4000);}
 return <section className="held-fixer" data-testid="held-fixer">
  <header className="book-section-heading"><div><span className="eyebrow">FIX THIS MOCK</span><h2 data-testid="held-fixer-title">{data?.label||(error?'Mock not available':'Loading…')}</h2><p className="book-note">Each card is one question that could not be read for sure. Look at the picture, answer the three questions, save. The mock is rechecked by itself. No AI is used.</p></div><div className="book-actions"><Button variant="outline" onClick={()=>setReload(n=>n+1)} data-testid="held-fixer-refresh">Refresh</Button>{onClose&&<Button variant="outline" onClick={onClose} data-testid="held-fixer-close">Close</Button>}</div></header>
  <BookError error={error}/>
  {data&&<>
   {data.state!=='held'&&<p className="admin-note" data-testid="held-fixer-clear">Nothing is left to fix here. Go back to its list to make it Live.</p>}
   {data.frozen&&<p className="admin-note warn">This mock is published. Create a corrected version before changing it.</p>}
   {data.general.length>0&&<div className="held-general" data-testid="held-general"><strong>Other things to check</strong><ul>{data.general.map((x,i)=><li key={i}><span>{plain(x)}</span>{onOpenPage&&pagesIn(x).map(n=><Button key={n} variant="link" size="sm" onClick={()=>onOpenPage(n)} data-testid={`held-general-page-${i}-${n}`}>Open page {n}</Button>)}</li>)}</ul>{onOpenRules&&(data.rules_missing||data.general.some(rulesIssue))&&<Button variant="outline" onClick={onOpenRules} data-testid="held-open-rules">Open this mock’s rules</Button>}</div>}
   {data.questions.map(q=><QuestionCard key={q.id+data.revision} q={q} bookId={bookId} mockId={mockId} revision={data.revision} onSaved={saved} onOpenPage={onOpenPage}/>)}
   {!data.questions.length&&!data.general.length&&data.state==='held'&&<p data-testid="held-fixer-none">No problems are listed right now. Press Refresh in a moment.</p>}
  </>}
 </section>;
}
