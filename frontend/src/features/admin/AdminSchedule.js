import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {ExternalLink} from 'lucide-react';
import {api} from '../../lib/api';
import {Button} from '../../components/ui/button';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading,StatusChip} from '../../components/admin/AdminShared';
import {sourceLink} from '../../components/admin/SectionTests';
import {SeriesSchedulePanel} from '../../components/studio/SeriesSchedulePanel';

const ist=x=>x?new Date(x*1000).toLocaleString('en-IN',{timeZone:'Asia/Kolkata',dateStyle:'medium',timeStyle:'short'})+' IST':'—';

function Timed(){
 const [items,setItems]=useState(null),[error,setError]=useState('');
 useEffect(()=>{api('/admin/schedule/timed').then(d=>setItems(d.items)).catch(e=>setError(e.message));},[]);
 if(error)return <ErrorBox error={error}/>;
 if(!items)return <Skeleton className="h-24"/>;
 if(!items.length)return <p className="admin-empty" data-testid="timed-empty">No scheduled tests or open time windows right now.</p>;
 return <ul className="admin-list" data-testid="timed-list">{items.map(t=>{const link=sourceLink(t);return <li key={t.id} className="admin-row" data-testid={'timed-'+t.id}><div className="admin-row-main"><strong>{t.title}</strong><small>{t.exam} · opens {ist(t.start_at)}{t.end_at?` · closes ${ist(t.end_at)}`:''}</small></div><StatusChip state={t.state} testId={'timed-state-'+t.id}/>{link&&<Button asChild variant="ghost" size="icon"><Link to={link} aria-label={'Open '+t.title} data-testid={'timed-open-'+t.id}><ExternalLink size={16}/></Link></Button>}</li>;})}</ul>;
}

export default function AdminSchedule(){
 return <div className="admin-page" data-testid="admin-schedule-page">
  <AdminCrumbs items={[{label:'Super Admin',to:'/super-admin'},{label:'Schedule & Live'}]}/>
  <AdminHeading testId="admin-schedule-title" title="Schedule & Live" text="The All India JEE series and every test with a start time or a time window."/>
  <section className="admin-panel"><h2>Tests with a time window</h2><Timed/></section>
  <SeriesSchedulePanel/>
 </div>;
}
