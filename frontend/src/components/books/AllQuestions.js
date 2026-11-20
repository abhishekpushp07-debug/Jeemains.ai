import React,{useEffect,useMemo,useRef,useState} from 'react';
import {ChevronDown,AlertTriangle,Type,Scissors} from 'lucide-react';
import {Button} from '../ui/button';
import {api} from '../../lib/api';
import {BookError,PrivateBookImage} from './BookShared';
import {QuestionCard,CutSummary} from './HeldFixer';
import {PiecesPreview} from './CutTool';

const FILTERS=[['all','Saare sawaal'],['cut','Cut dekhna hai'],['few','4 se kam option'],['marked','Engine ne mark kiye'],['proof','Proof view']];
const few=q=>q.type==='mcq'&&q.options.length<4;
const slug=q=>`${String(q.subject||'q').toLowerCase().replace(/\W+/g,'-')}-${q.number}`;
const pick={all:()=>true,cut:q=>q.cut?.status==='held',few,marked:q=>q.issues.length>0,proof:()=>true};
const CUT={ok:['Saaf kata','ok'],manual:['Aapke boxes','ok'],trim:['Numerical','ok'],whole:['Poori picture','whole'],held:['Dekhna hai','held']};

function Row({q,open,onToggle,children}){
 const typed=Object.keys(q.typed_options||{}).length;
 return <li className={'all-q-row'+(open?' is-open':'')} data-testid={'all-q-'+slug(q)}>
  <button type="button" className="all-q-head" onClick={onToggle} aria-expanded={open} data-testid={'all-q-toggle-'+slug(q)}>
   <span className="all-q-num">Q{q.number}</span>
   <span className="all-q-main"><strong>{q.subject}</strong><small>{q.type==='mcq'?`Buttons ${q.options.join(' ')}`:'Numerical jawab'} · Jawab {q.answer||'nahi mila'}</small></span>
   {q.cut&&<span className={'all-q-flag is-cut-'+CUT[q.cut.status]?.[1]} data-testid={'all-q-cut-'+slug(q)}><Scissors size={13} aria-hidden="true"/>{CUT[q.cut.status]?.[0]}</span>}
   {few(q)&&<span className="all-q-flag" data-testid={'all-q-few-'+slug(q)}><AlertTriangle size={13} aria-hidden="true"/>Sirf {q.options.length} option</span>}
   {typed>0&&<span className="all-q-flag is-typed" data-testid={'all-q-typed-'+slug(q)}><Type size={13} aria-hidden="true"/>{typed} typed</span>}
   {q.issues.length>0&&<span className="all-q-flag is-marked">Marked</span>}
   <ChevronDown size={17} className={'all-q-chevron'+(open?' is-open':'')} aria-hidden="true"/>
  </button>
  {open&&children}
 </li>;
}

// Proof view: one question exactly as the student gets it. Drawn only when it scrolls near the screen.
function Proof({q,bookId,mockId}){
 const node=useRef(null);const [seen,setSeen]=useState(false);
 useEffect(()=>{const observer=new IntersectionObserver(list=>{if(list.some(e=>e.isIntersecting)){setSeen(true);observer.disconnect();}},{rootMargin:'400px'});if(node.current)observer.observe(node.current);return()=>observer.disconnect();},[]);
 const cut=q.cut,pieces=cut&&['ok','manual','trim'].includes(cut.status);
 return <li className="proof-row" ref={node} data-testid={'proof-'+slug(q)}>
  <header><strong>Q{q.number}</strong><span>{q.subject}</span>{cut&&<span className={'all-q-flag is-cut-'+CUT[cut.status]?.[1]}>{CUT[cut.status]?.[0]}</span>}<span className="proof-key">Key: {q.answer||'nahi mili'}</span></header>
  {!seen?<div className="proof-wait"/>:pieces?<PiecesPreview bookId={bookId} mockId={mockId} parts={cut.parts} q={q} empty=""/>
   :<div className="held-crops">{Array.from({length:q.question_images},(_,i)=><PrivateBookImage key={i} path={`/admin/books/${bookId}/mocks/${mockId}/questions/${q.id}/asset/question/${i}`} alt={`${q.subject} sawaal ${q.number}`} testId={`proof-img-${slug(q)}-${i}`}/>)}</div>}
 </li>;
}

// Every question of a Draft PDF mock, so the owner can change buttons, type cut-off options or the answer.
export function AllQuestions({bookId,mockId,onOpenPage}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[open,setOpen]=useState(null),[filter,setFilter]=useState('all');
 useEffect(()=>{api(`/admin/books/${bookId}/mocks/${mockId}/problems?all=true`).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[bookId,mockId,reload]);
 const list=useMemo(()=>data?.questions||[],[data]);
 const counts=useMemo(()=>Object.fromEntries(FILTERS.map(([id])=>[id,list.filter(pick[id]).length])),[list]);
 const shown=list.filter(pick[filter]);
 function saved(){[4000,11000].forEach(ms=>setTimeout(()=>{setOpen(null);setReload(n=>n+1);},ms));}
 return <section className="held-fixer all-questions" data-testid="all-questions">
  <header className="book-section-heading"><div><span className="eyebrow">SAWAAL DEKHO AUR BADLO</span><h2 data-testid="all-questions-title">{data?.label||(error?'Mock nahi mila':'Khul raha hai…')}</h2><p className="book-note">Is Draft ka har sawaal. Kisi ko kholo: uska cut dekho ya boxes hilao, option khud type karo, ya jawab badlo. Proof view me poora paper waisa dikhta hai jaisa student ko milega. Mock apne aap dobara check hota hai. Koi AI nahi lagta.</p><CutSummary cut={data?.cut_summary} testId="all-questions-cut-summary"/></div><div className="book-actions"><Button variant="outline" onClick={()=>setReload(n=>n+1)} data-testid="all-questions-refresh">Refresh</Button></div></header>
  <BookError error={error}/>
  {data?.frozen&&<p className="admin-note warn" data-testid="all-questions-frozen">Yeh mock Live ho chuka hai. Badalne se pehle iska naya sudhaara hua version banao.</p>}
  {data&&<>
   <div className="library-segments" role="tablist" aria-label="Kya dikhana hai" data-testid="all-questions-filters">{FILTERS.map(([id,name])=><button key={id} type="button" role="tab" aria-selected={filter===id} className={filter===id?'is-active':''} onClick={()=>{setFilter(id);setOpen(null);}} data-testid={'all-questions-filter-'+id}>{name}{id!=='proof'&&<span className="library-count">{counts[id]}</span>}</button>)}</div>
   {filter==='proof'?<ol className="proof-list" data-testid="proof-list">{list.map(q=><Proof key={q.id+data.revision} q={q} bookId={bookId} mockId={mockId}/>)}</ol>
   :shown.length?<ul className="all-q-list" data-testid="all-questions-list">{shown.map(q=><Row key={q.id} q={q} open={open===q.id} onToggle={()=>setOpen(o=>o===q.id?null:q.id)}>
    <QuestionCard key={q.id+data.revision} q={q} bookId={bookId} mockId={mockId} revision={data.revision} frozen={data.frozen} onSaved={saved} onOpenPage={onOpenPage}/>
   </Row>)}</ul>:<p className="admin-empty" data-testid="all-questions-empty">{filter==='few'?'Har sawaal me kam se kam 4 option button hain.':filter==='marked'?'Engine ne yahan kuch mark nahi kiya.':filter==='cut'?'Har sawaal saaf kata hai. Kuch dekhna baaki nahi.':'Is mock ka koi sawaal abhi padha nahi gaya.'}</p>}
  </>}
 </section>;
}
