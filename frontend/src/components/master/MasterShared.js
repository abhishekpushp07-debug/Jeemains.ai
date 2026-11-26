import React from 'react';
import {AdminCrumbs} from '../admin/AdminShared';

export const STATUS={draft:['Draft','hidden'],live:['Live','live'],scheduled:['Scheduled','scheduled'],off:['Off','paused'],ended:['Khatam','ended'],publishing:['Live ho raha hai…','processing']};
export const KIND_LABEL={pyq:'PYQ',mocks:'Mock',chapters:'Chapter-wise',aits:'All India Test Series',custom:'Apna type'};
export const SOURCE={book:'PDF se',chapter_book:'PDF se',import:'Paper upload',mock_book:'Mock book',pyq:'Verified PYQ',manual:'Purana editor'};
export const plural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;
export const fmtIST=t=>new Date(t*1000).toLocaleString('en-IN',{day:'numeric',month:'short',year:'numeric',hour:'numeric',minute:'2-digit',timeZone:'Asia/Kolkata'})+' IST';
export const dayIST=d=>new Date(d+'T12:00:00+05:30').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Kolkata'});
export const clock=t=>{const [h,m]=t.split(':').map(Number);return `${h%12||12}:${String(m).padStart(2,'0')} ${h<12?'AM':'PM'}`;};
export const istToEpoch=(d,t)=>new Date(`${d}T${t}:00+05:30`).getTime()/1000;
export const marks=d=>d?`${d.minutes} min · +${d.correct} / ${d.wrong}`:'';
export const fixLink=m=>m.kind==='book_mock'?`/super-admin/fix/${m.book_id}/${m.id}`:`/super-admin/write/${m.id}`;

export const StatusLabel=({m})=>{
 if(m.stuck)return ['Atki hai','attention'];
 // Switched on again (or back from the Library) and waiting for its pictures to be proven in storage: Off until then.
 if(m.pictures_wait?.state==='checking')return ['Off · pictures ki jaanch','processing'];
 if(m.pictures_wait?.state==='stuck')return ['Off · pictures saabit nahi hui','attention'];
 if(m.pictures_wait?.state==='missed')return ['Off · samay nikal gaya','attention'];
 if(m.status==='draft'&&m.rereading)return ['Draft · dobara padh rahe hain','processing'];
 if(m.status==='draft'&&m.to_fix)return ['Draft · '+m.to_fix+' fix karne hain','attention'];
 if(m.status==='draft'&&m.empty)return ['Draft · koi sawaal nahi','hidden'];
 if(m.status==='draft'&&m.missed_at)return ['Draft · samay nikal gaya','attention'];
 return STATUS[m.status]||['Off','paused'];
};

export const MasterCrumbs=({exam,type,last})=><AdminCrumbs items={[{label:'Master',to:'/super-admin'},...(exam?[{label:exam.name,to:'/super-admin/exam/'+exam.slug}]:[]),...(type?[{label:type.name,to:`/super-admin/exam/${exam.slug}/${type.id}`}]:[]),...(last?[{label:last}]:[])]}/>;

const PLAIN=[[/response type is unresolved|confirm response type/i,'Pata nahi chala ki is sawaal mein options hain ya numerical answer.'],
 [/missing or conflicting supplied key/i,'Iska answer, answer key mein nahi mila, ya do alag answer mile.'],
 [/incomplete options or key does not match/i,'Answer, sawaal mein chhape options se match nahi karta.'],
 [/unsupported exact-integer key/i,'Numerical answer poori sankhya (whole number) nahi hai.'],
 [/original solution expected/i,'Book is sawaal ka solution chhapti hai, par woh nahi mila.'],
 [/original key region required/i,'Iska answer, answer key mein nahi mila.'],
 [/answer (or solution )?visible/i,'Lagta hai answer sawaal ki picture ke andar hi chhapa hai.'],
 [/overlaps another/i,'Is sawaal ki picture doosre sawaal par chadh rahi hai.'],
 [/duplicate question|missing starting/i,'Yeh sawaal number do baar aaya hai.'],
 [/ambiguous worked-solution/i,'Solution ki picture galat jagah se shuru ya khatam ho sakti hai. Neeche kholkar dekhiye ki usme sirf isi sawaal ka solution hai.'],
 [/needs review|continuation/i,'Dekhiye ki poora sawaal picture mein aa gaya hai.'],
 [/confirm printed examination rules/i,'Is mock ka time aur marks padhe nahi ja sake.'],
 [/unmapped pages/i,'Is mock ke paas ke kuch page padhe nahi ja sake.'],
 [/no complete questions found/i,'Is mock ka ek bhi poora sawaal padha nahi ja saka.']];
// Reader messages in plain words for the Fix screens.
export const plain=text=>{const hit=PLAIN.find(([re])=>re.test(text||''));if(hit)return hit[1];
 return String(text||'').replace(/\bheld\b/gi,'ruka hua').replace(/source regions?/gi,'page ka hissa').replace(/regions?/gi,'hissa').replace(/publication/gi,'Live hona').replace(/allowances?/gi,'manzoori').replace(/matching/gi,'jaanch');};

// Why a paper that was asked to go Live (or was given a series day) is not there yet: said the same way wherever its row is shown.
export const stuckLine=(k,what='yeh abhi Live nahi hua')=>`Atki hai: ${k.kind==='hang'?'is PDF ka kaam baar-baar beech mein latak gaya':k.kind==='proof'?'iski pictures storage mein saabit nahi hui':'iski ek picture Supabase mein nahi ja rahi'}, isliye ${what}.${k.reason?` Wajah: ${k.reason}.`:''} ${k.kind==='hang'?'Har ghante':'Har 15 minute mein'} apne aap phir koshish hoti hai; abhi ke liye upar Uploads mein “Dobara chalao” dabaiye.`;

// A Draft whose chosen time passed while it waited for storage or for its pictures: the machine never opens it late.
export const missedLine=t=>`Chuna hua samay (${fmtIST(t)}) nikal gaya, isliye yeh Live nahi hua. Yeh der se apne aap nahi khulega: “Live karo” dabaiye ya naya samay chuniye.`;

export const Field=({label,id,children})=><div className="master-field"><label htmlFor={id}>{label}</label>{children}</div>;
