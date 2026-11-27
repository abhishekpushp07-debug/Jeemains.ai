import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {ListChecks,ChevronRight} from 'lucide-react';
import {api} from '../../lib/api';
import {useAuth} from '../../lib/auth';

// Home card for Student Choice. Shown only while the owner has a way open (both switches Off = Home as before).
export function ChoiceCard(){
 const {user}=useAuth();const [d,setD]=useState(null);
 useEffect(()=>{if(!user)return undefined;const c=new AbortController();api('/choice/home',{signal:c.signal}).then(setD).catch(()=>{});return()=>c.abort();},[user]);
 if(!d||!(d.pick||d.random))return null;
 return <Link to="/choice" className="misfire-card choice-card" data-testid="home-choice-card">
  <span className="pc-icon mf-icon"><ListChecks size={26} strokeWidth={1.6}/></span>
  <span className="mf-body"><span className="mf-title">STUDENT CHOICE</span>
   <span className="mf-sub" data-testid="home-choice-sub">{d.pick?'apna paper khud banao: chapters aur sawaal tum chuno':'random mock: bas ginti batao'}</span>
   <span className="mf-chips"><b>{d.chapters} chapters</b><b>{d.questions} sawaal</b>{d.made_today>0&&<b data-testid="home-choice-today">aaj {d.made_today} / {d.daily_limit}</b>}</span>
  </span>
  <ChevronRight size={20} className="mf-go" aria-hidden="true"/>
 </Link>;
}
