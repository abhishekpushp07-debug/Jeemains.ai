import React,{useCallback,useEffect,useState} from 'react';
import {Loader2,Eraser,Square} from 'lucide-react';
import {toast} from 'sonner';
import {api,post} from '../../lib/api';

const ACTIVE=['running','waiting'];
const SAYS={running:'Line hatayi ja rahi hai…',waiting:'Supabase ka intezaar. Lautte hi kaam wahin se aage chalega.',stopped:'Roka gaya. “Line hatao” dabane par wahin se aage chalega.',
 interrupted:'Server restart se ruka. “Line hatao” dabane par wahin se aage chalega.',done:'Kaam poora hua.'};

function useRepaint(){
 const [data,setData]=useState(null);
 const load=useCallback(()=>api('/admin/pictures/source-line/status').then(setData).catch(()=>{}),[]);
 useEffect(()=>{load();},[load]);
 useEffect(()=>{if(!ACTIVE.includes(data?.state))return;const t=setInterval(load,3000);return()=>clearInterval(t);},[data?.state,load]);
 return {data,setData,load};
}

function Left({items}){
 if(!items?.length)return null;
 return <ul className="move-failures" data-testid="source-line-failures">{items.map((f,i)=><li key={i} data-testid={'source-line-failure-'+i}><strong>{f.label}</strong><small>{f.reason}</small></li>)}</ul>;
}

// Super Admin: tests made Live before the printed 'Source: … / Q…' line was hidden still show it in their saved pictures. This paints it out.
export function SourceRepaint(){
 const {data,setData,load}=useRepaint();
 const [busy,setBusy]=useState(false);
 if(!data)return null;
 const act=async path=>{setBusy(true);try{setData(await post('/admin/pictures/source-line/'+path));}catch(e){toast.error(e.message);load();}finally{setBusy(false);}};
 const active=ACTIVE.includes(data.state),done=data.painted+data.clean+data.left;
 if(!data.waiting&&!active)return data.painted_ever>0?<p className="storage-meta" data-testid="source-line-all-done">Purani pictures: {data.painted_ever} se ‘Source’ line hata di gayi. Ab kisi mein nahi bachi.</p>:null;
 return <section className="legacy-move" data-testid="source-line">
  <strong data-testid="source-line-title">Purani pictures jinmein ‘Source’ line ho sakti hai: {data.waiting}</strong>
  <small>Jo test is badlav se pehle Live hue, unke poore sawaal aur solution ki pictures mein “Source: AITS Mock … / Q…” abhi chhapa hai. Yahan sirf woh line safed hoti hai; baaki picture ka har pixel wahi rehta hai. Purani picture storage se hatai nahi jaati. Ise tab chalaiye jab koi live exam na chal raha ho.</small>
  {(active||done>0)&&<div className="admin-progress" role="status"><progress value={done} max={data.total||1}/><small data-testid="source-line-progress">{done} / {data.total} · {data.painted} saaf hui{data.clean?` · ${data.clean} mein line thi hi nahi`:''}{data.left?` · ${data.left} nahi ho payi`:''}</small></div>}
  {SAYS[data.state]&&<small data-testid="source-line-state">{SAYS[data.state]}{data.state==='running'&&data.current?` (${data.current})`:''}</small>}
  <Left items={data.failures}/>
  <div className="legacy-move-actions">{active
   ?<button type="button" className="machine-retry" disabled={busy} onClick={()=>act('stop')} data-testid="source-line-stop"><Square size={13} aria-hidden="true"/>Roko</button>
   :<button type="button" className="machine-retry" disabled={busy} onClick={()=>act('start')} data-testid="source-line-start">{busy?<Loader2 size={14} className="spin" aria-hidden="true"/>:<Eraser size={14} aria-hidden="true"/>}Line hatao</button>}</div>
 </section>;
}
