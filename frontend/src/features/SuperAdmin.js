import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {ArrowLeft,Search,RefreshCw,UsersRound} from 'lucide-react';
import {useAuth} from '../lib/auth';
import {api} from '../lib/api';
import {Button} from '../components/ui/button';
import {Input} from '../components/ui/input';
import {ErrorBox,Loading} from '../components/Shared';
import {OwnerPinReset} from '../components/OwnerPinReset';

export default function SuperAdmin(){
 const {user}=useAuth();
 const [query,setQuery]=useState(''),[page,setPage]=useState(1),[data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(true),[reload,setReload]=useState(0);
 useEffect(()=>{
  if(user?.role!=='owner')return;
  const controller=new AbortController();setBusy(true);setError('');
  const timer=setTimeout(()=>{api('/admin/students?'+new URLSearchParams({q:query,page:String(page)}),{signal:controller.signal}).then(value=>{if(!controller.signal.aborted)setData(value);}).catch(e=>{if(!controller.signal.aborted)setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});},250);
  return()=>{clearTimeout(timer);controller.abort();};
 },[user?.role,query,page,reload]);
 if(user?.role!=='owner')return <div className="container page" data-testid="super-admin-denied"><h1>Owner access only</h1><p>This student directory is private.</p><Link to="/home" data-testid="super-admin-denied-home">Back to Home</Link></div>;
 return <div className="container page max-w-4xl" data-testid="super-admin-page">
 <Link to="/home" className="breadcrumb" data-testid="super-admin-home"><ArrowLeft size={15}/>Home</Link>
 <nav className="flex gap-4 flex-wrap mb-6"><Link className="btn btn-primary" to="/super-admin/uploads" data-testid="super-admin-uploads">Uploads · Upload Book</Link><Link className="btn btn-outline" to="/studio" data-testid="super-admin-paired-import">Separate Questions / Solutions PDFs</Link></nav>
 <header className="page-title"><div><span className="eyebrow" data-testid="super-admin-eyebrow">SUPER ADMIN</span><h1 data-testid="super-admin-title">Students.</h1><p data-testid="super-admin-description">Registered student mobile numbers. Only you can view this list and reset a student's PIN.</p></div><span className="badge" data-testid="student-total"><UsersRound size={16}/>{data?.total??'—'} students</span></header>
 <div className="flex gap-3 mb-6"><label className="flex items-center gap-2 flex-1 min-w-0"><Search size={18}/><Input aria-label="Search mobile number" type="search" inputMode="tel" placeholder="Search mobile number" maxLength={32} value={query} onChange={e=>{setQuery(e.target.value.replace(/[^+0-9\s()-]/g,''));setPage(1);}} data-testid="student-search"/></label><Button variant="outline" aria-label="Refresh student list" onClick={()=>setReload(v=>v+1)} disabled={busy} data-testid="student-refresh"><RefreshCw size={17}/></Button></div>
 <ErrorBox error={error} retry={()=>setReload(v=>v+1)}/>
 {busy?<Loading text="Loading students…"/>:!error&&<><div className="card p-0 overflow-hidden" data-testid="student-directory"><div className="px-5 py-4 border-b font-semibold" data-testid="student-phone-heading">Mobile number</div>{data?.items.map(student=><div className="px-5 py-4 border-b last:border-0 flex flex-wrap items-center justify-between gap-3" key={student.id} data-testid={'student-row-'+student.id}><span className="tabular-nums" data-testid={'student-phone-'+student.id}>{student.phone}</span><OwnerPinReset student={student} onSaved={()=>setReload(v=>v+1)}/></div>)}{!data?.items.length&&<p className="p-6" data-testid="students-empty">{query?'No matching students.':'No students registered yet.'}</p>}</div>
 {data?.pages>1&&<div className="flex items-center justify-between gap-3 mt-6"><Button variant="outline" disabled={page===1} onClick={()=>setPage(v=>v-1)} data-testid="students-prev">Previous</Button><span data-testid="students-page">{page} / {data.pages}</span><Button variant="outline" disabled={page>=data.pages} onClick={()=>setPage(v=>v+1)} data-testid="students-next">Next</Button></div>}</>}
 </div>;
}
