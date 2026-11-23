import React,{useRef,useState} from 'react';
import {Link} from 'react-router-dom';
import {ArrowUpRight} from 'lucide-react';
import {SectionLabel} from './SeriesHeader';
import {TodayCard,DayCard} from './DayCards';
import {DayStrip,DayMap} from './DayStrip';
import {ScoreTrend,trendSummary} from './ScoreTrend';
import {ResultsList} from './ResultsList';
import {LIST_PATH,istTime} from './seriesData';

export function HubToday({data,days,user,history,early}){
  const [picked,setPicked]=useState(null),[all,setAll]=useState(false),strip=useRef(null);
  const today=days.find(d=>d.isToday);
  const selected=picked??today?.day??(data.today>data.last_date?days.length:1);
  const sel=days.find(d=>d.day===selected),trend=trendSummary(days),items=history?.items||[];
  const dayOf=date=>days.find(d=>d.date===date)?.day;
  return <div className="sh-sections">
    <section><SectionLabel title="Today" right={<span data-testid="series-timing-note">{today?`Live ${istTime(today.slot.opens_at)} – ${istTime(today.slot.closes_at)} IST`:'Live 12:01 AM – 11:59 PM IST'}</span>}/><TodayCard series={data} day={today}/></section>
    {early}
    <section ref={strip} className="sh-scroll-target"><SectionLabel title="All days" right={<span>swipe ›</span>}/><DayStrip days={days} selected={selected} onSelect={setPicked}/>{sel&&!sel.isToday&&<DayCard d={sel}/>}</section>
    <section><SectionLabel title="Score trend" right={trend&&<span data-testid="series-trend-summary">Best {trend.best} · Avg {trend.avg}</span>}/><ScoreTrend days={days}/></section>
    {user&&<section><SectionLabel title="My results" right={<span className="sh-label-actions">{items.length>3&&<button type="button" data-testid="series-results-toggle" onClick={()=>setAll(v=>!v)}>{all?'show less':'view all'}</button>}<Link to={LIST_PATH} state={{fromHub:true}} data-testid="series-all-analysis-link">Analysis<ArrowUpRight size={14}/></Link></span>}/>{history?<ResultsList items={items} dayOf={dayOf} limit={all?items.length:3}/>:<div className="sh-load sh-skeleton">Loading your results…</div>}</section>}
    <section><SectionLabel title={`${data.total}-day map`}/><DayMap days={days} selected={selected} onSelect={d=>{setPicked(d);strip.current?.scrollIntoView({behavior:'smooth',block:'start'});}}/></section>
  </div>;
}
