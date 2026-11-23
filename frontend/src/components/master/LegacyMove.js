import React,{useCallback,useEffect,useState} from 'react';
import {Loader2,ArrowRightLeft,Square} from 'lucide-react';
import {toast} from 'sonner';
import {api,post} from '../../lib/api';
import {STORAGE_EVENT} from './UploadProgress';

const ACTIVE=['running','waiting'];
const SAYS={running:'Copy chal rahi hai…',waiting:'Supabase ka intezaar. Lautte hi copy wahin se aage chalegi.',stopped:'Roki gayi. Copy dabane par wahin se aage chalegi.',
 interrupted:'Server restart se ruki. Copy dabane par wahin se aage chalegi.',done:'Copy poori hui.'};

function useMove(){
 const [data,setData]=useState(null);
 const load=useCallback(()=>api('/admin/storage/move/status').then(setData).catch(()=>{}),[]);
 useEffect(()=>{load();},[load]);
 useEffect(()=>{if(!ACTIVE.includes(data?.state))return;const t=setInterval(load,3000);return()=>clearInterval(t);},[data?.state,load]);
 return {data,setData,load};
}

function Failures({items}){
 if(!items?.length)return null;
 return <ul className="move-failures" data-testid="move-failures">{items.map((f,i)=><li key={i} data-testid={'move-failure-'+i}><strong>{f.label}</strong><small>{f.reason}</small></li>)}</ul>;
}

// Super Admin: copies the old Emergent files into Supabase. Same bytes, so the app re-downloads nothing; Emergent copies are kept.
export function LegacyMove(){
 const {data,setData,load}=useMove();
 const [busy,setBusy]=useState(false);
 if(!data)return null;
 // A refusal (Supabase just went down) refreshes this section and the badge at once.
 const act=async path=>{setBusy(true);try{setData(await post('/admin/storage/move/'+path));}catch(e){toast.error(e.message);load();window.dispatchEvent(new Event(STORAGE_EVENT));}finally{setBusy(false);}};
 const left=data.remaining_total,active=ACTIVE.includes(data.state),done=data.moved+data.failed+data.skipped;
 // Files that failed or were skipped this run are still on Emergent, so they are in "left" too: count them once.
 const total=done+Math.max(0,left-data.failed-data.skipped);
 if(!left&&!active&&!data.failed)return <p className="storage-meta" data-testid="move-all-done">Purani files: sab Supabase mein hain.</p>;
 return <section className="legacy-move" data-testid="legacy-move">
  <strong data-testid="move-title">Purani files Emergent mein: {left}</strong>
  <small>Har file ke bytes Supabase se wapas padh kar milaye jaate hain, tabhi switch hota hai. App kuch dobara download nahi karta. Emergent wali copy delete nahi hoti.</small>
  {(active||done>0)&&<div className="admin-progress" role="status"><progress value={done} max={total||1}/><small data-testid="move-progress">{done} / {total} · {data.moved} copy hui{data.failed?` · ${data.failed} nahi ho payi`:''}{data.current?.size?` · abhi ${Math.round(100*data.current.sent/data.current.size)}%`:''}</small></div>}
  {SAYS[data.state]&&<small data-testid="move-state">{SAYS[data.state]}</small>}
  <Failures items={data.failures}/>
  <div className="legacy-move-actions">{active
   ?<button type="button" className="machine-retry" disabled={busy} onClick={()=>act('stop')} data-testid="move-stop"><Square size={13} aria-hidden="true"/>Roko</button>
   :left>0&&<button type="button" className="machine-retry" disabled={busy||!data.supabase_ready} onClick={()=>act('start')} data-testid="move-start">{busy?<Loader2 size={14} className="spin" aria-hidden="true"/>:<ArrowRightLeft size={14} aria-hidden="true"/>}Supabase mein copy karo</button>}</div>
  {!data.supabase_ready&&!active&&<small data-testid="move-wait-note">Supabase abhi taiyaar nahi; lautne par copy kar sakte hain.</small>}
 </section>;
}
