import React,{useEffect,useState} from 'react';
import {Link,useNavigate} from 'react-router-dom';
import {Plus,BookOpen} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Button} from '../../components/ui/button';
import {Field,SelectField,Confirm,ErrorBox} from '../../components/Shared';
import {JeeTransferPanel} from '../../components/studio/JeeTransferPanel';

function ManualSets(){
 const [sets,setSets]=useState(null),[error,setError]=useState(''),[open,setOpen]=useState(false),[title,setTitle]=useState(''),[exam,setExam]=useState('JEE Main'),[busy,setBusy]=useState(false);const nav=useNavigate();
 useEffect(()=>{api('/studio/sets').then(setSets).catch(e=>setError(e.message));},[]);
 async function add(){setBusy(true);try{const s=await post('/studio/sets',{title,exam});nav('/studio/'+s.id);}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <div data-testid="manual-sets"><div className="admin-panel-head"><div><h3>Manual editor sets</h3><p>Hand-built sets. New ones start as private drafts.</p></div><Button variant="outline" onClick={()=>setOpen(true)} data-testid="studio-new-set"><Plus size={16}/>Manual editor</Button></div><ErrorBox error={error}/>
  {sets&&(sets.length?<ul className="admin-list">{sets.map(s=><li className="admin-row" key={s.id}><Link className="admin-row-main" to={'/studio/'+s.id} data-testid="studio-set-row"><strong><BookOpen size={15}/> {s.title}</strong><small>{s.exam} · {s.status} · {s.count} questions · {s.approved_count} approved</small></Link></li>)}</ul>:<p className="admin-empty">No manual sets.</p>)}
  <Confirm open={open} onClose={()=>setOpen(false)} title="Create a practice set" button="Create draft" busy={busy} onConfirm={add}><Field id="new-set-title" label="Paper or set title" value={title} onChange={e=>setTitle(e.target.value)} placeholder="Name your source paper"/><SelectField id="new-set-exam" label="Exam" value={exam} onChange={setExam} options={['JEE Main','BITSAT']}/><p>New sets are private drafts with no publication permissions. You will define timing, marks and rights next.</p></Confirm>
 </div>;
}

export const ContentTools=()=><details className="admin-panel admin-tools" data-testid="content-tools"><summary data-testid="content-tools-toggle">Advanced content tools</summary><ManualSets/><JeeTransferPanel/></details>;
