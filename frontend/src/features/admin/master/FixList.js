import React,{useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {Wrench,ArrowUpRight} from 'lucide-react';
import {api} from '../../../lib/api';
import {useAuth} from '../../../lib/auth';
import {Button} from '../../../components/ui/button';
import {Skeleton} from '../../../components/ui/skeleton';
import {Tabs,TabsList,TabsTrigger} from '../../../components/ui/tabs';
import {ErrorBox} from '../../../components/Shared';
import {AdminHeading} from '../../../components/admin/AdminShared';
import {MasterCrumbs,fixLink,plural} from '../../../components/master/MasterShared';

export function FixItems({tab}){
 const [data,setData]=useState(null),[error,setError]=useState('');
 useEffect(()=>{api('/admin/master/fix').then(setData).catch(e=>setError(e.message));},[]);
 if(error)return <ErrorBox error={error}/>;
 if(!data)return <Skeleton className="h-40"/>;
 const items=tab==='ready'?data.ready:data.items;
 if(!items.length)return <p className="admin-empty" data-testid={'fix-empty-'+tab}>{tab==='ready'?'Nothing is waiting. New mocks appear here once they are complete.':'Nothing to fix. Every uploaded or written mock is complete.'}</p>;
 return <ul className="admin-list" data-testid={'fix-list-'+tab}>{items.map(m=><li key={m.kind+m.id} className="admin-row" data-testid={'fix-item-'+m.id}>
  <div className="admin-row-main"><strong>{m.title}</strong><small>{[m.place,m.source,tab==='ready'?plural(m.count,'question'):plural(m.count,'thing')+' to fix'].filter(Boolean).join(' · ')}</small>{m.reason&&<p className="admin-reason">{m.reason}</p>}</div>
  {tab==='ready'?(m.section_id&&<Button asChild variant="outline"><Link to={`/super-admin/exam/${m.exam_slug}/${m.section_id}`} data-testid={'fix-open-'+m.id}>Open its list<ArrowUpRight size={15}/></Link></Button>)
   :<Button asChild><Link to={fixLink(m)} data-testid={'fix-open-'+m.id}><Wrench size={15}/>Fix</Link></Button>}
 </li>)}</ul>;
}

export default function FixList(){
 const {user}=useAuth();const [params,setParams]=useSearchParams();
 const tab=user.role==='owner'&&params.get('tab')==='ready'?'ready':'fix';
 return <div className="admin-page master-page" data-testid="fix-page">
  <MasterCrumbs last={tab==='ready'?'Ready for Live':'To fix'}/>
  <AdminHeading testId="fix-title" title={tab==='ready'?'Ready for Live':'Mocks to fix'} text={tab==='ready'?'Complete drafts. Open their list to make them Live or schedule them.':'Each one needs a few answers checked against its photo. No AI is used.'}/>
  {user.role==='owner'&&<Tabs value={tab} onValueChange={v=>setParams(v==='ready'?{tab:'ready'}:{})}><TabsList className="admin-tabs"><TabsTrigger value="fix" data-testid="fix-tab-fix">To fix</TabsTrigger><TabsTrigger value="ready" data-testid="fix-tab-ready">Ready for Live</TabsTrigger></TabsList></Tabs>}
  <section className="admin-panel"><FixItems key={tab} tab={tab}/></section>
 </div>;
}
