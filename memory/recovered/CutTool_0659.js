import React,{useEffect,useMemo,useRef,useState} from 'react';
import {Loader2,CheckCircle2,AlertTriangle,RotateCcw,Maximize2,Minimize2,Scissors,Pencil,Move,ZoomIn,ZoomOut,FileText,ScanSearch,Plus,Minus,X,Check} from 'lucide-react';
import {Button} from '../ui/button';
import {post,fetchWithSession} from '../../lib/api';
import {useAuth} from '../../lib/auth';
import {PieceScaleProvider,PieceStem,PieceOptions} from '../QuestionPieces';
import {BookError} from './BookShared';
import {toast} from 'sonner';

// PDF Engine 2.0 fix tool: the whole page; draw a rectangle (or tap a printed box), say whose it is (Sawaal, A, B, C, D), and see beside it exactly what the student gets.
const TONES=['#2563EB','#D97706','#059669','#7C3AED','#DB2777','#0891B2'];
const NAME=k=>k==='q'?'Sawaal':k;
const MIN=.006,STEP=.002,ZOOMS=[1,1.5,2,3];
const round=b=>b.map(x=>Math.round(x*1e5)/1e5);
const cache=new Map();

function pageImage(path){
 if(!cache.has(path)){
  const job=fetchWithSession(path).then(async res=>{
   if(!res.ok)throw new Error('Page ki picture nahi khuli. Refresh dabao aur dobara dekho.');
   const url=URL.createObjectURL(await res.blob());
   return new Promise((done,fail)=>{const img=new Image();img.onload=()=>{URL.revokeObjectURL(url);done(img);};img.onerror=()=>{URL.revokeObjectURL(url);fail(new Error('Page ki picture nahi khuli. Refresh dabao aur dobara dekho.'));};img.src=url;});
  });
  job.catch(()=>cache.delete(path));
  cache.set(path,job);
  if(cache.size>24)cache.delete(cache.keys().next().value);
 }
 return cache.get(path);
}

function usePages(bookId,mockId,list){
 const key=list.join(',');
 const [state,setState]=useState({images:{},error:''});
 useEffect(()=>{
  let on=true;
  const wanted=key?key.split(',').map(Number):[];
  Promise.all(wanted.map(n=>pageImage(`/admin/books/${bookId}/mocks/${mockId}/page/${n}`).then(img=>[n,img])))
   .then(rows=>{if(on)setState({images:Object.fromEntries(rows),error:''});}).catch(e=>{if(on)setState({images:{},error:e.message});});
  return()=>{on=false;};
 },[bookId,mockId,key]);
 return state;
}

function CanvasPiece({image,part,width}){
 const ref=useRef(null);
 useEffect(()=>{
  const c=ref.current;if(!c||!image)return;
  const W=image.naturalWidth,H=image.naturalHeight,[x0,y0,x1,y1]=part.rect;
  const sx=Math.round(x0*W),sy=Math.round(y0*H),sw=Math.max(1,Math.round((x1-x0)*W)),sh=Math.max(1,Math.round((y1-y0)*H));
  c.width=sw;c.height=sh;
  const g=c.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,sw,sh);g.drawImage(image,sx,sy,sw,sh,0,0,sw,sh);
  // Ruled borders and the printed option label are painted white, as in the picture students get.
  for(const e of part.erase||[])g.fillRect(Math.floor(e[0]*W)-sx-1,Math.floor(e[1]*H)-sy-1,Math.ceil((e[2]-e[0])*W)+2,Math.ceil((e[3]-e[1])*H)+2);
 },[image,part]);
 return <canvas ref={ref} className="piece-img" style={{width,aspectRatio:`${part.w} / ${part.h}`}} role="img" aria-label={part.part==='q'?'Sawaal ki picture':'Option '+part.part}/>;
}

// parts: [{part, page, rect, erase, size}] as saved on the question's cut.
export function PiecesPreview({bookId,mockId,parts,q,empty}){
 const pages=useMemo(()=>[...new Set(parts.map(p=>p.page))],[parts]);
 const {images,error}=usePages(bookId,mockId,pages);
 const pieces=useMemo(()=>parts.map(p=>({...p,w:(p.rect[2]-p.rect[0])*p.size[0],h:(p.rect[3]-p.rect[1])*p.size[1]})),[parts]);
 if(!parts.length)return <p className="cut-empty">{empty}</p>;
 if(error)return <p className="cut-reason" role="alert">{error}</p>;
 const draw=(i,p,width)=><CanvasPiece key={i} image={images[p.page]} part={p} width={width}/>;
 return <PieceScaleProvider pieces={pieces} max={1.25}>
  <PieceStem pieces={pieces} draw={draw} zoom={false} testId={'cut-preview-stem-'+q.number}/>
  {q.type==='mcq'&&<PieceOptions mode="review" pieces={pieces} options={q.options} typed={q.typed_options||{}} draw={draw} correct={q.answer?[q.answer]:[]} words={{right:'Answer key'}} testPrefix={'cut-preview-'+q.number}/>}
 </PieceScaleProvider>;
}

function shift(b,handle,dx,dy,v){
 let [x0,y0,x1,y1]=b;
 if(handle==='move'){
  dx=Math.max(v[0]-x0,Math.min(v[2]-x1,dx));dy=Math.max(v[1]-y0,Math.min(v[3]-y1,dy));
  return [x0+dx,y0+dy,x1+dx,y1+dy];
 }
 if(handle.includes('w'))x0=Math.max(v[0],Math.min(x1-MIN,x0+dx));
 if(handle.includes('e'))x1=Math.min(v[2],Math.max(x0+MIN,x1+dx));
 if(handle.includes('n'))y0=Math.max(v[1],Math.min(y1-MIN,y0+dy));
 if(handle.includes('s'))y1=Math.min(v[3],Math.max(y0+MIN,y1+dy));
 return [x0,y0,x1,y1];
}

// Boxes to start from: the owner's saved boxes, else the engine's own cut or the page's printed boxes, else plain slices of the region.
function starting(cut,keys){
 const r=cut.region.rect,page=cut.region.page,out={};
 const inside=p=>{const x=(p.rect[0]+p.rect[2])/2,y=(p.rect[1]+p.rect[3])/2;return p.page===page&&x>=r[0]&&x<=r[2]&&y>=r[1]&&y<=r[3];};
 const own=cut.parts.filter(inside);
 const shares=keys.map(k=>k==='q'?2:1),total=shares.reduce((a,b)=>a+b,0);
 const x0=r[0]+(r[2]-r[0])*.04,x1=r[2]-(r[2]-r[0])*.04,top=r[1]+(r[3]-r[1])*.02,height=(r[3]-r[1])*.96;
 let used=0;
 keys.forEach((k,i)=>{
  const slice=[x0,top+height*used/total+.003,x1,top+height*(used+shares[i])/total-.003];used+=shares[i];
  out[k]=[...(cut.draft?.[k]||own.find(p=>p.part===k)?.rect||slice)];
 });
 return out;
}

function PageView({image,view}){
 const ref=useRef(null);
 useEffect(()=>{
  const c=ref.current;if(!c||!image)return;
  const W=image.naturalWidth,H=image.naturalHeight;
  const sx=Math.round(view[0]*W),sy=Math.round(view[1]*H),sw=Math.max(1,Math.round((view[2]-view[0])*W)),sh=Math.max(1,Math.round((view[3]-view[1])*H));
  c.width=sw;c.height=sh;c.getContext('2d').drawImage(image,sx,sy,sw,sh,0,0,sw,sh);
 },[image,view]);
 return <canvas ref={ref} role="img" aria-label="Kitaab ka page"/>;
}

// The page with its boxes. mode 'draw': pull out a new rectangle, or tap a printed box. mode 'move': drag and resize the boxes already there.
function Board({image,view,keys,boxes,frames,active,onActive,onChange,mode,pending,onPending,disabled}){
 const frame=useRef(null),drag=useRef(null),fingers=useRef(new Map());
 const [rubber,setRubber]=useState(null);
 const vw=view[2]-view[0],vh=view[3]-view[1];
 const place=b=>({left:(b[0]-view[0])/vw*100+'%',top:(b[1]-view[1])/vh*100+'%',width:(b[2]-b[0])/vw*100+'%',height:(b[3]-b[1])/vh*100+'%'});
 const seen=b=>b[2]>view[0]&&b[0]<view[2]&&b[3]>view[1]&&b[1]<view[3];
 const at=e=>{const r=frame.current.getBoundingClientRect();return [view[0]+Math.max(0,Math.min(1,(e.clientX-r.left)/r.width))*vw,view[1]+Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))*vh];};
 const span=(a,b)=>[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[0],b[0]),Math.max(a[1],b[1])];
 function down(e,key,handle){
  if(disabled||mode!=='move')return;
  e.preventDefault();e.stopPropagation();
  e.currentTarget.setPointerCapture?.(e.pointerId);
  const r=frame.current.getBoundingClientRect();
  drag.current={key,handle,x:e.clientX,y:e.clientY,box:boxes[key],w:r.width,h:r.height};
  onActive(key);
 }
 function move(e){
  const d=drag.current;if(!d||d.draw)return;
  onChange(d.key,shift(d.box,d.handle,(e.clientX-d.x)/d.w*vw,(e.clientY-d.y)/d.h*vh,view));
 }
 const up=()=>{drag.current=null;};
 function nudge(e,key){
  const step={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];
  if(!step||disabled)return;
  e.preventDefault();
  onChange(key,shift(boxes[key],e.shiftKey?'se':'move',step[0]*STEP,step[1]*STEP,view));
 }
 function start(e){
  e.preventDefault();e.currentTarget.setPointerCapture?.(e.pointerId);
  fingers.current.set(e.pointerId,[e.clientX,e.clientY]);
  // One finger (or the mouse) draws. Two fingers slide the zoomed page instead.
  if(fingers.current.size>1){drag.current=null;setRubber(null);return;}
  drag.current={draw:true,from:at(e),x:e.clientX,y:e.clientY};setRubber(null);
 }
 function pull(e){
  const f=fingers.current,was=f.get(e.pointerId);
  if(f.size>1&&was){
   const pane=frame.current.closest('.cut-scroll');
   if(pane){pane.scrollLeft-=(e.clientX-was[0])/f.size;pane.scrollTop-=(e.clientY-was[1])/f.size;}
   f.set(e.pointerId,[e.clientX,e.clientY]);return;
  }
  const d=drag.current;if(d?.draw)setRubber(span(d.from,at(e)));
 }
 function finish(e){
  const sliding=fingers.current.size>1;fingers.current.delete(e.pointerId);
  const d=drag.current;drag.current=null;setRubber(null);
  if(sliding||!d?.draw)return;
  if(Math.hypot(e.clientX-d.x,e.clientY-d.y)<6){
   // A tap: the smallest printed box under the finger is taken whole.
   const hit=frames.filter(f=>d.from[0]>=f[0]&&d.from[0]<=f[2]&&d.from[1]>=f[1]&&d.from[1]<=f[3]).sort((a,b)=>(a[2]-a[0])*(a[3]-a[1])-(b[2]-b[0])*(b[3]-b[1]))[0];
   if(hit)onPending([...hit]);
   return;
  }
  const r=span(d.from,at(e));
  if(r[2]-r[0]>=MIN&&r[3]-r[1]>=MIN)onPending(r);
 }
 const shown=rubber||pending;
 return <div className={'cut-frame is-'+mode} ref={frame} data-testid="cut-frame">
  <PageView image={image} view={view}/>
  {frames.filter(seen).map((f,i)=><span key={'f'+i} className="cut-printed" style={place(f)} aria-hidden="true" data-testid={'cut-printed-'+i}/>)}
  {keys.map((key,i)=><div key={key} role="button" tabIndex={0} aria-label={`${NAME(key)} ka box. Arrow keys se hilao, Shift ke saath size badlo.`}
   className={'cut-box'+(active===key?' is-active':'')} style={{...place(boxes[key]),'--tone':TONES[i%TONES.length]}}
   onPointerDown={e=>down(e,key,'move')} onPointerMove={move} onPointerUp={up} onPointerCancel={up} onKeyDown={e=>nudge(e,key)} onFocus={()=>onActive(key)} data-testid={'cut-box-'+key}>
   <span className="cut-box-tag">{NAME(key)}</span>
   {mode==='move'&&active===key&&!disabled&&['nw','ne','sw','se'].map(h=><span key={h} className={'cut-handle h-'+h} onPointerDown={e=>down(e,key,h)} onPointerMove={move} onPointerUp={up} onPointerCancel={up} data-testid={`cut-handle-${key}-${h}`}/>)}
  </div>)}
  {mode==='draw'&&!disabled&&<div className="cut-draw" role="application" aria-label="Page par naya box kheencho" onPointerDown={start} onPointerMove={pull} onPointerUp={finish} onPointerCancel={e=>{fingers.current.delete(e.pointerId);drag.current=null;setRubber(null);}} data-testid="cut-draw-layer"/>}
  {shown&&<span className={'cut-pending'+(rubber?'':' is-set')} style={place(shown)} data-testid="cut-pending"/>}
 </div>;
}

export function CutTool({q,bookId,mockId,revision,frozen,onSaved}){
 const {user}=useAuth();const owner=user?.role==='owner';
 const cut=q.cut,page=cut.region.page,tag='cut-q-'+q.number,held=cut.status==='held';
 const keys=useMemo(()=>['q',...cut.labels],[cut]);
 const frames=useMemo(()=>cut.frames||[],[cut]);
 const [open,setOpen]=useState(held),[wide,setWide]=useState(false),[full,setFull]=useState(true),[zoom,setZoom]=useState(0),[mode,setMode]=useState(held?'draw':'move');
 const view=useMemo(()=>{if(full)return [0,0,1,1];const r=cut.region.rect;return [Math.max(0,r[0]-.012),Math.max(0,r[1]-.012),Math.min(1,r[2]+.012),Math.min(1,r[3]+.012)];},[cut,full]);
 const [boxes,setBoxes]=useState(()=>starting(cut,keys)),[dirty,setDirty]=useState(held),[pending,setPending]=useState(null),[placed,setPlaced]=useState([]);
 const [check,setCheck]=useState(null),[checking,setChecking]=useState(false),[accept,setAccept]=useState(!!cut.accept_outside);
 const [busy,setBusy]=useState(''),[error,setError]=useState(''),[active,setActive]=useState('q'),[done,setDone]=useState(false),[target,setTarget]=useState(null);
 const turn=useRef(0);
 const {images,error:pageError}=usePages(bookId,mockId,open?[page]:[]);
 const url=`/admin/books/${bookId}/mocks/${mockId}/cut`;
 const payload=()=>Object.fromEntries(keys.map(k=>[k,round(boxes[k])]));
 useEffect(()=>{
  if(!open||!dirty||frozen)return undefined;
  const mine=++turn.current;
  // Live preview: every change of a box is checked by the same engine checks, without saving.
  const timer=setTimeout(async()=>{
   setChecking(true);
   try{const r=await post(url,{revision,question_id:q.id,mode:'boxes',boxes:payload(),save:false,accept_outside:accept});if(mine===turn.current)setCheck(r);}
   catch(e){if(mine===turn.current)setCheck({ok:false,reason:e.message,outside:false,pieces:{}});}
   finally{if(mine===turn.current)setChecking(false);}
  },450);
  return()=>clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
 },[boxes,accept,dirty,open,frozen]);
 const parts=useMemo(()=>{
  if(check)return keys.filter(k=>check.pieces?.[k]).map(k=>({part:k,page,size:check.size,...check.pieces[k]}));
  return dirty?[]:cut.parts;
 },[check,dirty,cut,keys,page]);
 async function send(sendMode,extra={}){
  setBusy(sendMode);setError('');
  try{const r=await post(url,{revision,question_id:q.id,mode:sendMode,save:true,...extra});toast.success(r.message);setDone(true);onSaved?.();}
  catch(e){setError(e.message);}finally{setBusy('');}
 }
 function change(next,mine){setBoxes(next);setDirty(true);setPlaced(mine);if(keys.every(k=>mine.includes(k)))setMode('move');}
 // The rectangle just drawn (or the printed box just tapped) becomes this piece's box.
 function place(key,rect){const mine=[...new Set([...placed,key])];change({...boxes,[key]:rect},mine);setPending(null);setActive(key);return mine;}
 // Two ways, both work: draw first and then say whose it is, or pick Sawaal / A / B / C / D first and then draw (the next one is picked by itself).
 function drawn(rect){if(!target){setPending(rect);return;}const mine=place(target,rect);setTarget(keys.find(k=>!mine.includes(k))||null);}
 function choose(key){if(pending)place(key,pending);else setTarget(t=>t===key?null:key);}
 function takePrinted(){change(Object.fromEntries(keys.map((k,i)=>[k,[...frames[i]]])),keys);setPending(null);setTarget(null);}
 function resize(d){const b=boxes[active];if(b[2]-b[0]+2*d<MIN||b[3]-b[1]+2*d<MIN)return;setBoxes({...boxes,[active]:[Math.max(0,b[0]-d),Math.max(0,b[1]-d),Math.min(1,b[2]+d),Math.min(1,b[3]+d)]});setDirty(true);}
 function reset(){setBoxes(starting(cut,keys));setCheck(null);setDirty(held);setAccept(!!cut.accept_outside);setPending(null);setPlaced([]);setTarget(null);}
 const next=keys.find(k=>!placed.includes(k));
 const locked=frozen||done;
 const line={ok:`Engine ne saaf kaat diya: sawaal${cut.labels.length?` + ${cut.labels.length} option`:''}.`,manual:'Aapke banaye boxes se kata hai.',trim:'Numerical sawaal: sirf sawaal ki picture banti hai, options nahi.',
  whole:'Aapne chuna hai: yeh sawaal ek poori picture me dikhega (purana look).',held:'Engine ne yahan andaza nahi lagaya. Aap theek karo.'}[cut.status]||'';
 const empty=cut.status==='whole'&&!dirty?'Yeh sawaal ek poori picture me dikhega. Naya look chahiye toh boxes bana kar save karo.':'Jab boxes saare check paas karenge, yahan wahi dikhega jo student ko milega.';
 return <section className={'cut-tool is-'+cut.status} data-testid={tag}>
  <div className="cut-status" data-testid={tag+'-status'}>
   {held?<AlertTriangle size={18} aria-hidden="true"/>:<CheckCircle2 size={18} aria-hidden="true"/>}
   <div><strong>{line}</strong>{held&&<p data-testid={tag+'-held-reason'}>{cut.reason}</p>}</div>
   <Button size="sm" variant="outline" onClick={()=>setOpen(o=>!o)} aria-expanded={open} data-testid={tag+'-toggle'}><Scissors size={15}/>{open?'Band karo':'Cut dekho ya badlo'}</Button>
  </div>
  {open&&<>
   <div className={'cut-grid'+(wide?' is-wide':'')}>
    <div className="cut-pane">
     <div className="cut-pane-head"><h4>Page {page} par boxes</h4><Button size="sm" variant="ghost" onClick={()=>setWide(w=>!w)} data-testid={tag+'-wide'}>{wide?<Minimize2 size={14}/>:<Maximize2 size={14}/>}{wide?'Chhota karo':'Bada karo'}</Button></div>
     <div className="cut-bar">
      {!locked&&<div className="cut-seg" role="group" aria-label="Kya karna hai">
       <button type="button" className={mode==='draw'?'is-on':''} aria-pressed={mode==='draw'} onClick={()=>setMode('draw')} data-testid={tag+'-mode-draw'}><Pencil size={14}/>Naya box kheencho</button>
       <button type="button" className={mode==='move'?'is-on':''} aria-pressed={mode==='move'} onClick={()=>{setMode('move');setPending(null);setTarget(null);}} data-testid={tag+'-mode-move'}><Move size={14}/>Box hilao</button>
      </div>}
      <div className="cut-seg" role="group" aria-label="Kitna page dikhe">
       <button type="button" className={full?'is-on':''} aria-pressed={full} onClick={()=>setFull(true)} data-testid={tag+'-view-full'}><FileText size={14}/>Poora page</button>
       <button type="button" className={full?'':'is-on'} aria-pressed={!full} onClick={()=>setFull(false)} data-testid={tag+'-view-region'}><ScanSearch size={14}/>Sirf yeh sawaal</button>
      </div>
      <div className="cut-seg" role="group" aria-label="Page ka size">
       <button type="button" disabled={zoom===0} onClick={()=>setZoom(z=>z-1)} aria-label="Page chhota karo" data-testid={tag+'-zoom-out'}><ZoomOut size={15}/></button>
       <button type="button" disabled={zoom===ZOOMS.length-1} onClick={()=>setZoom(z=>z+1)} aria-label="Page bada karo" data-testid={tag+'-zoom-in'}><ZoomIn size={15}/></button>
      </div>
     </div>
     {pageError?<p className="cut-reason" role="alert">{pageError}</p>:!images[page]?<p className="cut-wait" data-testid={tag+'-page-loading'}><Loader2 size={16} className="spin"/>Page khul raha hai…</p>
      :<div className={'cut-scroll'+(zoom?' is-zoomed':'')} style={{'--zoom':ZOOMS[zoom]}} data-testid={tag+'-scroll'}>
       <Board image={images[page]} view={view} keys={keys} boxes={boxes} frames={frames} active={active} onActive={setActive} mode={locked?'move':mode} pending={pending} onPending={drawn} disabled={locked}
        onChange={(k,b)=>{setBoxes(old=>({...old,[k]:b}));setDirty(true);}}/>
      </div>}
     {!locked&&mode==='draw'&&<div className={'cut-assign'+(pending?' is-asking':target?' is-armed':'')} role="group" aria-label={pending?'Yeh hissa kiska hai':'Kiska box banana hai'} data-testid={tag+'-assign'}>
      <strong data-testid={tag+'-assign-title'}>{pending?'Yeh hissa kiska hai?':target?`Ab page par ${NAME(target)} ka box kheencho`:'Box kheencho, phir batao kiska hai. Ya pehle yahan chuno, phir kheencho.'}</strong>
      {keys.map((k,i)=><button type="button" key={k} className={'cut-key'+((pending?k===next:k===target)?' is-active':'')} style={{'--tone':TONES[i%TONES.length]}} aria-pressed={!pending&&k===target} onClick={()=>choose(k)} data-testid={`${tag}-assign-${k}`}>{placed.includes(k)&&<Check size={13}/>}{NAME(k)}</button>)}
      {pending&&<button type="button" className="cut-drop" onClick={()=>setPending(null)} aria-label="Yeh rectangle hatao" data-testid={tag+'-assign-cancel'}><X size={15}/></button>}
     </div>}
     {!locked&&!pending&&mode==='move'&&<div className="cut-keys" role="group" aria-label="Box chuno">
      {keys.map((k,i)=><button type="button" key={k} className={'cut-key'+(active===k?' is-active':'')} style={{'--tone':TONES[i%TONES.length]}} onClick={()=>setActive(k)} data-testid={`${tag}-key-${k}`}>{NAME(k)}</button>)}
      <span className="cut-size"><button type="button" onClick={()=>resize(-STEP)} aria-label={`${NAME(active)} ka box chhota karo`} data-testid={tag+'-shrink'}><Minus size={15}/></button><button type="button" onClick={()=>resize(STEP)} aria-label={`${NAME(active)} ka box bada karo`} data-testid={tag+'-grow'}><Plus size={15}/></button></span>
     </div>}
     {!locked&&frames.length===keys.length&&keys.length>1&&<Button size="sm" variant="outline" onClick={takePrinted} data-testid={tag+'-use-printed'}>Page ke chhape hue {frames.length} boxes hi laga do</Button>}
     {!locked&&<small className="held-hint" data-testid={tag+'-hint'}>{mode==='draw'
      ?`Do tareeke, dono chalte hain. (1) Page par ungli ya mouse se rectangle kheencho${frames.length?' ya kisi chhape hue box par tap karo':''}, phir batao ki woh Sawaal hai ya option ${cut.labels.join(', ')||'A, B, C, D'}. (2) Pehle Sawaal ya option ka button dabao, phir kheencho: agla button apne aap chun jata hai. Type karne ki zaroorat nahi.`
      :'Box ko pakad kar hilao, kone ke gol nishaan se chhota-bada karo, ya − + dabao. Keyboard par arrow keys hilati hain, Shift + arrow size badalti hai. Do box ek doosre par na chadhen.'}</small>}
    </div>
    <div className="cut-pane">
     <div className="cut-pane-head"><h4>Student ko aise dikhega</h4>{checking&&<span className="cut-checking" data-testid={tag+'-checking'}><Loader2 size={14} className="spin"/>Check ho raha hai…</span>}</div>
     {check&&!check.ok&&<p className="cut-reason" role="alert" data-testid={tag+'-reason'}><AlertTriangle size={15} aria-hidden="true"/>{check.reason}</p>}
     {check?.ok&&dirty&&<p className="cut-good" data-testid={tag+'-good'}><CheckCircle2 size={15} aria-hidden="true"/>Saare check paas. Ab save kar sakte ho.</p>}
     <div className="cut-student" data-testid={tag+'-preview'}><PiecesPreview bookId={bookId} mockId={mockId} parts={parts} q={q} empty={empty}/></div>
    </div>
   </div>
   {owner&&!frozen&&(check?.outside||accept)&&<label className="book-check held-override"><input type="checkbox" checked={accept} onChange={e=>{setAccept(e.target.checked);setDirty(true);}} data-testid={tag+'-accept-outside'}/><span><strong>Override:</strong> Boxes ke bahar jo chhapa hai woh is sawaal ka hissa nahi hai (jaise watermark ya page ka nishaan). Use chhod do.</span></label>}
   <BookError error={error}/>
   {!frozen&&<div className="book-actions">
    <Button disabled={!check?.ok||checking||!!busy||done} onClick={()=>send('boxes',{boxes:payload(),accept_outside:accept})} data-testid={tag+'-save'}>{busy==='boxes'&&<Loader2 size={16} className="spin"/>}Boxes save karo</Button>
    <Button variant="outline" disabled={!!busy||done} onClick={reset} data-testid={tag+'-reset'}><RotateCcw size={15}/>Boxes pehle jaise</Button>
    {owner&&cut.mode!=='whole'&&<Button variant="outline" disabled={!!busy||done} onClick={()=>send('whole')} data-testid={tag+'-whole'}>{busy==='whole'&&<Loader2 size={16} className="spin"/>}Poori picture hi dikhao</Button>}
    {cut.mode!=='auto'&&<Button variant="ghost" disabled={!!busy||done} onClick={()=>send('auto')} data-testid={tag+'-auto'}>{busy==='auto'&&<Loader2 size={16} className="spin"/>}Engine ka apna cut wapas lo</Button>}
   </div>}
   {done&&<p className="held-saved" data-testid={tag+'-saved'}><CheckCircle2 size={15}/>Save ho gaya · dobara check ho raha hai</p>}
  </>}
 </section>;
}
