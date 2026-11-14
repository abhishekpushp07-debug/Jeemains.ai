import React,{useState} from 'react';
import {Wrench,Send} from 'lucide-react';
import {Button} from '../ui/button';
import {Switch} from '../ui/switch';
import {Input} from '../ui/input';
import {StatusChip,StudentPath} from './AdminShared';

function PublishBar({ready,busy,onPublish}){
 const [when,setWhen]=useState('now'),[at,setAt]=useState('');
 return <div className="admin-publish-bar" data-testid="publish-ready-bar">
  <div><strong data-testid="publish-ready-count">{ready} ready mock{ready===1?'':'s'}</strong><small>Held mocks stay private until their problems are fixed.</small></div>
  <div className="admin-choice-row" role="radiogroup" aria-label="When to publish">{[['now','Now'],['later','Choose date and time']].map(([v,l])=><button type="button" role="radio" aria-checked={when===v} key={v} className={'admin-pill'+(when===v?' is-picked':'')} onClick={()=>setWhen(v)} data-testid={'publish-when-'+v}>{l}</button>)}</div>
  {when==='later'&&<Input type="datetime-local" aria-label="Publish at (your local time)" value={at} onChange={e=>setAt(e.target.value)} data-testid="publish-at"/>}
  <Button disabled={busy||!ready||(when==='later'&&!at)} onClick={()=>onPublish(when==='later'?new Date(at).getTime()/1000:null)} data-testid="publish-all-ready"><Send size={16}/>Publish all ready</Button>
 </div>;
}

function MockRow({m,set,busy,onRequest,onToggle,onFix,index}){
 const state=set?set.state:m.publish_requested?'publishing':m.state==='published'?'live':m.state;
 const on=set?set.state!=='unlive':m.publish_requested;
 const canSwitch=!busy&&(set?true:m.state==='ready'&&!m.publish_requested);
 return <li className={'admin-row is-new'+(m.state==='held'?' is-held':'')} data-testid={'preview-mock-'+m.id}>
  <span className="admin-test-index" aria-hidden="true">{String(index).padStart(2,'0')}</span>
  <div className="admin-row-main"><strong data-testid={'preview-mock-title-'+m.id}>{set?.title||m.label}</strong><small>{m.count} questions · {m.original_solutions} original explanations · {m.key_only} key-only</small>{m.state==='held'&&<p className="admin-reason" data-testid={'preview-mock-reason-'+m.id}>{m.issues[0]}{m.issues.length>1?` (+${m.issues.length-1} more)`:''}</p>}</div>
  <StatusChip state={state} testId={'preview-mock-state-'+m.id}/>
  <div className="admin-test-actions">
   {m.state==='held'&&<Button variant="outline" onClick={()=>onFix(m.id)} data-testid={'preview-mock-fix-'+m.id}><Wrench size={15}/>Fix</Button>}
   <label className="admin-switch"><Switch checked={on} disabled={!canSwitch} onCheckedChange={v=>set?onToggle(set,v):v&&onRequest(m)} aria-label={'Live for students: '+m.label} data-testid={'preview-mock-live-'+m.id}/><span>{on?'Live':'Off'}</span></label>
  </div>
 </li>;
}

export function StudentPreview({book,section,busy,onPublish,onRequest,onToggle,onFix}){
 const dest=book.destination;const items=section?.items||[];
 const others=items.filter(t=>t.book_import_id!==book.id);
 const mine=new Map(items.filter(t=>t.book_import_id===book.id).map(t=>[t.id,t]));
 const ready=book.mocks.filter(m=>m.state==='ready'&&!m.publish_requested).length;
 return <section className="admin-panel admin-preview" data-testid="student-preview">
  <span className="eyebrow">STUDENTS WILL SEE IT LIKE THIS</span>
  <StudentPath exam={dest.exam_name} section={dest.section_name}/>
  <p className="admin-note">Tests already in this section stay first. New mocks follow in printed order and use their printed names. Nothing goes live until you publish it.</p>
  <PublishBar ready={ready} busy={busy} onPublish={onPublish}/>
  <ol className="admin-list admin-preview-list" data-testid="student-preview-list">
   {others.map((t,i)=><li key={t.id} className="admin-row is-existing" data-testid={'preview-existing-'+t.id}><span className="admin-test-index" aria-hidden="true">{String(i+1).padStart(2,'0')}</span><div className="admin-row-main"><strong>{t.title}</strong><small>Already in this section</small></div><StatusChip state={t.state}/></li>)}
   {book.mocks.map((m,i)=><MockRow key={m.id} m={m} set={m.set_id&&mine.get(m.set_id)} index={others.length+i+1} busy={busy} onRequest={onRequest} onToggle={onToggle} onFix={onFix}/>)}
   {!book.mocks.length&&<li className="admin-empty" data-testid="preview-no-mocks">Mocks appear here as soon as reading finds their printed boundaries.</li>}
  </ol>
 </section>;
}
