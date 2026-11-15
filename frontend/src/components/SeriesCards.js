import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {ArrowUpRight,CalendarDays,Clock3,Radio} from 'lucide-react';
import {api} from '../lib/api';
import {Button} from './ui/button';

const day=d=>new Date(d+'T12:00:00+05:30').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Kolkata'});
const clock=t=>{const [h,m]=t.split(':').map(Number);return `${h%12||12}:${String(m).padStart(2,'0')} ${h<12?'AM':'PM'}`;};

function SeriesCard({s}){
 const t=s.today_slot,live=t?.ready&&['live','start_closed'].includes(t.state),path='/series/'+s.id;
 return <section className={'series-exam-card home-card-surface exam-color-'+(s.exam.color||'teal')} data-testid={'series-card-'+s.id}>
  <Link className="home-card-whole-link" to={path} aria-label={'Open '+s.title} data-testid={'series-card-link-'+s.id}/>
  <span className="series-exam-card-eyebrow">{s.exam.name} · ALL INDIA</span>
  <h2>{s.title}</h2>
  <div className="series-exam-card-facts"><span><CalendarDays size={15}/>{day(s.first_date)} – {day(s.last_date)}</span><span><Clock3 size={15}/>{s.total} tests · opens {clock(s.open_time)} IST</span>
   <span className={'series-live-badge'+(live?' is-live':'')} data-testid={'series-card-state-'+s.id}><Radio size={13}/>{live?'Live today':s.today<s.first_date?'Starts '+day(s.first_date):s.today>s.last_date?'Practice archive':'Today'}</span></div>
  <Button asChild className="series-exam-card-cta"><Link to={path} data-testid={'series-card-open-'+s.id}>Open the series<ArrowUpRight size={16}/></Link></Button>
 </section>;
}

export function SeriesCards(){
 const [items,setItems]=useState([]);
 useEffect(()=>{api('/series').then(d=>setItems(d.items.filter(s=>!s.builtin))).catch(()=>setItems([]));},[]);
 if(!items.length)return null;
 return <div className={'series-exam-cards count-'+Math.min(items.length,3)} data-testid="series-exam-cards">{items.map(s=><SeriesCard key={s.id} s={s}/>)}</div>;
}
