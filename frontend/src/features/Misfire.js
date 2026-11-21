// Misfire: every wrong or skipped question from every paper, in one place. Solve again; once right, "Samajh gaya".
import React,{useCallback,useEffect,useState} from 'react';
import {Crosshair,Loader2} from 'lucide-react';
import {api} from '../lib/api';
import {MisfireItem} from '../components/misfire/MisfireItem';
import {ChapterReport} from '../components/misfire/ChapterReport';
import '../misfire.css';

const TABS=[['open','Galtiyan'],['fixed','Samajh gaya'],['chapters','Chapter report']];

function useList(status,subject,chapter){
 const [d,setD]=useState(null),[items,setItems]=useState([]),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const load=useCallback(async page=>{setBusy(true);setError('');
  try{const x=await api('/my/misfire?'+new URLSearchParams({status,subject,chapter,page:String(page)}));setD(x);setItems(list=>page===1?x.items:[...list,...x.items]);return x;}
  catch(e){setError(e.message);return null;}finally{setBusy(false);}},[status,subject,chapter]);
 useEffect(()=>{if(status==='chapters')return undefined;let live=true;
  const first=()=>load(1).then(x=>{if(live&&x?.waiting>0)setTimeout(first,2500);});first();return()=>{live=false;};},[load,status]);
 return {d,items,setItems,busy,error,more:()=>load((d?.page||1)+1)};
}

function Filters({subjects,subject,setSubject,chapters,chapter,setChapter}){
 return <div className="mf-filters">
  <div className="mf-chips" role="group" aria-label="Subject">{[{name:'',label:'Sab'},...subjects.map(s=>({name:s.name,label:s.name}))].map(s=>
   <button type="button" key={s.name||'all'} className={'mf-chip'+(subject===s.name?' is-on':'')} onClick={()=>{setSubject(s.name);setChapter('');}} data-testid={'misfire-subject-'+(s.name||'all').toLowerCase()}>{s.label}</button>)}</div>
  {chapters.length>0&&<select className="mf-select" value={chapter} onChange={e=>setChapter(e.target.value)} aria-label="Chapter" data-testid="misfire-chapter-filter">
   <option value="">Saare chapter</option>{chapters.map(c=><option key={c.name} value={c.name}>{c.name} ({c.count})</option>)}</select>}
 </div>;
}

export default function Misfire(){
 const [tab,setTab]=useState('open'),[subject,setSubject]=useState(''),[chapter,setChapter]=useState(''),[sum,setSum]=useState(null);
 const list=useList(tab,subject,chapter);
 const counts=useCallback(()=>api('/my/misfire/summary').then(setSum).catch(()=>{}),[]);
 useEffect(()=>{counts();},[counts]);
 const changed=id=>{list.setItems(x=>x.filter(m=>m.id!==id));counts();};
 const n={open:sum?.open,fixed:sum?.fixed};
 return <div className="container page mf-page" data-testid="misfire-page">
  <header className="mf-hero"><span className="mf-hero-icon"><Crosshair size={28}/></span><div><h1 data-testid="misfire-title">Misfire</h1>
   <p>Har paper ke galat aur chhode sawaal ek jagah. Dobara solve karo; sahi ho jaye toh "Samajh gaya" dabao aur sawaal list se hat jayega.</p></div></header>
  <nav className="mf-tabs" role="tablist">{TABS.map(([k,word])=><button type="button" key={k} role="tab" aria-selected={tab===k} className={'mf-tab'+(tab===k?' is-on':'')}
   onClick={()=>{setTab(k);setChapter('');}} data-testid={'misfire-tab-'+k}>{word}{n[k]!=null&&<b data-testid={'misfire-count-'+k}>{n[k]}</b>}</button>)}</nav>
  {tab==='chapters'?<ChapterReport/>:<>
   <Filters subjects={(sum?.subjects||[]).filter(s=>s[tab]>0)} subject={subject} setSubject={setSubject} chapters={list.d?.chapters||[]} chapter={chapter} setChapter={setChapter}/>
   {list.d?.waiting>0&&<p className="mf-muted" data-testid="misfire-waiting"><Loader2 size={14} className="spin"/>Aapke kuch papers abhi jud rahe hain…</p>}
   {list.error&&<p className="mf-bad" role="alert" data-testid="misfire-error">{list.error}</p>}
   {!list.d&&!list.error&&<p className="mf-muted" data-testid="misfire-loading"><Loader2 size={15} className="spin"/>Load ho raha hai…</p>}
   {list.d&&!list.items.length&&<p className="mf-empty" data-testid="misfire-empty">{tab==='open'?'Koi galti baaki nahi. Agla mock do; jo galat ya chhoot jaye, yahan aa jayega.':'Abhi tak koi sawaal "Samajh gaya" nahi hua.'}</p>}
   <div className="mf-list" data-testid="misfire-list">{list.items.map(m=><MisfireItem key={m.id} m={m} onChanged={changed}/>)}</div>
   {list.d&&list.d.page<list.d.pages&&<button type="button" className="mf-btn ghost mf-more" disabled={list.busy} onClick={list.more} data-testid="misfire-more">{list.busy?<Loader2 size={15} className="spin"/>:null}Aur dikhao</button>}
  </>}
 </div>;
}
