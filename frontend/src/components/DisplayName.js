import React, {useState} from 'react';
import {Loader2, PencilLine, Trophy} from 'lucide-react';
import {toast} from 'sonner';
import {put} from '../lib/api';
import {useAuth} from '../lib/auth';
import {Button} from './ui/button';
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription} from './ui/dialog';
import {Field, ErrorBox} from './Shared';

export const DisplayName = ({onSaved}) => {
 const {user,setUser}=useAuth();
 const current=user.display_name||'';
 const [open,setOpen]=useState(false),[name,setName]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 function toggle(value){if(busy)return;setOpen(value);setName(current);setError('');}
 async function save(next){
  setError('');setBusy(true);
  try{const done=await put('/profile/display-name',{name:next});setUser({...user,display_name:done.display_name||undefined});setOpen(false);onSaved?.();toast.success(done.display_name?'Naam save ho gaya. Leaderboard par ab "'+done.display_name+'" dikhega.':'Naam hat gaya. Leaderboard par aap phir se Learner dikhoge.');}
  catch(e){setError(e.message);}finally{setBusy(false);}
 }
 function submit(e){e.preventDefault();const clean=name.trim().replace(/\s+/g,' ');if(!clean){setError('Naam likho, ya "Naam hatao" dabao.');return;}save(clean);}
 return <div className="display-name-row" data-testid="display-name-row"><Trophy size={14}/><span>Leaderboard naam: <b data-testid="display-name-value">{current||'Abhi nahi likha'}</b></span>
  <Button variant="link" size="sm" onClick={()=>toggle(true)} data-testid="display-name-edit"><PencilLine size={14}/>{current?'Naam badlo':'Naam likho'}</Button>
  <Dialog open={open} onOpenChange={toggle}><DialogContent data-testid="display-name-dialog" onOpenAutoFocus={event=>{event.preventDefault();document.getElementById('display-name-input')?.focus();}}><DialogHeader><DialogTitle data-testid="display-name-title">Leaderboard par aapka naam</DialogTitle><DialogDescription data-testid="display-name-description">Leaderboard, Compare aur aapki report par "Learner" aur code ki jagah yeh naam dikhega. Aapka phone number kabhi nahi dikhta. Naam din mein 3 baar badal sakte ho.</DialogDescription></DialogHeader>
  <ErrorBox error={error}/><form onSubmit={submit} className="space-y-4" data-testid="display-name-form">
  <Field id="display-name-input" label="Aapka naam" placeholder="Jaise: Arjun Sharma" autoComplete="nickname" maxLength={20} value={name} onChange={e=>setName(e.target.value)} hint={'2 se 20 akshar, ank ya space · '+name.trim().length+'/20'}/>
  <div className="flex flex-wrap gap-3"><Button type="button" variant="outline" disabled={busy} onClick={()=>toggle(false)} data-testid="display-name-cancel">Rehne do</Button>{current&&<Button type="button" variant="ghost" disabled={busy} onClick={()=>save('')} data-testid="display-name-remove">Naam hatao</Button>}<Button type="submit" disabled={busy} data-testid="display-name-save">{busy&&<Loader2 size={16} className="spin"/>}{busy?'Save ho raha hai…':'Naam save karo'}</Button></div>
  </form></DialogContent></Dialog></div>;
};
