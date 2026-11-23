import React from 'react';
import {Lines} from './Lines';
import {Block,Dir,colorOf,slug} from './parts';

export function SubjectTrend({subjects}){
  if(!subjects.length)return null;
  const series=subjects.map(s=>({key:slug(s.subject),label:s.subject,color:colorOf(s.subject),points:s.points.map(p=>({day:p.day,value:p.score}))}));
  return <Block title="Subject-wise trend" note="Har din ke marks, subject ke hisaab se" testId="si-subjects">
    <Lines series={series} hi={Math.max(...subjects.map(s=>s.maximum||0))} label="Subject marks by day" testId="si-subject-chart"/>
    <div className="si-dirs">{subjects.map(s=><Dir key={s.subject} name={s.subject} way={s.direction} change={s.change} testId={'si-dir-'+slug(s.subject)}/>)}</div>
    <div className="si-rows">{subjects.map(s=><div className="si-row" key={s.subject} data-testid={'si-subject-'+slug(s.subject)}>
      <span className="si-row-main"><i style={{background:colorOf(s.subject)}}/><small>{s.subject}</small><b>{s.average}</b> avg / {s.maximum}</span>
      <span><small>Best</small><b>{s.best}</b></span><span><small>Accuracy</small><b>{s.accuracy==null?'—':s.accuracy+'%'}</b></span>
    </div>)}</div>
  </Block>;
}
