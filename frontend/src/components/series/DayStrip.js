import React,{useEffect,useRef} from 'react';
import {useNavigate} from 'react-router-dom';
import {goDay,shortDate} from './seriesData';

const Marks=({d,prefix})=>d.scored?<em data-testid={prefix+d.day}>{d.scored.summary.score}</em>:null;

export function DayStrip({days,selected,onSelect}){
  const nav=useNavigate(),ref=useRef(null),first=useRef(true);
  useEffect(()=>{
    const box=ref.current,el=box?.querySelector(`[data-day="${selected}"]`);
    if(el)box.scrollTo({left:Math.max(0,el.offsetLeft-box.offsetLeft-120),behavior:first.current?'auto':'smooth'});
    first.current=false;
  },[selected,days.length]);
  return <div className="sh-strip" ref={ref} data-testid="series-day-strip">{days.map(d=><button type="button" key={d.day} data-day={d.day} className={'sh-chip tone-'+d.tone+(d.day===selected?' on':'')} data-testid={'series-chip-'+d.day} aria-label={`Day ${d.day}, ${shortDate(d.date)}, ${d.label}${d.scored?`, ${d.scored.summary.score} marks`:''}`} aria-pressed={d.day===selected} onClick={()=>goDay(nav,d,onSelect)}>
    <small>{d.isToday?'TODAY':'DAY'}</small><strong>{d.day}</strong><Marks d={d} prefix="series-chip-marks-"/>
  </button>)}</div>;
}

const LEGEND=[['done','Completed'],['today','Today'],['upcoming','Upcoming'],['missed','Missed']];

export function DayMap({days,selected,onSelect}){
  const nav=useNavigate(),legend=LEGEND.filter(([t])=>t!=='missed'||days.some(d=>d.tone==='missed'));
  return <div className="sh-card sh-map" data-testid="series-calendar">
    <div className="sh-map-grid">{days.map(d=><button type="button" key={d.day} className={'sh-cell tone-'+d.tone+(d.isToday||d.day===selected?' on':'')} data-testid={'series-calendar-day-'+d.day} aria-label={`Day ${d.day}, ${shortDate(d.date)}, ${d.label}${d.scored?`, ${d.scored.summary.score} marks`:''}`} title={`Day ${d.day} · ${shortDate(d.date)} · ${d.label}`} onClick={()=>goDay(nav,d,onSelect)}>
      {d.scored?<Marks d={d} prefix="series-map-marks-"/>:(d.isToday||d.day===selected)?<b>{d.day}</b>:null}
    </button>)}</div>
    <div className="sh-legend">{legend.map(([t,l])=><span key={t}><i className={'tone-'+t}/>{l}</span>)}</div>
  </div>;
}
