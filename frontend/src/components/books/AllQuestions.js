import React,{useEffect,useMemo,useState} from 'react';
import {ChevronDown,AlertTriangle,Type} from 'lucide-react';
import {Button} from '../ui/button';
import {api} from '../../lib/api';
import {BookError} from './BookShared';
import {QuestionCard} from './HeldFixer';

const FILTERS=[['all','All questions'],['few','Fewer than 4 options'],['marked','Marked by the reader']];
const few=q=>q.type==='mcq'&&q.options.length<4;
const slug=q=>`${String(q.subject||'q').toLowerCase().replace(/\W+/g,'-')}-${q.number}`;
const pick={all:()=>true,few,marked:q=>q.issues.length>0};

function Row({q,open,onToggle,children}){
 const typed=Object.keys(q.typed_options||{}).length;
 return <li className={'all-q-row'+(open?' is-open':'')} data-testid={'all-q-'+slug(q)}>
  <button type="button" className="all-q-head" onClick={onToggle} aria-expanded={open} data-testid={'all-q-toggle-'+slug(q)}>
   <span className="all-q-num">Q{q.number}</span>
   <span className="all-q-main"><strong>{q.subject}</strong><small>{q.type==='mcq'?`Buttons ${q.options.join(' ')}`:'Numerical answer'} · Answer {q.answer||'not read'}</small></span>
   {few(q)&&<span className="all-q-flag" data-testid={'all-q-few-'+slug(q)}><AlertTriangle size={13} aria-hidden="true"/>Only {q.options.length} options</span>}
   {typed>0&&<span className="all-q-flag is-typed" data-testid={'all-q-typed-'+slug(q)}><Type size={13} aria-hidden="true"/>{typed} typed</span>}
   {q.issues.length>0&&<span className="all-q-flag is-marked">Marked</span>}
   <ChevronDown size={17} className={'all-q-chevron'+(open?' is-open':'')} aria-hidden="true"/>
  </button>
  {open&&children}
 </li>;
}

// Every question of a Draft PDF mock, so the owner can change buttons, type cut-off options or the answer.
export function AllQuestions({bookId,mockId,onOpenPage}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[open,setOpen]=useState(null),[filter,setFilter]=useState('all');
 useEffect(()=>{api(`/admin/books/${bookId}/mocks/${mockId}/problems?all=true`).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[bookId,mockId,reload]);
 const list=useMemo(()=>data?.questions||[],[data]);
 const counts=useMemo(()=>Object.fromEntries(FILTERS.map(([id])=>[id,list.filter(pick[id]).length])),[list]);
 const shown=list.filter(pick[filter]);
 function saved(){setTimeout(()=>{setOpen(null);setReload(n=>n+1);},4000);}
 return <section className="held-fixer all-questions" data-testid="all-questions">
  <header className="book-section-heading"><div><span className="eyebrow">EDIT QUESTIONS</span><h2 data-testid="all-questions-title">{data?.label||(error?'Mock not available':'Loading…')}</h2><p className="book-note">Every question in this Draft. Open one to change its answer buttons, type the options its picture cuts off, or change the answer. The mock is rechecked by itself. No AI is used.</p></div><div className="book-actions"><Button variant="outline" onClick={()=>setReload(n=>n+1)} data-testid="all-questions-refresh">Refresh</Button></div></header>
  <BookError error={error}/>
  {data?.frozen&&<p className="admin-note warn" data-testid="all-questions-frozen">This mock is published. Create a corrected version before changing it.</p>}
  {data&&<>
   <div className="library-segments" role="tablist" aria-label="Show" data-testid="all-questions-filters">{FILTERS.map(([id,name])=><button key={id} type="button" role="tab" aria-selected={filter===id} className={filter===id?'is-active':''} onClick={()=>{setFilter(id);setOpen(null);}} data-testid={'all-questions-filter-'+id}>{name}<span className="library-count">{counts[id]}</span></button>)}</div>
   {shown.length?<ul className="all-q-list" data-testid="all-questions-list">{shown.map(q=><Row key={q.id} q={q} open={open===q.id} onToggle={()=>setOpen(o=>o===q.id?null:q.id)}>
    <QuestionCard key={q.id+data.revision} q={q} bookId={bookId} mockId={mockId} revision={data.revision} onSaved={saved} onOpenPage={onOpenPage}/>
   </Row>)}</ul>:<p className="admin-empty" data-testid="all-questions-empty">{filter==='few'?'Every question has at least 4 answer buttons.':filter==='marked'?'The reader marked nothing here.':'No questions were read for this mock yet.'}</p>}
  </>}
 </section>;
}
