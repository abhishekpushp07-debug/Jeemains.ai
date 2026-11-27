// Student Choice's chapter search, the same as the app's (src/choice/search.ts): a chapter by its name, in all three
// subjects at once. Best first: short name by first letters ("goc"), a word starts so ("therm"), first letters start so,
// the letters are inside the name; and only when nothing is found as typed, a near spelling ("kinametics").
const SHORT_NAMES={'3d':'three dimensional','3':'three',shm:'oscillations',emi:'electromagnetic induction',emw:'electromagnetic waves',nlm:'laws of motion',pnc:'permutations'};
const SMALL=new Set(['and','of','the','in','to','under']);
const plain=s=>s.toLowerCase().replace(/&/g,' and ').replace(/[^a-z0-9\u0080-\uffff]+/g,' ').trim();

export function searchIndex(subjects){
 return subjects.flatMap(s=>s.chapters.map(c=>{
  const words=plain(c.title).split(' ').filter(Boolean),big=words.filter(w=>!SMALL.has(w));
  return {c,subject:s.name,words,joined:words.join(''),initials:[...new Set([big.map(w=>w[0]).join(''),words.map(w=>w[0]).join('')])]};
 }));
}

function distance(a,b){
 let before=[],last=Array.from({length:b.length+1},(_,j)=>j);
 for(let i=1;i<=a.length;i++){
  const row=[i];
  for(let j=1;j<=b.length;j++){
   row[j]=Math.min(last[j]+1,row[j-1]+1,last[j-1]+(a[i-1]===b[j-1]?0:1));
   if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])row[j]=Math.min(row[j],before[j-2]+1);
  }
  before=last;last=row;
 }
 return last[b.length];
}
function slips(typed,word){
 if(typed.length<4||typed[0]!==word[0])return -1;
 let best=typed.length>=8?3:2;
 for(let n=typed.length-1;n<=typed.length+1;n++)if(n>=3&&n<=word.length)best=Math.min(best,distance(typed,word.slice(0,n)));
 return best<=(typed.length>=8?2:1)?best:-1;
}
function nearness(e,typed){
 let sum=0;
 for(const t of typed){
  if(e.words.some(w=>w.startsWith(t)))continue;
  const best=Math.min(...e.words.map(w=>slips(t,w)).filter(n=>n>=0));
  if(!Number.isFinite(best))return -1;
  sum+=best;
 }
 return sum;
}
function fit(e,typed){
 let worst=0;
 for(const t of typed){
  const alone=typed.length===1&&t.length>=2;
  const score=alone&&e.initials.includes(t)?0:e.words.some(w=>w.startsWith(t))?1:alone&&e.initials.some(i=>i.startsWith(t))?2:t.length>=3&&e.joined.includes(t)?3:-1;
  if(score<0)return -1;
  worst=Math.max(worst,score);
 }
 return worst;
}

export function findChapters(index,query){
 const typed=plain(query).split(' ').filter(Boolean).flatMap(t=>(SHORT_NAMES[t]||t).split(' ')).slice(0,8);
 if(!typed.length)return {items:[],close:false};
 const scored=index.map((e,at)=>({e,at,score:fit(e,typed)})).filter(x=>x.score>=0).sort((a,b)=>a.score-b.score||a.at-b.at);
 if(scored.length)return {items:scored.map(x=>({c:x.e.c,subject:x.e.subject})),close:false};
 const close=index.map((e,at)=>({e,at,off:nearness(e,typed)})).filter(x=>x.off>=0).sort((a,b)=>a.off-b.off||a.at-b.at);
 return {items:close.map(x=>({c:x.e.c,subject:x.e.subject})),close:close.length>0};
}
