import React from 'react';
import {SERIES_PATH,useSeriesSchedule} from '../components/LiveSeriesBanner';
import {Greeting,SectionLabel,SeriesFeatureCard,PracticeGrid,ForYou} from '../components/home/HomeParts';

export default function Home(){
 const series=useSeriesSchedule();
 return <div className="container page app-home" data-testid="exam-home-page">
  <Greeting/>
  <SectionLabel title="All India Series" to={SERIES_PATH} testId="home-series-view-all"/>
  <SeriesFeatureCard series={series}/>
  <SectionLabel title="Practice"/>
  <PracticeGrid series={series}/>
  <SectionLabel title="For you" to="/profile" testId="home-for-you-view-all"/>
  <ForYou/>
 </div>;
}
