import React,{useState} from 'react';
import {KeyRound,Loader2} from 'lucide-react';
import {toast} from 'sonner';
import {post} from '../lib/api';
import {Button} from './ui/button';
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription} from './ui/dialog';
import {Field,ErrorBox} from './Shared';

export const OwnerPinReset=({student,onSaved})=>{
 const [open,setOpen]=useState(false),[pin,setPin]=useState(''),[confirm,setConfirm]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const tag='owner-reset-'+student.id;
 function toggle(value){if(busy)return;if(value)toast.dismiss();setOpen(value);setPin('');setConfirm('');setError('');}
 async function submit(e){
  e.preventDefault();setError('');
  if(pin!==confirm){setError('Dono PIN ek jaise hone chahiye.');return;}
  setBusy(true);
  try{
   await post('/auth/owner/student-pin-reset',{phone:student.phone,new_pin:pin,confirm_pin:confirm,expected_pin_version:student.pin_version});
   setPin('');setConfirm('');setOpen(false);toast.success('PIN reset ho gaya. Purane session sign out ho gaye; result aur history waise hi hain.');onSaved();
  }catch(e){setError(e.message);}finally{setBusy(false);}
 }
 return <><Button variant="outline" size="sm" onClick={()=>toggle(true)} data-testid={tag+'-open'}><KeyRound size={15}/>PIN reset</Button>
 <Dialog open={open} onOpenChange={toggle}><DialogContent className="owner-pin-reset-dialog" data-testid={tag+'-dialog'} onOpenAutoFocus={e=>{e.preventDefault();document.getElementById(tag+'-pin')?.focus();}}>
 <DialogHeader className="pr-8 text-left"><DialogTitle data-testid={tag+'-title'}>Student ka PIN reset karo</DialogTitle><DialogDescription data-testid={tag+'-description'}>Sirf tab, jab student ne khud maanga ho aur aapne pakka kar liya ho. Purane login session band ho jayenge. Save hue test, answer aur result waise hi rahenge. Koi OTP nahi jata.</DialogDescription></DialogHeader>
 <ErrorBox error={error}/><form onSubmit={submit} className="space-y-4" data-testid={tag+'-form'}>
 <Field id={tag+'-phone'} label="Student ka mobile number" type="tel" value={student.phone} readOnly required/>
 <Field id={tag+'-pin'} label="Naya 4 digit PIN" type="password" inputMode="numeric" autoComplete="new-password" pattern="[0-9]{4}" minLength={4} maxLength={4} required value={pin} onChange={e=>setPin(e.target.value.replace(/[^0-9]/g,''))}/>
 <Field id={tag+'-confirm'} label="PIN dobara likho" type="password" inputMode="numeric" autoComplete="new-password" pattern="[0-9]{4}" minLength={4} maxLength={4} required value={confirm} onChange={e=>setConfirm(e.target.value.replace(/[^0-9]/g,''))}/>
 <div className="flex flex-wrap gap-3"><Button type="button" variant="outline" disabled={busy} onClick={()=>toggle(false)} data-testid={tag+'-cancel'}>Cancel</Button><Button type="submit" disabled={busy} data-testid={tag+'-submit'}>{busy&&<Loader2 size={16} className="spin"/>}{busy?'Reset ho raha hai…':'PIN reset karo aur sign out karo'}</Button></div>
 </form></DialogContent></Dialog></>;
};
