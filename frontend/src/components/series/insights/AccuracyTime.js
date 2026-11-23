import React from 'react';
import {Lines} from './Lines';
import {Block,avg} from './parts';

function tip(days){
  const last=days.slice(-3),n=last.length;
  const m=avg(last.map(d=>d.minutes)),acc=avg(last.map(d=>d.accuracy).filter(v=>v!=null)),rate=avg(last.map(d=>d.attempt_rate).filter(v=>v!=null));
  const per=avg(last.map(d=>d.sec_per_attempted).filter(v=>v!=null));
  if(m!=null&&rate!=null&&m<150&&rate<70)return `Pichhle ${n} din: average ${m} minute lage aur ${rate}% sawaal try kiye. Time bach raha hai, aur sawaal try kar sakte ho.`;
  if(m!=null&&acc!=null&&m>=170&&acc<60)return `Pichhle ${n} din: poora time (${m} minute) lag raha hai par accuracy ${acc}% hai. Pehle pakke sawaal karo, phir baaki.`;
  return `Pichhle ${n} din: average ${m??'—'} minute, accuracy ${acc==null?'—':acc+'%'}${per!=null?`, ek sawaal par ${per} second`:''}.`;
}

export function AccuracyTime({days}){
  const acc=[{key:'accuracy',label:'Accuracy %',color:'#0E9F6E',points:days.filter(d=>d.accuracy!=null).map(d=>({day:d.day,value:d.accuracy}))},
    {key:'tried',label:'Kitne sawaal try kiye %',color:'#2563EB',dash:'5 4',points:days.filter(d=>d.attempt_rate!=null).map(d=>({day:d.day,value:d.attempt_rate}))}];
  const time=[{key:'minutes',label:'Minute lage',color:'#7C3AED',points:days.map(d=>({day:d.day,value:d.minutes}))}];
  return <Block title="Accuracy aur time" note="Har din" testId="si-accuracy-time">
    <Lines series={acc} lo={0} hi={100} suffix="%" label="Accuracy and questions tried by day" testId="si-accuracy-chart"/>
    <Lines series={time} lo={0} hi={Math.max(180,...days.map(d=>d.minutes))} label="Minutes used by day" testId="si-time-chart"/>
    <p className="si-tip" data-testid="si-time-tip">{tip(days)}</p>
  </Block>;
}
