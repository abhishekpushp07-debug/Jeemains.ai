import React,{useEffect,useState} from 'react';
import {Search,RefreshCw,UsersRound,Ban,CircleCheck} from 'lucide-react';
import {api,post,del} from '../../lib/api';
import {toast} from 'sonner';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {ErrorBox,Loading} from '../../components/Shared';
import {OwnerPinReset} from '../../components/OwnerPinReset';
import {AdminCrumbs,AdminHeading,ConfirmDialog} from '../../components/admin/AdminShared';

function BlockButton({student,onDone}){
 const [open,setOpen]=useState(false),[busy,setBusy]=useState(false);
 const blocked=student.blocked,tag=(blocked?'student-unblock-':'student-block-')+student.id;
 async function run(){
  setBusy(true);
  try{const r=blocked?await del('/admin/students/'+student.id+'/block'):await post('/admin/students/'+student.id+'/block');toast.success(r.message);setOpen(false);onDone();}
  catch(e){toast.error(e.message);}finally{setBusy(false);}
 }
 return <>
  <Button variant="outline" size="sm" className={blocked?'':'student-block-button'} onClick={()=>setOpen(true)} data-testid={tag}>{blocked?<CircleCheck size={15}/>:<Ban size={15}/>}{blocked?'Chalu karo':'Band karo'}</Button>
  <ConfirmDialog open={open} onClose={()=>{if(!busy)setOpen(false);}} busy={busy} testId={tag+'-confirm'} button={blocked?'Haan, chalu karo':'Haan, band karo'} onConfirm={run}
   title={blocked?'Yeh account phir se chalu karein?':'Yeh account band karein?'}
   text={blocked?`${student.phone} apne number aur PIN se dobara sign in kar payega.`:`${student.phone} har device se turant sign out ho jayega. Jab tak aap chalu na karein, sign in aur Forgot PIN nahi chalega. Purane attempt, score aur rank waise hi rahenge.`}/>
 </>;
}

function StudentRow({student,onChanged}){
 async function removeName(){try{await del('/admin/students/'+student.id+'/display-name');toast.success('Naam hata diya. Leaderboard par ab yeh student "Learner" dikhega.');onChanged();}catch(e){toast.error(e.message);}}
 return <div className={'student-row'+(student.blocked?' is-blocked':'')} data-testid={'student-row-'+student.id}>
  <div className="student-row-main"><strong className="tabular-nums" data-testid={'student-phone-'+student.id}>{student.phone}</strong>
   {student.blocked&&<em className="admin-chip tone-attention" data-testid={'student-blocked-'+student.id}><i aria-hidden="true"/>Band hai</em>}
   {student.display_name&&<small data-testid={'student-name-'+student.id}>Leaderboard naam: <b>{student.display_name}</b></small>}
  </div>
  <div className="student-row-actions">
   {student.display_name&&<Button variant="ghost" size="sm" data-testid={'student-name-remove-'+student.id} onClick={removeName}>Naam hatao</Button>}
   <OwnerPinReset student={student} onSaved={onChanged}/>
   <BlockButton student={student} onDone={onChanged}/>
  </div>
 </div>;
}

export default function AdminStudents(){
 const [query,setQuery]=useState(''),[page,setPage]=useState(1),[data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(true),[reload,setReload]=useState(0);
 useEffect(()=>{
  const controller=new AbortController();setBusy(true);setError('');
  const timer=setTimeout(()=>{api('/admin/students?'+new URLSearchParams({q:query,page:String(page)}),{signal:controller.signal}).then(value=>{if(!controller.signal.aborted)setData(value);}).catch(e=>{if(!controller.signal.aborted)setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});},250);
  return()=>{clearTimeout(timer);controller.abort();};
 },[query,page,reload]);
 const refresh=()=>setReload(v=>v+1);
 return <div className="admin-page" data-testid="admin-students-page">
  <AdminCrumbs items={[{label:'Master',to:'/super-admin'},{label:'Students'}]}/>
  <AdminHeading testId="admin-students-title" title="Students" text="Register hue students ke mobile number. Yeh list sirf aap dekh sakte hain. Yahin se PIN reset, leaderboard naam hatana aur account band ya chalu karna hota hai." action={<span className="badge" data-testid="student-total"><UsersRound size={16}/>{data?.total??'—'} students</span>}/>
  <div className="student-search-bar"><label className="student-search"><Search size={18} aria-hidden="true"/><Input aria-label="Mobile number se dhoondhein" type="search" inputMode="tel" placeholder="Mobile number se dhoondhein" maxLength={32} value={query} onChange={e=>{setQuery(e.target.value.replace(/[^+0-9\s()-]/g,''));setPage(1);}} data-testid="student-search"/></label><Button variant="outline" aria-label="List refresh karo" onClick={refresh} disabled={busy} data-testid="student-refresh"><RefreshCw size={17}/></Button></div>
  <ErrorBox error={error} retry={refresh}/>
  {busy?<Loading text="Students load ho rahe hain…"/>:!error&&<><div className="admin-panel p-0 overflow-hidden" data-testid="student-directory"><div className="px-5 py-4 border-b font-semibold" data-testid="student-phone-heading">Mobile number</div>{data?.items.map(student=><StudentRow key={student.id} student={student} onChanged={refresh}/>)}{!data?.items.length&&<p className="p-6" data-testid="students-empty">{query?'Is number se koi student nahi mila.':'Abhi tak koi student register nahi hua.'}</p>}</div>
  {data?.pages>1&&<div className="flex items-center justify-between gap-3 mt-6"><Button variant="outline" disabled={page===1} onClick={()=>setPage(v=>v-1)} data-testid="students-prev">Pichhla</Button><span data-testid="students-page">{page} / {data.pages}</span><Button variant="outline" disabled={page>=data.pages} onClick={()=>setPage(v=>v+1)} data-testid="students-next">Agla</Button></div>}</>}
 </div>;
}
