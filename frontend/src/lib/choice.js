// Student Choice (JEE Main): the website's own copy of the app's rules (app book Part 1.4 to 1.6). The website makes the
// paper (POST /api/choice/papers); these helpers only show what it will be: its make-up, its time and its marks.
import {useCallback,useEffect,useState,useSyncExternalStore} from 'react';
import {api,post} from './api';

export const SUBJECTS=['Physics','Chemistry','Mathematics'];
export const SHORT={Physics:'Physics',Chemistry:'Chemistry',Mathematics:'Maths'};
export const MARKS={correct:4,wrong:-1};
export const NONE={Physics:0,Chemistry:0,Mathematics:0};
export const totalOf=c=>SUBJECTS.reduce((n,s)=>n+(c[s]||0),0);

/** Each question brings its subject's minutes; the paper's time is their sum rounded up (no three-hour cap). */
export const minutesFor=(counts,per)=>Math.ceil(Number(SUBJECTS.reduce((n,s)=>n+(counts[s]||0)*per[s],0).toFixed(4)));

/** The paper's time shared over its subjects, so the rows add up to exactly the paper's time. */
export function splitMinutes(counts,per){
 const total=minutesFor(counts,per),raw=SUBJECTS.map(s=>({s,v:(counts[s]||0)*per[s]}));
 const out={};raw.forEach(x=>{out[x.s]=Math.floor(x.v);});
 let left=total-SUBJECTS.reduce((n,s)=>n+out[s],0);
 [...raw].filter(x=>counts[x.s]).sort((a,b)=>(b.v%1)-(a.v%1)).forEach(x=>{if(left>0){out[x.s]+=1;left-=1;}});
 return out;
}

/** Equal over the subjects; one or two left over go to the first ones (Physics, then Chemistry). */
export function splitOf(n,subjects=SUBJECTS){
 const out={...NONE};subjects.forEach((s,i)=>{out[s]=Math.floor(n/subjects.length)+(i<n%subjects.length?1:0);});
 return out;
}

export function timeLabel(m){
 if(!m)return '0 min';const h=Math.floor(m/60),r=m%60;
 return h?`${h} ${h===1?'ghanta':'ghante'}${r?` ${r} min`:''}`:`${r} min`;
}

export const uuid=()=>(crypto.randomUUID?crypto.randomUUID():'k'+Math.random().toString(36).slice(2)+Date.now().toString(36));

/** One paper, one request_key: a retry of the same paper sends the same key, so it is never made (or counted) twice. */
export async function makePaper(body,key){
 const d=await post('/choice/papers',{exam:'jee-main',request_key:key,...body});
 return d.set_id;
}

/** The page's data: the open ways, the chapters with this student's own test state, today's count. */
export function useChoiceHome(enabled=true){
 const [data,setData]=useState(null),[error,setError]=useState(''),[tick,setTick]=useState(0);
 useEffect(()=>{
  if(!enabled)return undefined;const c=new AbortController();setError('');
  api('/choice/home',{signal:c.signal}).then(d=>{if(!c.signal.aborted)setData(d);}).catch(e=>{if(!c.signal.aborted&&e.name!=='AbortError')setError(e.message);});
  return()=>c.abort();
 },[enabled,tick]);
 return {data,error,reload:useCallback(()=>setTick(v=>v+1),[])};
}

// ---- what the student has chosen: chapters stay on this browser for the account; questions stay for this tab
let owner='',chapters=[],picked={},version=0;
const listeners=new Set();
const changed=()=>{version+=1;listeners.forEach(f=>f());};
const keep=()=>{
 if(!owner)return;
 try{localStorage.setItem('jl-choice-chapters-'+owner,JSON.stringify(chapters));sessionStorage.setItem('jl-choice-picked-'+owner,JSON.stringify(picked));}catch{/* private mode */}
};
function open(uid){
 if(owner===uid)return;
 owner=uid;chapters=[];picked={};
 try{
  const c=JSON.parse(localStorage.getItem('jl-choice-chapters-'+uid)||'[]'),p=JSON.parse(sessionStorage.getItem('jl-choice-picked-'+uid)||'{}');
  chapters=Array.isArray(c)?c.filter(x=>typeof x==='string').slice(0,300):[];
  picked=p&&typeof p==='object'&&!Array.isArray(p)?p:{};
 }catch{/* a broken copy starts empty */}
 changed();
}
export function useChoiceStore(uid){
 useEffect(()=>{if(uid)open(uid);},[uid]);
 return useSyncExternalStore(f=>{listeners.add(f);return()=>listeners.delete(f);},()=>version);
}
export const chosenChapters=()=>chapters;
export const hasChapter=id=>chapters.includes(id);
export function toggleChapter(id){
 if(chapters.includes(id)){chapters=chapters.filter(c=>c!==id);picked=Object.fromEntries(Object.entries(picked).filter(([,p])=>p.chapter!==id));}
 else chapters=[...chapters,id];
 keep();changed();
}
export const hasQuestion=id=>!!picked[id];
export const pickedCount=()=>Object.keys(picked).length;
export const pickedIn=chapter=>Object.values(picked).filter(p=>p.chapter===chapter).length;
export function counts(){const c={...NONE};Object.values(picked).forEach(p=>{c[p.subject]+=1;});return c;}
/** 'full' / 'subject' = not ticked: the paper, or its subject, already has all it may. */
export function toggleQuestion(id,from,bank){
 if(picked[id]){const next={...picked};delete next[id];picked=next;}
 else if(pickedCount()>=bank.max_questions)return 'full';
 else if(bank.max_per_subject&&counts()[from.subject]>=bank.max_per_subject)return 'subject';
 else picked={...picked,[id]:from};
 keep();changed();return 'ok';
}
/** Chosen questions that are still in the bank (a chapter may have gone since). */
export function dropGone(bank){
 const live=new Set(bank.subjects.flatMap(s=>s.chapters.map(c=>c.id)));
 const next=Object.fromEntries(Object.entries(picked).filter(([,p])=>live.has(p.chapter)));
 if(Object.keys(next).length!==pickedCount()){picked=next;keep();changed();}
}
/** The paper's order: Physics, Chemistry, Mathematics; then the chapter's place; then the question's number. */
export function orderedIds(bank){
 const place=new Map();bank.subjects.forEach(s=>s.chapters.forEach((c,i)=>place.set(c.id,i)));
 return Object.entries(picked).sort(([,a],[,b])=>SUBJECTS.indexOf(a.subject)-SUBJECTS.indexOf(b.subject)||(place.get(a.chapter)??0)-(place.get(b.chapter)??0)||a.n-b.n).map(([id])=>id);
}
export function clearChoice(){chapters=[];picked={};keep();changed();}
