import React from 'react';
import {Link} from 'react-router-dom';
import {ArrowUpRight,Clock3,Bookmark,CheckCircle2,History,GitCompareArrows} from 'lucide-react';
import {Button} from '../ui/button';
import {Checkbox} from '../ui/checkbox';
import {ReportButton} from '../ReportButton';
import {SavePaperButton} from '../SavePaperButton';

const date=value=>new Date(value*1000).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'});
const labels={active:'In progress',completed:'Completed',expired:'Time expired',grading:'Preparing result',embargoed:'Result sealed'};
export const AttemptCard=({item,returnTo,selected,onSelect,comparisonFull})=>{
 const s=item.summary;
 const accuracy=typeof s?.correct==='number'&&typeof s?.attempted==='number'?(s.attempted?Math.round(1000*s.correct/s.attempted)/10:null):(s?.accuracy??null);
 return <article className={'test-library-card state-'+item.status} data-testid={'my-attempt-'+item.id}>
  <div className="test-card-top"><span>{item.exam} · {item.mode==='retry'?'Revision retry':'Paper v'+item.version}</span><span className="library-status" data-testid={'my-attempt-status-'+item.id}>{labels[item.status]}</span></div>
  <h3 data-testid={'my-attempt-title-'+item.id}>{item.title}</h3><p className="library-date"><History size={14}/>{date(item.started_at)}</p>
  {s?<div className="test-score-line" data-testid={'my-attempt-score-'+item.id}><strong>{s.score}<small> / {s.maximum}</small></strong><span>{accuracy==null?'Accuracy unavailable':accuracy+'% accuracy'}</span></div>:<p data-testid={'my-attempt-save-state-'+item.id}>{item.resumable?`${item.saved_answers} answers saved · ${item.deadline?Math.ceil(item.remaining_seconds/60)+' min remaining at refresh':'untimed'}`:item.status==='expired'?'Your original deadline has passed. This attempt cannot resume.':'Your submitted work is retained; marks are not released yet.'}</p>}
  {item.last_saved_at&&<small data-testid={'my-attempt-last-saved-'+item.id}>Last server acknowledgement: {date(item.last_saved_at)}</small>}
  <div className="test-card-actions"><Button asChild><Link state={{returnTo}} to={(item.resumable?'/attempts/':'/results/')+item.id} data-testid={'my-attempt-open-'+item.id}>{item.resumable?'Resume original attempt':s?'Open result':'Check result'}<ArrowUpRight size={16}/></Link></Button>{item.report_allowed&&<ReportButton id={item.id} scoreVersion="original"/>}</div>
  {item.compare_eligible&&<label className="compare-check"><Checkbox checked={selected} onCheckedChange={()=>onSelect(item)} disabled={!selected&&comparisonFull} data-testid={'compare-select-'+item.id}/><span><GitCompareArrows size={14}/> Compare this attempt</span></label>}
 </article>;
};

export const SavedPaperCard=({item,returnTo,onRemoved})=><article className="test-library-card saved-paper-card" data-testid={'saved-paper-card-'+item.set_id}>
 <div className="test-card-top"><span>{item.exam}</span><span className="library-status" data-testid={'saved-paper-availability-'+item.set_id}>{item.available?'Available':'Unavailable'}</span></div><h3>{item.title}</h3><p className="library-date"><Bookmark size={14}/>Saved {date(item.saved_at)}</p>
 {item.available?<p><Clock3 size={15}/> {item.paper.count} questions · {item.paper.rules.minutes||'Untimed'}{item.paper.rules.minutes?' min':''} · +{item.paper.rules.correct} / {item.paper.rules.wrong}</p>:<p className="unavailable-copy" data-testid={'saved-paper-reason-'+item.set_id}>{item.reason}</p>}
 <div className="test-card-actions">{item.available&&<Button asChild><Link state={{returnTo}} to={'/sets/'+item.set_id} data-testid={'saved-paper-open-'+item.set_id}>View rules & start<ArrowUpRight size={16}/></Link></Button>}<SavePaperButton setId={item.set_id} initialSaved={true} onChange={value=>{if(!value)onRemoved()}}/></div><small><CheckCircle2 size={13}/> Saving never creates an attempt or starts its timer.</small>
</article>;
