import React,{useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {UploadCloud,RefreshCw} from 'lucide-react';
import {api} from '../../lib/api';
import {Button} from '../../components/ui/button';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading,DestinationChip,StatusChip} from '../../components/admin/AdminShared';
import BookPublishing from '../BookPublishing';
import {ReadyAction} from '../../components/admin/ReadyAction';

const chapterState=r=>r.chapters?.some(c=>c.status==='ready')?'ready':r.chapters?.length&&r.chapters.every(c=>['live','unlive','expired'].includes(c.status))?'published':r.status;

function Recent({title,path,pick,testId,empty}){
 const [items,setItems]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0);
 useEffect(()=>{setError('');api(path).then(d=>setItems(d.items)).catch(e=>setError(e.message));},[path,reload]);
 return <section className="admin-panel" data-testid={testId}><div className="admin-panel-head"><h2>{title}</h2><Button variant="ghost" size="icon" aria-label={'Refresh '+title} onClick={()=>setReload(n=>n+1)} data-testid={testId+'-refresh'}><RefreshCw size={16}/></Button></div><ErrorBox error={error}/>
  {!items&&!error?<Skeleton className="h-20"/>:items&&(items.length?<ul className="admin-list">{items.map(item=>{const r=pick(item);return <li className="admin-row" key={item.id} data-testid={testId+'-'+item.id}><Link className="admin-row-main" to={r.to} data-testid={testId+'-open-'+item.id}><strong>{r.title}</strong><small>{r.facts}</small>{r.dest&&<DestinationChip exam={r.dest.exam_name} section={r.dest.section_name} testId={testId+'-destination-'+item.id}/>}</Link>{r.ready?<ReadyAction item={r.ready} onDone={()=>setReload(n=>n+1)} testId={testId+'-state-'+item.id}/>:<StatusChip state={r.state} testId={testId+'-state-'+item.id}/>}</li>;})}</ul>:<p className="admin-empty" data-testid={testId+'-empty'}>{empty}</p>)}
 </section>;
}

export default function AdminUpload(){
 const [params]=useSearchParams();
 if(params.get('book'))return <BookPublishing/>;
 return <div className="admin-page" data-testid="admin-upload-page">
  <AdminCrumbs items={[{label:'Super Admin',to:'/super-admin'},{label:'Upload'}]}/>
  <AdminHeading testId="admin-upload-title" title="Upload" text="Every upload starts by choosing where it goes. Nothing goes live until you publish it." action={<Button asChild><Link to="/super-admin/upload/new" data-testid="upload-add-content"><UploadCloud size={17}/>Add content</Link></Button>}/>
  <Recent title="Combined books" path="/admin/books" testId="recent-books" empty="No combined books yet." pick={b=>({to:'/super-admin/upload?book='+b.id,title:b.title,facts:`${b.read_pages} / ${b.pages||'—'} pages · ${(b.size/1024/1024).toFixed(1)} MB`,dest:b.destination,state:b.paused?'paused':b.state,ready:b.state==='ready'&&!b.paused&&b.destination&&!b.destination.series?{kind:'book',id:b.id,title:'Every ready mock of '+b.title}:null})}/>
  <Recent title="Papers and Excel uploads" path="/studio/imports" testId="recent-imports" empty="No paper or Excel uploads yet." pick={r=>({to:'/studio/imports/'+r.id,title:r.title,facts:`${r.count} questions · ${r.format.toUpperCase()}`,state:r.status,ready:r.status==='ready'?{kind:'import',id:r.id,title:r.title}:null})}/>
  <Recent title="Chapter books" path="/studio/chapter-books" testId="recent-chapter-books" empty="No chapter books yet." pick={r=>({to:'/studio/chapter-books/'+r.id,title:r.title,facts:`${r.chapters?.length??r.chapter_count??0} chapters`,state:chapterState(r),ready:chapterState(r)==='ready'?{kind:'chapter_book',id:r.id,title:'All chapters of '+r.title}:null})}/>
 </div>;
}
