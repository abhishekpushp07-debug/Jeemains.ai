import React,{useEffect,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {ArrowLeft,ArrowUpRight,CalendarDays,Radio,Archive,BarChart3} from 'lucide-react';
import {useAuth} from '../lib/auth';
import {api} from '../lib/api';
import {Button} from '../components/ui/button';
import {Tabs,TabsList,TabsTrigger} from '../components/ui/tabs';
import {Loading,ErrorBox,Empty} from '../components/Shared';

const dayLabel=d=>new Date(d+'T12:00:00+05:30').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Kolkata'});
const at=t=>new Date(t*1000).toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit',timeZone:'Asia/Kolkata'});
const STATE={live:'LIVE TODAY',archive:'PRACTICE',start_closed:'STARTS CLOSED',ended:'DAY ENDED',upcoming:'UPCOMING'};

function Slot({s,path,attempt}){
 return <article className={'series-slot state-'+s.state} data-testid={'series-day-'+s.day}>
  <div className="series-slot-top"><span>TEST {String(s.day).padStart(2,'0')}</span><span>{s.state==='live'&&!s.ready?'AWAITING PAPER':STATE[s.state]}</span></div>
  <h3>{s.title}</h3><p><CalendarDays size={15}/>{dayLabel(s.date)} · {at(s.opens_at)} – last start {at(s.last_start_at)} IST</p>
  <div className="series-actions">{attempt&&<Button asChild variant="outline"><Link to={(attempt.resumable?'/attempts/':'/results/')+attempt.id} state={{returnTo:path}} data-testid={'series-resume-'+s.day}>{attempt.resumable?'Resume live attempt':'Open live result'}</Link></Button>}
   {s.can_start&&(!attempt||s.state==='archive')&&<Button asChild><Link to={'/sets/'+s.set_id} state={{returnTo:path}} data-testid={'series-start-'+s.day}>{s.state==='archive'?'Practise this paper':'Check device & start'}<ArrowUpRight size={16}/></Link></Button>}</div>
 </article>;
}

export default function SeriesPage(){
 const {seriesId}=useParams();const {user}=useAuth();const path='/series/'+seriesId;
 const [data,setData]=useState(null),[error,setError]=useState(''),[history,setHistory]=useState(null),[tab,setTab]=useState('today');
 useEffect(()=>{api(`/series/${seriesId}/schedule`).then(setData).catch(e=>setError(e.message));},[seriesId]);
 useEffect(()=>{if(user)api(`/series/${seriesId}/history`).then(setHistory).catch(()=>setHistory({items:[]}));},[seriesId,user]);
 if(error)return <div className="container page"><Empty title="This series is not open." action={<Button asChild><Link to="/home">Back to Home</Link></Button>}>{error}</Empty></div>;
 if(!data)return <Loading/>;
 const today=data.today_slot,live=history?.items.find(a=>a.mode==='series_live'&&a.series_date===data.today),archive=data.slots.filter(s=>s.state==='archive').reverse();
 return <div className={'container page series-hub exam-color-'+(data.exam.color||'teal')} data-testid="generic-series-hub">
  <Link className="breadcrumb" to={user?'/home':'/'} data-testid="series-back-home"><ArrowLeft size={15}/>Back to home</Link>
  <header className="series-hub-header"><div><span className="series-kicker">{data.exam.name.toUpperCase()} · ALL INDIA</span><h1 data-testid="series-hub-title">{data.title}</h1><p data-testid="series-hub-dates">{dayLabel(data.first_date)} – {dayLabel(data.last_date)} · {data.total} scheduled tests · Free</p></div></header>
  <Tabs value={tab} onValueChange={setTab} className="series-tabs"><TabsList>{[['today','Live & schedule',Radio],['archive','Practice archive',Archive],['results','My results',BarChart3]].map(([v,l,Icon])=><TabsTrigger key={v} value={v} data-testid={'series-tab-'+v}><Icon size={16}/>{l}</TabsTrigger>)}</TabsList></Tabs>
  {tab==='today'&&<>{today?<Slot s={today} path={path} attempt={live}/>:<div className="series-empty" data-testid="series-prelaunch"><Radio size={28}/><h2>{data.today<data.first_date?`The first test opens ${dayLabel(data.first_date)}.`:'The live series has ended.'}</h2><p>Live results release when each day closes. Earlier days move to the practice archive.</p></div>}
   <h2 className="series-section-title">The {data.total}-day schedule</h2>
   <div className="series-calendar" data-testid="series-calendar">{data.slots.map(s=><div key={s.day} className={'series-calendar-day '+s.state}><strong>{String(s.day).padStart(2,'0')}</strong><span>{dayLabel(s.date).replace(/ 20\d\d/,'')}</span><small>{s.date===data.today?'Today':s.state==='archive'?'Archive':s.state==='upcoming'?'Upcoming':s.ready?'Scheduled':'Awaiting paper'}</small></div>)}</div></>}
  {tab==='archive'&&(archive.length?<div className="series-slot-grid">{archive.map(s=><Slot key={s.day} s={s} path={path}/>)}</div>:<div className="series-empty" data-testid="series-archive-empty"><Archive/><h2>The archive begins after day one.</h2></div>)}
  {tab==='results'&&(!user?<div className="series-empty"><h2>Your results belong to your profile.</h2><Button asChild><Link to={'/login?next='+encodeURIComponent(path)} data-testid="series-signin">Sign in</Link></Button></div>
   :!history?<Loading/>:history.items.length?<div className="series-result-list">{history.items.map(a=><article key={a.id} className="series-result-row" data-testid={'series-result-'+a.id}><div><small>{a.mode==='series_live'?'LIVE ATTEMPT':'ARCHIVE PRACTICE'} · {dayLabel(a.series_date)}</small><h3>{a.title}</h3><p>{a.summary?`${a.summary.score} / ${a.summary.maximum} marks`:a.status==='embargoed'?'Result releases when the day closes':a.resumable?'Attempt in progress':'Preparing result'}</p></div><Button asChild variant="outline"><Link to={(a.resumable?'/attempts/':'/results/')+a.id} state={{returnTo:path}}>{a.resumable?'Resume':'Result'}<ArrowUpRight size={16}/></Link></Button></article>)}</div>
   :<div className="series-empty" data-testid="series-history-empty"><h2>Your first attempt starts your story.</h2></div>)}
  <ErrorBox error=""/>
 </div>;
}
