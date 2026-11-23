import React from 'react';
import {ErrorBox} from '../../Shared';
import {useInsights} from './useInsights';
import {Overall} from './Overall';
import {SubjectTrend} from './SubjectTrend';
import {VsClass} from './VsClass';
import {AccuracyTime} from './AccuracyTime';
import {WeakSpots} from './WeakSpots';

// All attempted days joined: overall, subjects, you vs class, accuracy and time, where marks keep going.
export function SeriesInsights({uid}){
  const {data,error,retry}=useInsights(uid);
  if(error)return <ErrorBox error={error} retry={retry}/>;
  if(!data)return <div className="sh-card sh-skeleton si-loading" data-testid="series-insights-loading"/>;
  if(!data.days.length)return null;
  return <section className="si" data-testid="series-insights">
    <div className="sh-label"><h2>Saare din ek saath</h2><span data-testid="si-days-count">{data.overall.days} din ka joda hua analysis</span></div>
    <Overall o={data.overall} total={data.total_days} max={data.days[0].maximum}/>
    <SubjectTrend subjects={data.subjects}/>
    <VsClass days={data.days}/>
    <AccuracyTime days={data.days}/>
    <WeakSpots chapters={data.chapters} tagged={data.chapters_tagged} subjects={data.subjects}/>
  </section>;
}
