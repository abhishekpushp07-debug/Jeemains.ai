import React, {useState} from 'react';
import {Loader2, PencilLine, Trophy} from 'lucide-react';
import {toast} from 'sonner';
import {put} from '../lib/api';
import {useAuth} from '../lib/auth';
import {Button} from './ui/button';
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription} from './ui/dialog';
import {Field, ErrorBox} from './Shared';

export const DisplayName = () => {
 const {user,setUser}=useAuth();
 const current=user.display_name||'';
 const [open,setOpen]=useState(false),[name,setName]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 function toggle(value){if(busy)return;setOpen(value);setName(current);setError('');}
 async function save(next){
  setError('');setBusy(true);
  try{const done=await put('/profile/display-name',{name:next});setUser({...user,display_name:done.display_name||undefined});setOpen(false);toast.success(done.display_name?'Name saved. Leaderboards now show "'+done.display_name+'".':'Name removed. Leaderboards show you as Learner again.');}
  catch(e){setError(e.message);}finally{setBusy(false);}
 }
 function submit(e){e.preventDefault();const clean=name.trim().replace(/\s+/g,' ');if(!clean){setError('Type a name, or use Remove name.');return;}save(clean);}
 return <div className="display-name-row" data-testid="display-name-row"><Trophy size={14}/><span>Leaderboard name: <b data-testid="display-name-value">{current||'Not set'}</b></span>
  <Button variant="link" size="sm" onClick={()=>toggle(true)} data-testid="display-name-edit"><PencilLine size={14}/>{current?'Change':'Set name'}</Button>
  <Dialog open={open} onOpenChange={toggle}><DialogContent data-testid="display-name-dialog" onOpenAutoFocus={event=>{event.preventDefault();document.getElementById('display-name-input')?.focus();}}><DialogHeader><DialogTitle data-testid="display-name-title">Your name on leaderboards</DialogTitle><DialogDescription data-testid="display-name-description">Shown on leaderboards, in Compare and on your report instead of "Learner" and a code. Your phone number is never shown. You can change it 3 times a day.</DialogDescription></DialogHeader>
  <ErrorBox error={error}/><form onSubmit={submit} className="space-y-4" data-testid="display-name-form">
  <Field id="display-name-input" label="Your name" placeholder="e.g. Arjun Sharma" autoComplete="nickname" maxLength={20} value={name} onChange={e=>setName(e.target.value)} hint={'2 to 20 letters, numbers or spaces · '+name.trim().length+'/20'}/>
  <div className="flex flex-wrap gap-3"><Button type="button" variant="outline" disabled={busy} onClick={()=>toggle(false)} data-testid="display-name-cancel">Cancel</Button>{current&&<Button type="button" variant="ghost" disabled={busy} onClick={()=>save('')} data-testid="display-name-remove">Remove name</Button>}<Button type="submit" disabled={busy} data-testid="display-name-save">{busy&&<Loader2 size={16} className="spin"/>}{busy?'Saving…':'Save name'}</Button></div>
  </form></DialogContent></Dialog></div>;
};
