import React,{useEffect,useMemo,useState} from 'react';
import {Archive,Download,RotateCcw,Search} from 'lucide-react';
import {api,post,downloadFile} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {Button} from '../../components/ui/button';
import {Input} from '../../components/ui/input';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading} from '../../components/admin/AdminShared';
import {toast} from 'sonner';

const SOURCE={book:'Combined book',mock_book:'Mock book',import:'Paper / Excel',chapter_book:'Chapter book',manual:'Manual editor'};
const when=t=>t?new Date(t*1000).toLocaleDateString('en-IN',{dateStyle:'medium'}):'';

function LibraryRow({t,checked,onCheck,onRestore,busy}){
 return <li className="admin-test-row" data-testid={'library-item-'+t.id}>
  <input type="checkbox" className="admin-row-check" checked={checked} onChange={e=>onCheck(t.id,e.target.checked)} aria-label={'Select '+t.title} data-testid={'library-select-'+t.id}/>
  <div className="admin-row-main"><strong>{t.title}</strong><small>{[t.subject,`${t.count} questions`,SOURCE[t.source],`moved ${when(t.archived_at)}`,t.attempts?`${t.attempts} student attempt${t.attempts===1?'':'s'} kept`:null].filter(Boolean).join(' · ')}</small>{t.reason&&<small className="admin-library-reason">{t.reason}</small>}</div>
  <Button variant="outline" size="sm" disabled={busy} onClick={()=>onRestore([t.id])} data-testid={'library-restore-'+t.id}><RotateCcw size={15}/>Restore</Button>
 </li>;
}

function Group({g,picked,onCheck,onRestore,busy}){
 const ids=g.items.map(t=>t.id);
 return <section className="admin-panel" data-testid={'library-group-'+(g.sid||'none')}>
  <div className="admin-panel-head"><div><h2>{g.exam} › {g.section}</h2><p>{g.items.length} test{g.items.length===1?'':'s'}</p></div>
   <div className="admin-actions"><Button variant="outline" disabled={!g.sid} onClick={()=>downloadFile('/admin/library/export?section_id='+encodeURIComponent(g.sid),`library-${g.exam}-${g.section}.zip`).catch(e=>toast.error(e.message))} data-testid={'library-zip-'+(g.sid||'none')}><Download size={16}/>ZIP</Button><Button variant="outline" disabled={busy} onClick={()=>onRestore(ids)} data-testid={'library-restore-group-'+(g.sid||'none')}><RotateCcw size={16}/>Restore all</Button></div></div>
  <ul className="admin-list admin-test-list">{g.items.map(t=><LibraryRow key={t.id} t={t} checked={picked.has(t.id)} onCheck={onCheck} onRestore={onRestore} busy={busy}/>)}</ul>
 </section>;
}

const UPLOAD={book:'PDF upload',chapter_book:'Chapter PDF',import:'Paper / Excel',book_mock:'Draft mock from a PDF'};

function Uploads({items,busy,onRestore}){
 if(!items.length)return null;
 return <section className="admin-panel admin-uploads-panel" data-testid="library-uploads">
  <div className="admin-panel-head"><div><h2>Uploads in the Library</h2><p>Their mocks were never published. Restore one to see it again as a Draft in its mock type.</p></div></div>
  <ul className="admin-list">{items.map(x=><li key={x.kind+x.id} className="admin-row" data-testid={'library-upload-'+x.id}><div className="admin-row-main"><strong>{x.title}</strong><small>{[UPLOAD[x.kind],x.place,`moved ${when(x.archived_at)}`].filter(Boolean).join(' · ')}</small></div><Button variant="outline" size="sm" disabled={busy} onClick={()=>onRestore([],[{kind:x.kind,id:x.id}])} data-testid={'library-upload-restore-'+x.id}><RotateCcw size={15}/>Restore</Button></li>)}</ul>
 </section>;
}

export default function AdminLibrary(){
 const [data,setData]=useState(null),[error,setError]=useState(''),[picked,setPicked]=useState(new Set()),[busy,setBusy]=useState(false),[reload,setReload]=useState(0),[q,setQ]=useState(''),[zipping,setZipping]=useState(false);
 useEffect(()=>{api('/admin/library').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[reload]);
 const groups=useMemo(()=>{const map=new Map();(data?.items||[]).filter(t=>!q||t.title.toLowerCase().includes(q.toLowerCase())).forEach(t=>{const key=t.section_id||'none:'+t.exam_name;if(!map.has(key))map.set(key,{sid:t.section_id,exam:t.exam_name||'Other',section:t.section_name,items:[]});map.get(key).items.push(t);});return [...map.values()];},[data,q]);
 function check(id,on){setPicked(p=>{const n=new Set(p);on?n.add(id):n.delete(id);return n;});}
 async function restore(ids,uploads=[]){setBusy(true);try{const r=await post('/admin/library/restore',{ids,uploads});invalidateCatalog();toast.success(r.message);setPicked(new Set());setReload(n=>n+1);}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 async function zipAll(){setZipping(true);try{await downloadFile('/admin/library/export','jeelive-library.zip');}catch(e){toast.error(e.message);}finally{setZipping(false);}}
 return <div className="admin-page" data-testid="admin-library-page">
  <AdminCrumbs items={[{label:'Master',to:'/super-admin'},{label:'Library'}]}/>
  <AdminHeading testId="admin-library-title" title="Library" text="Tests taken away from students. Everyone keeps their old scores in their history. Restore any time, or download everything as a ZIP." action={<Button onClick={zipAll} disabled={zipping||!data?.items.length} data-testid="library-zip-all"><Download size={17}/>{zipping?'Preparing ZIP…':'Download all as ZIP'}</Button>}/>
  <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>
  {!data&&!error&&<Skeleton className="h-64"/>}
  {data&&<>
   <div className="admin-select-bar" data-testid="library-toolbar"><Search size={16} aria-hidden="true"/><Input value={q} onChange={e=>setQ(e.target.value)} placeholder="Find a test by name" aria-label="Find a test" className="admin-search" data-testid="library-search"/>{picked.size>0&&<><span data-testid="library-selected-count">{picked.size} selected</span><Button size="sm" disabled={busy} onClick={()=>restore([...picked])} data-testid="library-restore-selected"><RotateCcw size={15}/>Restore selected</Button><Button size="sm" variant="ghost" onClick={()=>setPicked(new Set())} data-testid="library-clear-selection">Clear</Button></>}</div>
   <Uploads items={data.uploads||[]} busy={busy} onRestore={restore}/>
   {!data.items.length?<div className="admin-empty" data-testid="library-empty"><Archive size={22}/><p>The Library is empty. Mocks you move here from Master, or replace with a new PDF, appear here.</p></div>:groups.map(g=><Group key={g.sid||g.exam+g.section} g={g} picked={picked} onCheck={check} onRestore={restore} busy={busy}/>)}
  </>}
 </div>;
}
