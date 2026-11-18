import React from 'react';
import {ChartNoAxesColumn,ChartLine,Target,GraduationCap,ArrowLeftRight,Sparkles} from 'lucide-react';

const TOOLS=[
 ['rank-predictor','Rank predictor','marks se rank',ChartNoAxesColumn,'maroon'],
 ['percentile','Percentile se rank','NTA percentile',ChartLine,'indigo'],
 ['target-marks','Target marks','college ke liye',Target,'teal'],
 ['college-predictor','College predictor','colleges + cutoffs',GraduationCap,'red'],
 ['college-compare','College compare','3 college · 2 branch',ArrowLeftRight,'amber'],
 ['dream-college','Dream college','1 dream chune',Sparkles,'violet'],
];

export default function Rank(){
 return <div className="container page app-page" data-testid="rank-page">
  <header className="app-page-head"><span className="app-kicker">JEELIVE.AI · RANK</span><h1 data-testid="rank-title">Rank & college predictor</h1><p>JoSAA · CSAB · JAC Delhi · BITSAT · COMEDK</p></header>
  <div className="rank-tools">{TOOLS.map(([id,title,sub,Icon,tone],i)=><div key={id} className={'rank-tool tone-'+tone} style={{animationDelay:i*55+'ms'}} aria-disabled="true" data-testid={'rank-tool-'+id}><span className="rank-tool-icon"><Icon size={20}/></span><span><strong>{title}</strong><small>{sub}</small></span><b>SOON</b></div>)}</div>
  <section className="feature-dark soon-card" data-testid="rank-coming-soon"><span className="sf-chip"><i/>COMING SOON</span><h2>Rank tools are on their way to the website.</h2><p>Marks se rank, college predictor aur cutoffs, sab yahin milenge.</p></section>
 </div>;
}
