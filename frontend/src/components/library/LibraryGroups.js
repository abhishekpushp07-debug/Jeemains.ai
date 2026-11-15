import React,{useState} from 'react';
import {ChevronDown,Download,RotateCcw} from 'lucide-react';
import {Button} from '../ui/button';
import {downloadFile} from '../../lib/api';
import {toast} from 'sonner';

const when=t=>t?new Date(t*1000).toLocaleDateString('en-IN',{dateStyle:'medium'}):'';
const day=d=>d?new Date(d+'T00:00:00').toLocaleDateString('en-IN',{day:'numeric',month:'short'}):'';
export const WAS={live:'Was Live',ended:'Was Live',draft:'Was Draft',unlive:'Was Off',paused:'Was Off',scheduled:'Was Scheduled'};
const plural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;

function Row({t,checked,onCheck,onRestore,busy}){
 const was=WAS[t.state]||'Was Off';
 return <li className="library-row" data-testid={'library-item-'+t.id}>
  <input type="checkbox" className="admin-row-check" checked={checked} onChange={e=>onCheck([t.id],e.target.checked)} aria-label={'Select '+t.title} data-testid={'library-select-'+t.id}/>
  <div className="library-row-main"><strong>{t.title}</strong>
   <div className="library-tags">
    {t.subject&&<span className="library-tag">{t.subject}</span>}
    <span className="library-tag">{plural(t.count,'question')}</span>
    <span className={'library-tag was-'+(t.state==='live'||t.state==='ended'?'live':'other')} data-testid={'library-was-'+t.id}>{was}</span>
    {t.series_date&&<span className="library-tag">Had day {day(t.series_date)}</span>}
    {t.attempts>0&&<span className="library-tag has-attempts">{plural(t.attempts,'student attempt')} kept</span>}
    <span className="library-tag is-quiet">Moved {when(t.archived_at)}</span>
   </div>
   {t.reason&&<small className="library-reason">{t.reason}</small>}
  </div>
  <Button variant="outline" size="sm" disabled={busy} onClick={()=>onRestore([t])} data-testid={'library-restore-'+t.id}><RotateCcw size={15}/>Restore</Button>
 </li>;
}

function bySubject(items){
 const map=new Map();items.forEach(t=>{const k=t.subject||'';if(!map.has(k))map.set(k,[]);map.get(k).push(t);});
 return [...map.entries()].sort((a,b)=>a[0].localeCompare(b[0]));
}

// One exam › mock type, folded by default when the list is long; chapter-wise tests are split by subject.
export function LibraryGroup({g,startOpen,picked,onCheck,onRestore,busy}){
 const [open,setOpen]=useState(startOpen),[zipping,setZipping]=useState(false);
 const key=g.sid||'none-'+g.exam;
 const all=g.items.every(t=>picked.has(t.id)),attempts=g.items.reduce((n,t)=>n+t.attempts,0);
 const parts=g.kind==='chapters'?bySubject(g.items):[['',g.items]];
 async function zip(){setZipping(true);try{await downloadFile('/admin/library/export?section_id='+encodeURIComponent(g.sid),`library-${g.exam}-${g.section}.zip`);}catch(e){toast.error(e.message);}finally{setZipping(false);}}
 return <section className="library-group" data-testid={'library-group-'+key}>
  <div className="library-group-head">
   <input type="checkbox" className="admin-row-check" checked={all} onChange={e=>onCheck(g.items.map(t=>t.id),e.target.checked)} aria-label={`Select all of ${g.exam} ${g.section}`} data-testid={'library-select-group-'+key}/>
   <button type="button" className="library-group-title" onClick={()=>setOpen(o=>!o)} aria-expanded={open} data-testid={'library-group-toggle-'+key}>
    <span><strong>{g.exam} › {g.section}</strong><small>{plural(g.items.length,'test')}{attempts?` · ${plural(attempts,'student attempt')} kept`:''}</small></span>
    <ChevronDown size={18} className={open?'is-open':''} aria-hidden="true"/>
   </button>
   <div className="library-group-actions">
    <Button variant="ghost" size="sm" disabled={!g.sid||zipping} onClick={zip} data-testid={'library-zip-'+key}><Download size={15}/>{zipping?'Preparing…':'ZIP'}</Button>
    <Button variant="outline" size="sm" disabled={busy} onClick={()=>onRestore(g.items)} data-testid={'library-restore-group-'+key}><RotateCcw size={15}/>Restore all</Button>
   </div>
  </div>
  {open&&parts.map(([subject,items])=><div key={subject||'all'} className="library-subgroup">
   {subject&&<h4 className="library-subhead" data-testid={`library-subject-${key}-${subject}`}>{subject} <span>{items.length}</span></h4>}
   <ul className="library-list">{items.map(t=><Row key={t.id} t={t} checked={picked.has(t.id)} onCheck={onCheck} onRestore={onRestore} busy={busy}/>)}</ul>
  </div>)}
 </section>;
}

const UPLOAD={book:'PDF upload',chapter_book:'Chapter PDF',import:'Paper / Excel',book_mock:'Draft mock from a PDF'};

export function LibraryUploads({items,busy,onRestore}){
 return <section className="library-group" data-testid="library-uploads">
  <div className="library-group-head library-uploads-head"><span><strong>Uploads that never went Live</strong><small>Restore one to see it again as a Draft in its mock type.</small></span></div>
  <ul className="library-list">{items.map(x=><li key={x.kind+x.id} className="library-row" data-testid={'library-upload-'+x.id}>
   <div className="library-row-main"><strong>{x.title}</strong><div className="library-tags"><span className="library-tag">{UPLOAD[x.kind]}</span>{x.place&&<span className="library-tag">{x.place}</span>}{x.archived_at&&<span className="library-tag is-quiet">Moved {when(x.archived_at)}</span>}</div></div>
   <Button variant="outline" size="sm" disabled={busy} onClick={()=>onRestore([],[{kind:x.kind,id:x.id}])} data-testid={'library-upload-restore-'+x.id}><RotateCcw size={15}/>Restore</Button>
  </li>)}</ul>
 </section>;
}
