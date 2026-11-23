import React from 'react';
import {useNavigate} from 'react-router-dom';
import {ChevronRight,LineChart} from 'lucide-react';
import {SERIES_PATH} from '../LiveSeriesBanner';
import {openAnalysis,shortDate} from './seriesData';

export function ResultsList({items,dayOf,limit}){
  const nav=useNavigate();
  if(!items.length)return <div className="sh-card sh-empty" data-testid="series-results-empty"><span><LineChart size={26}/></span><h3>Your first attempt starts your story.</h3><p>Series attempts and released results appear here. No sample scores are shown.</p></div>;
  const open=a=>a.summary?openAnalysis(nav,a.id):nav((a.resumable?'/attempts/':'/results/')+a.id,{state:{returnTo:SERIES_PATH}});
  return <div className="sh-results">{items.slice(0,limit).map(a=>{const day=dayOf(a.series_date);return <button type="button" key={a.id} className={'sh-result tone-'+(a.summary?'done':a.resumable?'today':'upcoming')} data-testid={'series-hub-result-'+a.id} onClick={()=>open(a)}>
    <span className="sh-result-text"><small>{day?`DAY ${day} · `:''}{a.mode==='series_live'?'LIVE':'PRACTICE'}{a.series_date?` · ${shortDate(a.series_date).toUpperCase()}`:''}</small><strong>{a.title}</strong></span>
    <b>{a.summary?`${a.summary.score}/${a.summary.maximum}`:a.resumable?'Resume':'Preparing'}</b><ChevronRight size={20}/>
  </button>;})}</div>;
}
