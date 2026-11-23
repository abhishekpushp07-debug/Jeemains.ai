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
import {MasterCrumbs,fixLink,plain} from '../../../components/master/MasterShared';

// PDFs being read again: their fixes come back here once the new reading is in.
const Rereading=({items})=>items?.length?<p className="admin-note" data-testid="fix-rereading-note">{items.length} PDF dobara padhi ja rahi {items.length===1?'hai':'hain'} ({items.slice(0,3).map(r=>`${r.title} · ${r.read_pages}/${r.pages} page`).join(', ')}). Inke fix naye padhne ke baad yahan aayenge.</p>:null;

export function FixItems({tab}){
 const [data,setData]=useState(null),[error,setError]=useState('');
 useEffect(()=>{api('/admin/master/fix').then(setData).catch(e=>setError(e.message));},[]);
 if(error)return <ErrorBox error={error}/>;
 if(!data)return <Skeleton className="h-40"/>;
 const items=tab==='ready'?data.ready:data.items;
 if(!items.length)return <><Rereading items={data.rereading}/><p className="admin-empty" data-testid={'fix-empty-'+tab}>{tab==='ready'?'Abhi kuch intezaar mein nahi hai. Naye mock poore hote hi yahan aayenge.':'Kuch fix nahi karna. Har upload ya likha hua mock poora hai.'}</p></>;
 return <><Rereading items={data.rereading}/><ul className="admin-list" data-testid={'fix-list-'+tab}>{items.map(m=><li key={m.kind+m.id} className="admin-row" data-testid={'fix-item-'+m.id}>
  <div className="admin-row-main"><strong>{m.title}</strong><small>{[m.place,m.source==='Written'?'Likha hua':m.source,tab==='ready'?`${m.count} sawaal`:`${m.count}${m.more?'+':''} check karne hain`].filter(Boolean).join(' · ')}</small>{m.reason&&<p className="admin-reason">{plain(m.reason)}</p>}</div>
  {tab==='ready'?(m.section_id&&<Button asChild variant="outline"><Link to={`/super-admin/exam/${m.exam_slug}/${m.section_id}`} data-testid={'fix-open-'+m.id}>Uski list kholo<ArrowUpRight size={15}/></Link></Button>)
   :<Button asChild><Link to={fixLink(m)} data-testid={'fix-open-'+m.id}><Wrench size={15}/>Fix</Link></Button>}
 </li>)}</ul></>;
}

export default function FixList(){
 const {user}=useAuth();const [params,setParams]=useSearchParams();
 const tab=user.role==='owner'&&params.get('tab')==='ready'?'ready':'fix';
 return <div className="admin-page master-page" data-testid="fix-page">
  <MasterCrumbs last={tab==='ready'?'Live ke liye taiyaar':'Fix karna hai'}/>
  <AdminHeading testId="fix-title" title={tab==='ready'?'Live ke liye taiyaar':'Fix karne wale mock'} text={tab==='ready'?'Poore Draft. Live ya schedule karne ke liye unki list kholiye.':'Har ek mein kuch answer photo se mila kar check karne hain. Koi AI nahi lagta.'}/>
  {user.role==='owner'&&<Tabs value={tab} onValueChange={v=>setParams(v==='ready'?{tab:'ready'}:{})}><TabsList className="admin-tabs"><TabsTrigger value="fix" data-testid="fix-tab-fix">Fix karna hai</TabsTrigger><TabsTrigger value="ready" data-testid="fix-tab-ready">Live ke liye taiyaar</TabsTrigger></TabsList></Tabs>}
  <section className="admin-panel"><FixItems key={tab} tab={tab}/></section>
 </div>;
}
