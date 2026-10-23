import React, {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {ArrowUpRight, CalendarDays, Clock3, Layers, Sparkles, Target, Radio} from 'lucide-react';
import {api} from '../lib/api';
import {Button} from './ui/button';
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription} from './ui/dialog';
export const SERIES_PATH = '/series/all-india-jee';

export function useSeriesSchedule() {
  const [data,setData]=useState(null), [error,setError]=useState(''), [refresh,setRefresh]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();
    const load=()=>api(SERIES_PATH,{signal:controller.signal}).then(d=>{setData(d);setError('');}).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
    load();
    const onFocus=()=>{if(!document.hidden)load();};
    document.addEventListener('visibilitychange',onFocus);
    return()=>{controller.abort();document.removeEventListener('visibilitychange',onFocus);};
  },[refresh]);
  useEffect(()=>{
    if(!data)return;
    const next=data.slots.flatMap(s=>[s.opens_at,s.last_start_at+1,s.closes_at,s.archive_at]).filter(t=>t>data.server_now).sort((a,b)=>a-b)[0];
    if(!next)return;
    const timer=setTimeout(()=>setRefresh(v=>v+1),Math.min(2147483647,Math.max(1000,(next-data.server_now)*1000)));
    return()=>clearTimeout(timer);
  },[data]);
  return {data,error,reload:()=>setRefresh(v=>v+1)};
}

export const SeriesExplainer=({open,onOpenChange,today})=><Dialog open={open} onOpenChange={onOpenChange}><DialogContent className="series-dialog" data-testid="series-explainer"><DialogHeader><span className="series-kicker" data-testid="series-modal-eyebrow">THE DAILY FULL-SYLLABUS CHALLENGE</span><DialogTitle data-testid="series-modal-title">62 days. One focused mission.</DialogTitle><DialogDescription data-testid="series-modal-description">All India JEE Mains Test Series · 1 Dec 2026 – 31 Jan 2027</DialogDescription></DialogHeader><div className="series-method"><article data-testid="series-80-factor"><Sparkles/><strong>AI 80-factor analysis on PYQs</strong><p>The series’ stated paper-design approach: use patterns in previous-year questions to focus practice. This is not an AI prediction of the official paper.</p></article><article data-testid="series-60-concepts"><Target/><strong>60+ expected concept matches</strong><p>An expected concept-overlap target—not 60 guaranteed questions or a verified outcome. Actual matches can only be checked after the real exam.</p></article></div><ul className="series-rules" data-testid="series-modal-rules"><li>One owner-uploaded full mock each day. 75 questions · 300 marks · 180 minutes.</li><li>Live window: 12:01 AM–11:59 PM IST. Last start: 8:59:00 PM IST.</li><li>One live attempt per profile. Resume keeps the original deadline.</li><li>Live results and solutions unlock at 11:59 PM IST for fairness.</li><li>Previous days unlock in the practice archive at midnight. Archive attempts stay separate.</li></ul><p className="series-disclaimer" data-testid="series-claims-disclaimer">Independent practice, not affiliated with NTA. The 80-factor and 60+ statements are the series’ proposed approach and target, not independently validated performance claims. Explanations appear only when supplied or manually saved by the owner.</p><div className="series-actions"><Button asChild><Link data-testid="series-modal-hub" to={SERIES_PATH} onClick={()=>onOpenChange(false)}>Open series hub<ArrowUpRight size={16}/></Link></Button>{today?.can_start&&<Button asChild variant="outline"><Link data-testid="series-modal-start" to={'/sets/'+today.set_id} state={{returnTo:SERIES_PATH}}>Check device & start</Link></Button>}</div></DialogContent></Dialog>;

export const LiveSeriesBanner=()=>{
  const {data,error}=useSeriesSchedule();const [open,setOpen]=useState(false);
  const live=!!data?.today_slot?.ready&&['live','start_closed'].includes(data.today_slot.state);
  const ended=data&&data.today>data.last_date;
  return <><section className="flagship-banner" data-testid="all-india-series-banner"><div className="flagship-copy"><div className="flagship-topline"><span className="series-kicker" data-testid="series-flagship-label">THE FLAGSHIP SERIES · FREE</span><button className={'series-live-badge '+(live?'is-live':'')} data-testid="series-live-badge" onClick={()=>setOpen(true)}><Radio size={14}/>{live?(data.today_slot.state==='start_closed'?'Live · starts closed':'Live'):ended?'Practice archive':'Live series · starts 1 Dec'}</button></div><h2 data-testid="series-banner-title">All India<br/><span>JEE Mains Test Series.</span></h2><p data-testid="series-banner-description">A fresh challenge every day.<br className="mobile-break"/> A clearer path to your next attempt.</p><div className="series-banner-facts" data-testid="series-banner-facts"><span><CalendarDays size={16}/>1 Dec 2026 – 31 Jan 2027</span><span><Clock3 size={16}/>3 hours · daily</span><span><Layers size={16}/>62 scheduled tests</span></div><div className="series-actions"><Button className="flagship-primary" data-testid="series-explore-button" onClick={()=>setOpen(true)}>Explore the series<ArrowUpRight size={18}/></Button><Link data-testid="series-banner-hub" to={SERIES_PATH}>Your series hub <ArrowUpRight size={16}/></Link></div>{error&&<small data-testid="series-banner-status-error">Live status unavailable. Open the hub to retry.</small>}</div><div className="flagship-counter" aria-hidden="true"><span>SHOW UP. STEP UP.</span><strong>62<span>DAYS</span></strong><div>ONE TEST. EVERY DAY.</div><small>12:01 AM – 11:59 PM IST<br/>Last start · 8:59 PM</small></div></section><SeriesExplainer open={open} onOpenChange={setOpen} today={data?.today_slot}/></>;
};
