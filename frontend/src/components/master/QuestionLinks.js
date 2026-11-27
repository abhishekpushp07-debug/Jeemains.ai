import React,{useCallback,useEffect,useState} from 'react';
import {Link2,Loader2,TriangleAlert} from 'lucide-react';
import {toast} from 'sonner';
import {api,post,put} from '../../lib/api';
import {Button} from '../ui/button';
import {Switch} from '../ui/switch';
import {fmtIST} from './MasterShared';

const SIDE={paper:'AITS paper',chapter:'Chapter-wise'};
const TILES=[['records','Kul record','Har sawaal ka ek'],['linked','Dono jagah jude','AITS paper + chapter test'],['paper','Sirf AITS paper','Chapter-wise mein abhi nahi'],
 ['chapter','Sirf chapter-wise','AITS paper abhi nahi aaya'],['review','Aap dekhiye','Taala nahi khula'],['bare','Bina pate ke','PDF par pata chhapa nahi']];

function Mocks({rows}){
 if(!rows.length)return null;
 return <div className="link-block"><h3>Har mock: 75 mein se kitne chapter-wise se jude</h3>
  <ol className="link-mocks" data-testid="links-mocks">{rows.map(m=>{const full=m.questions>0&&m.linked===m.questions;
   return <li key={m.mock} className={'link-mock'+(full?' is-full':'')+(m.review?' has-review':'')} data-testid={'links-mock-'+m.mock}>
    <span>{m.label||'Mock '+m.mock}</span><strong data-testid={'links-mock-count-'+m.mock}>{m.linked} / {m.questions}</strong>
    <progress value={m.linked} max={m.questions||1} aria-label={(m.label||'Mock '+m.mock)+': jude hue sawaal'}/>
    {m.review>0&&<small data-testid={'links-mock-review-'+m.mock}>{m.review} aap dekhiye</small>}
   </li>;})}</ol></div>;
}

function Review({items,more}){
 if(!items.length)return null;
 return <div className="link-block"><h3><TriangleAlert size={16} aria-hidden="true"/>Aap dekhiye ({items.length+more})</h3>
  <p className="admin-note">Inka pata mila, par ek taala nahi khula, isliye inhe joda nahi gaya. PDF theek karke dobara upload kijiye, ya Draft mein jawab sudhaar kar “Dobara jodo” dabaiye.</p>
  <ul className="link-review" data-testid="links-review">{items.map((r,i)=><li key={r.id} data-testid={'links-review-'+i}>
   <strong>{r.address}{r.subject?' · '+r.subject:''}</strong>
   {r.problems.map((p,k)=><small key={k} data-testid={`links-review-${i}-reason-${k}`}>{p.say} <em>{p.with}</em></small>)}
  </li>)}</ul>
  {more>0&&<p className="admin-note" data-testid="links-review-more">…aur {more}. Upar wale theek hote hi yeh dikhenge.</p>}</div>;
}

function Books({items}){
 if(!items.length)return null;
 return <div className="link-block"><h3>Kis upload se padha gaya</h3>
  <ul className="link-books" data-testid="links-books">{items.map((b,i)=><li key={i} data-testid={'links-book-'+i}>
   <strong>{b.title}</strong><small>{[SIDE[b.side],b.archived?'Library mein':'',b.questions!==undefined?`${b.mocks} ${b.side==='paper'?'mock':'chapter'} · ${b.questions} sawaal · ${b.addressed} par pata`:''].filter(Boolean).join(' · ')}</small>
  </li>)}</ul></div>;
}

// Super Admin › All India Test Series: one record per question. The paper's question and the chapter test's question meet on it by the address printed on both. No AI.
export function QuestionLinks({exam,reloadKey}){
 const [data,setData]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const load=useCallback(()=>api('/admin/links/'+exam.slug).then(d=>{setData(d);setError('');}).catch(e=>setError(e.message)),[exam.slug]);
 useEffect(()=>{load();},[load,reloadKey]);
 async function run(){setBusy(true);
  try{const d=await post(`/admin/links/${exam.slug}/run`);setData(d);setError('');toast.success(`Jod ban gaya: ${d.counts.records} record, ${d.counts.linked} dono jagah jude${d.counts.review?`, ${d.counts.review} aap dekhiye`:''}.`);}
  catch(e){toast.error(e.message,{duration:10000});load();}finally{setBusy(false);}}
 const [saving,setSaving]=useState(false);
 const show=v=>{setSaving(true);put(`/admin/links/${exam.slug}/analysis`,{on:v}).then(d=>{setData(d);toast.success(v?'On: AITS ke analysis mein chapter ke naam dikhenge.':'Off: AITS ka analysis pehle jaisa.');})
  .catch(e=>toast.error(e.message,{duration:10000})).finally(()=>setSaving(false));};
 if(!data)return error?<section className="admin-panel" data-testid="links-panel"><p className="admin-note error" data-testid="links-error">{error}</p></section>:null;
 const c=data.counts,made=!!data.ran_at;
 return <section className="admin-panel link-panel" data-testid="links-panel">
  <div className="admin-panel-head"><div><h2>Jod: ek sawaal, ek record</h2>
    <p>AITS paper ka sawaal aur chapter-wise test ka wahi sawaal ek hi record par baithte hain. Jod PDF par chhape pate (“Source: AITS Mock 04 / Q68”) se banta hai, aur tabhi pakka hota hai jab kism, jawab, subject aur shabd milen. Isme AI nahi lagta; kisi paper, test ya score mein kuch nahi badalta.</p></div>
   <div className="admin-actions"><Button onClick={run} disabled={busy||data.running||!data.sources} data-testid="links-run">{busy||data.running?<Loader2 size={16} className="spin" aria-hidden="true"/>:<Link2 size={16} aria-hidden="true"/>}{made?'Dobara jodo':'Jod banao'}</Button></div></div>
  {!data.sources&&<p className="admin-note" data-testid="links-empty">Is exam mein abhi koi AITS paper ya chapter-wise PDF nahi hai jise joda ja sake. Upload ke baad yahan “Jod banao” dabaiye.</p>}
  {!!data.sources&&!made&&<p className="admin-note" data-testid="links-never">Jod abhi nahi bana. “Jod banao” dabaiye: {data.sources} upload ke Draft padhe jayenge. Kuch second lagte hain.</p>}
  {made&&<>
   <ul className="link-counts" data-testid="links-counts">{TILES.map(([k,label,hint])=><li key={k} className={'link-count is-'+k+(c[k]?'':' is-zero')} data-testid={'links-count-'+k}><strong>{c[k].toLocaleString('en-IN')}</strong><span>{label}</span><small>{hint}</small></li>)}</ul>
   <p className={'admin-note'+(data.fresh?'':' warn')} data-testid="links-state" data-fresh={data.fresh?'yes':'no'}>{data.fresh
    ?`Pichhli baar bana: ${fmtIST(data.ran_at)}. Tab se koi upload ya Draft nahi badla.`
    :`Pichhli baar bana: ${fmtIST(data.ran_at)}. Uske baad koi upload ya Draft badla hai: “Dobara jodo” dabaiye.`}
    {c.gone>0&&` ${c.gone} record aise hain jinki chhapi copy ab kisi upload mein nahi hai; unke shabd, jawab aur chapter rakhe hue hain.`}
    {c.changed>0&&` ${c.changed} sawaal ke shabd ya jawab pichhli baar se badle hain.`}</p>
   <label className="master-switch-row" data-testid="links-show-label"><Switch checked={!!data.show_chapters} disabled={busy||saving} onCheckedChange={show} data-testid="links-show-switch"/>
    <span><strong>AITS ke analysis mein chapter ke naam dikhao</strong>
     <small data-testid="links-named">{data.named} AITS sawaalon ko chapter-wise book se chapter ka naam mila hai. On karne par students ke AITS analysis mein (chapter-wise hisaab, kamzor chapter, Qs by Qs) yeh naam dikhte hain. Score aur rank nahi badalte; Off karte hi analysis pehle jaisa ho jata hai.</small></span></label>
   <Mocks rows={data.mocks}/>
   <Review items={data.review} more={data.review_more}/>
  </>}
  <Books items={data.books}/>
 </section>;
}
