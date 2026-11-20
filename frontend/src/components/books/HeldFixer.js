import React,{useEffect,useState} from 'react';
import {Loader2,CheckCircle2} from 'lucide-react';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {api,post} from '../../lib/api';
import {useAuth} from '../../lib/auth';
import {BookError,PrivateBookImage} from './BookShared';
import {CutTool} from './CutTool';
import {plain} from '../master/MasterShared';
import {toast} from 'sonner';

const LETTERS=['A','B','C','D','E'];
const pagesIn=text=>[...new Set([...text.matchAll(/Page (\d+)/g)].map(m=>Number(m[1])))].slice(0,4);
const rulesIssue=text=>/rules|count|mechanic|marking|instructions|duration/i.test(text);

function Choice({value,options,onChange,testId}){
 return <div className="admin-choice-row" role="radiogroup">{options.map(([v,l])=><button type="button" role="radio" aria-checked={value===v} key={v} className={'admin-pill'+(value===v?' is-picked':'')} onClick={()=>onChange(v)} data-testid={`${testId}-${v}`}>{l}</button>)}</div>;
}

function TypedOptions({tag,options,typed,onChange,cut}){
 return <fieldset><legend>3. Option khud type karo (zaroorat ho tabhi)</legend><small className="held-hint">Sirf woh option type karo jo picture me kata hai ya chhapa hi nahi. {cut?'Student ko us option ke button par aapka likha text dikhega, picture nahi.':'Student ko aapka text picture ke neeche dikhega.'} Maths ke liye $x^2$ jaisa likh sakte ho.</small>
  <div className="held-typed-list">{options.map(l=><label key={l} className="held-typed"><span>{l}</span><Input value={typed[l]||''} maxLength={2000} placeholder={`Option ${l} ka text`} onChange={e=>onChange({...typed,[l]:e.target.value})} data-testid={`${tag}-typed-${l}`}/></label>)}</div>
 </fieldset>;
}

export function QuestionCard({q,bookId,mockId,revision,frozen,onSaved,onOpenPage}){
 const tag='held-q-'+q.number;const {user}=useAuth();const owner=user?.role==='owner';
 const [confirmed,setConfirmed]=useState(false),[showSol,setShowSol]=useState(false),[showWhole,setShowWhole]=useState(!q.cut);
 const solPages=q.solution_pages||[];
 const say=x=>{const p=Number((x.match(/^Page (\d+)/)||[])[1]);return solPages.includes(p)&&/needs review|continuation|crop boundary/i.test(x)?`Solution page ${p}: dekho ki solution ki picture me is sawaal ka poora solution hai aur kuch aur nahi.`:plain(x);};
 const [type,setType]=useState(q.type==='integer'?'integer':'mcq'),[options,setOptions]=useState(q.options.filter(x=>LETTERS.includes(x)).length>=2?q.options.filter(x=>LETTERS.includes(x)):['A','B','C','D']);
 const [answer,setAnswer]=useState(q.answer||''),[typed,setTyped]=useState(q.typed_options||{}),[complete,setComplete]=useState(false),[keyOnly,setKeyOnly]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[done,setDone]=useState(false);
 const needsSolution=q.issues.some(x=>/original solution expected/i.test(x));
 const valid=complete&&answer.trim()&&(type==='integer'?/^[+-]?\d{1,20}$/.test(answer.trim()):options.length>=2&&options.includes(answer));
 function toggle(letter){if(options.includes(letter)&&answer===letter)setAnswer('');setOptions(o=>o.includes(letter)?o.filter(x=>x!==letter):LETTERS.filter(x=>o.includes(x)||x===letter));}
 async function save(){setBusy(true);setError('');try{const option_texts=type==='mcq'?Object.fromEntries(options.filter(l=>(typed[l]||'').trim()).map(l=>[l,typed[l].trim()])):{};
  const r=await post(`/admin/books/${bookId}/mocks/${mockId}/fix`,{revision,question_id:q.id,response_type:type,option_labels:type==='mcq'?options:[],option_texts,answer:answer.trim(),complete:true,key_only:keyOnly,confirmed});toast.success(r.message);setDone(true);onSaved();}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <article className={'held-card'+(done?' is-done':'')} data-testid={tag}>
  <header className="held-card-head"><strong>{q.subject} · Q{q.number}</strong><span>Page {q.pages.join(', ')}</span>{done&&<span className="held-saved" data-testid={tag+'-saved'}><CheckCircle2 size={15}/>Save ho gaya · dobara check ho raha hai</span>}</header>
  {q.issues.length>0&&<ul className="admin-reasons">{[...new Set(q.issues.map(say))].map((x,i)=><li key={i}>{x}</li>)}</ul>}
  {q.cut&&<CutTool q={q} bookId={bookId} mockId={mockId} revision={revision} frozen={frozen} onSaved={onSaved}/>}
  {q.cut?<details className="held-solutions" onToggle={e=>setShowWhole(e.currentTarget.open)} data-testid={tag+'-whole-picture'}><summary>Kitaab me poora sawaal (ek picture) ({q.question_images})</summary><div className="held-crops">{showWhole&&Array.from({length:q.question_images},(_,i)=><PrivateBookImage key={i} path={`/admin/books/${bookId}/mocks/${mockId}/questions/${q.id}/asset/question/${i}`} alt={`${q.subject} sawaal ${q.number}, hissa ${i+1}`} testId={`${tag}-img-${i}`}/>)}</div></details>
   :<div className="held-crops">{Array.from({length:q.question_images},(_,i)=><PrivateBookImage key={i} path={`/admin/books/${bookId}/mocks/${mockId}/questions/${q.id}/asset/question/${i}`} alt={`${q.subject} sawaal ${q.number}, hissa ${i+1}`} testId={`${tag}-img-${i}`}/>)}</div>}
  {q.solution_images>0&&<details className="held-solutions" onToggle={e=>setShowSol(e.currentTarget.open)} data-testid={tag+'-solutions'}><summary>Solution ki picture jo student dekhega ({q.solution_images})</summary><div className="held-crops">{showSol&&Array.from({length:q.solution_images},(_,i)=><PrivateBookImage key={i} path={`/admin/books/${bookId}/mocks/${mockId}/questions/${q.id}/asset/solution/${i}`} alt={`${q.subject} solution ${q.number}, hissa ${i+1}`} testId={`${tag}-sol-img-${i}`}/>)}</div></details>}
  {onOpenPage&&<div className="book-actions">{q.pages.map(n=><Button key={n} variant="outline" size="sm" onClick={()=>onOpenPage(n)} data-testid={`${tag}-page-${n}`}>Poora page {n}</Button>)}{q.next_page&&<Button variant="outline" size="sm" onClick={()=>onOpenPage(q.next_page)} data-testid={`${tag}-next-page`}>Agla page {q.next_page}</Button>}{solPages.slice(0,3).map(n=><Button key={'s'+n} variant="outline" size="sm" onClick={()=>onOpenPage(n)} data-testid={`${tag}-sol-page-${n}`}>Solution page {n}</Button>)}</div>}
  <div className="held-form">
   <fieldset><legend>1. Jawab kis tarah ka hai</legend><Choice value={type} onChange={v=>{setType(v);setAnswer('');}} options={[['mcq','Options (MCQ)'],['integer','Numerical jawab']]} testId={tag+'-type'}/></fieldset>
   {type==='mcq'&&<fieldset><legend>2. Student ko kaun se option button milenge</legend>{LETTERS.map(l=><label key={l} className="book-check held-option"><input type="checkbox" checked={options.includes(l)} onChange={()=>toggle(l)} data-testid={`${tag}-option-${l}`}/><span>{l}</span></label>)}</fieldset>}
   {type==='mcq'&&<TypedOptions tag={tag} options={options} typed={typed} onChange={setTyped} cut={!!q.cut}/>}
   <fieldset><legend>{type==='mcq'?'4. Sahi option':'2. Sahi jawab'}</legend>{type==='mcq'?<Choice value={answer} onChange={setAnswer} options={options.map(l=>[l,l])} testId={tag+'-answer'}/>:<Input value={answer} onChange={e=>setAnswer(e.target.value)} placeholder="jaise 12" inputMode="numeric" className="held-number" data-testid={tag+'-answer-input'}/>}<small className="held-hint">{q.answer?`Kitaab ki answer key kehti hai: ${q.answer}.`:'Iski chhapi hui key abhi tak nahi mili.'}</small></fieldset>
   {needsSolution&&q.key_only_allowed&&<label className="book-check"><input type="checkbox" checked={keyOnly} onChange={e=>setKeyOnly(e.target.checked)} data-testid={tag+'-key-only'}/><span>Kitaab me is sawaal ka solution nahi hai. Ise sirf answer key ke saath Live karo.</span></label>}
   <label className="book-check"><input type="checkbox" checked={complete} onChange={e=>setComplete(e.target.checked)} data-testid={tag+'-complete'}/><span>Maine picture dekh li. Har option picture me hai ya upar type kiya hai, aur kuch kata nahi hai.</span></label>
   {owner&&q.issues.length>0&&<label className="book-check held-override"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)} data-testid={tag+'-override'}/><span><strong>Override:</strong> Maine yeh sawaal aur iska solution khud dekh liya, sab sahi hai. Iski baaki warnings hata do.{q.cut?.status==='held'?' Iska cut theek nahi hua hai, isliye yeh sawaal ek poori picture me dikhega.':''}</span></label>}
   {q.confirmed&&<p className="held-hint" data-testid={tag+'-override-done'}>Is sawaal ki warnings aap pehle hi hata chuke ho.</p>}
   <BookError error={error}/>
   <Button disabled={busy||!valid||done} onClick={save} data-testid={tag+'-save'}>{busy?<Loader2 size={16} className="spin"/>:null}Save karo aur dobara check karo</Button>
  </div>
 </article>;
}

function MockOverride({bookId,mockId,revision,count,onDone}){
 const [ask,setAsk]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function go(){setBusy(true);setError('');try{const r=await post(`/admin/books/${bookId}/mocks/${mockId}/confirm-all`,{revision,confirm:'CHECKED'});toast.success(r.message);setAsk(false);onDone();}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <div className="held-override held-mock-override" data-testid="held-mock-override">
  {!ask?<Button variant="outline" onClick={()=>setAsk(true)} data-testid="held-mock-override-open">Poore mock ko override karo</Button>
  :<><p><strong>Pakka?</strong> Aapne is mock ke saare {count} sawaal aur unke solution khud dekh liye hain. Sawaalon ki baaki saari warnings hat jayengi. Jis sawaal ka cut theek nahi hua, woh ek poori picture me dikhega. Jis sawaal ka jawab hi nahi mila, use phir bhi theek karna hoga.</p>
   <div className="book-actions"><Button disabled={busy} onClick={go} data-testid="held-mock-override-confirm">{busy?<Loader2 size={16} className="spin"/>:null}Haan, maine sab dekh liya</Button><Button variant="ghost" onClick={()=>setAsk(false)} data-testid="held-mock-override-cancel">Rehne do</Button></div></>}
  <BookError error={error}/>
 </div>;
}

export function CutSummary({cut,testId='cut-summary'}){
 if(!cut)return null;
 return <p className="cut-summary" data-testid={testId}><strong>{cut.total}</strong> sawaal · <strong>{cut.clean}</strong> saaf kate{cut.by_hand>0?` (${cut.by_hand} aapke boxes se)`:''}{cut.held>0&&<> · <b className="is-held">{cut.held} aapko dekhne hain</b></>}{cut.whole>0&&<> · {cut.whole} poori picture me</>}</p>;
}

export function HeldFixer({bookId,mockId,onClose,onOpenPage,onOpenRules,onSaved}){
 const {user}=useAuth();
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0);
 useEffect(()=>{api(`/admin/books/${bookId}/mocks/${mockId}/problems`).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[bookId,mockId,reload]);
 // The mock is rechecked in the background; a big book takes a little longer, so the list is read again twice.
 function saved(){onSaved?.();[4000,11000].forEach(ms=>setTimeout(()=>setReload(n=>n+1),ms));}
 return <section className="held-fixer" data-testid="held-fixer">
  <header className="book-section-heading"><div><span className="eyebrow">IS MOCK KO THEEK KARO</span><h2 data-testid="held-fixer-title">{data?.label||(error?'Mock nahi mila':'Khul raha hai…')}</h2><p className="book-note">Har card ek sawaal hai jise engine pakke se nahi padh paya. Box hila kar cut theek karo, ya option khud type karo, phir neeche ke sawaalon ka jawab dekar save karo. Mock apne aap dobara check hota hai. Koi AI nahi lagta.</p><CutSummary cut={data?.cut_summary} testId="held-cut-summary"/></div><div className="book-actions"><Button variant="outline" onClick={()=>setReload(n=>n+1)} data-testid="held-fixer-refresh">Refresh</Button>{onClose&&<Button variant="outline" onClick={onClose} data-testid="held-fixer-close">Band karo</Button>}</div></header>
  <BookError error={error}/>
  {data&&<>
   {data.state!=='held'&&<p className="admin-note" data-testid="held-fixer-clear">Yahan theek karne ko kuch nahi bacha. Wapas list me jao aur ise Live karo.</p>}
   {user?.role==='owner'&&data.state==='held'&&!data.frozen&&data.questions.length>0&&<MockOverride bookId={bookId} mockId={mockId} revision={data.revision} count={data.total||data.questions.length} onDone={saved}/>}
   {data.frozen&&<p className="admin-note warn">Yeh mock Live ho chuka hai. Badalne se pehle iska naya sudhaara hua version banao.</p>}
   {data.general.length>0&&<div className="held-general" data-testid="held-general"><strong>Aur cheezein jo dekhni hain</strong><ul>{data.general.map((x,i)=><li key={i}><span>{plain(x)}</span>{onOpenPage&&pagesIn(x).map(n=><Button key={n} variant="link" size="sm" onClick={()=>onOpenPage(n)} data-testid={`held-general-page-${i}-${n}`}>Page {n} kholo</Button>)}</li>)}</ul>{onOpenRules&&(data.rules_missing||data.general.some(rulesIssue))&&<Button variant="outline" onClick={onOpenRules} data-testid="held-open-rules">Is mock ke rules kholo</Button>}</div>}
   {data.questions.map(q=><QuestionCard key={q.id+data.revision} q={q} bookId={bookId} mockId={mockId} revision={data.revision} frozen={data.frozen} onSaved={saved} onOpenPage={onOpenPage}/>)}
   {!data.questions.length&&!data.general.length&&data.state==='held'&&<p data-testid="held-fixer-none">Abhi koi dikkat list me nahi hai. Thodi der me Refresh dabao.</p>}
  </>}
 </section>;
}
