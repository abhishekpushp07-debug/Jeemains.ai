import React, {useCallback, useEffect, useRef, useState} from 'react';
import {Sparkles, Loader2, RefreshCw} from 'lucide-react';
import {api, post} from '../../lib/api';
import {useAuth} from '../../lib/auth';
import {Button} from '../ui/button';
import {Select, SelectTrigger, SelectValue, SelectContent, SelectItem} from '../ui/select';
import {Input} from '../ui/input';

export const ManualSolve = ({setId}) => {
 const {user}=useAuth(); const [data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const request=useRef(null);
 const load=useCallback(()=>api(`/studio/sets/${setId}/solve`).then(setData).catch(e=>setError(e.message)),[setId]);
 useEffect(()=>{setData(null);setError('');request.current=null;if(user?.role==='owner')load()},[load,user?.role]);
 useEffect(()=>{if(!data?.queued&&!data?.solving)return;const timer=setTimeout(load,4000);return()=>clearTimeout(timer)},[data,load]);
 if(user?.role!=='owner')return null;
 async function solve(){setBusy(true);setError('');request.current ||= crypto.randomUUID();try{setData(await post(`/studio/sets/${setId}/solve`,{request_id:request.current}));request.current=null}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <section className="manual-solve" data-testid={'manual-solve-'+setId} aria-label="Generate missing explanations">
  <div className="manual-solve-main"><strong>Solutions, on your terms.</strong><p data-testid={'solve-protection-'+setId}>One click solves only this test’s missing explanations. Your solutions and saved AI explanations are never replaced.</p>
  {data&&<p role="status" data-testid={'solve-status-'+setId}><b>{data.missing}</b> eligible missing · {data.owner_saved} supplied · {data.ai_saved} AI saved{data.queued+data.solving>0?` · ${data.queued} queued · ${data.solving} solving`:''}{data.blocked>0?` · ${data.blocked} need source/key checks`:''}</p>}
  {data?.errors.map((text,i)=><p className="warning-text" data-testid={`solve-failure-${setId}-${i}`} key={i}>{text}</p>)}
  {error&&<p role="alert" className="warning-text" data-testid={'solve-error-'+setId}>{error}</p>}</div>
  <div className="manual-solve-actions"><Button data-testid={'solve-button-'+setId} disabled={busy||!data||data.missing===0} onClick={solve}>{busy?<Loader2 size={16} className="spin"/>:<Sparkles size={16}/>} {data?.missing===0?(data?.queued||data?.solving?'Solving in background':'Nothing to solve'):data?.failed?'Retry missing solutions':'Solve with AI'}</Button><Button variant="ghost" onClick={load} data-testid={'solve-refresh-'+setId} aria-label="Refresh solution status"><RefreshCw size={16}/></Button></div>
  <small className="manual-solve-usage" data-testid={'solve-usage-'+setId}>Uses your AI balance and daily processing allowance. Automatic generation stays off; progress continues if you leave this page.</small>
 </section>;
};

export const ManualSolvePanel = () => {
 const {user}=useAuth();const [items,setItems]=useState([]),[selected,setSelected]=useState(''),[search,setSearch]=useState(''),[error,setError]=useState('');
 useEffect(()=>{if(user?.role==='owner')api('/studio/solve-tests').then(d=>setItems(d.items)).catch(e=>setError(e.message))},[user?.role]);
 if(user?.role!=='owner')return null;
 const filtered=items.filter(s=>(s.title+' '+s.kind+' '+s.exam).toLowerCase().includes(search.toLowerCase()));
 return <section className="import-card" data-testid="manual-solve-panel"><span className="import-section-label">OWNER CONTROL · NO AUTOMATIC SOLVING</span><h2>Solve one selected test.</h2><div className="solve-picker"><Input aria-label="Find a test to solve" placeholder="Find a mock or chapter…" value={search} onChange={e=>setSearch(e.target.value)} data-testid="solve-test-search"/><Select value={selected} onValueChange={setSelected}><SelectTrigger data-testid="solve-test-select" aria-label="Select a test"><SelectValue placeholder="Choose one test"/></SelectTrigger><SelectContent className="solve-test-options">{filtered.map(s=><SelectItem className="solve-test-option" key={s.id} value={s.id} data-testid={'solve-test-option-'+s.id}>{s.kind} · {s.exam} · {s.title}</SelectItem>)}</SelectContent></Select></div>{error&&<p role="alert" data-testid="solve-picker-error">{error}</p>}{!filtered.length&&!error&&<p data-testid="solve-picker-empty">No matching tests. Try a different search.</p>}{selected&&<ManualSolve key={selected} setId={selected}/>}</section>;
};
