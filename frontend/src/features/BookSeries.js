import React,{useEffect,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {api} from '../lib/api';
import {BookOpen,ArrowRight} from 'lucide-react';
import {ErrorBox,Loading} from '../components/Shared';
import '../book-publishing.css';

export default function BookSeries(){
 const {id}=useParams();const [loaded,setLoaded]=useState(null),[error,setError]=useState('');
 const data=loaded?.key===(id||'list')?loaded.payload:null;
 useEffect(()=>{const c=new AbortController();setError('');api('/book-series'+(id?'/'+id:''),{signal:c.signal}).then(payload=>setLoaded({key:id||'list',payload})).catch(e=>{if(e.name!=='AbortError')setError(e.message);});return()=>c.abort();},[id]);
 return <div className="container page book-workspace" data-testid="book-series-page"><Link className="breadcrumb" to={id?'/book-series':'/home'} data-testid="book-series-back">← {id?'All book series':'Home'}</Link><header className="page-title"><div><span className="eyebrow">SOURCE-BACKED PRACTICE</span><h1 data-testid="book-series-title">{data?.title||'Book series.'}</h1><p>Original questions, supplied keys and matched explanations. Only available mocks are listed.</p></div><BookOpen size={36}/></header><ErrorBox error={error}/>{!data&&!error&&<Loading/>}{data&&!data.items.length&&<p data-testid="book-series-empty">No released book series yet.</p>}<div className="book-upload-list">{data?.items.map(item=><Link className="book-list-row" key={item.id} to={id?`/sets/${item.id}`:`/book-series/${item.id}`} data-testid={`book-series-item-${item.id}`}><div><strong>{item.title}</strong><small>{id?`${item.count} questions · ${item.rules.minutes} minutes · ${item.exam}`:`${item.published_count} released mocks`}</small></div><ArrowRight size={20}/></Link>)}</div></div>;
}
