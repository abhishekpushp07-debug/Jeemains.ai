import React,{useState} from 'react';
import {useLocation,useNavigate} from 'react-router-dom';
import {Eye,Loader2} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Button} from '../ui/button';
import {plural} from './MasterShared';
import {toast} from 'sonner';

const wait=ms=>new Promise(done=>setTimeout(done,ms));

// Opens a Draft exactly as students see it. An uploaded Draft is first copied privately; written Drafts open directly.
export function TryAsStudent({m,size='sm'}){
 const nav=useNavigate(),loc=useLocation();const [busy,setBusy]=useState(false);
 const go=id=>nav('/sets/'+id+'?preview=true',{state:{previewBack:loc.pathname}});
 async function open(){
  if(m.kind!=='book_mock')return go(m.id);
  setBusy(true);
  try{
   let r=await post('/admin/master/preview/'+m.id);
   for(let i=0;r.state==='building'&&i<80;i++){await wait(1500);r=await api('/admin/master/preview/'+m.id);}
   if(r.state!=='ready')throw new Error(r.message||'Still preparing. Try again in a minute.');
   if(r.left_out?.length)toast.message(`${plural(r.left_out.length,'question')} left out until fixed`,{description:'Questions marked to fix are not in this try. Everything else is exactly what students get.'});
   go(r.set_id);
  }catch(e){toast.error(e.message);}finally{setBusy(false);}
 }
 return <Button size={size} variant="outline" disabled={busy} onClick={open} data-testid={'mock-try-'+m.id}>{busy?<Loader2 size={15} className="spin"/>:<Eye size={15}/>}{busy?'Preparing…':'Try as student'}</Button>;
}
