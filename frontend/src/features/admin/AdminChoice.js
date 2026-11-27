// Super Admin › Student Choice: the two switches (both Off by default), the paper's limits and each subject's minutes,
// with today's numbers and the chapters students can choose from. The website follows within 15 s; the app within 2–4 minutes.
import React,{useEffect,useState} from 'react';
import {Loader2,Save} from 'lucide-react';
import {toast} from 'sonner';
import {api,put} from '../../lib/api';
import {usePageTitle} from '../../lib/pageMeta';
import {Switch} from '../../components/ui/switch';
import {ErrorBox} from '../../components/Shared';
import {SHORT,SUBJECTS,minutesFor} from '../../lib/choice';
import '../../choice.css';

const asForm=s=>({pick:s.pick,random:s.random,max_questions:String(s.max_questions),max_per_subject:s.max_per_subject==null?'':String(s.max_per_subject),
 daily_limit:String(s.daily_limit),...Object.fromEntries(SUBJECTS.map(x=>[x,String(s.minutes[x])]))});

function Num({label,value,onChange,testId,hint}){
 return <label className="ch-admin-field"><span>{label}</span><input inputMode="decimal" value={value} onChange={e=>onChange(e.target.value.replace(/[^0-9.]/g,'').slice(0,6))} data-testid={testId}/>{hint&&<small>{hint}</small>}</label>;
}

function Stats({s}){
 return <div className="ch-admin-stats" data-testid="admin-choice-stats">{[['today','Aaj ke papers'],['creators_today','Aaj banane wale'],['total','Sab papers'],['creators','Sab students'],['pick','Chune sawaal'],['random','Random mock'],['started','Shuru hue']].map(([k,l])=>
  <div key={k}><strong data-testid={'admin-choice-stat-'+k}>{s[k]}</strong><span>{l}</span></div>)}</div>;
}

export default function AdminChoice(){
 usePageTitle('Student Choice');
 const [d,setD]=useState(null),[f,setF]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[tick,setTick]=useState(0);
 useEffect(()=>{api('/admin/choice/jee-main').then(x=>{setD(x);setF(asForm(x.settings));}).catch(e=>setError(e.message));},[tick]);
 const set=(k,v)=>setF(x=>({...x,[k]:v}));
 async function save(){
  setBusy(true);setError('');
  try{
   const body={expected_revision:d.settings.revision,pick:f.pick,random:f.random,max_questions:parseInt(f.max_questions,10)||0,max_per_subject:f.max_per_subject===''?null:parseInt(f.max_per_subject,10)||0,
    daily_limit:parseInt(f.daily_limit,10)||0,minutes_per_question:Object.fromEntries(SUBJECTS.map(x=>[x,Number(f[x])||0]))};
   const r=await put('/admin/choice/jee-main',body);toast.success(r.message);setTick(v=>v+1);
  }catch(e){setError(e.message);}finally{setBusy(false);}
 }
 if(!d||!f)return <div className="ch-admin" data-testid="admin-choice-page"><ErrorBox error={error} retry={()=>setTick(v=>v+1)}/>{!error&&<p className="ch-muted"><Loader2 size={15} className="spin"/>Loading…</p>}</div>;
 const per=Object.fromEntries(SUBJECTS.map(x=>[x,Number(f[x])||0]));
 return <div className="ch-admin" data-testid="admin-choice-page">
  <header><span className="ch-kicker dark">JEE MAIN</span><h1>Student Choice</h1><p className="ch-muted">Students make their own paper from the live JEE Main chapter-wise questions. Both Off = website and app work exactly as before.</p></header>
  <Stats s={d.stats}/>
  <section className="ch-card ch-admin-form">
   <div className="ch-admin-switch"><Switch checked={f.pick} onCheckedChange={v=>set('pick',v)} id="choice-pick" data-testid="admin-choice-pick-switch"/><label htmlFor="choice-pick"><b>Sawaal khud chunna</b><small>Chapters, then questions (shown without options), one paper of them.</small></label></div>
   <div className="ch-admin-switch"><Switch checked={f.random} onCheckedChange={v=>set('random',v)} id="choice-random" data-testid="admin-choice-random-switch"/><label htmlFor="choice-random"><b>Random mock</b><small>The student gives only a count; questions are drawn equally over the subjects.</small></label></div>
   <div className="ch-admin-grid">
    <Num label="Most questions in a paper" value={f.max_questions} onChange={v=>set('max_questions',v)} testId="admin-choice-max" hint="1 to 75"/>
    <Num label="Top per subject" value={f.max_per_subject} onChange={v=>set('max_per_subject',v)} testId="admin-choice-per-subject" hint="Empty = no top"/>
    <Num label="Papers a student may make a day" value={f.daily_limit} onChange={v=>set('daily_limit',v)} testId="admin-choice-daily" hint="Counted per IST day"/>
    {SUBJECTS.map(x=><Num key={x} label={`${SHORT[x]}: minutes a question`} value={f[x]} onChange={v=>set(x,v)} testId={'admin-choice-minutes-'+x.toLowerCase()}/>)}
   </div>
   <p className="ch-muted" data-testid="admin-choice-preview">With these minutes: 25 + 25 + 25 = {minutesFor({Physics:25,Chemistry:25,Mathematics:25},per)} min · 3 + 2 + 2 = {minutesFor({Physics:3,Chemistry:2,Mathematics:2},per)} min · 25 Maths = {minutesFor({Physics:0,Chemistry:0,Mathematics:25},per)} min.</p>
   <ErrorBox error={error}/>
   <button type="button" className="ch-btn" disabled={busy} onClick={save} data-testid="admin-choice-save">{busy?<Loader2 size={16} className="spin"/>:<Save size={16}/>}Save</button>
   <small className="ch-muted" data-testid="admin-choice-revision">Revision {d.settings.revision}{d.settings.updated_at?` · saved ${new Date(d.settings.updated_at*1000).toLocaleString('en-IN')}`:''}</small>
  </section>
  <section className="ch-card"><h2 className="ch-h2">Chapters students can choose from</h2><p className="ch-muted">Only live JEE Main chapter-wise tests appear; dropped and bonus questions are left out.</p>
   <div className="ch-admin-pool" data-testid="admin-choice-pool">{d.pool.map(s=><div key={s.name}><h3>{SHORT[s.name]} · {s.chapters.length} chapters · {s.chapters.reduce((n,c)=>n+c.count,0)} sawaal</h3>
    <ul>{s.chapters.map(c=><li key={c.id} data-testid={'admin-choice-chapter-'+c.id}><span>{c.number?c.number+'. ':''}{c.title}</span><small>{c.mcq} MCQ · {c.integer} num</small></li>)}</ul></div>)}</div>
  </section>
 </div>;
}
