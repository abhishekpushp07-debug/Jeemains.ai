import React,{useEffect,useState} from 'react';
import {Bookmark,BookmarkCheck,Loader2} from 'lucide-react';
import {api,post} from '../lib/api';
import {Button} from './ui/button';
import {useAuth} from '../lib/auth';
import {toast} from 'sonner';

export const SavePaperButton=({setId,initialSaved,onChange,compact=false})=>{
 const {user}=useAuth();const [saved,setSaved]=useState(initialSaved??false),[busy,setBusy]=useState(false),[ready,setReady]=useState(initialSaved!==undefined),[readError,setReadError]=useState(false);
 useEffect(()=>{let active=true;if(!user)return; if(initialSaved!==undefined){setSaved(initialSaved);setReady(true);return}setReadError(false);setReady(false);api(`/my/tests/saved/${setId}`).then(d=>{if(active){setSaved(d.saved);setReady(true)}}).catch(()=>{if(active)setReadError(true)});return()=>{active=false}},[user?.id,setId,initialSaved]);
 if(!user)return null;
 async function toggle(){setBusy(true);try{if(readError){const d=await api(`/my/tests/saved/${setId}`);setSaved(d.saved);setReady(true);setReadError(false);return}const next=saved?await api(`/my/tests/saved/${setId}`,{method:'DELETE'}):await post(`/my/tests/saved/${setId}`);setSaved(next.saved);onChange?.(next.saved);toast.success(next.saved?'Saved to My Tests. No timer started.':'Removed from saved papers.')}catch(e){toast.error(e.message)}finally{setBusy(false)}}
 return <Button variant="outline" size={compact?'icon':'default'} className="save-paper-button" onClick={toggle} disabled={busy||(!ready&&!readError)} title={readError?'Saved status unavailable. Click to retry.':undefined} aria-label={readError?'Retry saved status':saved?'Remove saved paper':'Save paper for later'} aria-pressed={ready?saved:undefined} data-testid={'save-paper-'+setId}>{busy?<Loader2 size={16} className="spin"/>:saved?<BookmarkCheck size={17}/>:<Bookmark size={17}/>} {!compact&&(readError?'Retry saved status':saved?'Saved':'Save for later')}</Button>;
};
