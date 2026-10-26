import React, {useState} from 'react';
import {KeyRound, Loader2} from 'lucide-react';
import {toast} from 'sonner';
import {post} from '../lib/api';
import {useAuth} from '../lib/auth';
import {Button} from './ui/button';
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription} from './ui/dialog';
import {Field, ErrorBox} from './Shared';

export const ChangePin = () => {
 const {user,setUser}=useAuth();
 const [open,setOpen]=useState(false),[pin,setPin]=useState(''),[confirm,setConfirm]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 function toggle(value){if(busy)return;setOpen(value);setPin('');setConfirm('');setError('');}
 async function submit(e){
  e.preventDefault();setError('');
  if(pin!==confirm){setError('PINs must match.');return;}
  setBusy(true);
  try{const next=await post('/auth/pin',{phone:user.phone,new_pin:pin,confirm_pin:confirm});setUser(next);setOpen(false);setPin('');setConfirm('');toast.success('PIN saved. Other sessions have been signed out.');}
  catch(e){setError(e.message);}finally{setBusy(false);}
 }
 return <><Button variant="outline" onClick={()=>toggle(true)} data-testid="profile-change-pin"><KeyRound size={16}/>{user.pin_configured?'Change PIN':'Set your PIN'}</Button>
 <Dialog open={open} onOpenChange={toggle}><DialogContent data-testid="change-pin-dialog" onOpenAutoFocus={event=>{event.preventDefault();document.getElementById('change-pin-new')?.focus();}}><DialogHeader><DialogTitle data-testid="change-pin-title">{user.pin_configured?'Change your PIN':'Set your PIN'}</DialogTitle><DialogDescription data-testid="change-pin-description">Only your signed-in account can be changed here. No OTP required. Other sessions will be signed out.</DialogDescription></DialogHeader>
 <ErrorBox error={error}/><form onSubmit={submit} className="space-y-4" data-testid="change-pin-form">
 <Field id="change-pin-phone" label="Your mobile number" type="tel" value={user.phone} readOnly required/>
 <Field id="change-pin-new" label="New 4-digit PIN" type="password" inputMode="numeric" autoComplete="new-password" pattern="[0-9]{4}" minLength={4} maxLength={4} required value={pin} onChange={e=>setPin(e.target.value.replace(/[^0-9]/g,''))}/>
 <Field id="change-pin-confirm" label="Confirm PIN" type="password" inputMode="numeric" autoComplete="new-password" pattern="[0-9]{4}" minLength={4} maxLength={4} required value={confirm} onChange={e=>setConfirm(e.target.value.replace(/[^0-9]/g,''))}/>
 <div className="flex gap-3"><Button type="button" variant="outline" disabled={busy} onClick={()=>toggle(false)} data-testid="change-pin-cancel">Cancel</Button><Button type="submit" disabled={busy} data-testid="change-pin-save">{busy&&<Loader2 size={16} className="spin"/>}{busy?'Saving…':'Save PIN'}</Button></div>
 </form></DialogContent></Dialog></>;
};
