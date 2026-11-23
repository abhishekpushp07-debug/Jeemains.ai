import {useEffect} from 'react';

// Each Super Admin screen names its own browser tab; the old title comes back when the screen closes.
export function usePageTitle(title){
 useEffect(()=>{
  if(!title)return undefined;
  const before=document.title;
  document.title=`${title} · Super Admin · JEELIVE.AI`;
  return()=>{document.title=before;};
 },[title]);
}

// Admin and sign-in screens ask search engines not to list them.
export function useNoIndex(on=true){
 useEffect(()=>{
  if(!on)return undefined;
  const tag=document.createElement('meta');
  tag.name='robots';tag.content='noindex, nofollow';tag.setAttribute('data-testid','robots-noindex');
  document.head.appendChild(tag);
  return()=>tag.remove();
 },[on]);
}
