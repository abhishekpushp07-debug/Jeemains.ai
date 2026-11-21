import React,{useEffect,useState} from 'react';
import {AlertTriangle} from 'lucide-react';
import {api} from '../../lib/api';

const line=d=>`${d.subject} Q${d.number} = ${d.matches.map(x=>`${x.title} Q${x.number}`).join(', ')}`;

// Red note on a mock row: questions already present in another test of the same section and subject.
export function DuplicateNote({m}){
 const list=m.duplicates||[];
 if(!list.length)return null;
 return <details className="dup-note" data-testid={'mock-duplicates-'+m.id}><summary><AlertTriangle size={13} aria-hidden="true"/>{list.length} sawaal is section mein pehle se hain</summary>
  <ul>{list.slice(0,12).map(d=><li key={d.question_id} data-testid={'mock-duplicate-'+m.id+'-'+d.question_id}>{line(d)}</li>)}</ul>
  {list.length>12&&<small>+{list.length-12} aur</small>}
 </details>;
}

// Fix page: the same red alert for the open mock.
export function DuplicateAlert({mockId}){
 const [list,setList]=useState([]);
 useEffect(()=>{let live=true;api('/admin/duplicates/mock/'+mockId).then(d=>{if(live)setList(d.items||[]);}).catch(()=>{});return()=>{live=false;};},[mockId]);
 if(!list.length)return null;
 return <div className="dup-alert" role="alert" data-testid="fix-duplicate-alert"><AlertTriangle size={18} aria-hidden="true"/><div>
  <strong>{list.length} sawaal is section mein pehle se maujood hain</strong>
  <small>Sirf warning hai: mock waise hi banega. Same section aur same subject mein mile sawaal hi gine gaye hain.</small>
  <ul>{list.map(d=><li key={d.question_id} data-testid={'fix-duplicate-'+d.question_id}>{line(d)}</li>)}</ul>
 </div></div>;
}
