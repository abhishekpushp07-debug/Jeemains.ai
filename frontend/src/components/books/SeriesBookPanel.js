import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {CalendarDays,Wrench,X} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Button} from '../ui/button';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {StatusChip} from '../admin/AdminShared';
import {BookError} from './BookShared';
import {toast} from 'sonner';

const label=s=>`Day ${s.day} · ${new Date(s.date+'T00:00:00').toLocaleDateString('en-IN',{day:'numeric',month:'short'})}`;

function MockDay({m,data,busy,onGive,onRemove,onFix}){
 const slot=data.slots.find(s=>s.date===m.series_date);
 const free=data.slots.filter(s=>s.state==='upcoming'&&!s.set_id&&!s.pending);
 const can=m.state==='ready'&&!m.series_date&&!m.problem;
 return <li className={'admin-row'+(m.state==='held'?' is-held':'')} data-testid={'series-book-mock-'+m.id}>
  <div className="admin-row-main"><strong>{m.label}</strong>{m.state==='held'&&<p className="admin-reason">{m.issue}</p>}{m.problem&&<p className="admin-reason" data-testid={'series-book-problem-'+m.id}>{m.problem}</p>}</div>
  {slot?<StatusChip state={m.pending?'publishing':slot.state==='upcoming'?'scheduled':'live'} label={label(slot)+(m.pending?' · preparing':'')} testId={'series-book-day-'+m.id}/>:<StatusChip state={m.state} testId={'series-book-state-'+m.id}/>}
  <div className="admin-test-actions">
   {m.state==='held'&&<Button variant="outline" size="sm" onClick={()=>onFix(m.id)} data-testid={'series-book-fix-'+m.id}><Wrench size={15}/>Fix problems</Button>}
   {can&&<Select value="" onValueChange={day=>onGive(m,day)} disabled={busy}><SelectTrigger className="admin-move-select" aria-label={'Choose a day for '+m.label} data-testid={'series-book-pick-'+m.id}><SelectValue placeholder="Give it a day…"/></SelectTrigger><SelectContent>{free.map(s=><SelectItem key={s.date} value={s.date}>{label(s)}</SelectItem>)}</SelectContent></Select>}
   {slot&&slot.state==='upcoming'&&<Button variant="ghost" size="sm" disabled={busy} onClick={()=>onRemove(m)} data-testid={'series-book-remove-'+m.id}><X size={15}/>Remove day</Button>}
  </div>
 </li>;
}

export function SeriesBookPanel({book,onChanged,onFix}){
 const [data,setData]=useState(null),[error,setError]=useState(''),[start,setStart]=useState(''),[replace,setReplace]=useState(false),[busy,setBusy]=useState(false),[reload,setReload]=useState(0);
 useEffect(()=>{api('/studio/all-india-jee').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[reload,book.revision]);
 async function run(fn){setBusy(true);setError('');try{const r=await fn();if(r?.message)toast.success(r.message);(r?.left||[]).slice(0,5).forEach(x=>toast.message(`${x.label}: ${x.reason}`));setReload(n=>n+1);onChanged?.();}catch(e){setError(e.message);toast.error(e.message);}finally{setBusy(false);}}
 const give=(m,day)=>run(()=>m.set_id?post('/studio/all-india-jee/assign',{set_id:m.set_id,date:day,expected_revision:data.papers.find(p=>p.id===m.set_id)?.revision??0}).then(()=>({message:`${m.label} goes live on ${day}.`})):post('/studio/all-india-jee/assign',{set_id:m.id,date:day,expected_revision:0,kind:'book_mock'}).then(()=>({message:`${m.label} goes live on ${day}.`})));
 const remove=m=>run(()=>api(m.pending?'/studio/all-india-jee/book-mocks/'+m.id:'/studio/all-india-jee/'+m.set_id,{method:'DELETE'}).then(()=>({message:`${m.label} has no day now.`})));
 const mine=data?data.book_mocks.filter(m=>m.book_id===book.id):[];
 const upcoming=data?data.slots.filter(s=>s.state==='upcoming'):[];
 return <section className="admin-panel admin-preview" data-testid="series-book-panel">
  <span className="eyebrow"><CalendarDays size={15}/> ALL INDIA TEST SERIES · DAYS</span>
  <p className="admin-note">On its day, students can start a mock from 12:01 AM until 8:59 PM IST; afterwards it stays as practice. Days run 1 December – 31 January. Only mocks with 75 questions (20 MCQ + 5 numerical per subject), 180 minutes and +4/−1 marking can take a day.</p>
  <BookError error={error}/>
  {!data?<p data-testid="series-book-loading">Loading days…</p>:<>
   <div className="admin-publish-bar" data-testid="series-fill-bar">
    <div><strong>Fill days in printed order</strong><small>Mock 1 on the start day, the next mock the next free day, and so on.</small></div>
    <Select value={start} onValueChange={setStart}><SelectTrigger className="admin-move-select" aria-label="Start day" data-testid="series-fill-start"><SelectValue placeholder="Start day"/></SelectTrigger><SelectContent>{upcoming.map(s=><SelectItem key={s.date} value={s.date}>{label(s)}</SelectItem>)}</SelectContent></Select>
    <label className="book-check"><input type="checkbox" checked={replace} onChange={e=>setReplace(e.target.checked)} data-testid="series-fill-replace"/><span>Replace papers already on those days</span></label>
    <Button disabled={busy||!start} onClick={()=>run(()=>post('/studio/all-india-jee/fill',{book_id:book.id,start_date:start,replace}))} data-testid="series-fill-run">Fill days</Button>
   </div>
   <ul className="admin-list" data-testid="series-book-list">{mine.map(m=><MockDay key={m.id} m={m} data={data} busy={busy} onGive={give} onRemove={remove} onFix={onFix}/>)}{!mine.length&&<li className="admin-empty" data-testid="series-book-empty">Mocks appear here as soon as reading finds them.</li>}</ul>
   <Button asChild variant="outline"><Link to="/super-admin/schedule" data-testid="series-book-open-schedule"><CalendarDays size={16}/>See all 62 days</Link></Button>
  </>}
 </section>;
}
