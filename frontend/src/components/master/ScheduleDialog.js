import React,{useEffect,useState} from 'react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Switch} from '../ui/switch';
import {Field,istToEpoch} from './MasterShared';

const today=()=>new Date(Date.now()+86400000).toLocaleDateString('en-CA',{timeZone:'Asia/Kolkata'});

export function ScheduleDialog({open,count,onClose,onSave}){
 const [day,setDay]=useState(today()),[time,setTime]=useState('09:00'),[live,setLive]=useState(false);
 useEffect(()=>{if(open){setDay(today());setTime('09:00');setLive(false);}},[open]);
 const at=day&&time?istToEpoch(day,time):0,future=at>Date.now()/1000+60;
 return <Dialog open={open} onOpenChange={v=>!v&&onClose()}><DialogContent className="tejas-dialog admin-dialog" data-testid="schedule-dialog">
  <DialogTitle>{count} mock schedule karo</DialogTitle><DialogDescription>Is date aur time (India time) par yeh apne aap Live ho jayenge.</DialogDescription>
  <form className="admin-form" onSubmit={e=>{e.preventDefault();if(future)onSave(at,live);}}>
   <div className="master-field-row">
    <Field label="Date" id="schedule-date"><Input id="schedule-date" type="date" value={day} onChange={e=>setDay(e.target.value)} data-testid="schedule-date"/></Field>
    <Field label="Time (IST)" id="schedule-time"><Input id="schedule-time" type="time" value={time} onChange={e=>setTime(e.target.value)} data-testid="schedule-time"/></Field>
   </div>
   <label className="master-switch-row" data-testid="schedule-live-exam-label"><Switch checked={live} onCheckedChange={setLive} data-testid="schedule-live-exam"/><span><strong>Live exam</strong><small>{live?'Sab ek saath dete hain: shuru karne ke liye 15 minute, submit karte hi score, aur rank.':'Off: is time se yeh bas practice ke liye khul jayega.'}</small></span></label>
   {!future&&<p className="admin-note warn" data-testid="schedule-past-note">Aage ka time chuniye.</p>}
   <div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid="schedule-cancel">Cancel</Button><Button type="submit" disabled={!future} data-testid="schedule-save">Schedule karo</Button></div>
  </form>
 </DialogContent></Dialog>;
}
