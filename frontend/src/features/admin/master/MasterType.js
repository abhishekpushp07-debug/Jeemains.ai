import React,{useEffect,useState} from 'react';
import {Link,useNavigate,useParams} from 'react-router-dom';
import {UploadCloud,PencilLine,Loader2,RotateCw} from 'lucide-react';
import {api,post} from '../../../lib/api';
import {toast} from 'sonner';
import {Button} from '../../../components/ui/button';
import {Skeleton} from '../../../components/ui/skeleton';
import {ErrorBox} from '../../../components/Shared';
import {AdminHeading,StudentPath,StatusChip} from '../../../components/admin/AdminShared';
import {SectionTests} from '../../../components/admin/SectionTests';
import {PreviewLink} from '../../../components/admin/PreviewLink';
import {MasterCrumbs,KIND_LABEL,marks} from '../../../components/master/MasterShared';
import {MockList} from '../../../components/master/MockList';
import {UploadDialog} from '../../../components/master/UploadDialog';
import {WriteDialog} from '../../../components/master/WriteDialog';
import {SeriesDays} from '../../../components/master/SeriesDays';

const readLine=b=>b.rereading?`dobara padhi ja rahi hai · ${b.read_pages} / ${b.pages} page`:`${b.read_pages} / ${b.pages} page padhe gaye${b.message?` · ${b.message}`:''}`;

function Uploads({items,onChanged}){
 if(!items.length)return null;
 const dismiss=b=>post(`/admin/master/uploads/${b.kind}/${b.id}/dismiss`).then(r=>{toast.success(r.message);onChanged();}).catch(e=>toast.error(e.message));
 const retry=b=>post(`/admin/books/${b.id}/control`,{revision:b.revision,action:'retry'}).then(()=>{toast.success('Phir se shuru. Jo pages padhe ja chuke hain woh rakhe gaye hain.');onChanged();}).catch(e=>toast.error(e.message));
 return <section className="admin-panel master-uploads" data-testid="type-uploads"><h2>Uploads</h2><ul className="admin-list">{items.map(b=><li key={b.id} className="admin-row" data-testid={'type-upload-'+b.id}>
  <div className="admin-row-main"><strong>{b.title}</strong>{b.pages>0?<div className="admin-progress"><progress value={b.read_pages} max={b.pages}/><small data-testid={'type-upload-progress-'+b.id}>{readLine(b)}</small></div>:<small>{b.message||'Shuru hone ka intezaar…'}</small>}</div>
  <StatusChip state={b.state} testId={'type-upload-state-'+b.id}/>{b.can_retry&&<Button size="sm" onClick={()=>retry(b)} data-testid={'type-upload-retry-'+b.id}><RotateCw size={15}/>Dobara chalao</Button>}{b.kind==='book'&&b.chapters&&b.state!=='uploading'&&<Button asChild size="sm" variant={b.state==='chapters_needed'?'default':'outline'}><Link to={'/super-admin/chapters/'+b.id} data-testid={'type-upload-chapters-'+b.id}>{b.state==='chapters_needed'?'Chapter ke shuru wale page mark karo':'Chapters'}</Link></Button>}{b.kind==='book'&&!b.chapters&&b.state!=='uploading'&&<Button asChild size="sm" variant="ghost"><Link to={'/super-admin/upload?book='+b.id} data-testid={'type-upload-open-'+b.id}>Pages</Link></Button>}{!b.active&&<Button size="sm" variant="outline" onClick={()=>dismiss(b)} data-testid={'type-upload-dismiss-'+b.id}>Library mein bhejo</Button>}
 </li>)}</ul></section>;
}

function Unplaced({slug}){
 const [exam,setExam]=useState(null);
 useEffect(()=>{api('/admin/catalog').then(d=>setExam(d.items.find(e=>e.slug===slug)));},[slug]);
 if(!exam)return <Skeleton className="h-40"/>;
 return <div className="admin-page master-page" data-testid="master-unplaced">
  <MasterCrumbs exam={exam} last="Kisi type mein nahi"/>
  <AdminHeading testId="master-unplaced-title" title="Kisi type mein nahi" text="Purane practice ya competition tests jo kisi type ki list mein nahi hain. Har ek ko Move se sahi jagah rakhiye."/>
  <section className="admin-panel"><SectionTests exam={exam} path={`/admin/catalog/exams/${slug}/unplaced`}/></section>
 </div>;
}

function TypePage({sid}){
 const nav=useNavigate();
 const [data,setData]=useState(null),[error,setError]=useState(''),[reload,setReload]=useState(0),[dialog,setDialog]=useState(null);
 useEffect(()=>{api(`/admin/master/types/${sid}/mocks`).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message));},[sid,reload]);
 const busy=data&&(data.uploads.some(u=>u.active)||data.items.some(m=>m.status==='publishing'||m.rereading));
 useEffect(()=>{if(!busy)return;const t=setInterval(()=>setReload(n=>n+1),6000);return()=>clearInterval(t);},[busy]);
 if(error)return <ErrorBox error={error} retry={()=>setReload(n=>n+1)}/>;
 if(!data)return <Skeleton className="h-64"/>;
 const {section,exam}=data,series=section.kind==='aits',refresh=()=>setReload(n=>n+1);
 return <div className="admin-page master-page" data-testid={'master-type-page-'+section.slug}>
  <MasterCrumbs exam={exam} type={section}/>
  <AdminHeading testId="master-type-title" title={section.name} text={[KIND_LABEL[section.kind]||'Apna type',section.layout==='chapters'?'Subject › chapter':'Seedhi list',marks(section.defaults)].join(' · ')}
   action={<div className="admin-actions master-make">
    <Button onClick={()=>setDialog({upload:''})} data-testid="type-upload-pdf"><UploadCloud size={17}/>Upload PDF</Button>
    <Button variant="outline" onClick={()=>setDialog('write')} data-testid="type-write"><PencilLine size={17}/>Write</Button>
    {!series&&<PreviewLink section={section} exam={exam}/>}
   </div>}/>
  {!series&&<StudentPath exam={exam.name} section={section.name}/>}
  {section.hidden&&<p className="admin-note warn" data-testid="type-hidden-note">Yeh mock type students se chhupa hai.</p>}
  <Uploads items={data.uploads} onChanged={()=>setReload(n=>n+1)}/>
  {series?<SeriesDays section={section} reloadKey={reload} onChanged={refresh}/>:<section className="admin-panel" data-testid="type-mocks-panel">
   <div className="admin-panel-head"><h2>Mocks</h2>{busy&&<small className="master-live-note"><Loader2 size={13} className="spin"/>Apne aap update ho raha hai</small>}</div>
   <MockList items={data.items} onChanged={refresh} onReplace={ids=>setDialog({upload:ids})}/>
  </section>}
  <UploadDialog open={dialog?.upload!==undefined} onClose={()=>setDialog(null)} section={section} exam={exam} replace={dialog?.upload||''} onStarted={refresh}/>
  <WriteDialog open={dialog==='write'} onClose={()=>setDialog(null)} section={section} exam={exam} onCreated={id=>nav('/super-admin/write/'+id)}/>
 </div>;
}

export default function MasterType(){
 const {slug,sid}=useParams();
 return sid==='unplaced'?<Unplaced slug={slug}/>:<TypePage key={sid} sid={sid}/>;
}
