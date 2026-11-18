import React from 'react';
import {Link,useLocation} from 'react-router-dom';
import {House,ChartNoAxesColumn,ClipboardList,Compass} from 'lucide-react';

const TABS=[
 {id:'home',to:'/home',label:'Home',Icon:House,match:p=>p==='/home'||/^\/(exams|series|sets|competitions)/.test(p)},
 {id:'rank',to:'/rank',label:'Rank',Icon:ChartNoAxesColumn,match:p=>p.startsWith('/rank')},
 null,
 {id:'my-tests',to:'/profile',label:'My Tests',Icon:ClipboardList,match:p=>/^\/(profile|results|saved-drafts)/.test(p)},
 {id:'mission',to:'/mission',label:'Mission',Icon:Compass,match:p=>p.startsWith('/mission')},
];

export const RapidFireMark=({className='',testId})=><div className={'rapid-fire-mark '+className} role="img" aria-label="Rapid Fire, coming soon on the app" title="Rapid Fire · coming soon" data-testid={testId}><img src="/brand/rapid-fire.png" alt="" width="177" height="300" decoding="async"/><span>Rapid Fire</span></div>;

export const BottomTabs=()=>{
 const {pathname}=useLocation();
 return <nav className="bottom-tabs" aria-label="Main" data-testid="bottom-tabs">{TABS.map(t=>{
  if(!t)return <RapidFireMark key="rapid" className="bottom-tab bottom-tab-rapid" testId="bottom-tab-rapid-fire"/>;
  const on=t.match(pathname);
  return <Link key={t.id} to={t.to} className={'bottom-tab'+(on?' is-active':'')} aria-current={on?'page':undefined} data-testid={'bottom-tab-'+t.id}><t.Icon size={23} strokeWidth={on?2.3:1.7}/><span>{t.label}</span></Link>;
 })}</nav>;
};
