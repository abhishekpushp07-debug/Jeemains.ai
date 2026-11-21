import React,{useEffect,useState} from 'react';
import {TrendingUp,TrendingDown,Minus,Loader2} from 'lucide-react';
import {api} from '../../lib/api';

const TREND={up:[TrendingUp,'Behtar ho raha hai','good'],down:[TrendingDown,'Kamzor ho raha hai','bad'],same:[Minus,'Waisa hi','info']};
const slug=s=>String(s).toLowerCase().replace(/[^a-z0-9]+/g,'-');

function Trend({t}){
 if(!TREND[t])return <small className="mf-muted">Ek hi paper</small>;
 const [I,word,tone]=TREND[t];
 return <span className={'mf-trend '+tone}><I size={14} aria-hidden="true"/>{word}</span>;
}

function Row({g,most,i}){
 return <li className="cr-row" style={{'--i':i}} data-testid={'chapter-row-'+slug(g.subject+'-'+g.chapter)}>
  <div className="cr-name"><strong>{g.chapter}</strong><small>{g.subject} · {g.papers} paper · {g.total} sawaal</small></div>
  <div className="cr-bar" aria-hidden="true"><i style={{width:`${Math.max(4,(g.lost/most)*100)}%`}}/></div>
  <div className="cr-nums"><b>{g.lost}</b><small>marks gaye</small></div>
  <div className="cr-nums"><b>{g.sahi}%</b><small>sahi</small></div>
  <Trend t={g.trend}/>
 </li>;
}

// Across every paper: which chapter keeps costing marks, and whether it is getting better.
export function ChapterReport(){
 const [d,setD]=useState(null),[error,setError]=useState('');
 useEffect(()=>{let live=true;const load=()=>api('/my/chapters').then(x=>{if(!live)return;setD(x);if(x.waiting>0)setTimeout(load,2500);}).catch(e=>live&&setError(e.message));load();return()=>{live=false;};},[]);
 if(error)return <p className="mf-bad" role="alert" data-testid="chapter-report-error">{error}</p>;
 if(!d)return <p className="mf-muted" data-testid="chapter-report-loading"><Loader2 size={15} className="spin"/>Report ban rahi hai…</p>;
 if(!d.papers)return <p className="mf-empty" data-testid="chapter-report-empty">Abhi koi graded paper nahi hai. Ek mock do, report yahan banegi.</p>;
 const most=Math.max(1,...d.chapters.map(g=>g.lost));
 return <section className="chapter-report" data-testid="chapter-report">
  <p className="mf-muted" data-testid="chapter-report-papers">{d.papers} paper milakar{d.waiting>0?' · kuch papers abhi jud rahe hain':''}</p>
  <div className="cr-subjects">{d.subjects.map(s=><div key={s.subject} className="cr-subject" data-testid={'chapter-subject-'+slug(s.subject)}>
   <small>{s.subject}</small><b>{s.sahi}%</b><span>sahi · {s.lost} marks gaye</span><Trend t={s.trend}/></div>)}</div>
  {d.chapters.length?<ol className="cr-list" data-testid="chapter-report-list">{d.chapters.map((g,i)=><Row key={g.subject+g.chapter} g={g} most={most} i={i}/>)}</ol>
   :<p className="mf-muted" data-testid="chapter-report-no-chapters">In papers mein chapter ka naam nahi likha tha, isliye sirf subject ki report hai. Chapter-wise tests do, chapter yahan dikhenge.</p>}
  {d.untagged>0&&d.chapters.length>0&&<p className="mf-muted" data-testid="chapter-report-untagged">{d.untagged} sawaal par chapter ka naam nahi tha; woh sirf subject mein gine gaye.</p>}
 </section>;
}
