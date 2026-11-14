import React,{useEffect,useState} from 'react';
import {Navigate,useParams} from 'react-router-dom';
import {api} from '../lib/api';
import {Loading} from '../components/Shared';

// Old book-series links open the exam section where those mocks now live.
export default function BookSeries(){
 const {id}=useParams();const [target,setTarget]=useState(id?'':'/home');
 useEffect(()=>{if(!id)return;const c=new AbortController();api('/book-series/'+id,{signal:c.signal}).then(d=>setTarget(d.path||'/home')).catch(e=>{if(e.name!=='AbortError')setTarget('/home');});return()=>c.abort();},[id]);
 return target?<Navigate to={target} replace/>:<Loading text="Opening the section…"/>;
}
