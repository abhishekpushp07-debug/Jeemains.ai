import React,{useCallback,useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {UploadCloud,FolderTree,BookOpen,CheckCircle2,AlertTriangle,MessageSquareWarning,ArrowUpRight} from 'lucide-react';
import {api} from '../../lib/api';
import {Button} from '../../components/ui/button';
import {Skeleton} from '../../components/ui/skeleton';
import {ErrorBox} from '../../components/Shared';
import {AdminCrumbs,AdminHeading,DestinationChip,StatusChip} from '../../components/admin/AdminShared';
import {DataHealth} from '../../components/admin/DataHealth';

const plural=(n,word)=>`${n} ${word}${n===1?'':'s'}`;

const Tile=({Icon,value,label,to,testId,tone})=><Link to={to} className={'admin-tile tone-'+tone} data-testid={testId}><Icon size={20} aria-hidden="true"/><strong data-testid={testId+'-value'}>{value}</strong><span>{label}</span><ArrowUpRight size={16} className="admin-tile-go" aria-hidden="true"/></Link>;

function Processing({items}){
 if(!items.length)return <p className="admin-empty" data-testid="overview-no-processing">No upload is reading right now. <Link to="/super-admin/upload/new" data-testid="overview-add-content-inline">Add content</Link></p>;
 return <ul className="admin-list" data-testid="overview-processing-list">{items.map(b=><li key={b.id} className="admin-row" data-testid={'overview-book-'+b.id}><div className="admin-row-main"><Link to={'/super-admin/upload?book='+b.id} className="admin-row-title" data-testid={'overview-book-open-'+b.id}>{b.title}</Link>{b.destination&&<DestinationChip exam={b.destination.exam_name} section={b.destination.section_name} testId={'overview-book-destination-'+b.id}/>}<div className="admin-progress"><progress value={b.read_pages} max={b.pages||1} aria-label={'Pages read for '+b.title}/><small>{b.read_pages} / {b.pages||'—'} pages read</small></div></div><StatusChip state={b.paused?'paused':b.state} testId={'overview-book-state-'+b.id}/></li>)}</ul>;
}

export default function AdminOverview(){
 const [data,setData]=useState(null),[error,setError]=useState('');
 const load=useCallback(()=>api('/admin/overview').then(d=>{setData(d);setError('');}).catch(e=>setError(e.message)),[]);
 useEffect(()=>{load();const timer=setInterval(load,15000);return()=>clearInterval(timer);},[load]);
 const readyLink=data?.ready_books.length===1?'/super-admin/upload?book='+data.ready_books[0]:'/super-admin/upload';
 return <div className="admin-page" data-testid="admin-overview-page">
  <AdminCrumbs items={[{label:'Super Admin'},{label:'Overview'}]}/>
  <AdminHeading testId="super-admin-title" title="What needs you today." text={data?`${plural(data.processing.filter(b=>['uploading','received','reading','matching'].includes(b.state)).length,'upload')} reading · ${plural(data.ready,'mock')} ready · ${data.held} held`:'Loading your publishing desk…'} action={<div className="admin-actions"><Button asChild><Link to="/super-admin/upload/new" data-testid="overview-add-content"><UploadCloud size={17}/>Add content</Link></Button><Button asChild variant="outline"><Link to="/super-admin/content" data-testid="overview-open-content"><FolderTree size={17}/>Exams & Content</Link></Button></div>}/>
  <ErrorBox error={error} retry={load}/>
  {!data&&!error?<div className="admin-tiles">{[1,2,3,4].map(n=><Skeleton key={n} className="h-28"/>)}</div>:data&&<>
   <div className="admin-tiles" data-testid="overview-tiles">
    <Tile Icon={BookOpen} value={data.processing.length} label="Uploads in progress" to="/super-admin/upload" testId="overview-tile-uploads" tone="processing"/>
    <Tile Icon={CheckCircle2} value={data.ready} label="Mocks ready to publish" to={readyLink} testId="overview-tile-ready" tone="ready"/>
    <Tile Icon={AlertTriangle} value={data.held} label="Held mocks" to="/super-admin/review?tab=held" testId="overview-tile-held" tone="attention"/>
    <Tile Icon={MessageSquareWarning} value={data.open_reports} label="New question reports" to="/super-admin/review?tab=reports" testId="overview-tile-reports" tone="scheduled"/>
   </div>
   <section className="admin-panel"><h2>Uploads</h2><Processing items={data.processing}/></section>
   <section className="admin-panel"><h2>Held, and why</h2>{data.held_items.length?<ul className="admin-list" data-testid="overview-held-list">{data.held_items.map(m=><li key={m.id} className="admin-row" data-testid={'overview-held-'+m.id}><div className="admin-row-main"><strong>{m.label}</strong><small>{m.book_title}</small><p className="admin-reason">{m.reason}</p></div><Button asChild variant="outline"><Link to={'/super-admin/upload?book='+m.book_id} data-testid={'overview-held-fix-'+m.id}>Fix</Link></Button></li>)}</ul>:<p className="admin-empty" data-testid="overview-no-held">Nothing is held. Every checked mock is ready or live.</p>}</section>
   <DataHealth/>
  </>}
 </div>;
}
