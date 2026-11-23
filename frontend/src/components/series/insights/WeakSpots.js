import React from 'react';
import {Link} from 'react-router-dom';
import {ArrowUpRight} from 'lucide-react';
import {Block,colorOf,slug} from './parts';

const ChapterRow=({c})=><li data-testid={'si-chapter-'+slug(c.chapter)}><span><b>{c.chapter}</b><small>{c.days} din mein · {c.wrong} galat, {c.skipped} chhode</small></span><em>{c.wrong+c.skipped} sawaal</em></li>;

function SubjectRow({s,most}){
  return <li data-testid={'si-lost-'+slug(s.subject)}><span><b>{s.subject}</b><small>Average {s.average}/{s.maximum} · accuracy {s.accuracy==null?'—':s.accuracy+'%'}</small>
    <i className="si-bar" style={{width:`${most?Math.max(6,Math.round(100*s.lost/most)):0}%`,background:colorOf(s.subject)}}/></span><em>{s.lost} marks gaye</em></li>;
}

export function WeakSpots({chapters,tagged,subjects}){
  const byLoss=[...subjects].sort((a,b)=>b.lost-a.lost),most=byLoss[0]?.lost||0,useChapters=chapters.length>0;
  return <Block title={useChapters?'Bar-bar galat hone wale chapter':'Marks kahan ja rahe hain'} note={useChapters?'Jo chapter sabse zyada din galat hue':'Saare din jod kar'} testId="si-weak">
    <ul className="si-weak">{useChapters?chapters.map(c=><ChapterRow key={c.chapter} c={c}/>):byLoss.map(s=><SubjectRow key={s.subject} s={s} most={most}/>)}</ul>
    {!tagged&&<p className="si-note" data-testid="si-weak-untagged">In papers ke sawaalon par chapter ka naam nahi likha hai, isliye abhi subject ke hisaab se dikh raha hai.</p>}
    <Link className="sh-pill si-misfire" to="/misfire" data-testid="si-misfire-link">Galat sawaal dobara karo<ArrowUpRight size={16}/></Link>
  </Block>;
}
