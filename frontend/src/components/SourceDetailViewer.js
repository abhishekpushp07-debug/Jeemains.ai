import React,{useEffect,useRef,useState} from 'react';
import {ArrowDown,ArrowLeft,ArrowRight,ArrowUp,RotateCcw,ZoomIn,ZoomOut,Maximize2} from 'lucide-react';
import {Button} from './ui/button';
import {Skeleton} from './ui/skeleton';

// Only authenticated original pixels are drawn; no formula or option is transcribed.
export const SourceDetailViewer=({src,alt,inline=false,testId='source',onExpand,onLoad,onError})=>{
 const callbacks=useRef({onLoad,onError});callbacks.current={onLoad,onError};
 const canvas=useRef(null),frame=useRef(null),drag=useRef(null),metrics=useRef(null);
 const [image,setImage]=useState(null),[mode,setMode]=useState('fit'),[zoom,setZoom]=useState(1),[pan,setPan]=useState({x:0,y:0}),[size,setSize]=useState({w:1,h:1}),[error,setError]=useState(false),[reload,setReload]=useState(0);
 useEffect(()=>{setMode('fit');setZoom(1);setPan({x:0,y:0});drag.current=null;},[src]);
 useEffect(()=>{let active=true;setImage(null);setError(false);setPan({x:0,y:0});const img=new Image();img.onload=()=>{if(active){setImage(img);callbacks.current.onLoad?.()}};img.onerror=()=>{if(active){setError(true);callbacks.current.onError?.()}};img.src=src;return()=>{active=false}},[src,reload]);
 useEffect(()=>{const observer=new ResizeObserver(entries=>{const r=entries[0].contentRect;setSize({w:r.width,h:r.height})});if(frame.current)observer.observe(frame.current);return()=>observer.disconnect()},[]);
 useEffect(()=>{
  if(!image||!canvas.current)return;
  const c=canvas.current,dpr=Math.min(window.devicePixelRatio||1,2),ctx=c.getContext('2d');
  c.width=Math.round(size.w*dpr);c.height=Math.round(size.h*dpr);ctx.scale(dpr,dpr);ctx.clearRect(0,0,size.w,size.h);
  const readableWidth=parseFloat(getComputedStyle(frame.current).getPropertyValue('--source-readable-width'))||760;
  const fit=Math.min(size.w/image.naturalWidth,size.h/image.naturalHeight);
  const ratio=(mode==='readable'?Math.max(fit,Math.min(readableWidth,image.naturalWidth)/image.naturalWidth):fit)*zoom;
  const w=image.naturalWidth*ratio,h=image.naturalHeight*ratio,minX=Math.min(0,size.w-w),minY=Math.min(0,size.h-h);
  metrics.current={minX,minY};const x=Math.max(minX,Math.min(0,pan.x)),y=Math.max(minY,Math.min(0,pan.y));
  ctx.drawImage(image,x,y,w,h);
 },[image,zoom,mode,pan,size]);
 function move(x,y){const m=metrics.current||{minX:0,minY:0};setPan(p=>({x:Math.max(m.minX,Math.min(0,p.x+x)),y:Math.max(m.minY,Math.min(0,p.y+y))}))}
 function changeZoom(next){setZoom(Math.max(1,Math.min(5,next)));setPan({x:0,y:0})}
 function setView(next){setMode(next);setZoom(1);setPan({x:0,y:0})}
 function keys(e){const action={ArrowLeft:()=>move(60,0),ArrowRight:()=>move(-60,0),ArrowUp:()=>move(0,60),ArrowDown:()=>move(0,-60),'+':()=>changeZoom(zoom+.5),'-':()=>changeZoom(zoom-.5)}[e.key];if(action){e.preventDefault();e.stopPropagation();action()}}
 const id=name=>testId+'-'+name;
 return <div className={'source-detail-viewer '+(inline?'source-inline-viewer':'')} data-testid={inline?id('viewport'):'source-detail-viewer'}>
  <div className="source-zoom-controls">
   <Button variant="outline" onClick={()=>setView('fit')} aria-pressed={mode==='fit'} disabled={!image} data-testid={inline?id('fit'):'source-zoom-reset'}><RotateCcw size={15}/>Fit</Button>
   <Button variant="outline" onClick={()=>setView('readable')} aria-pressed={mode==='readable'} disabled={!image} data-testid={id('readable')}>Readable</Button>
   <Button variant="outline" size="icon" onClick={()=>changeZoom(zoom-.5)} disabled={zoom<=1||!image} aria-label="Zoom out" data-testid={inline?id('zoom-out'):'source-zoom-out'}><ZoomOut size={18}/></Button>
   <Button variant="outline" size="icon" onClick={()=>changeZoom(zoom+.5)} disabled={zoom>=5||!image} aria-label="Zoom in" data-testid={inline?id('zoom-in'):'source-zoom-in'}><ZoomIn size={18}/></Button>
   {!inline&&<span role="status" data-testid="source-zoom-level">{Math.round(zoom*100)}% {mode==='readable'?'readable':''}</span>}
   {onExpand&&<Button variant="outline" size="icon" onClick={onExpand} aria-label="Open full-screen source detail" data-testid={id('fullscreen')}><Maximize2 size={18}/></Button>}
  </div>
  <div ref={frame} className="source-canvas-frame" data-view-mode={mode} style={inline&&image?{'--source-ratio':image.naturalHeight/image.naturalWidth,'--source-fit-width':size.w+'px'}:undefined}>
   {!image&&!error&&<Skeleton className="source-canvas-loading" data-testid={id('loading')}/>}
   <canvas ref={canvas} className="source-pan-canvas" tabIndex={0} role="img" aria-label={alt+' Drag or use arrow keys to read across the original. Plus and minus zoom.'} data-testid={inline?id('canvas'):'source-zoom-canvas'} onKeyDown={keys}
    onPointerDown={e=>{drag.current={x:e.clientX,y:e.clientY};e.currentTarget.setPointerCapture(e.pointerId)}}
    onPointerMove={e=>{if(!drag.current)return;move(e.clientX-drag.current.x,e.clientY-drag.current.y);drag.current={x:e.clientX,y:e.clientY}}}
    onPointerUp={()=>{drag.current=null}} onPointerCancel={()=>{drag.current=null}}/>
  </div>
  {error&&<p role="alert" data-testid={id('error')}>The original image could not load. <Button variant="outline" onClick={()=>setReload(v=>v+1)} data-testid={id('retry')}>Retry</Button></p>}
  <div className="source-reader-bottom"><p className="import-fineprint" data-testid={id('help')}>{mode==='readable'?'Drag to read across · Original question and options':'Full original region · Choose Readable to enlarge'}</p><div className="source-pan-controls" aria-label="Pan original image">{[[ArrowLeft,100,0,'left'],[ArrowRight,-100,0,'right'],[ArrowUp,0,100,'up'],[ArrowDown,0,-100,'down']].map(([Icon,x,y,label])=><Button key={label} variant="outline" size="icon" disabled={!image||(mode==='fit'&&zoom<=1)} aria-label={'Pan '+label} onClick={()=>move(x,y)} data-testid={inline?id('pan-'+label):'source-pan-'+label}><Icon size={17}/></Button>)}</div></div>
 </div>;
};
