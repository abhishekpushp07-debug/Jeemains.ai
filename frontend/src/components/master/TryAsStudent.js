import React,{useState} from 'react';
import {useLocation,useNavigate} from 'react-router-dom';
import {Eye,Loader2} from 'lucide-react';
import {api,post} from '../../lib/api';
import {Button} from '../ui/button';
import {toast} from 'sonner';

const wait=ms=>new Promise(done=>setTimeout(done,ms));

// Opens a Draft exactly as students see it, in a new tab. An uploaded Draft is first copied privately; written Drafts open directly.
export function TryAsStudent({m,size='sm'}){
 const nav=useNavigate(),loc=useLocation();const [busy,setBusy]=useState(false);
 const url=id=>'/sets/'+id+'?preview=true&back='+encodeURIComponent(loc.pathname+loc.search);
 // Tab is opened on the click itself so the browser does not block it; same tab only if the browser refuses.
 const show=(tab,id)=>{if(tab&&!tab.closed){tab.location.replace(url(id));tab.focus();}else nav(url(id),{state:{previewBack:loc.pathname+loc.search}});};
 async function open(){
  const tab=window.open('','_blank');
  if(m.kind!=='book_mock')return show(tab,m.id);
  if(tab)tab.document.title='Student paper taiyaar ho raha hai…';
  setBusy(true);
  try{
   let r=await post('/admin/master/preview/'+m.id);
   for(let i=0;r.state==='building'&&i<200;i++){await wait(i<10?300:1000);r=await api('/admin/master/preview/'+m.id);}
   if(r.state!=='ready')throw new Error(r.message||'Abhi taiyaar ho raha hai. Ek minute baad phir dabaiye.');
   if(r.left_out?.length)toast.message(`${r.left_out.length} sawaal fix hone tak bahar rakhe gaye`,{description:'Fix ke liye marked sawaal is try mein nahi hain. Baaki sab bilkul waisa hai jaisa students ko milega.'});
   show(tab,r.set_id);
   if(tab&&!tab.closed)toast.success('Student paper naye tab me khul gaya',{description:'Yeh Fix page yahin khula hai.'});
  }catch(e){if(tab&&!tab.closed)tab.close();toast.error(e.message);}finally{setBusy(false);}
 }
 return <Button size={size} variant="outline" disabled={busy} onClick={open} data-testid={'mock-try-'+m.id}>{busy?<Loader2 size={15} className="spin"/>:<Eye size={15}/>}{busy?'Taiyaar ho raha hai…':'Student ki tarah try karo'}</Button>;
}
