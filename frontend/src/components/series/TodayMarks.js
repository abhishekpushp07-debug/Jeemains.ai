import React from 'react';
import {useNavigate} from 'react-router-dom';
import {BarChart3,ArrowUpRight} from 'lucide-react';
import {SERIES_PATH} from '../LiveSeriesBanner';
import {LIST_PATH,openAnalysis,shortDate} from './seriesData';

function todayAction(today,streak,nav){
  const go=(to,extra)=>()=>nav(to,{state:{returnTo:SERIES_PATH,...extra}});
  if(!today)return {value:'—',note:streak.stage==='prelaunch'?`Pehla test ${shortDate(streak.first_date)}`:'Series poori ho gayi'};
  const {live,slot}=today,s=live?.summary;
  if(s)return {value:s.score,max:s.maximum,note:'Aaj ke marks',onClick:()=>openAnalysis(nav,live.id)};
  if(live?.resumable)return {value:'Resume',note:'Aaj ka test chal raha hai',onClick:go('/attempts/'+live.id)};
  if(live)return {value:'…',note:'Result ban raha hai',onClick:go('/results/'+live.id)};
  if(slot.can_start&&slot.set_id)return {value:'Start',note:'Aaj ka test abhi do',onClick:go('/sets/'+slot.set_id,{autoStart:true})};
  return {value:'—',note:!slot.ready?'Aaj ka paper abhi aa raha hai':'Aaj ke naye start band'};
}

export function TodayMarks({today,streak}){
  const nav=useNavigate();
  const a=todayAction(today,streak,nav);
  return <div className="sh-marks-row" data-testid="today-marks-row">
    <button type="button" className="sh-red" disabled={!a.onClick} onClick={a.onClick} data-testid="today-marks-button">
      <span className="sh-red-body"><small>TODAY'S MARKS</small><strong data-testid="today-marks-value">{a.value}{a.max!=null&&<em>/{a.max}</em>}</strong><i data-testid="today-marks-note">{a.note}</i></span>
    </button>
    <button type="button" className="sh-red is-action" onClick={()=>nav(LIST_PATH,{state:{fromHub:true}})} data-testid="today-analysis-button">
      <span className="sh-red-body"><BarChart3 size={20}/><strong>Analysis</strong><ArrowUpRight size={18}/></span>
    </button>
  </div>;
}
