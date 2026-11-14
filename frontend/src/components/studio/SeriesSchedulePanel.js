import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {CalendarDays,UploadCloud} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Button} from '../ui/button';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '../ui/select';
import {ErrorBox,Loading} from '../Shared';
import {ConfirmDialog} from '../admin/AdminShared';
import {toast} from 'sonner';

const KIND={private_import:'Private import · ',book_mock:'Book · '};

function AssignForm({data,busy,run}){
 const [paper,setPaper]=useState(''),[day,setDay]=useState(''),[replace,setReplace]=useState(false);
 const p=data.papers.find(x=>x.id===paper);
 const save=()=>run(()=>post('/studio/all-india-jee/assign',{set_id:paper,date:day,expected_revision:p.revision,kind:p.kind,replace}),p.kind==='book_mock'?'Day given. The paper is built privately and opens on its day.':'Series date assigned. The paper unlocks at its scheduled time.').then(ok=>{if(ok){setPaper('');setDay('');}});
 return <><div className="series-assign-form"><div><label htmlFor="series-paper">Paper or book mock</label><Select value={paper} onValueChange={setPaper}><SelectTrigger id="series-paper" data-testid="series-paper-select"><SelectValue placeholder="Choose a compatible paper"/></SelectTrigger><SelectContent>{data.papers.map(x=><SelectItem value={x.id} key={x.id} data-testid={'series-paper-'+x.id}>{KIND[x.kind]||''}{x.title}{x.series_date?' · '+x.series_date:''}</SelectItem>)}</SelectContent></Select></div>
  <div><label htmlFor="series-date">Series day (IST)</label><Select value={day} onValueChange={setDay}><SelectTrigger id="series-date" data-testid="series-date-select"><SelectValue placeholder="Choose a future day"/></SelectTrigger><SelectContent>{data.slots.filter(s=>s.state==='upcoming').map(s=>{const used=(s.set_id&&s.set_id!==paper)||s.pending;return <SelectItem value={s.date} key={s.date} disabled={!replace&&!!used} data-testid={'series-date-'+s.date}>Day {s.day} · {s.date}{used?' · Assigned':''}</SelectItem>;})}</SelectContent></Select></div>
  <Button data-testid="series-assign-save" disabled={!paper||!day||busy} onClick={save}>{busy?'Saving…':'Assign paper'}</Button></div>
  <label className="book-check"><input type="checkbox" checked={replace} onChange={e=>{setReplace(e.target.checked);setDay('');}} data-testid="series-assign-replace"/><span>Replace the paper already on that day (it goes back to unassigned, nothing is deleted)</span></label></>;
}

function FillForm({data,busy,run}){
 const [book,setBook]=useState(''),[start,setStart]=useState(''),[replace,setReplace]=useState(false);
 if(!data.books.length)return null;
 return <div className="series-fill" data-testid="series-fill-form"><h3>Auto-fill days from a book</h3><p>Ready mocks take free days in printed order, starting from the day you choose.</p><div className="series-assign-form">
  <div><label htmlFor="series-fill-book">Book</label><Select value={book} onValueChange={setBook}><SelectTrigger id="series-fill-book" data-testid="series-fill-book"><SelectValue placeholder="Choose a book"/></SelectTrigger><SelectContent>{data.books.map(b=><SelectItem value={b.id} key={b.id}>{b.title}</SelectItem>)}</SelectContent></Select></div>
  <div><label htmlFor="series-fill-day">Start day</label><Select value={start} onValueChange={setStart}><SelectTrigger id="series-fill-day" data-testid="series-fill-day"><SelectValue placeholder="First day"/></SelectTrigger><SelectContent>{data.slots.filter(s=>s.state==='upcoming').map(s=><SelectItem value={s.date} key={s.date}>Day {s.day} · {s.date}</SelectItem>)}</SelectContent></Select></div>
  <Button disabled={!book||!start||busy} onClick={()=>run(()=>post('/studio/all-india-jee/fill',{book_id:book,start_date:start,replace}))} data-testid="series-fill-save">Fill days</Button></div>
  <label className="book-check"><input type="checkbox" checked={replace} onChange={e=>setReplace(e.target.checked)} data-testid="series-fill-replace-all"/><span>Replace papers already on those days</span></label></div>;
}

export const SeriesSchedulePanel=()=>{
 const [data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[refresh,setRefresh]=useState(0),[confirm,setConfirm]=useState(false);
 useEffect(()=>{const c=new AbortController();api('/studio/all-india-jee',{signal:c.signal}).then(d=>{setData(d);setError('');}).catch(e=>{if(!c.signal.aborted)setError(e.message);});return()=>c.abort();},[refresh]);
 async function run(fn,message){setBusy(true);setError('');try{const r=await fn();toast.success(r?.message||message);(r?.left||[]).slice(0,5).forEach(x=>toast.message(`${x.label}: ${x.reason}`));setRefresh(v=>v+1);return true;}catch(e){setError(e.message);return false;}finally{setBusy(false);}}
 const toggle=slot=>run(()=>post('/studio/imports/'+slot.set_id+'/live',{live:!slot.live_enabled,revision:slot.revision}),slot.live_enabled?'New starts paused; active attempts are unchanged.':'Series paper enabled.');
 const remove=slot=>run(()=>api(slot.pending?'/studio/all-india-jee/book-mocks/'+slot.pending.mock_id:'/studio/all-india-jee/'+slot.set_id,{method:'DELETE'}),'Future assignment removed. Paper content is unchanged.');
 const filled=data?data.slots.filter(s=>s.set_id||s.pending):[];
 return <section className="import-card series-studio" data-testid="series-studio-panel"><header><span className="eyebrow"><CalendarDays size={16}/>ALL INDIA TEST SERIES · OWNER SCHEDULE</span><h2 data-testid="series-studio-title">Your papers. 62 daily challenges.</h2><p data-testid="series-studio-instructions">Upload a book of full mocks or one paper with Upload › Add content › JEE Main › All India Test Series. Give each ready paper a day here, one by one, or auto-fill a whole book in printed order. Nothing shows to students before its day. No AI is used.</p><Button asChild variant="outline"><Link to="/super-admin/upload/new?exam=jee-main&section=jee-main:aits" data-testid="series-upload-link"><UploadCloud size={16}/>Upload a book or paper</Link></Button></header><ErrorBox error={error} retry={()=>setRefresh(v=>v+1)}/>{!data&&!error&&<Loading/>}{data&&<>
  <AssignForm data={data} busy={busy} run={run}/>
  {!data.papers.length&&<p className="series-timing-note" data-testid="series-no-papers">No compatible ready papers yet. Required: 20 MCQ + 5 numerical questions in each of Physics, Chemistry and Mathematics, 180 minutes, +4/−1/0.</p>}
  <FillForm data={data} busy={busy} run={run}/>
  <details><summary data-testid="series-assigned-toggle">Assigned papers ({filled.length} / 62)</summary>{filled.map(s=><div className="series-assigned-row" key={s.date} data-testid={'series-assigned-'+s.date}><div><strong>Day {s.day} · {s.date}</strong><p>{s.pending?`${s.pending.title} · being built privately`:`${s.title} · ${s.publication_status}`}</p></div>{s.series_import&&<Button variant="outline" data-testid={'series-toggle-'+s.date} disabled={busy} onClick={()=>toggle(s)}>{s.live_enabled?'Pause new starts':'Enable paper'}</Button>}{s.state==='upcoming'&&<Button variant="outline" data-testid={'series-unassign-'+s.date} disabled={busy} onClick={()=>remove(s)}>Remove assignment</Button>}</div>)}</details>
  {filled.some(s=>s.state==='upcoming')&&<Button variant="outline" disabled={busy} onClick={()=>setConfirm(true)} data-testid="series-clear-future">Clear all future days</Button>}
  <p className="import-fineprint" data-testid="series-owner-limitations">Series papers stay hidden until their day opens and remain as practice afterward. Removing a future day makes its paper private again; content is preserved. Days that have opened never change, so every student's score stays as it was.</p></>}
  <ConfirmDialog open={confirm} onClose={()=>setConfirm(false)} busy={busy} testId="series-clear-confirm" title="Clear all future days?" text="Every day that has not opened yet becomes empty. The papers stay private and can be given days again. Opened days and scores are not touched." button="Clear future days" onConfirm={()=>run(()=>post('/studio/all-india-jee/clear',{book_id:''})).then(()=>setConfirm(false))}/>
 </section>;
};
