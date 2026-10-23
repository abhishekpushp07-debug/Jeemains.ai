import React,{createContext,useCallback,useContext,useEffect,useMemo,useRef,useState} from 'react';
import {api,post} from './api';
import {profileDrafts,discardProfileDraft} from './drafts';
import {AlertDialog,AlertDialogContent,AlertDialogHeader,AlertDialogTitle,AlertDialogDescription,AlertDialogFooter} from '../components/ui/alert-dialog';
import {Button} from '../components/ui/button';
const AuthContext=createContext();
export function AuthProvider({children}){
 const [user,commitUser]=useState(null); const [checking,setChecking]=useState(true);
 const [signoutDrafts,setSignoutDrafts]=useState(null); const decision=useRef(null);
 const generation=useRef(0),mounted=useRef(true),bootstrap=useRef(null);
 const setUser=useCallback(next=>{generation.current+=1;bootstrap.current?.abort();commitUser(next);setChecking(false);},[]);
 useEffect(()=>{mounted.current=true;const controller=new AbortController();bootstrap.current=controller;const epoch=generation.current;
  api('/auth/session',{signal:controller.signal}).then(data=>{if(mounted.current&&epoch===generation.current){commitUser(data.user);setChecking(false);}}).catch(()=>{if(mounted.current&&!controller.signal.aborted&&epoch===generation.current){commitUser(null);setChecking(false);}});
  return()=>{mounted.current=false;controller.abort();};
 },[]);
 const choose=choice=>{const resolve=decision.current;decision.current=null;setSignoutDrafts(null);resolve?.(choice);};
 const logout=useCallback(async()=>{
  if(decision.current)return false;
  const drafts=profileDrafts(user?.id);let choice='keep';
  if(drafts.length)choice=await new Promise(resolve=>{decision.current=resolve;setSignoutDrafts(drafts);});
  if(choice==='cancel')return false;
  generation.current+=1;bootstrap.current?.abort();await post('/auth/logout');
  if(choice==='discard')profileDrafts(user?.id).forEach(discardProfileDraft);
  if(mounted.current){commitUser(null);setChecking(false);}return true;
 },[user?.id]);
 const value=useMemo(()=>({user,setUser,checking,logout}),[user,setUser,checking,logout]);
 return <AuthContext.Provider value={value}>{children}
  <AlertDialog open={!!signoutDrafts} onOpenChange={open=>!open&&choose('cancel')}><AlertDialogContent data-testid="signout-draft-dialog"><AlertDialogHeader><AlertDialogTitle>Unsynced answers found</AlertDialogTitle><AlertDialogDescription data-testid="signout-draft-warning">{signoutDrafts?.length} attempt draft(s) for this profile are saved on this device but not acknowledged. Keeping them allows recovery after signing in with the same number. A deadline still applies; late drafts cannot change a sealed score. On a shared device, discard only if you are sure.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter className="signout-draft-actions"><Button variant="outline" data-testid="signout-draft-cancel-button" onClick={()=>choose('cancel')}>Stay signed in</Button><Button className="btn btn-primary" data-testid="signout-draft-keep-button" onClick={()=>choose('keep')}>Keep drafts & sign out</Button><Button variant="ghost" data-testid="signout-draft-discard-button" onClick={()=>choose('discard')}>Discard my drafts & sign out</Button></AlertDialogFooter></AlertDialogContent></AlertDialog>
 </AuthContext.Provider>;
}
export const useAuth=()=>useContext(AuthContext);
