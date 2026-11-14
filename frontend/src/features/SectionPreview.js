import React,{useEffect,useState} from 'react';
import {useParams} from 'react-router-dom';
import {ChevronRight,Smartphone,AlertTriangle} from 'lucide-react';
import {api} from '../lib/api';
import {StatusChip} from '../components/admin/AdminShared';
import {previewWhen} from '../components/admin/PreviewLink';
import {Empty} from '../components/Shared';
import {Skeleton} from '../components/ui/skeleton';

const NOTE={live:'Students see this now',scheduled:'Opens to students at its start time',ready:'Ready. Goes live when you publish it',publishing:'Publishing now',held:'Held. Needs a fix before it can go live',draft:'Draft. Not published yet',paused:'Not live yet',unlive:'Switched off for students',ended:'Its time window has ended'};
const LABEL={live:'Live',ready:'Ready',paused:'Not live yet'};

function Row({t,n}){
 const meta=[t.book?'From '+t.book:null,`${t.count} questions`,t.minutes?`${t.minutes} min`:null,t.state==='scheduled'&&t.start_at?'Opens '+previewWhen(t.start_at):NOTE[t.state]].filter(Boolean).join(' · ');
 return <li className={'admin-row'+(t.state==='live'?'':' is-pending')} data-testid={'section-preview-item-'+n}>
  <span className="admin-test-index" aria-hidden="true">{String(n).padStart(2,'0')}</span>
  <div className="admin-row-main"><strong data-testid={'section-preview-title-'+n}>{t.title}</strong><small>{meta}</small></div>
  <StatusChip state={t.state} label={LABEL[t.state]} testId={'section-preview-state-'+n}/>
 </li>;
}

function Warnings({data}){
 const notes=[!data.exam.shown&&`${data.exam.name} is hidden from Home. Students cannot reach this section until you choose Show on Home.`,
  data.section.hidden&&'This section is hidden from students.',
  !data.live_count&&'Students do not see this section yet because it has no live test.'].filter(Boolean);
 return notes.map(n=><p key={n} className="admin-note warn section-preview-warn" data-testid="section-preview-warning"><AlertTriangle size={15}/>{n}</p>);
}

function List({items,chapters}){
 if(!items.length)return <Empty title="Nothing in this section yet.">Tests appear here as soon as they are added to this section.</Empty>;
 const groups=[];let n=0;
 items.forEach(t=>{const key=!chapters?'':t.book?'Waiting to publish':t.subject||'';let g=groups.find(x=>x.key===key);if(!g){g={key,items:[]};groups.push(g);}g.items.push(t);});
 return groups.map(g=><div key={g.key} className="section-preview-group">{g.key&&<h2 data-testid={'section-preview-subject-'+g.key.toLowerCase().replace(/\s+/g,'-')}>{g.key}</h2>}<ol className="admin-list" data-testid="section-preview-list">{g.items.map(t=>{n+=1;return <Row key={n} t={t} n={n}/>;})}</ol></div>);
}

export default function SectionPreview(){
 const {token}=useParams();const [data,setData]=useState(null),[error,setError]=useState('');
 useEffect(()=>{setData(null);setError('');api('/preview/sections/'+encodeURIComponent(token)).then(setData).catch(e=>setError(e.message));},[token]);
 if(error)return <div className="container page"><Empty title="This preview link does not open." >{error}</Empty></div>;
 if(!data)return <div className="container page section-preview" data-testid="section-preview-loading"><Skeleton className="h-10 w-2/3"/><Skeleton className="h-64 mt-6"/></div>;
 return <div className="container page section-preview" data-testid="section-preview-page">
  <p className="section-preview-banner" data-testid="section-preview-banner"><Smartphone size={16}/>Owner preview. Students only see the Live tests. Link works until {previewWhen(data.expires_at)}.</p>
  <p className="admin-student-path" data-testid="section-preview-path"><span>Home</span><ChevronRight size={14}/><span>{data.exam.name}</span><ChevronRight size={14}/><strong>{data.section.name}</strong></p>
  <header className="exam-simple-heading"><span className="eyebrow" data-testid="section-preview-exam">{data.exam.name}</span><h1 data-testid="section-preview-title">{data.section.name}</h1>{data.section.description&&<p>{data.section.description}</p>}</header>
  <Warnings data={data}/>
  <p className="section-preview-count" aria-live="polite" data-testid="section-preview-count">{data.live_count} live now · {data.items.length-data.live_count} not live yet</p>
  <List items={data.items} chapters={data.section.layout==='chapters'}/>
 </div>;
}
