import React,{useEffect,useRef,useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {LineChart} from 'lucide-react';
import {openAnalysis} from './seriesData';

// SVG parts are built with createElement: the preview editor wraps JSX list children in <span>, which SVG cannot draw.
const h=React.createElement,H=180,TOP=28,BOTTOM=28,LEFT=38,RIGHT=18;
const points=days=>days.filter(d=>d.live?.summary&&!d.live.resumable).map(d=>({day:d.day,score:d.live.summary.score,maximum:d.live.summary.maximum,id:d.live.id}));

export function trendSummary(days){
  const p=points(days);
  return p.length?{best:Math.max(...p.map(x=>x.score)),avg:Math.round(p.reduce((a,x)=>a+x.score,0)/p.length)}:null;
}

function useWidth(on){
  const ref=useRef(null),[w,setW]=useState(0);
  useEffect(()=>{
    const el=ref.current;if(!el)return undefined;
    const ro=new ResizeObserver(([e])=>setW(Math.round(e.contentRect.width)));ro.observe(el);
    return()=>ro.disconnect();
  },[on]);
  return [ref,w];
}

export function ScoreTrend({days}){
  const nav=useNavigate(),pts=points(days),[ref,w]=useWidth(pts.length>0);
  if(!pts.length)return <div className="sh-card sh-empty" data-testid="series-trend-empty"><span><LineChart size={26}/></span><h3>Your score trend begins here.</h3><p>Finish a live day. Your marks appear right after you submit — no sample scores.</p></div>;
  const today=days.find(d=>d.isToday)?.day||0,maxDay=Math.max(pts[pts.length-1].day,today,pts[0].day+1);
  const scores=pts.map(p=>p.score);
  let lo=Math.floor((Math.min(...scores)-20)/50)*50,hi=Math.min(Math.ceil((Math.max(...scores)+20)/50)*50,Math.max(...pts.map(p=>p.maximum)));
  if(hi-lo<100)lo=hi-100;
  const x=d=>LEFT+(d-1)/Math.max(1,maxDay-1)*Math.max(1,w-LEFT-RIGHT),y=s=>TOP+(1-(s-lo)/(hi-lo))*(H-TOP-BOTTOM);
  const best=pts.reduce((a,p)=>p.score>a.score?p:a,pts[0]),ticks=[0,1,2,3].map(i=>lo+(hi-lo)*i/3);
  const grid=ticks.map(t=>h('g',{key:'t'+t},h('line',{x1:LEFT,x2:w-RIGHT,y1:y(t),y2:y(t),className:'sh-trend-grid'}),h('text',{x:LEFT-8,y:y(t)+4,textAnchor:'end',className:'sh-trend-tick'},Math.round(t))));
  const labels=[...new Set([1,Math.round((1+maxDay)/2),maxDay])].map(d=>h('text',{key:'d'+d,x:x(d),y:H-8,textAnchor:'middle',className:'sh-trend-tick'},'D'+d));
  const line=h('polyline',{key:'line',points:pts.map(p=>`${x(p.day)},${y(p.score)}`).join(' '),className:'sh-trend-line'});
  const dots=pts.map(p=>h('g',{key:'p'+p.day,className:'sh-trend-point',role:'button',tabIndex:0,'data-testid':'series-trend-point-'+p.day,'aria-label':`Day ${p.day}: ${p.score} of ${p.maximum}. Open analysis`,onClick:()=>openAnalysis(nav,p.id),onKeyDown:e=>{if(e.key==='Enter')openAnalysis(nav,p.id);}},
    h('circle',{cx:x(p.day),cy:y(p.score),r:18,fill:'transparent'}),h('circle',{cx:x(p.day),cy:y(p.score),r:p===best?6:4,className:p===best?'is-best':''}),
    p===best&&h('text',{x:x(p.day),y:y(p.score)-12,textAnchor:'middle',className:'sh-trend-best'},'BEST '+p.score)));
  return <div className="sh-card sh-trend" data-testid="series-trend" ref={ref}>
    <small className="sh-trend-cap">Marks out of {pts[0].maximum}</small>
    {w>0&&h('svg',{width:w,height:H,role:'img','aria-label':`Live marks for ${pts.length} days`},grid,labels,line,dots)}
  </div>;
}
