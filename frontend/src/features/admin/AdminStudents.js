import React,{useEffect,useState} from 'react';
import {Search,RefreshCw,UsersRound} from 'lucide-react';
import {api,del} from '../../lib/api';
import {toast} from 'sonner';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {ErrorBox,Loading} from '../../components/Shared';
import {OwnerPinReset} from '../../components/OwnerPinReset';
import {AdminCrumbs,AdminHeading} from '../../components/admin/AdminShared';

export default function AdminStudents(){
 const [query,setQuery]=useState(''),[page,setPage]=useState(1),[data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(true),[reload,setReload]=useState(0);
 useEffect(()=>{
  const controller=new AbortController();setBusy(true);setError('');
  const timer=setTimeout(()=>{api('/admin/students?'+new URLSearchParams({q:query,page:String(page)}),{signal:controller.signal}).then(value=>{if(!controller.signal.aborted)setData(value);}).catch(e=>{if(!controller.signal.aborted)setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});},250);
  return()=>{clearTimeout(timer);controller.abort();};
 },[query,page,reload]);
 async function removeName(student){try{await del('/admin/students/'+student.id+'/display-name');toast.success('Name removed. Leaderboards show this student as Learner again.');setReload(v=>v+1);}catch(e){toast.error(e.message);}}
 return <div className="admin-page" data-testid="admin-students-page">
  <AdminCrumbs items={[{label:'Master',to:'/super-admin'},{label:'Students'}]}/>
  <AdminHeading testId="admin-students-title" title="Students" text="Registered student mobile numbers. Only you can view this list, reset a student's PIN or remove a leaderboard name." action={<span className="badge" data-testid="student-total"><UsersRound size={16}/>{data?.total??'—'} students</span>}/>
  <div className="flex gap-3 mb-6"><label className="flex items-center gap-2 flex-1 min-w-0"><Search size={18}/><Input aria-label="Search mobile number" type="search" inputMode="tel" placeholder="Search mobile number" maxLength={32} value={query} onChange={e=>{setQuery(e.target.value.replace(/[^+0-9\s()-]/g,''));setPage(1);}} data-testid="student-search"/></label><Button variant="outline" aria-label="Refresh student list" onClick={()=>setReload(v=>v+1)} disabled={busy} data-testid="student-refresh"><RefreshCw size={17}/></Button></div>
  <ErrorBox error={error} retry={()=>setReload(v=>v+1)}/>
  {busy?<Loading text="Loading students…"/>:!error&&<><div className="admin-panel p-0 overflow-hidden" data-testid="student-directory"><div className="px-5 py-4 border-b font-semibold" data-testid="student-phone-heading">Mobile number</div>{data?.items.map(student=><div className="px-5 py-4 border-b last:border-0 flex flex-wrap items-center justify-between gap-3" key={student.id} data-testid={'student-row-'+student.id}><span className="tabular-nums" data-testid={'student-phone-'+student.id}>{student.phone}</span>{student.display_name&&<span className="flex items-center gap-2 text-sm" data-testid={'student-name-'+student.id}>Leaderboard name: <b>{student.display_name}</b><Button variant="ghost" size="sm" data-testid={'student-name-remove-'+student.id} onClick={()=>removeName(student)}>Remove name</Button></span>}<OwnerPinReset student={student} onSaved={()=>setReload(v=>v+1)}/></div>)}{!data?.items.length&&<p className="p-6" data-testid="students-empty">{query?'No matching students.':'No students registered yet.'}</p>}</div>
  {data?.pages>1&&<div className="flex items-center justify-between gap-3 mt-6"><Button variant="outline" disabled={page===1} onClick={()=>setPage(v=>v-1)} data-testid="students-prev">Previous</Button><span data-testid="students-page">{page} / {data.pages}</span><Button variant="outline" disabled={page>=data.pages} onClick={()=>setPage(v=>v+1)} data-testid="students-next">Next</Button></div>}</>}
 </div>;
}
