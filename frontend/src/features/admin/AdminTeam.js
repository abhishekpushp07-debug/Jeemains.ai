import React,{useCallback,useEffect,useState} from 'react';
import {UserPlus,UserMinus} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {Label} from '../../components/ui/label';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox,Confirm} from '../../components/Shared';
import {AdminCrumbs,AdminHeading} from '../../components/admin/AdminShared';
import {toast} from 'sonner';

export default function AdminTeam(){
 const [items,setItems]=useState(null),[error,setError]=useState(''),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[removing,setRemoving]=useState(null);
 const load=useCallback(()=>api('/studio/reviewers').then(d=>{setItems(d.items);setError('');}).catch(e=>setError(e.message)),[]);
 useEffect(()=>{load();},[load]);
 async function update(target,role,initial=''){setBusy(true);try{await post('/studio/reviewers',{email:target,role,initial_password:initial});toast.success(role==='reviewer'?`${target} can now review.`:`Reviewer access removed for ${target}.`);setEmail('');setPassword('');setRemoving(null);await load();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <div className="admin-page" data-testid="admin-team-page">
  <AdminCrumbs items={[{label:'Super Admin',to:'/super-admin'},{label:'Team'}]}/>
  <AdminHeading testId="admin-team-title" title="Team" text="Reviewers see only Review: held mocks, question reports and solution checks. Upload, publishing, exams, students and team stay with you."/>
  <section className="admin-panel"><h2>Reviewers</h2><ErrorBox error={error} retry={load}/>{!items&&!error?<Skeleton className="h-20"/>:items&&(items.length?<ul className="admin-list" data-testid="reviewer-list">{items.map(r=><li className="admin-row" key={r.id} data-testid={'reviewer-'+r.id}><div className="admin-row-main"><strong>{r.email}</strong><small>Reviewer</small></div><Button variant="outline" disabled={busy} onClick={()=>setRemoving(r.email)} data-testid={'reviewer-remove-'+r.id}><UserMinus size={15}/>Remove access</Button></li>)}</ul>:<p className="admin-empty" data-testid="reviewer-empty">No reviewers yet.</p>)}</section>
  <section className="admin-panel"><h2>Give review access</h2><form className="admin-form" onSubmit={e=>{e.preventDefault();update(email.trim(),'reviewer',password);}}>
   <Label htmlFor="reviewer-email">Staff email</Label><Input id="reviewer-email" type="email" value={email} onChange={e=>setEmail(e.target.value)} data-testid="reviewer-email"/>
   <Label htmlFor="reviewer-initial-password">Initial password (new staff only)</Label><Input id="reviewer-initial-password" type="password" autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)} data-testid="reviewer-initial-password"/>
   <p className="admin-note">At least 10 characters. Existing accounts keep their password. Share it through your own secure channel. Student phone profiles can never become staff.</p>
   <Button type="submit" disabled={busy||!email.includes('@')} data-testid="reviewer-grant"><UserPlus size={16}/>Give review access</Button></form></section>
  <Confirm open={!!removing} onClose={()=>setRemoving(null)} title="Remove reviewer access?" button="Remove access" busy={busy} onConfirm={()=>update(removing,'student')}><p>{removing} will no longer open Super Admin. Their past review notes stay.</p></Confirm>
 </div>;
}
