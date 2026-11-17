import {useEffect,useState} from 'react';
import {api} from './api';
import {useAuth} from './auth';
import {registerExams} from './exams';

const cache=new Map();
function cached(key,load){
 const hit=cache.get(key);
 if(hit&&Date.now()-hit.at<30000)return hit.promise;
 const promise=load().catch(e=>{cache.delete(key);throw e;});
 cache.set(key,{at:Date.now(),promise});
 return promise;
}
export const invalidateCatalog=()=>cache.clear();

export function useExamList(){
 const {user}=useAuth();const [items,setItems]=useState(null);const who=user?.id||'guest';
 useEffect(()=>{let live=true;if(who==='guest'){setItems([]);return;}cached(who+':exams',()=>api('/catalog/exams')).then(d=>{registerExams(d.items);if(live)setItems(d.items);}).catch(()=>{if(live)setItems([]);});return()=>{live=false;};},[who]);
 return items;
}

export function useExamStructure(slug){
 const {user}=useAuth();const who=user?.id||'guest';const [state,setState]=useState({slug:'',data:null,error:''});
 useEffect(()=>{if(!slug)return;let live=true;cached(who+':exam:'+slug,()=>api('/catalog/exams/'+slug)).then(d=>{registerExams([d]);if(live)setState({slug,data:d,error:''});}).catch(e=>{if(live)setState({slug,data:null,error:e.message});});return()=>{live=false;};},[slug,who]);
 return state.slug===slug?state:{slug,data:null,error:''};
}
