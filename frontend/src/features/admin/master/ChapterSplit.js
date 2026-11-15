import React,{useEffect,useRef,useState} from 'react';
import {useParams} from 'react-router-dom';
import {Loader2,Save,Plus,Trash2,RotateCcw,Flag,X,ListOrdered} from 'lucide-react';
import {api,put,fetchWithSession} from '../../../lib/api';
import {toast} from 'sonner';
import {Button} from '../../../components/ui/button';
import {Input} from '../../../components/ui/input';
import {Skeleton} from '../../../components/ui/skeleton';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../../../components/ui/select';
import {ErrorBox} from '../../../components/Shared';
import {AdminHeading,StatusChip,ConfirmDialog} from '../../../components/admin/AdminShared';
import {MasterCrumbs,plural} from '../../../components/master/MasterShared';

const ROLE={question:'Questions',key:'Answer key',solution:'Solutions'};
const CHIP={live:['live','Live'],library:['archived','In Library'],ready:['ready','Draft · ready'],held:['held','Draft · to fix']};

// Page pictures are rendered on the server one by one, so at most three load at a time and a busy reply is retried.
const queue={active:0,waiting:[]};
const slot=()=>new Promise(go=>{if(queue.active<3){queue.active++;go();}else queue.waiting.push(go);});
const free=()=>{const next=queue.waiting.shift();if(next)next();else queue.active--;};
async function loadPage(path,signal){
 await slot();
 try{for(let tries=0;;tries++){
  const r=await fetchWithSession(path,{signal});
  if(r.ok)return URL.createObjectURL(await r.blob());
  if(r.status!==503||tries>=4)throw new Error('Page picture unavailable. Reload to retry.');
  await new Promise(done=>setTimeout(done,1500*(tries+1)));
 }}finally{free();}
}

function PageImage({path,alt,testId}){
 const [url,setUrl]=useState(''),[error,setError]=useState('');
 useEffect(()=>{const c=new AbortController();let made='';
  loadPage(path,c.signal).then(u=>{made=u;if(!c.signal.aborted)setUrl(u);}).catch(e=>{if(e.name!=='AbortError')setError(e.message);});
  return()=>{c.abort();if(made)URL.revokeObjectURL(made);};
 },[path]);
 return error?<p role="alert" data-testid={testId+'-error'}>{error}</p>:url?<img src={url} alt={alt} data-testid={testId}/>:<p data-testid={testId+'-loading'}>Loading page…</p>;
}

function SubjectPick({value,subjects,onChange,disabled,testId}){
 return <Select value={value||'none'} onValueChange={v=>onChange(v==='none'?'':v)} disabled={disabled}>
  <SelectTrigger className="chapter-subject" data-testid={testId} aria-label="Subject"><SelectValue/></SelectTrigger>
  <SelectContent><SelectItem value="none">Not sure yet</SelectItem>{subjects.map(s=><SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
 </Select>;
}

function pagesText(c){
 return [c.question_page&&`Questions p.${c.question_page}`,c.key_page&&`Key p.${c.key_page}`,c.solution_page&&`Solutions p.${c.solution_page}`].filter(Boolean).join(' · ');
}

function ChapterRow({c,row,subjects,onChange}){
 const locked=c.state==='live'||c.state==='library',[tone,label]=CHIP[c.state]||['held','Draft'];
 return <li className="chapter-row" data-testid={'chapter-row-'+c.number}>
  <span className="admin-test-index" aria-hidden="true">{String(c.number).padStart(2,'0')}</span>
  <div className="chapter-row-main">
   <Input value={row.title} maxLength={120} disabled={locked} onChange={e=>onChange({...row,title:e.target.value})} aria-label={'Name of chapter '+c.number} data-testid={'chapter-title-'+c.number}/>
   <small>{[pagesText(c),plural(c.count,'question'),c.subject_from&&row.subject===c.subject?'Subject: '+c.subject_from.toLowerCase():null].filter(Boolean).join(' · ')}</small>
  </div>
  <SubjectPick value={row.subject} subjects={subjects} disabled={locked} onChange={subject=>onChange({...row,subject})} testId={'chapter-subject-'+c.number}/>
  <StatusChip state={tone} label={c.to_fix&&!locked?`Draft · ${c.to_fix} to fix`:label} testId={'chapter-state-'+c.number}/>
 </li>;
}

function ChapterTable({data,onSaved}){
 const fresh=()=>data.chapters.map(c=>({label:c.label,title:c.title,subject:c.subject}));
 const [rows,setRows]=useState(fresh),[busy,setBusy]=useState(false);
 useEffect(()=>{setRows(data.chapters.map(c=>({label:c.label,title:c.title,subject:c.subject})));},[data.chapters]);
 if(!data.chapters.length)return <section className="admin-panel admin-empty" data-testid="chapter-table-empty"><p>{data.reading?'Reading the pages… chapters appear here by themselves.':'No chapter tests yet.'}</p></section>;
 const changed=rows.filter((r,i)=>data.chapters[i]&&(r.title.trim()!==data.chapters[i].title||r.subject!==data.chapters[i].subject));
 const unsure=data.chapters.filter(c=>!c.subject&&c.state!=='live').length;
 async function save(){setBusy(true);try{const r=await put(`/admin/master/chapters/${data.id}/details`,{items:changed.map(r=>({...r,title:r.title.trim()}))});toast.success(r.message);onSaved();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <section className="admin-panel" data-testid="chapter-table">
  <div className="admin-panel-head"><h2>{plural(data.chapters.length,'chapter test')}</h2><small>Names and subjects are what students see.</small></div>
  {unsure>0&&<p className="admin-note warn" data-testid="chapter-subject-ask">The PDF did not make the subject clear for {plural(unsure,'chapter')}. Choose it below; those chapters cannot go Live until you do.</p>}
  <ol className="chapter-rows" data-testid="chapter-rows">{data.chapters.map((c,i)=>rows[i]&&<ChapterRow key={c.id} c={c} row={rows[i]} subjects={data.subjects} onChange={r=>setRows(all=>all.map((x,j)=>j===i?r:x))}/>)}</ol>
  <div className="button-row"><Button disabled={!changed.length||busy||changed.some(r=>r.title.trim().length<2)} onClick={save} data-testid="chapter-details-save">{busy?<Loader2 size={16} className="spin"/>:<Save size={16}/>}Save {changed.length?plural(changed.length,'change'):'changes'}</Button></div>
 </section>;
}

function MarkForm({page,chapters,starts,restart,onMark,onClear,onClose}){
 const before=starts.filter(s=>s.role==='question'&&s.page<=page).sort((a,b)=>b.page-a.page)[0];
 const fresh=restart||!before;
 const [chapter,setChapter]=useState(fresh?'new':String(before.chapter)),[role,setRole]=useState(fresh?'question':'key');const box=useRef(null);
 useEffect(()=>{box.current?.scrollIntoView({block:'nearest',behavior:'smooth'});},[]);
 useEffect(()=>{if(role==='question')setChapter(c=>c===(before?String(before.chapter):'')?'new':c);},[role]);// eslint-disable-line react-hooks/exhaustive-deps
 return <div className="chapter-mark-form" ref={box} data-testid={'chapter-mark-form-'+page}>
  <div className="chapter-mark-head"><strong>Page {page} starts…</strong><Button size="icon" variant="ghost" onClick={onClose} aria-label="Close" data-testid="chapter-mark-close"><X size={15}/></Button></div>
  <div className="chapter-role-pick" role="radiogroup" aria-label="What starts on this page">{Object.entries(ROLE).map(([k,v])=><button type="button" key={k} role="radio" aria-checked={role===k} className={role===k?'is-on':''} onClick={()=>setRole(k)} data-testid={'chapter-mark-role-'+k}>{v}</button>)}</div>
  <Select value={chapter} onValueChange={setChapter}><SelectTrigger data-testid="chapter-mark-chapter" aria-label="Of which chapter"><SelectValue/></SelectTrigger><SelectContent>
   <SelectItem value="new">A new chapter</SelectItem>{chapters.map((c,i)=><SelectItem key={i} value={String(i)}>{i+1}. {c.title||'Unnamed chapter'}</SelectItem>)}
  </SelectContent></Select>
  <div className="button-row"><Button size="sm" onClick={()=>onMark(page,chapter==='new'?'new':Number(chapter),role)} data-testid="chapter-mark-save"><Flag size={14}/>Mark</Button>{starts.some(s=>s.page===page)&&<Button size="sm" variant="ghost" onClick={()=>onClear(page)} data-testid="chapter-mark-clear">Clear this page</Button>}</div>
 </div>;
}

function PageCard({id,n,marks,chapters,restart,open,onOpen,children}){
 return <li className={'chapter-page'+(marks.length?' is-marked':'')+(open?' is-open':'')} data-testid={'chapter-page-'+n}>
  <button type="button" className="chapter-page-shot" onClick={onOpen} aria-label={'Mark what starts on page '+n} data-testid={'chapter-page-open-'+n}>
   <PageImage path={`/admin/master/chapters/${id}/asset/page/${n}`} alt={'Page '+n} testId={'chapter-page-img-'+n}/>
  </button>
  <div className="chapter-page-foot"><strong>Page {n}</strong>{restart&&<small className="chapter-hint" title="Question 1 is printed on this page">Q1 here</small>}</div>
  {marks.map(m=><span key={m.role+m.chapter} className={'chapter-page-tag role-'+m.role} data-testid={`chapter-page-tag-${n}-${m.role}`}>{m.chapter+1}. {chapters[m.chapter]?.title||'New chapter'} · {ROLE[m.role]}</span>)}
  {children}
 </li>;
}

function PlanChapters({chapters,starts,subjects,onChange,onRemove,onAdd}){
 return <div className="chapter-plan-list" data-testid="chapter-plan-list"><h3><ListOrdered size={16}/>Chapters</h3>
  <ol>{chapters.map((c,i)=>{const q=starts.find(s=>s.chapter===i&&s.role==='question');return <li key={i} data-testid={'chapter-plan-'+i}>
   <span className="admin-test-index" aria-hidden="true">{String(i+1).padStart(2,'0')}</span>
   <div className="chapter-plan-fields"><Input value={c.title} maxLength={120} placeholder="Chapter name" onChange={e=>onChange(i,{...c,title:e.target.value})} aria-label={'Name of chapter '+(i+1)} data-testid={'chapter-plan-title-'+i}/>
    <SubjectPick value={c.subject} subjects={subjects} onChange={subject=>onChange(i,{...c,subject})} testId={'chapter-plan-subject-'+i}/>
    <small className={q?'':'warn'}>{q?`Questions start on page ${q.page}`:'Mark the page where its questions start'}</small></div>
   <Button size="icon" variant="ghost" onClick={()=>onRemove(i)} aria-label={'Remove chapter '+(i+1)} data-testid={'chapter-plan-remove-'+i}><Trash2 size={15}/></Button>
  </li>;})}</ol>
  <Button size="sm" variant="outline" onClick={onAdd} data-testid="chapter-plan-add"><Plus size={15}/>Add chapter</Button>
 </div>;
}

function StartMarker({data,onDone,onCancel}){
 const [chapters,setChapters]=useState(()=>data.draft.chapters.length?data.draft.chapters:[]);
 const [starts,setStarts]=useState(data.draft.starts),[open,setOpen]=useState(null),[shown,setShown]=useState(24),[busy,setBusy]=useState(false);
 const restarts=new Set(data.restarts),blank={title:'',subject:data.subject_mode||''};
 function mark(page,chapter,role){
  const idx=chapter==='new'?chapters.length:chapter;
  if(chapter==='new')setChapters(c=>[...c,{...blank}]);
  setStarts(s=>[...s.filter(x=>!(x.page===page&&x.role===role)&&!(x.chapter===idx&&x.role===role)),{page,chapter:idx,role}].sort((a,b)=>a.page-b.page||a.chapter-b.chapter));setOpen(null);
 }
 function remove(i){setChapters(c=>c.filter((_,j)=>j!==i));setStarts(s=>s.filter(x=>x.chapter!==i).map(x=>x.chapter>i?{...x,chapter:x.chapter-1}:x));}
 const problem=!chapters.length?'Mark the first page of each chapter.':chapters.findIndex(c=>c.title.trim().length<2)>=0?'Give every chapter a name.':chapters.findIndex((_,i)=>!starts.some(s=>s.chapter===i&&s.role==='question'))>=0?'Every chapter needs the page where its questions start.':'';
 async function save(){setBusy(true);try{const r=await put(`/admin/master/chapters/${data.id}/starts`,{chapters:chapters.map(c=>({title:c.title.trim(),subject:c.subject})),starts});toast.success(r.message);onDone();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 const pages=Array.from({length:Math.min(shown,data.pages)},(_,i)=>i+1);
 return <section className="admin-panel chapter-marker" data-testid="chapter-marker">
  <div className="admin-panel-head"><h2>Where chapters start</h2><small>Tap a page to mark it. Pages with “Q1 here” are where a question 1 is printed, usually a new chapter.</small></div>
  <div className="chapter-marker-body">
   <PlanChapters chapters={chapters} starts={starts} subjects={data.subjects} onChange={(i,c)=>setChapters(all=>all.map((x,j)=>j===i?c:x))} onRemove={remove} onAdd={()=>setChapters(c=>[...c,{...blank}])}/>
   <div className="chapter-pages-wrap">
    <ol className="chapter-pages" data-testid="chapter-pages">{pages.map(n=><PageCard key={n} id={data.id} n={n} marks={starts.filter(s=>s.page===n)} chapters={chapters} restart={restarts.has(n)} open={open===n} onOpen={()=>setOpen(open===n?null:n)}>
     {open===n&&<MarkForm page={n} chapters={chapters} starts={starts} restart={restarts.has(n)} onMark={mark} onClear={p=>{setStarts(s=>s.filter(x=>x.page!==p));setOpen(null);}} onClose={()=>setOpen(null)}/>}
    </PageCard>)}</ol>
    {shown<data.pages&&<Button variant="outline" onClick={()=>setShown(s=>s+24)} data-testid="chapter-pages-more">Show more pages ({data.pages-shown} left)</Button>}
   </div>
  </div>
  <div className="chapter-marker-bar">{problem?<small className="warn" data-testid="chapter-marker-problem">{problem}</small>:<small data-testid="chapter-marker-ready">{plural(chapters.length,'chapter')} ready to read.</small>}
   <div className="button-row">{onCancel&&<Button variant="outline" onClick={onCancel} data-testid="chapter-marker-cancel">Cancel</Button>}<Button disabled={!!problem||busy} onClick={save} data-testid="chapter-marker-save">{busy?<Loader2 size={16} className="spin"/>:<Save size={16}/>}Read these chapters</Button></div></div>
 </section>;
}

export default function ChapterSplit(){
 const {id}=useParams();
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[marking,setMarking]=useState(false),[asking,setAsking]=useState(false);
 useEffect(()=>{api('/admin/master/chapters/'+id).then(d=>{setData(d);setError('');if(d.state==='chapters_needed')setMarking(true);}).catch(e=>setError(e.message));},[id,reload]);
 const reading=data?.reading;
 useEffect(()=>{if(!reading)return;const t=setInterval(()=>setReload(n=>n+1),4000);return()=>clearInterval(t);},[reading]);
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!data)return <Skeleton className="h-64"/>;
 const refresh=()=>{setMarking(false);setReload(n=>n+1);};
 async function useHeadings(){setAsking(false);try{const r=await api(`/admin/master/chapters/${id}/starts`,{method:'DELETE'});toast.success(r.message);refresh();}catch(e){toast.error(e.message);}}
 const how=data.plan_source==='owner'?'Split by the pages you marked.':data.plan_source==='bookmarks'?'Split by the PDF’s own bookmarks.':'Split by the chapter headings printed in the PDF.';
 return <div className="admin-page master-page" data-testid="chapter-split-page">
  <MasterCrumbs exam={data.exam} type={{id:data.section.id,name:data.section.name}} last="Chapters"/>
  <AdminHeading testId="chapter-split-title" title={data.title} text={data.state==='chapters_needed'?'Chapter headings were not found in this PDF. Mark where each chapter starts and it is split by itself.':`${how} Each chapter is its own Draft test.`}
   action={!marking&&!data.reading&&<div className="admin-actions">{!data.locked&&<Button variant="outline" onClick={()=>setMarking(true)} data-testid="chapter-change-starts"><Flag size={16}/>Change where chapters start</Button>}{data.plan_source&&data.plan_source!=='headings'&&!data.locked&&<Button variant="ghost" onClick={()=>setAsking(true)} data-testid="chapter-use-headings"><RotateCcw size={16}/>Read the PDF by itself again</Button>}</div>}/>
  {data.reading&&<div className="admin-progress" role="status" data-testid="chapter-reading"><progress value={data.read_pages} max={data.pages||1}/><small><Loader2 size={13} className="spin"/> {data.message}</small></div>}
  {data.locked&&!marking&&<p className="admin-note" data-testid="chapter-locked-note">Some chapters are Live, so the split is fixed. You can still rename chapters that are not Live.</p>}
  {marking?<StartMarker data={data} onDone={refresh} onCancel={data.state==='chapters_needed'?null:()=>setMarking(false)}/>:<ChapterTable data={data} onSaved={()=>setReload(n=>n+1)}/>}
  <ConfirmDialog open={asking} onClose={()=>setAsking(false)} testId="chapter-use-headings-confirm" title="Read the PDF by itself again?" text="The pages you marked, and the chapter names and subjects you gave, are cleared. Draft chapter tests from this PDF are made again from the printed headings or bookmarks. If none are found, you mark the pages again." button="Read again" onConfirm={useHeadings}/>
 </div>;
}
