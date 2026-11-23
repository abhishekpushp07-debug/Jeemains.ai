import React from 'react';
import {TrendingUp,TrendingDown,Minus} from 'lucide-react';

const COLOR={Physics:'#2563EB',Chemistry:'#0E9F6E',Mathematics:'#D97706'};
export const colorOf=name=>COLOR[name]||'#7C3AED';
export const slug=s=>String(s).toLowerCase().replace(/[^a-z0-9]+/g,'-');
export const avg=xs=>xs.length?Math.round(xs.reduce((a,b)=>a+b,0)/xs.length*10)/10:null;

const WORD={up:'badh raha hai',down:'gir raha hai',flat:'ek jaisa chal raha hai',early:'ka trend 4 din ke baad'};

export function Dir({name,way,change,unit='marks',testId}){
  const Icon=way==='up'?TrendingUp:way==='down'?TrendingDown:Minus;
  return <span className={'si-dir is-'+way} data-testid={testId}><Icon size={14}/>{name} {WORD[way]}{change!=null&&way!=='early'?` (${change>0?'+':''}${change} ${unit})`:''}</span>;
}

export const Block=({title,note,testId,children})=><section className="si-block" data-testid={testId}>
  <div className="sh-label"><h2>{title}</h2><span className="si-label-note">{note||''}</span></div>
  <div className="sh-card si-card">{children}</div>
</section>;
