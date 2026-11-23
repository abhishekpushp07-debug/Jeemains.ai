import {useEffect,useState} from 'react';
import {api} from '../../../lib/api';
import {SERIES_PATH} from '../../LiveSeriesBanner';

let memo=null;

// One request for the whole series picture; reused for a minute so the list and a day's page share it.
export function useInsights(uid){
  const fresh=memo&&memo.uid===uid&&Date.now()-memo.at<60000;
  const [state,setState]=useState(()=>fresh?{data:memo.data,error:''}:{data:null,error:''});
  const [tick,setTick]=useState(0);
  useEffect(()=>{
    if(!uid)return undefined;
    if(!tick&&memo&&memo.uid===uid&&Date.now()-memo.at<60000){setState({data:memo.data,error:''});return undefined;}
    const c=new AbortController();
    api(SERIES_PATH+'/insights',{signal:c.signal})
      .then(data=>{memo={uid,at:Date.now(),data};setState({data,error:''});})
      .catch(e=>{if(!c.signal.aborted)setState(s=>({...s,error:e.message}));});
    return()=>c.abort();
  },[uid,tick]);
  return {...state,retry:()=>setTick(v=>v+1)};
}
