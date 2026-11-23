import React,{useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {BarChart3,TrendingUp,Target,Trophy,BookOpen} from 'lucide-react';
import {Tabs,TabsList,TabsTrigger} from '../ui/tabs';
import {Confirm} from '../Shared';
import {post} from '../../lib/api';
import {detailPath} from './seriesData';

const VIEWS=[['analysis','Analysis',BarChart3,'maroon'],['progress','Progress',TrendingUp,'amber'],['accuracy','Confidence',Target,'emerald'],['rank','Real-exam rank',Trophy,'sapphire'],['solutions','Solutions',BookOpen,'crimson']];

// The same five result buttons as a normal mock. Analysis stays on this page; the others open the full result page, and Back returns here.
export function DayDestinations({id}){
  const nav=useNavigate();
  const go=v=>{if(v!=='analysis')nav('/results/'+id+'?view='+v,{state:{returnTo:detailPath(id)}});};
  return <Tabs value="analysis" onValueChange={go} className="result-destinations sh-destinations" data-testid="series-day-destinations">
    <TabsList aria-label="Result sections">{VIEWS.map(([v,label,Icon,tone])=><TabsTrigger key={v} value={v} className={'tone-'+tone} data-testid={'series-day-view-'+v}><Icon size={16}/>{label}</TabsTrigger>)}</TabsList>
  </Tabs>;
}

// "Galat + chhode dobara", the same untimed retry a normal mock offers.
export function useDayRetry(id,summary){
  const nav=useNavigate(),[open,setOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const count=(summary?.incorrect||0)+(summary?.skipped||0);
  const start=async()=>{
    setBusy(true);setError('');
    try{const next=await post('/attempts/'+id+'/retry',{start_key:crypto.randomUUID(),score_version:'original'});nav('/attempts/'+next.id);}
    catch(e){setError(e.message);setOpen(false);}
    finally{setBusy(false);}
  };
  const dialog=<Confirm open={open} onClose={()=>setOpen(false)} title="Turn mistakes into revision." button="Start untimed retry" onConfirm={start} busy={busy}>
    <p>Create a separate attempt with {count} incorrect or skipped questions. Your original score and report will not change.</p>
    <p>This set is untimed. Its maximum marks reflect only the selected questions; it is not another full-paper simulation.</p>
  </Confirm>;
  return {onRetry:count?()=>setOpen(true):null,dialog,error};
}
