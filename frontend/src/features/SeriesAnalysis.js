import React,{useState} from 'react';
import {useLocation,useNavigate,useParams,useSearchParams} from 'react-router-dom';
import {BarChart3,ArrowUpRight} from 'lucide-react';
import {useAuth} from '../lib/auth';
import {Loading,ErrorBox} from '../components/Shared';
import {SERIES_PATH} from '../components/LiveSeriesBanner';
import {SeriesHeader} from '../components/series/SeriesHeader';
import {LIST_PATH,detailPath,shortDate,useSeriesHub} from '../components/series/seriesData';
import {AnalysisWorkspace} from '../components/analysis/AnalysisWorkspace';
import {useAnalysis} from '../components/analysis/useAnalysis';
import {ShareGate} from '../components/mission/ShareGate';
import {isResultLocked,unlockResult} from '../components/mission/gate';

const kicker=(a,day)=>`${day?`DAY ${day} · `:''}${a.mode==='series_live'?'LIVE':'PRACTICE'}${a.series_date?` · ${shortDate(a.series_date).toUpperCase()}`:''}`;
const when=a=>a.submitted_at||a.started_at;

const Stats=({s})=><div className="sh-stats">{[['Marks',`${s.score}`,`/${s.maximum}`],['Correct',s.correct],['Incorrect',s.incorrect],['Accuracy',s.accuracy==null?'—':`${s.accuracy}%`]].map(([l,v,m])=><div key={l}><small>{l}</small><strong>{v}{m&&<em>{m}</em>}</strong></div>)}</div>;

function Row({a,day}){
  const nav=useNavigate();
  const open=()=>a.summary?nav(detailPath(a.id),{state:{fromList:true}}):nav('/results/'+a.id,{state:{returnTo:LIST_PATH}});
  return <article className="sh-arow" data-testid={'series-analysis-row-'+a.id}>
    <div className="sh-arow-text"><small>{kicker(a,day)}</small><h3>{a.title}</h3>{a.summary?<Stats s={a.summary}/>:<p>Result ban raha hai. Thodi der mein yahan dikhega.</p>}</div>
    <button type="button" className="sh-red is-action" onClick={open} data-testid={'series-analysis-open-'+a.id}><span className="sh-red-body"><BarChart3 size={18}/><strong>{a.summary?'Analysis dekho':'Result kholo'}</strong><ArrowUpRight size={16}/></span></button>
  </article>;
}

function AnalysisList(){
  const nav=useNavigate(),loc=useLocation(),{days,history,error,retry}=useSeriesHub();
  const back=()=>loc.state?.fromHub?nav(-1):nav(SERIES_PATH,{replace:true});
  const rows=(history?.items||[]).filter(a=>!a.resumable).sort((a,b)=>when(b)-when(a));
  const dayOf=date=>days.find(d=>d.date===date)?.day;
  return <div className="container page sh-page" data-testid="series-analysis-list">
    <SeriesHeader eyebrow="ALL INDIA SERIES · ATTEMPTED DAYS" title="Analysis" onBack={back} backTestId="series-analysis-back" titleTestId="series-analysis-title"/>
    <p className="sh-dates">Har attempt kiya hua din, sabse naya sabse upar.</p>
    <ErrorBox error={error} retry={retry}/>{!history&&!error&&<Loading text="Aapke din khul rahe hain…"/>}
    {history&&!rows.length&&<div className="sh-card sh-empty" data-testid="series-analysis-empty"><span><BarChart3 size={26}/></span><h3>Abhi koi din attempt nahi hua.</h3><p>Live test do. Submit karte hi uska analysis yahan sabse upar aa jayega.</p></div>}
    <div className="sh-arows">{rows.map(a=><Row key={a.id} a={a} day={dayOf(a.series_date)}/>)}</div>
  </div>;
}

function AnalysisDetail({id}){
  const nav=useNavigate(),loc=useLocation(),[params]=useSearchParams(),{user}=useAuth(),{days,history}=useSeriesHub();
  const [locked,setLocked]=useState(()=>isResultLocked(id));
  const compare=params.get('mode')==='compare',vs=/^(topper|top10|average|user:[0-9a-f]{16})$/.test(params.get('vs')||'')?params.get('vs'):'topper';
  const analysis=useAnalysis(id,user.id,'original',!locked,compare,vs);
  if(locked)return <ShareGate onOpen={()=>{unlockResult(id);setLocked(false);}}/>;
  const item=history?.items.find(a=>a.id===id),day=item&&days.find(d=>d.date===item.series_date)?.day;
  const back=()=>loc.state?.fromList?nav(-1):nav(LIST_PATH,{replace:true});
  const solutions=q=>nav('/results/'+id+'?view=solutions'+(typeof q==='string'?'&question='+q:''),{state:{returnTo:detailPath(id)}});
  return <div className="container page sh-page sh-analysis-page" data-testid="series-analysis-detail">
    <SeriesHeader eyebrow={item?kicker(item,day):'ALL INDIA SERIES'} title={day?`Day ${day} · Analysis`:'Analysis'} onBack={back} backTestId="series-analysis-detail-back" titleTestId="series-analysis-detail-title"/>
    {item&&<p className="sh-dates">{item.title}</p>}
    {item?.summary&&<div className="sh-card sh-detail-stats" data-testid="series-analysis-stats"><Stats s={item.summary}/></div>}
    <AnalysisWorkspace id={id} state={analysis} onOpen={solutions} onSolutions={()=>solutions()} onRetry={null} extra={null}/>
  </div>;
}

export default function SeriesAnalysis(){
  const {attemptId}=useParams();
  return attemptId?<AnalysisDetail key={attemptId} id={attemptId}/>:<AnalysisList/>;
}
