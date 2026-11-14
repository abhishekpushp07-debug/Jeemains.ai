import React,{useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {Wrench} from 'lucide-react';
import {api} from '../../lib/api';
import {useAuth} from '../../lib/auth';
import {Button} from '../../components/ui/button';
import {Skeleton} from '../../components/ui/skeleton';
import {Tabs,TabsList,TabsTrigger} from '../../components/ui/tabs';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading,DestinationChip} from '../../components/admin/AdminShared';
import {QuestionReportsPanel} from '../../components/studio/QuestionReportsPanel';
import {AiReviewPanel} from '../../components/studio/AiReviewPanel';
import {MockBookPanel} from '../../components/studio/MockBookPanel';
import {ManualSolvePanel} from '../../components/studio/ManualSolve';

function HeldMocks({owner}){
 const [items,setItems]=useState(null),[error,setError]=useState('');
 useEffect(()=>{api('/admin/review/held').then(d=>setItems(d.items)).catch(e=>setError(e.message));},[]);
 if(error)return <ErrorBox error={error}/>;
 if(!items)return <Skeleton className="h-40"/>;
 if(!items.length)return <p className="admin-empty" data-testid="held-empty">No held mocks. Everything uploaded is either ready or live.</p>;
 return <ul className="admin-list" data-testid="held-list">{items.map(m=><li key={m.id} className="admin-row is-held" data-testid={'held-'+m.id}><div className="admin-row-main"><strong>{m.label}</strong><small>{m.book_title}</small>{m.destination&&<DestinationChip exam={m.destination.exam_name} section={m.destination.section_name} testId={'held-destination-'+m.id}/>}<ul className="admin-reasons" data-testid={'held-reasons-'+m.id}>{m.issues.map((x,i)=><li key={i}>{x}</li>)}</ul></div>{owner&&<Button asChild variant="outline"><Link to={'/super-admin/upload?book='+m.book_id} data-testid={'held-fix-'+m.id}><Wrench size={15}/>Open & fix</Link></Button>}</li>)}</ul>;
}

const TABS=[['held','Held mocks'],['reports','Question reports'],['solutions','Solutions'],['checks','Mock book checks']];

export default function AdminReview(){
 const {user}=useAuth();const owner=user.role==='owner';const [params,setParams]=useSearchParams();
 const tab=TABS.some(([v])=>v===params.get('tab'))?params.get('tab'):'held';
 return <div className="admin-page" data-testid="admin-review-page">
  <AdminCrumbs items={[{label:'Super Admin',to:owner?'/super-admin':undefined},{label:'Review'}]}/>
  <AdminHeading testId="admin-review-title" title="Review" text="Held mocks and their reasons, student question reports and solution checks. Nothing here changes scores by itself."/>
  <Tabs value={tab} onValueChange={v=>setParams({tab:v})}><TabsList className="admin-tabs">{TABS.map(([v,l])=><TabsTrigger key={v} value={v} data-testid={'review-tab-'+v}>{l}</TabsTrigger>)}</TabsList></Tabs>
  <div className="admin-tab-body">{tab==='held'&&<HeldMocks owner={owner}/>}{tab==='reports'&&<QuestionReportsPanel/>}{tab==='solutions'&&<><ManualSolvePanel/><AiReviewPanel/></>}{tab==='checks'&&<MockBookPanel/>}</div>
 </div>;
}
