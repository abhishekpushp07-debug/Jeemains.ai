import React,{useCallback,useEffect,useState} from 'react';
import {ShieldCheck,ShieldAlert,RefreshCw} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Button} from '../ui/button';
import {toast} from 'sonner';

const when=s=>s?new Date(s*1000).toLocaleString(undefined,{day:'numeric',month:'short',hour:'numeric',minute:'2-digit'}):'';
const STATE={fixed:'Fixed',needs_attention:'Needs you',fixing:'Fixing',not_checked:'Not checked',ok:'OK'};

function Row({c}){
 const detail=c.found===null?'This check could not finish. It will run again tonight.':c.action==='repair'?`Found ${c.found} · fixed ${c.fixed} · left ${c.left??0}`:`Found ${c.found}. Shown for you to decide; nothing was changed.`;
 return <li className="admin-row" data-testid={'data-health-check-'+c.key}><div className="admin-row-main"><strong>{c.label}</strong><small data-testid={'data-health-check-detail-'+c.key}>{detail}</small></div><span className={'admin-chip tone-'+(c.state==='fixed'?'ready':c.state==='fixing'?'processing':'attention')} data-testid={'data-health-check-state-'+c.key}>{STATE[c.state]}</span></li>;
}

function Summary({report}){
 const issues=report.checks.filter(c=>c.found||c.found===null);
 const left=report.needs_attention+report.checks.filter(c=>c.state==='not_checked').length;
 const Icon=left?ShieldAlert:ShieldCheck;
 const done=report.checks.filter(c=>c.state==='fixed').reduce((n,c)=>n+c.fixed,0);
 const fixing=report.checks.filter(c=>c.state==='fixing').reduce((n,c)=>n+(c.left||0),0);
 const text=!issues.length?`All ${report.checks.length} checks passed. No duplicate, broken or mismatched records.`:`${report.found} problem records found, ${done} fixed automatically${fixing?`, ${fixing} still being fixed`:''}${left?`, ${left} ${left===1?'check needs':'checks need'} you`:''}.`;
 return <><p className={'admin-health-summary'+(left?' warn':'')} data-testid="data-health-summary"><Icon size={18} aria-hidden="true"/>{text}</p>
  {issues.length>0&&<ul className="admin-list" data-testid="data-health-list">{issues.map(c=><Row key={c.key} c={c}/>)}</ul>}
  {report.missing_safeguards.length>0&&<p className="admin-note warn" data-testid="data-health-safeguards">Missing database safeguards: {report.missing_safeguards.join(', ')}.</p>}</>;
}

export function DataHealth(){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const load=useCallback(()=>api('/admin/integrity').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message)),[]);
 useEffect(()=>{load();},[load]);
 useEffect(()=>{if(!data?.running){return undefined;}const timer=setInterval(load,4000);return()=>clearInterval(timer);},[data?.running,load]);
 async function run(){setBusy(true);try{await post('/admin/integrity/run');toast.success('Data check started. Results appear here in about a minute.');await load();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 const report=data?.report;
 return <section className="admin-panel" data-testid="data-health-panel">
  <div className="admin-panel-head"><div><h2>Data health</h2><p className="admin-note" data-testid="data-health-last-run">{data?.running?'Checking now…':report?`Last checked ${when(report.last_run)} · took ${report.duration_s}s.`:data?'Not checked yet.':error?'':'Loading…'} Counts only, never student details. {data?.schedule}</p></div>
   {!data&&error?<Button variant="outline" onClick={load} data-testid="data-health-retry"><RefreshCw size={16}/>Try again</Button>
   :<Button variant="outline" disabled={busy||!data||data.running} onClick={run} data-testid="data-health-run"><RefreshCw size={16} className={data?.running?'spin':''}/>Check now</Button>}</div>
  {error&&<p className="admin-note warn" data-testid="data-health-error">{error}</p>}
  {report&&<Summary report={report}/>}
 </section>;
}
