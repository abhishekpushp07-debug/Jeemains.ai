import React from 'react';
import {AdminCrumbs} from '../admin/AdminShared';

export const STATUS={draft:['Draft','hidden'],live:['Live','live'],scheduled:['Scheduled','scheduled'],off:['Off','paused'],ended:['Ended','ended'],publishing:['Going live…','processing']};
export const KIND_LABEL={pyq:'PYQ',mocks:'Mock',chapters:'Chapter-wise',aits:'All India Test Series',custom:'Own type'};
export const SOURCE={book:'From PDF',chapter_book:'From PDF',import:'Paper upload',mock_book:'Mock book',pyq:'Verified PYQ',manual:'Older editor'};
export const plural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;
export const fmtIST=t=>new Date(t*1000).toLocaleString('en-IN',{day:'numeric',month:'short',year:'numeric',hour:'numeric',minute:'2-digit',timeZone:'Asia/Kolkata'})+' IST';
export const dayIST=d=>new Date(d+'T12:00:00+05:30').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Kolkata'});
export const clock=t=>{const [h,m]=t.split(':').map(Number);return `${h%12||12}:${String(m).padStart(2,'0')} ${h<12?'AM':'PM'}`;};
export const istToEpoch=(d,t)=>new Date(`${d}T${t}:00+05:30`).getTime()/1000;
export const marks=d=>d?`${d.minutes} min · +${d.correct} / ${d.wrong}`:'';
export const fixLink=m=>m.kind==='book_mock'?`/super-admin/fix/${m.book_id}/${m.id}`:`/super-admin/write/${m.id}`;

export const StatusLabel=({m})=>{
 if(m.status==='draft'&&m.to_fix)return ['Draft · '+m.to_fix+' to fix','attention'];
 if(m.status==='draft'&&m.empty)return ['Draft · no questions','hidden'];
 return STATUS[m.status]||['Off','paused'];
};

export const MasterCrumbs=({exam,type,last})=><AdminCrumbs items={[{label:'Master',to:'/super-admin'},...(exam?[{label:exam.name,to:'/super-admin/exam/'+exam.slug}]:[]),...(type?[{label:type.name,to:`/super-admin/exam/${exam.slug}/${type.id}`}]:[]),...(last?[{label:last}]:[])]}/>;

const PLAIN=[[/response type is unresolved|confirm response type/i,'Could not tell whether this question has options or a numerical answer.'],
 [/missing or conflicting supplied key/i,'Its answer was not found in the answer key, or two different answers were found.'],
 [/incomplete options or key does not match/i,'The answer does not match the options printed in the question.'],
 [/unsupported exact-integer key/i,'The numerical answer is not a whole number.'],
 [/original solution expected/i,'The book prints a solution for this question, but it was not found.'],
 [/original key region required/i,'Its answer was not found in the answer key.'],
 [/answer (or solution )?visible/i,'The answer seems to be printed inside the question picture.'],
 [/overlaps another/i,'The picture of this question overlaps another one.'],
 [/duplicate question|missing starting/i,'This question number appears twice.'],
 [/needs review|continuation/i,'Check that the whole question is in the picture.'],
 [/confirm printed examination rules/i,'Time and marks could not be read for this mock.'],
 [/unmapped pages/i,'Some pages near this mock could not be read.'],
 [/no complete questions found/i,'No complete question could be read for this mock.']];
// Reader messages in plain words for the Fix screens.
export const plain=text=>{const hit=PLAIN.find(([re])=>re.test(text||''));if(hit)return hit[1];
 return String(text||'').replace(/\bheld\b/gi,'waiting').replace(/source regions?/gi,'part of the page').replace(/regions?/gi,'part').replace(/publication/gi,'going Live').replace(/allowances?/gi,'approval').replace(/matching/gi,'checking');};

export const Field=({label,id,children})=><div className="master-field"><label htmlFor={id}>{label}</label>{children}</div>;
