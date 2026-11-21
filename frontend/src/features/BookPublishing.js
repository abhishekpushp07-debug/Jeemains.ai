import React,{useCallback,useEffect,useRef,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {RefreshCw,Pause,Play,AlertTriangle} from 'lucide-react';
import {useAuth} from '../lib/auth';
import {api,post,patch} from '../lib/api';
import {invalidateCatalog} from '../lib/catalog';
import {Button} from '../components/ui/button';
import {BookReview} from '../components/books/BookReview';
import {BookMockDesk} from '../components/books/BookMockDesk';
import {BookRangeMapping} from '../components/books/BookRangeMapping';
import {BookError,BookStatus,BookField} from '../components/books/BookShared';
import {AdminCrumbs,DestinationChip} from '../components/admin/AdminShared';
import {StudentPreview} from '../components/admin/StudentPreview';
import {HeldFixer} from '../components/books/HeldFixer';
import {toast} from 'sonner';
import '../book-publishing.css';

const RULE_EXAMS=['JEE Main','BITSAT','COMEDK'];

const FILTER_NAMES={detected:'detected',complete:'complete',held:'held',published:'published',scheduled:'scheduled'};
const KEEP={detected:()=>true,complete:m=>['ready','published','scheduled'].includes(m.state),held:m=>m.state==='held',published:m=>m.state==='published',scheduled:m=>m.state==='scheduled'};

function BookMap({book,onMock,onPage,onAction,onFix,filter,onClear}){
 const mocks=filter?book.mocks.filter(KEEP[filter]):book.mocks;
 return <section className="book-map" data-testid="book-map"><h2>Book map</h2><p className="book-note">Original numbering stays intact. Only published mocks appear to students.</p>{filter&&<p className="book-filter-note" data-testid="book-filter-note">Showing {mocks.length} {FILTER_NAMES[filter]} mock{mocks.length===1?'':'s'}.<button type="button" onClick={onClear} data-testid="book-filter-clear">Show all {book.mocks.length}</button></p>}{!book.mocks.length&&<p data-testid="book-no-mocks">No reliable mock boundaries yet. Open a source page and assign exact mock labels to its regions.</p>}{mocks.map(m=><article className="book-mock-row" key={m.id} data-testid={`book-mock-${m.id}`}><div className="book-section-heading"><div><strong>{m.label}</strong><small>{m.count} questions · {m.original_solutions} original explanations · {m.key_only} key-only</small></div><BookStatus state={m.state} id={`book-mock-state-${m.id}`}/></div><div className="book-page-ranges">{Object.entries(m.pages).map(([role,numbers])=><span key={role}>{role}: {numbers.length?numbers.map(n=><button key={n} data-testid={`book-${m.id}-${role}-page-${n}`} onClick={()=>onPage(n)}>{n}</button>):'—'}</span>)}</div>{m.issues.length>0&&<details><summary data-testid={`book-mock-issues-${m.id}`}><AlertTriangle size={14}/>{m.issues.length} blocking issues</summary><ul data-testid={`book-issue-list-${m.id}`}>{m.issues.map((issue,i)=><li key={i}>{issue}</li>)}</ul></details>}<div className="book-actions">{m.state==='held'&&<Button data-testid={`book-fix-mock-${m.id}`} onClick={()=>onFix(m.id)}>Fix problems</Button>}<Button variant="outline" data-testid={`book-review-mock-${m.id}`} onClick={()=>onMock(m.id)}>Rules & student preview</Button>{m.set_id&&<><Link className="book-text-link" to={`/sets/${m.set_id}`} data-testid={`book-open-test-${m.id}`}>Open test</Link>{m.published_generation===m.generation&&<Button variant="outline" data-testid={`book-new-version-${m.id}`} onClick={()=>onAction('new_version',m.id)}>Corrected version</Button>}</>}{m.missed_release&&<Button variant="outline" data-testid={`book-release-now-${m.id}`} onClick={()=>onAction('release_now',m.id)}>Decide new release</Button>}</div></article>)}</section>;
}

function Metric({label,value,id,filter,onFilter}){
 const tag=`book-count-${label.toLowerCase().replaceAll(' ','-')}`;
 if(!id)return <div className="book-metric"><strong data-testid={tag}>{value}</strong><span>{label}</span></div>;
 return <button type="button" className={'book-metric is-filter'+(filter===id?' is-active':'')} aria-pressed={filter===id} onClick={()=>onFilter(filter===id?null:id)} title={`Show ${label.toLowerCase()} mocks`} data-testid={'book-filter-'+id}><strong data-testid={tag}>{value}</strong><span>{label}</span></button>;
}

function BookProgress({book,filter,onFilter}){
 return <><div className="book-section-heading"><div><span className="eyebrow">SOURCE-FIRST PUBLISHING</span><h1 data-testid="book-detail-title">{book.title}</h1></div><BookStatus state={book.state} id="book-detail-state"/></div><p data-testid="book-detail-message">{book.message}</p><div className="book-metrics" data-testid="book-progress-counts">{[['Pages read',`${book.read_pages} / ${book.pages||'—'}`],['Detected',book.counts.detected,'detected'],['Complete',book.counts.complete,'complete'],['Held',book.counts.held,'held'],['Published',book.counts.published,'published'],['Scheduled',book.counts.scheduled,'scheduled']].map(([label,value,id])=><Metric key={label} label={label} value={value} id={id} filter={filter} onFilter={onFilter}/>)}</div><progress aria-label="Pages read" data-testid="book-reading-progress" value={book.read_pages} max={book.pages||1}/><p className="book-note" data-testid="book-scan-assessment">{book.scanned_pages} scanned/sparse pages found so far. Reading progress is measured, not estimated completion time. You can close this screen; reading continues.</p></>;
}

export default function BookPublishing(){
 const {user}=useAuth();const [params,setParams]=useSearchParams();const id=params.get('book');
 const [book,setBook]=useState(null),[section,setSection]=useState(null),[error,setError]=useState(''),[page,setPage]=useState(Number(params.get('page'))||null),[mock,setMock]=useState(params.get('mock')),[pageInput,setPageInput]=useState(1),[pageRows,setPageRows]=useState([]),[pageList,setPageList]=useState(1),[action,setAction]=useState(null),[reason,setReason]=useState(''),[busy,setBusy]=useState(false),[fixing,setFixing]=useState(params.get('fix'));
 const fixRef=useRef(null);const [filter,setFilter]=useState(null);
 const refresh=useCallback(async()=>{if(user?.role!=='owner')return;try{setError('');const b=await api(`/admin/books/${id}`);setBook(b);if(b.read_pages){const p=await api(`/admin/books/${id}/pages?page=${pageList}`);setPageRows(p.items);}if(b.destination&&!b.destination.series)setSection(await api(`/admin/catalog/sections/${b.destination.section_id}/tests`));}catch(e){setError(e.message);}},[id,user?.role,pageList]);
 useEffect(()=>{refresh();},[refresh]);
 // Asks again by itself only while the book is still being worked on; a finished book is not fetched every few seconds.
 const working=book&&(['uploading','received','reading','matching'].includes(book.state)||book.mocks?.some(m=>m.publish_requested&&m.state==='ready'));
 useEffect(()=>{if(!working)return;const timer=setInterval(refresh,8000);return()=>clearInterval(timer);},[refresh,working]);
 async function control(kind,mid='',note='',release=null,message=''){setBusy(true);setError('');try{await post(`/admin/books/${id}/control`,{revision:book.revision,action:kind,mock_id:mid,reason:note,...(release?{release_at:release}:{})});setAction(null);setReason('');invalidateCatalog();if(message)toast.success(message);if(kind==='remove')setParams({});else await refresh();}catch(e){setError(e.message);toast.error(e.message);}finally{setBusy(false);}}
 async function toggle(set,live){setBusy(true);try{const r=await patch('/admin/catalog/tests/'+set.id,{live});invalidateCatalog();toast.success(live?`${set.title} is live for students.`:`${set.title} is Unlive. Attempts and scores are kept.`);if(r.note)toast.message(r.note);await refresh();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 function fix(mid){setPage(null);setMock(null);setFixing(mid);setTimeout(()=>fixRef.current?.scrollIntoView({behavior:'smooth',block:'start'}),50);}
 function pick(key){setFilter(key);setPage(null);setMock(null);setFixing(null);if(key)setTimeout(()=>fixRef.current?.scrollIntoView({behavior:'smooth',block:'start'}),50);}
 if(user?.role!=='owner')return <div className="admin-page" data-testid="book-owner-denied"><h1>Owner access only</h1><p>Books and original answer sources are private.</p></div>;
 if(!book)return <div className="admin-page"><BookError error={error}/>{!error&&<p data-testid="book-loading">Loading book…</p>}</div>;
 const dest=book.destination,readingDone=book.pages>0&&book.read_pages===book.pages&&!['uploading','received','reading'].includes(book.state);
 const ruleExam=dest?(RULE_EXAMS.includes(dest.exam_key)?dest.exam_key:'Custom'):'';
 return <div className="admin-page book-workspace" data-testid="book-publishing-workspace">
  <AdminCrumbs items={[{label:'Master',to:'/super-admin'},...(dest?[{label:dest.exam_name,to:'/super-admin/exam/'+dest.exam_slug},{label:dest.section_name,to:`/super-admin/exam/${dest.exam_slug}/${dest.section_id}`}]:[]),{label:book.title}]}/>
  {dest?<DestinationChip large exam={dest.exam_name} section={dest.section_name} testId="book-destination"/>:<p className="admin-note warn" data-testid="book-no-destination">This older upload has no exam section. It publishes only through its original automatic setting.</p>}
  <BookError error={error}/>
  <BookProgress book={book} filter={filter} onFilter={pick}/>
  <div className="book-actions"><Button variant="outline" disabled={busy||book.state==='uploading'} data-testid="book-pause-resume" onClick={()=>control(book.paused?'resume':'pause')}>{book.paused?<Play size={15}/>:<Pause size={15}/>} {book.paused?'Resume processing':'Pause automatic work'}</Button><Button variant="outline" disabled={busy||book.state==='uploading'} onClick={()=>control('retry')} data-testid="book-retry">Retry saved work</Button><Button variant="outline" onClick={refresh} data-testid="book-refresh-detail"><RefreshCw size={15}/>Refresh</Button><Button variant="outline" onClick={()=>setAction({kind:'remove',mid:''})} data-testid="book-remove">Remove access</Button></div>
  {book.state==='uploading'&&<p className="book-note">Open this mock type in Master, press Upload PDF and choose this exact PDF again to resume the received parts.</p>}
  {action&&<section className="book-confirm" data-testid="book-control-confirm"><h2>{action.kind.replaceAll('_',' ')}</h2><p>{action.kind==='remove'?book.retention_notice:action.kind==='new_version'?'A new private version preserves previous attempts and scores. Automatic work pauses while you repair it.':'Record why this mock should change availability. A late release requires an explicit new decision.'}</p><BookField label="Reason" id="book-control-reason" value={reason} onChange={e=>setReason(e.target.value)}/><div className="book-actions"><Button disabled={busy||!reason.trim()} onClick={()=>control(action.kind,action.mid,reason)} data-testid="book-confirm-action">Confirm</Button><Button variant="outline" onClick={()=>setAction(null)} data-testid="book-cancel-action">Cancel</Button></div></section>}
  {dest?.series&&<p className="admin-note" data-testid="book-series-note">These are All India Test Series papers. <Link to={`/super-admin/exam/${dest.exam_slug}/${dest.section_id}`}>Give each one a day in its series.</Link></p>}
  {dest&&!dest.series&&<StudentPreview book={book} section={section} busy={busy} onFix={fix} onRefresh={refresh}
    onPublish={release=>control('publish_ready','','',release,release?'Ready mocks are scheduled. They open at the chosen time.':'Publishing ready mocks now. They appear to students in a moment.')}
    onRequest={m=>control('publish_ready',m.id,'',null,`${m.label} is being published.`)}
    onToggle={toggle}/>}
  <div ref={fixRef} className="admin-fix-area" data-testid="book-fix-area"><h2 className="admin-fix-title">Review & fix</h2>
   {fixing?<HeldFixer key={fixing} bookId={id} mockId={fixing} onClose={()=>setFixing(null)} onOpenPage={n=>{setFixing(null);setPage(n);}} onOpenRules={()=>{setMock(fixing);setFixing(null);}} onSaved={refresh}/>:page?<BookReview key={`${id}-${page}`} bookId={id} number={page} onSaved={refresh} onClose={()=>setPage(null)}/>:mock?<BookMockDesk key={mock} bookId={id} mockId={mock} ruleExam={ruleExam} onSaved={refresh} onClose={()=>setMock(null)}/>:<BookMap book={book} onMock={setMock} onPage={setPage} onFix={fix} onAction={(kind,mid)=>setAction({kind,mid})} filter={filter} onClear={()=>setFilter(null)}/>}
   <section className="book-pages"><BookRangeMapping book={book} onSaved={refresh}/><div className="book-section-heading"><h2>Source pages & attention queue</h2><div className="book-actions"><BookField label="Open page" id="book-open-page-number" type="number" min={1} max={book.read_pages||1} value={pageInput} onChange={e=>setPageInput(Number(e.target.value))}/><Button disabled={pageInput<1||pageInput>book.read_pages} onClick={()=>{setMock(null);setFixing(null);setPage(pageInput);}} data-testid="book-open-page">Review page</Button></div></div><div className="book-page-list">{pageRows.map(p=><button key={p.id} onClick={()=>{setMock(null);setFixing(null);setPage(p.number);}} data-testid={`book-page-${p.number}`} className={p.issues.length?'has-issues':''}><strong>Page {p.number}</strong><span>{p.classification.replaceAll('_',' ')}</span><small>{p.issues.length?`${p.issues.length} issue(s)`:`${p.region_count} regions`}</small></button>)}</div><div className="book-actions"><Button variant="outline" disabled={pageList===1} onClick={()=>setPageList(v=>v-1)} data-testid="book-pages-prev">Previous pages</Button><span data-testid="book-page-pagination">{pageList} / {Math.max(1,Math.ceil(book.pages/25))}</span><Button variant="outline" disabled={pageList*25>=book.read_pages} onClick={()=>setPageList(v=>v+1)} data-testid="book-pages-next">Next pages</Button></div></section>
   <section className="book-quality" data-testid="book-quality-report"><h2>Quality & provenance</h2><p>Automatically read: {book.metrics.native_pages||0} pages · manually repaired: {book.metrics.manually_repaired_pages||0} · AI proposals: {book.metrics.ai_proposed_pages||0}</p><p>Blocking issues: {book.metrics.blocking_issues||0}. Zero unresolved blockers is a publication rule, not a guarantee that detection never misses an error.</p>{book.metrics.first_ready_seconds!=null&&<p>Measured time to first ready publication: {Math.round(book.metrics.first_ready_seconds)} seconds</p>}<p className="book-note">{book.retention_notice}</p></section>
  </div>
 </div>;
}
