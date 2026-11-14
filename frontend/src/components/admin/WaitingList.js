import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {Send,Wrench} from 'lucide-react';
import {api,post} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Button} from '../ui/button';
import {Skeleton} from '../ui/skeleton';
import {ErrorBox} from '../Shared';
import {StatusChip,ConfirmDialog} from './AdminShared';
import {ReadyAction} from './ReadyAction';
import {toast} from 'sonner';

function WaitingRow({x,showPlace,onDone}){
 const fix=x.kind==='book_mock'?`/super-admin/upload?book=${x.book_id}&fix=${x.id}`:x.kind==='import'?'/studio/imports/'+x.id:'/studio/chapter-books/'+x.id;
 return <li className={'admin-row'+(x.state==='held'?' is-held':'')} data-testid={'waiting-'+x.id}>
  <div className="admin-row-main"><strong>{x.title}</strong><small>{x.book} · {x.count} {x.unit}{showPlace&&x.destination?` · ${x.destination.exam_name} › ${x.destination.section_name}`:''}</small>{x.state==='held'&&x.issue&&<p className="admin-reason">{x.issue}{x.issue_count>1?` (+${x.issue_count-1} more)`:''}</p>}</div>
  {x.state==='ready'?<ReadyAction item={x} onDone={onDone}/>:<StatusChip state={x.state} testId={'waiting-state-'+x.id}/>}
  {x.state==='held'&&<Button asChild variant="outline" size="sm"><Link to={fix} data-testid={'waiting-fix-'+x.id}><Wrench size={15}/>Fix</Link></Button>}
 </li>;
}

export function WaitingList({sectionId='',title='Waiting to publish',showPlace=false,onChanged,testId='waiting-list'}){
 const [items,setItems]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[confirm,setConfirm]=useState(false),[busy,setBusy]=useState(false);
 useEffect(()=>{api('/admin/catalog/waiting'+(sectionId?'?section_id='+encodeURIComponent(sectionId):'')).then(d=>{setItems(d.items);setError('');}).catch(e=>setError(e.message));},[sectionId,reload]);
 const refresh=()=>{setReload(n=>n+1);onChanged?.();};
 const ready=(items||[]).filter(x=>x.state==='ready'&&x.kind!=='import');
 async function all(){setBusy(true);try{const r=await post('/admin/publish-ready',{section_id:sectionId});invalidateCatalog();toast.success(r.message);(r.notes||[]).forEach(n=>toast.message(n));setConfirm(false);refresh();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!items)return <Skeleton className="h-20"/>;
 if(!items.length)return sectionId?null:<p className="admin-empty" data-testid={testId+'-empty'}>Nothing is waiting. Everything checked is already live or scheduled.</p>;
 return <section className="admin-waiting" data-testid={testId}>
  <div className="admin-panel-head"><div><h3>{title} ({items.length})</h3><p className="admin-note">Click a Ready chip to publish now or schedule it. Held items need a fix first.</p></div>{ready.length>0&&<Button onClick={()=>setConfirm(true)} data-testid={testId+'-publish-all'}><Send size={16}/>Publish all ready ({ready.length})</Button>}</div>
  <ul className="admin-list">{items.map(x=><WaitingRow key={x.kind+x.id} x={x} showPlace={showPlace} onDone={refresh}/>)}</ul>
  <ConfirmDialog open={confirm} onClose={()=>setConfirm(false)} busy={busy} onConfirm={all} testId={testId+'-confirm'} title={`Publish ${ready.length} ready item${ready.length===1?'':'s'} now?`} text="They appear to students straight away, in printed order. Held items stay private." button="Publish now"/>
 </section>;
}
