import React from 'react';
import {useNavigate} from 'react-router-dom';
import {Lines} from './Lines';
import {Block} from './parts';
import {detailPath,istTime} from '../seriesData';

const ready=d=>d.class?.state==='ready'&&d.class.average!=null;

export function VsClass({days}){
  const nav=useNavigate(),rows=days.filter(ready);
  if(!rows.length)return <Block title="Aap vs average vs topper" testId="si-vs"><p className="si-note" data-testid="si-vs-wait">{days.some(d=>d.class?.state==='sealed')?'Har live din ka average aur topper raat 11:59 PM ke baad, rank ke saath aata hai.':'Live din dene par yahan har din ka average aur topper dikhega.'}</p></Block>;
  const series=[{key:'you',label:'Aap',color:'#C1121F',points:rows.map(d=>({day:d.day,value:d.score}))},
    {key:'average',label:'Average',color:'#6B7280',dash:'5 4',points:rows.map(d=>({day:d.day,value:d.class.average}))},
    {key:'topper',label:'Topper',color:'#E9A92F',points:rows.map(d=>({day:d.day,value:d.class.topper}))}];
  return <Block title="Aap vs average vs topper" note="Live din, rank aane ke baad" testId="si-vs">
    <Lines series={series} hi={rows[0].maximum} label="Your marks against the day's average and topper" testId="si-vs-chart"/>
    <div className="si-rows">{[...rows].reverse().slice(0,5).map(d=><button type="button" className="si-row is-link" key={d.day} onClick={()=>nav(detailPath(d.attempt_id),{state:{fromList:true}})} data-testid={'si-vs-day-'+d.day}>
      <span className="si-row-main"><small>Day {d.day}</small><b>{d.score}</b> aap</span><span><small>Average</small><b>{d.class.average}</b></span>
      <span><small>Topper</small><b>{d.class.topper}</b></span><span><small>Students</small><b>{d.class.students}</b></span>
    </button>)}</div>
  </Block>;
}

export function DayVsClass({day}){
  if(!day?.class)return null;
  if(day.class.state==='sealed')return <div className="sh-card si-vs-day" data-testid="si-day-vs-sealed"><p className="si-note">Is din ka average aur topper {istTime(day.class.release_at)} ke baad, rank ke saath aayega.</p></div>;
  const {average,topper,students}=day.class,gap=average==null?null:Math.round((day.score-average)*10)/10;
  const items=[['Aap',day.score],['Average',average??'—'],['Topper',topper??'—'],['Average se',gap==null?'—':(gap>=0?'+':'')+gap]];
  return <div className="sh-card si-vs-day" data-testid="si-day-vs">
    <div className="sh-label"><h2>Aap vs average vs topper</h2><span>{students} students</span></div>
    <div className="sh-stats">{items.map(([l,v])=><div key={l} data-testid={'si-day-vs-'+l.split(' ')[0].toLowerCase()}><small>{l}</small><strong>{v}</strong></div>)}</div>
  </div>;
}
