import React,{useEffect,useState} from 'react';
import {Link,useNavigate} from 'react-router-dom';
import {Plus,ArrowUpRight,Wrench,CheckCircle2,MessageSquareWarning,ShieldAlert,Loader2} from 'lucide-react';
import {api} from '../../../lib/api';
import {useAuth} from '../../../lib/auth';
import {Button} from '../../../components/ui/button';
import {Skeleton} from '../../../components/ui/skeleton';
import {ErrorBox} from '../../../components/Shared';
import {AdminHeading,StatusChip,ExamDialog} from '../../../components/admin/AdminShared';
import {KIND_LABEL} from '../../../components/master/MasterShared';
import {FixItems} from './FixList';
import {QuestionReportsPanel} from '../../../components/studio/QuestionReportsPanel';
import {StorageAlert} from '../../../components/master/StorageBadge';

export function AttentionLine(){
 const [s,setS]=useState(null);
 useEffect(()=>{api('/admin/master/summary').then(setS).catch(()=>setS(null));},[]);
 if(!s)return <div className="master-attention is-loading" data-testid="master-attention"><Skeleton className="h-6 w-80"/></div>;
 const parts=[[Wrench,s.to_fix,`${s.to_fix} mock fix karne hain`,'/super-admin/fix','attention','attention-fix'],[CheckCircle2,s.ready,`${s.ready} Live ke liye taiyaar`,'/super-admin/fix?tab=ready','ready','attention-ready'],[MessageSquareWarning,s.reports,`${s.reports} student report`,'/super-admin/reports','reports','attention-reports']];
 return <div className="master-attention" data-testid="master-attention"><span className="master-attention-label">Aaj</span>{parts.map(([Icon,n,label,to,tone,id])=><Link key={id} to={to} className={'master-attention-item tone-'+(n?tone:'quiet')} data-testid={'master-'+id}><Icon size={15} aria-hidden="true"/><strong>{label}</strong></Link>)}
  {(s.rereading||[]).slice(0,3).map(r=><span key={r.book_id} className="master-attention-item tone-processing" data-testid={'master-rereading-'+r.book_id}><Loader2 size={15} className="spin" aria-hidden="true"/><strong>{r.title}</strong>dobara padhi ja rahi hai · {r.read_pages}/{r.pages} page</span>)}
  {s.health>0&&<span className="master-attention-item tone-attention" data-testid="master-health-line"><ShieldAlert size={15}/>Raat ki data jaanch mein {s.health} cheez dekhni hai</span>}</div>;
}

function ExamCard({e}){
 const types=e.sections.length,live=e.sections.reduce((n,s)=>n+s.counts.live,0),drafts=e.sections.reduce((n,s)=>n+s.counts.draft,0);
 return <Link to={'/super-admin/exam/'+e.slug} className={'master-exam-card exam-color-'+e.color} data-testid={'master-exam-'+e.slug}>
  <div className="master-exam-top"><span className="master-exam-short">{e.short}</span>{!e.shown&&<StatusChip state="hidden" label="Students se chhupa" testId={'master-exam-hidden-'+e.slug}/>}</div>
  <h2>{e.name}</h2>
  <p>{e.sections.map(s=>s.name).join(' · ')||'Abhi koi mock type nahi'}</p>
  <div className="master-exam-facts"><span>{types} mock type</span><span>{live} live</span>{drafts>0&&<span>{drafts} draft</span>}</div>
  <ArrowUpRight className="master-exam-go" size={18} aria-hidden="true"/>
 </Link>;
}

function OwnerHome(){
 const nav=useNavigate();
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[open,setOpen]=useState(false);
 useEffect(()=>{api('/admin/catalog').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[reload]);
 return <div className="admin-page master-page" data-testid="master-home">
  <AttentionLine/>
  <StorageAlert/>
  <AdminHeading testId="super-admin-title" title="Master" text="Exam › mock type › mock. Students website aur app par jo bhi dekhte hain, sab yahin se shuru hota hai." action={<Button onClick={()=>setOpen(true)} data-testid="master-new-exam"><Plus size={16}/>Naya exam</Button>}/>
  <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>
  {!data&&!error?<div className="master-exam-grid">{[1,2,3].map(n=><Skeleton key={n} className="h-44"/>)}</div>:data&&<div className="master-exam-grid" data-testid="master-exam-grid">{data.items.map(e=><ExamCard key={e.slug} e={e}/>)}</div>}
  <p className="admin-note" data-testid="master-kinds-note">Har exam ke apne mock type hote hain: {Object.values(KIND_LABEL).join(', ')}.</p>
  <ExamDialog open={open} onClose={()=>setOpen(false)} onCreated={e=>nav('/super-admin/exam/'+e.slug)}/>
 </div>;
}

function ReviewerHome(){
 return <div className="admin-page master-page" data-testid="reviewer-home">
  <AdminHeading testId="super-admin-title" title="Fix karne wali cheezein" text="Marked sawaal wale mock, aur students ne jo report kiya. Yahan kuch bhi apne aap score nahi badalta."/>
  <section className="admin-panel"><h2>Fix karne wale mock</h2><FixItems tab="fix"/></section>
  <section className="admin-panel"><h2>Students ki question reports</h2><QuestionReportsPanel/></section>
 </div>;
}

export default function MasterHome(){
 const {user}=useAuth();
 return user.role==='owner'?<OwnerHome/>:<ReviewerHome/>;
}
