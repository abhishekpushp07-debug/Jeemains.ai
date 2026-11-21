import React,{createContext,useContext,useEffect,useLayoutEffect,useMemo,useRef,useState} from 'react';
import {Check,X,ZoomIn,ZoomOut,RotateCw} from 'lucide-react';
import {acquireSourceAsset} from '../lib/privateResources';
import {useAuth} from '../lib/auth';
import {MathText} from './QuestionContent';

// PDF Engine 2.0: a question cut into its question picture and one picture per option, all drawn at one zoom.
const ZOOMS=[1,1.35,1.8],KEY='jeelive-piece-zoom',FLOOR=.85;
const remembered=()=>{try{return Math.max(0,Math.min(ZOOMS.length-1,Number(localStorage.getItem(KEY))||0));}catch{return 0;}};
const Scale=createContext({k:1,zoom:0,grid:true,setZoom:()=>{},stem:null,opt:null,cell:null});

export function PieceScaleProvider({pieces,max=1.5,children}){
 const stem=useRef(null),opt=useRef(null),cell=useRef(null);
 const [fit,setFit]=useState(1),[grid,setGrid]=useState(true),[zoom,setZoomState]=useState(remembered);
 const widest=useMemo(()=>({q:Math.max(1,...pieces.filter(p=>p.part==='q').map(p=>p.w)),o:Math.max(0,...pieces.filter(p=>p.part!=='q').map(p=>p.w))}),[pieces]);
 useLayoutEffect(()=>{
  // One zoom for the whole question: the widest piece decides, so text is the same size in the question and in every option.
  const measure=()=>{
   const sw=stem.current?.clientWidth||0,ow=opt.current?.clientWidth||0,cw=cell.current?.clientWidth||0;
   const own=Math.min(max,sw?sw/widest.q:max);
   // Options sit two by two (A B, then C D below) whenever every option can be read in half the width; a long option gets the whole width instead.
   const two=!widest.o||!cw||cw/widest.o>=own*(zoom?ZOOMS[zoom]:FLOOR);
   const room=two?cw:ow;
   const next=Math.min(own,room&&widest.o?room/widest.o:own);
   setGrid(two);setFit(old=>Math.abs(old-next)>.003?next:old);
  };
  measure();
  const observer=new ResizeObserver(measure);
  [stem,opt,cell].forEach(r=>{if(r.current)observer.observe(r.current);});
  return()=>observer.disconnect();
 },[widest,max,zoom,grid]);
 const value=useMemo(()=>({k:fit*ZOOMS[zoom],zoom,grid,stem,opt,cell,setZoom:n=>{setZoomState(n);try{localStorage.setItem(KEY,String(n));}catch{/* zoom still works for this visit */}}}),[fit,zoom,grid]);
 return <Scale.Provider value={value}>{children}</Scale.Provider>;
}

export function PieceZoom(){
 const s=useContext(Scale);
 return <div className="piece-zoom" role="group" aria-label="Likhai ka size">
  <button type="button" disabled={s.zoom===0} onClick={()=>s.setZoom(s.zoom-1)} aria-label="Likhai chhoti karo" data-testid="piece-zoom-out"><ZoomOut size={16}/></button>
  <button type="button" disabled={s.zoom===ZOOMS.length-1} onClick={()=>s.setZoom(s.zoom+1)} aria-label="Likhai badi karo" data-testid="piece-zoom-in"><ZoomIn size={16}/></button>
 </div>;
}

export function PieceImage({path,alt,width,ratio,testId,onLoad,onError}){
 const {user}=useAuth();
 const hooks=useRef({onLoad,onError});hooks.current={onLoad,onError};
 const [src,setSrc]=useState(null),[failed,setFailed]=useState(false),[tries,setTries]=useState(0);
 useEffect(()=>{
  setSrc(null);setFailed(false);
  if(!user?.id)return undefined;
  let stopped=false,asset;
  acquireSourceAsset(path,{reload:tries>0}).then(value=>{asset=value;if(stopped)value.release();else setSrc(value.url);})
   .catch(error=>{if(!stopped&&error.name!=='AbortError'){setFailed(true);hooks.current.onError?.();}});
  return()=>{stopped=true;asset?.release();};
 },[path,user?.id,tries]);
 const fail=()=>{setFailed(true);hooks.current.onError?.();};
 if(failed)return <button type="button" className="piece-retry" onClick={e=>{e.preventDefault();e.stopPropagation();setTries(n=>n+1);}} data-testid={testId+'-retry'}><RotateCw size={14}/>Picture load nahi hui. Dobara try karo</button>;
 const style={width,aspectRatio:String(ratio)};
 return src?<img className="piece-img" src={src} alt={alt} style={style} draggable={false} onLoad={()=>hooks.current.onLoad?.()} onError={fail} data-testid={testId}/>
  :<span className="piece-img piece-wait" style={style} data-testid={testId+'-loading'}/>;
}

// draw(index, piece, width) returns the picture of one piece; index is its place in `pieces`.
export function PieceStem({pieces,draw,zoom=true,testId='piece-stem'}){
 const s=useContext(Scale);
 return <div className="piece-stem" data-testid={testId}>
  {zoom&&<PieceZoom/>}
  <div className="piece-paper"><div className="piece-fit" ref={s.stem}>{pieces.map((p,i)=>p.part==='q'?draw(i,p,p.w*s.k):null)}</div></div>
 </div>;
}

const WORDS={right:'Sahi jawab',mine:'Aapka jawab',both:'Aapka jawab · Sahi'};

export function PieceOptions({pieces,options,labels={},typed={},draw,mode='answer',name,value,onPick,disabled=false,correct=[],response,words=WORDS,testPrefix='player'}){
 const s=useContext(Scale);
 const firstPicture=options.find(key=>!typed[key]&&pieces.some(p=>p.part===key));
 // A hidden two-column row with the real card paddings: its cell is exactly the room an option picture gets in the 2 x 2 layout.
 const ruler=<div className={'piece-options piece-ruler is-grid is-'+mode} aria-hidden="true"><div className="piece-option"><span className="option-index piece-chip"/><div className="piece-paper"><div className="piece-fit" ref={s.cell}/></div></div><div className="piece-option"/></div>;
 return <>{ruler}<div className={'piece-options is-'+mode+(s.grid?' is-grid':' is-stack')} data-layout={s.grid?'grid':'stack'} data-testid={testPrefix+'-piece-options'}>{options.map(key=>{
  const i=pieces.findIndex(p=>p.part===key),label=labels[key]||key;
  // An option the owner typed is shown as text; every other option shows its own picture from the book.
  const body=typed[key]?<div className="piece-typed" data-testid={`${testPrefix}-option-math-${key}`}><MathText text={typed[key]}/></div>
   :i>=0?<div className="piece-paper" data-testid={`${testPrefix}-option-math-${key}`}><div className="piece-fit" ref={key===firstPicture?s.opt:undefined}>{draw(i,pieces[i],pieces[i].w*s.k)}</div></div>
   :<div className="piece-typed" data-testid={`${testPrefix}-option-math-${key}`}>Option {label}</div>;
  if(mode==='answer')return <label key={key} className={'answer-option piece-option'+(value===key?' selected':'')+(disabled?' is-disabled':'')} data-testid={`${testPrefix}-option-card-${key}`}>
   <input type="radio" name={name} value={key} checked={value===key} disabled={disabled} onChange={()=>onPick(key)} data-testid={`${testPrefix}-option-${key}`}/>
   <span className="option-index piece-chip" data-testid={`${testPrefix}-option-label-${key}`}>{label}</span>
   {body}
   <span className="piece-tick" aria-hidden="true"><Check size={15}/></span>
  </label>;
  const right=correct.includes(key),mine=response===key;
  return <div key={key} className={'piece-option'+(right?' is-correct':mine?' is-wrong':'')} data-testid={`${testPrefix}-option-card-${key}`}>
   <span className="option-index piece-chip">{label}</span>
   {body}
   {(right||mine)&&<span className="piece-mark" data-testid={`${testPrefix}-option-mark-${key}`}>{right?<Check size={13}/>:<X size={13}/>}{right&&mine?words.both||WORDS.both:right?words.right:words.mine||WORDS.mine}</span>}
  </div>;
 })}</div></>;
}

// Result and Solutions screens: the same cut, with the right option and the student's own pick marked on the option itself.
export function PieceReview({q,attemptId,gradeVersion='original'}){
 const tail=gradeVersion!=='original'?'?score_version='+encodeURIComponent(gradeVersion):'';
 const draw=(i,p,width)=><PieceImage key={i} path={`/attempts/${attemptId}/questions/${q.id}/asset/piece/${i}${tail}`} alt={p.part==='q'?`Question ${q.number}`:`Option ${p.part}`} width={width} ratio={p.w/p.h} testId={`review-piece-${q.number}-${i}`}/>;
 const correct=q.disposition==='bonus_all'||q.disposition==='dropped'?[]:(q.accepted_answers||[q.answer]);
 return <PieceScaleProvider pieces={q.pieces}>
  <PieceStem pieces={q.pieces} draw={draw} testId={'review-piece-stem-'+q.number}/>
  {q.type==='mcq'&&<PieceOptions mode="review" pieces={q.pieces} options={Object.keys(q.options||{})} labels={q.source_option_labels||{}} typed={q.typed_options||{}} draw={draw} correct={correct} response={q.response} testPrefix={'review-'+q.number}/>}
 </PieceScaleProvider>;
}
