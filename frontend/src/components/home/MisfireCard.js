import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {Crosshair,ChevronRight} from 'lucide-react';
import {api} from '../../lib/api';
import {useAuth} from '../../lib/auth';

// Home tab card for Misfire: open wrong/skipped questions from every paper, by subject.
export function MisfireCard(){
 const {user}=useAuth();const [s,setS]=useState(null);
 useEffect(()=>{if(!user)return undefined;const c=new AbortController();api('/my/misfire/summary',{signal:c.signal}).then(setS).catch(()=>{});return()=>c.abort();},[user]);
 const subjects=(s?.subjects||[]).filter(x=>x.open>0).slice(0,3);
 return <Link to="/misfire" className="misfire-card" data-testid="home-misfire-card">
  <span className="pc-icon mf-icon"><Crosshair size={26} strokeWidth={1.6}/></span>
  <span className="mf-body"><span className="mf-title">MISFIRE</span>
   <span className="mf-sub" data-testid="home-misfire-sub">{!s?'galtiyon ki notebook':s.open?`${s.open} sawaal dobara solve karne hain`:s.fixed?'sab galtiyan theek ho gayi':'mock do, galtiyan yahan aayengi'}</span>
   {subjects.length>0&&<span className="mf-chips">{subjects.map(x=><b key={x.name} data-testid={'home-misfire-subject-'+x.name.toLowerCase()}>{x.name} {x.open}</b>)}</span>}
  </span>
  {s?.open>0&&<span className="pc-chip mf-count" data-testid="home-misfire-count">{s.open} OPEN</span>}
  <ChevronRight size={20} className="mf-go" aria-hidden="true"/>
 </Link>;
}
