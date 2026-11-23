import React from 'react';
import {useWidth} from '../ScoreTrend';

// SVG parts are built with createElement: the preview editor wraps JSX list children in <span>, which SVG cannot draw.
const h=React.createElement,H=170,TOP=14,BOTTOM=26,LEFT=40,RIGHT=14;

export function Lines({series,lo,hi,suffix='',label,testId}){
  const all=series.flatMap(s=>s.points);
  const [ref,w]=useWidth(all.length>0);
  if(!all.length)return null;
  const days=all.map(p=>p.day),d0=Math.min(...days),d1=Math.max(...days,d0+1);
  const low=lo??Math.min(0,Math.floor(Math.min(...all.map(p=>p.value))/10)*10);
  const high=Math.max(hi??Math.ceil(Math.max(...all.map(p=>p.value))/50)*50,low+10);
  const x=d=>LEFT+(d-d0)/(d1-d0)*Math.max(1,w-LEFT-RIGHT),y=v=>TOP+(1-(v-low)/(high-low))*(H-TOP-BOTTOM);
  const grid=[0,1,2].map(i=>low+(high-low)*i/2).map(t=>h('g',{key:'g'+t},h('line',{x1:LEFT,x2:w-RIGHT,y1:y(t),y2:y(t),className:'sh-trend-grid'}),h('text',{x:LEFT-6,y:y(t)+4,textAnchor:'end',className:'sh-trend-tick'},Math.round(t)+suffix)));
  const marks=[...new Set([d0,Math.round((d0+d1)/2),d1])].map(d=>h('text',{key:'d'+d,x:x(d),y:H-8,textAnchor:'middle',className:'sh-trend-tick'},'D'+d));
  const lines=series.map(s=>h('g',{key:s.key,'data-testid':testId+'-'+s.key},
    s.points.length>1&&h('polyline',{points:s.points.map(p=>`${x(p.day)},${y(p.value)}`).join(' '),fill:'none',stroke:s.color,strokeWidth:2.2,strokeLinejoin:'round',strokeLinecap:'round',strokeDasharray:s.dash}),
    ...s.points.map(p=>h('circle',{key:p.day,cx:x(p.day),cy:y(p.value),r:3.5,fill:s.color},h('title',null,`${s.label} · Day ${p.day}: ${p.value}${suffix}`)))));
  return <div className="si-chart" ref={ref} data-testid={testId}>
    {w>0&&h('svg',{width:w,height:H,role:'img','aria-label':label},grid,marks,lines)}
    <div className="si-legend">{series.map(s=><span key={s.key}><i style={{background:s.color}}/>{s.label}</span>)}</div>
  </div>;
}
