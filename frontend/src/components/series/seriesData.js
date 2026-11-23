import {useEffect,useState} from 'react';
import {api} from '../../lib/api';
import {useAuth} from '../../lib/auth';
import {SERIES_PATH,useSeriesSchedule} from '../LiveSeriesBanner';

export const LIST_PATH=SERIES_PATH+'/analysis';
export const detailPath=id=>LIST_PATH+'/'+id;
export const istTime=t=>new Date(t*1000).toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit',timeZone:'Asia/Kolkata'}).toUpperCase();
export const shortDate=day=>new Date(day+'T12:00:00+05:30').toLocaleDateString('en-IN',{day:'numeric',month:'short',timeZone:'Asia/Kolkata'});

// Up to 100 attempts: every live day plus archive practice.
async function allHistory(signal){
  const first=await api(SERIES_PATH+'/history?page=1',{signal});
  const items=[...first.items];
  for(let page=2;items.length<first.total&&page<=5;page++){
    const next=await api(SERIES_PATH+'/history?page='+page,{signal});
    if(!next.items.length)break;
    items.push(...next.items);
  }
  return {...first,items};
}

export function buildDays(s,streak,history){
  const byDate=new Map((streak?.days||[]).map(d=>[d.date,d]));
  const items=history?.items||[];
  return s.slots.map(slot=>{
    const mine=items.filter(a=>a.series_date===slot.date);
    const live=mine.find(a=>a.mode==='series_live');
    const practice=mine.find(a=>a.mode==='series_practice'&&a.summary);
    const openPractice=mine.find(a=>a.mode==='series_practice'&&a.resumable);
    const isToday=slot.date===s.today,past=slot.date<s.today,state=byDate.get(slot.date)?.state;
    const scored=live?.summary?live:practice||null;
    let tone,label;
    if(state==='completed'||state==='pending'||(live&&!live.resumable)){tone='done';label='Completed';}
    else if(state==='in_progress'||live?.resumable){tone='today';label='In progress';}
    else if(isToday){tone='today';label=!slot.ready?'Awaiting paper':slot.state==='start_closed'?'Starts closed':slot.state==='ended'?'Day ended':'Live today';}
    else if(past){tone='missed';label=practice?'Missed · practised':slot.can_start?'Missed · practise':'Missed';}
    else{tone='upcoming';label='Upcoming';}
    return {day:slot.day,date:slot.date,slot,tone,label,isToday,past,live,practice,openPractice,scored};
  });
}

// Where a tap on a day goes. null = just select the day.
export function dayTarget(d){
  if(d.live?.resumable)return {to:'/attempts/'+d.live.id};
  if(d.scored)return {analysis:d.scored.id};
  if(d.openPractice)return {to:'/attempts/'+d.openPractice.id};
  if(d.live)return {to:'/results/'+d.live.id};
  if(d.slot.state==='archive'&&d.slot.can_start&&d.slot.set_id)return {to:'/sets/'+d.slot.set_id,start:true};
  return null;
}

// Two steps in history: Back from a day's analysis lands on the list, Back again on the series.
export function openAnalysis(nav,id){
  nav(LIST_PATH,{state:{fromHub:true}});
  nav(detailPath(id),{state:{fromList:true}});
}

export function goDay(nav,d,select){
  const t=dayTarget(d);
  if(!t)return select(d.day);
  if(t.analysis)return openAnalysis(nav,t.analysis);
  nav(t.to,{state:{returnTo:SERIES_PATH,...(t.start?{autoStart:true}:{})}});
}

export function useSeriesHub(){
  const {user}=useAuth();const schedule=useSeriesSchedule();
  const [streak,setStreak]=useState(null),[history,setHistory]=useState(null),[error,setError]=useState(''),[tick,setTick]=useState(0);
  const stamp=schedule.data?.server_now;
  useEffect(()=>{
    setError('');
    if(!user?.id){setStreak(null);setHistory(null);return undefined;}
    const c=new AbortController();
    Promise.all([api(SERIES_PATH+'/streak',{signal:c.signal}),allHistory(c.signal)])
      .then(([s,h])=>{setStreak(s);setHistory(h);})
      .catch(e=>{if(!c.signal.aborted)setError(e.message);});
    return()=>c.abort();
  },[user?.id,tick,stamp]);
  const days=schedule.data?buildDays(schedule.data,streak,history):[];
  return {user,schedule,streak,history,days,error,retry:()=>setTick(v=>v+1)};
}
