import React from 'react';
import {useNavigate} from 'react-router-dom';
import {ArrowUpRight,BarChart3,Play} from 'lucide-react';
import {SERIES_PATH} from '../LiveSeriesBanner';
import {istTime,openAnalysis,shortDate} from './seriesData';

function action(d){
  const {live,slot,scored,openPractice}=d;
  if(live?.resumable)return {label:d.isToday?'Resume live attempt':'Resume',to:'/attempts/'+live.id,testid:'series-resume-'+d.day,icon:Play};
  if(scored)return {label:'Open analysis',analysis:scored.id,testid:'series-analysis-'+d.day,icon:BarChart3};
  if(openPractice)return {label:'Resume practice',to:'/attempts/'+openPractice.id,testid:'series-practice-resume-'+d.day,icon:Play};
  if(live)return {label:'Open live result',to:'/results/'+live.id,testid:'series-resume-'+d.day,icon:ArrowUpRight};
  if(slot.can_start&&slot.set_id)return {label:slot.state==='archive'?'Practise this paper':'Start test',to:'/sets/'+slot.set_id,start:slot.state==='archive',testid:'series-start-'+d.day,icon:ArrowUpRight};
  return null;
}

function dayNote(d){
  const {slot}=d;
  if(!slot.ready&&slot.state==='upcoming')return `Opens ${shortDate(d.date)} · ${istTime(slot.opens_at)} IST`;
  if(!slot.ready)return 'Paper abhi publish ho raha hai. Ready hote hi yahin khul jayega.';
  if(slot.state==='upcoming')return `Opens ${shortDate(d.date)} · ${istTime(slot.opens_at)} IST`;
  if(slot.state==='start_closed')return `New starts closed at ${istTime(slot.last_start_at)}. Existing attempts keep their timer.`;
  if(slot.state==='ended')return 'Results released. Archive opens at midnight.';
  return '75 questions · 180 minutes · +4 / −1';
}

export function DayAction({d}){
  const nav=useNavigate(),a=action(d);
  if(!a)return <p className="sh-day-note" data-testid={'series-day-note-'+d.day}>{dayNote(d)}</p>;
  const Icon=a.icon;
  return <button type="button" className="sh-pill" data-testid={a.testid} onClick={()=>a.analysis?openAnalysis(nav,a.analysis):nav(a.to,{state:{returnTo:SERIES_PATH,...(a.start?{autoStart:true}:{})}})}>{a.label}<Icon size={16}/></button>;
}

const Top=({d})=><div className="sh-day-top"><span>DAY {d.day} · {d.label.toUpperCase()}</span><span>{shortDate(d.date).toUpperCase()}</span></div>;

export function TodayCard({series,day}){
  if(!day){
    const before=series.today<series.first_date;
    return <article className="sh-glow sh-glow-sky sh-today" data-testid="series-prelaunch"><div className="sh-today-body">
      <span className="sh-caps">{before?`STARTS ${shortDate(series.first_date).toUpperCase()}`:'SERIES COMPLETE'}</span>
      <h3>{before?`The first challenge opens ${shortDate(series.first_date)}.`:'The live series has ended.'}</h3>
      <p>{before?`Your ${series.total}-day schedule is below. Papers unlock only after publication and their opening time.`:'Continue in the practice archive. Live results stay separate.'}</p>
    </div></article>;
  }
  return <article className="sh-glow sh-glow-sky sh-today" data-testid={'series-day-'+day.day}><div className="sh-today-body">
    <Top d={day}/><h3 data-testid="series-today-title">{day.slot.title}</h3><p>75 Q · 180 min · +4 / −1</p><DayAction d={day}/>
  </div></article>;
}

export function DayCard({d}){
  const s=d.scored?.summary;
  return <article className={'sh-daycard tone-'+d.tone} data-testid={'series-day-card-'+d.day}>
    <Top d={d}/><h3>{d.slot.title}</h3>
    <div className="sh-daycard-foot"><DayAction d={d}/>{s&&<div className="sh-daycard-marks" data-testid={'series-daycard-score-'+d.day}><small>MARKS</small><strong>{s.score}<em>/{s.maximum}</em></strong></div>}</div>
  </article>;
}
