import React,{useEffect,useState} from 'react';
import {fetchWithSession} from '../../lib/api';

export function PrivateBookImage({path,alt,onLoad,testId}){
 const [url,setUrl]=useState(''),[error,setError]=useState('');
 useEffect(()=>{const controller=new AbortController();let objectUrl;setUrl('');setError('');
  fetchWithSession(path,{signal:controller.signal}).then(async r=>{if(!r.ok)throw new Error('Original image unavailable. Reload to retry.');const blob=await r.blob();if(!controller.signal.aborted){objectUrl=URL.createObjectURL(blob);setUrl(objectUrl);}}).catch(e=>{if(e.name!=='AbortError')setError(e.message);});
  return()=>{controller.abort();if(objectUrl)URL.revokeObjectURL(objectUrl);};
 },[path]);
 return error?<p role="alert" data-testid={`${testId}-error`}>{error}</p>:url?<img src={url} alt={alt} onLoad={onLoad} data-testid={testId}/>:<p data-testid={`${testId}-loading`}>Loading original…</p>;
}

export function BookField({label,id,children,...props}){
 return <label className="book-field" htmlFor={id}><span>{label}</span>{children||<input id={id} data-testid={id} {...props}/>}</label>;
}
export function BookError({error}){return error?<p className="book-error" role="alert" data-testid="book-operation-error">{error}</p>:null;}
export function BookStatus({state,id}){return <span className={`book-status status-${state}`} data-testid={id}>{state.replaceAll('_',' ')}</span>;}
