import React,{useState} from 'react';
import {Link,NavLink} from 'react-router-dom';
import {ArrowUpRight,Atom,Orbit,GraduationCap,Pause,Play,Sparkles,BookMarked,EyeOff} from 'lucide-react';
import {Card} from '../ui/card';
import {Breadcrumb,BreadcrumbList,BreadcrumbItem,BreadcrumbLink,BreadcrumbPage,BreadcrumbSeparator} from '../ui/breadcrumb';
import {EXAMS} from '../../lib/exams';
import {useExamList,useExamStructure} from '../../lib/catalog';

export const ExamBreadcrumbs=({exam,section,subject})=>{
 const items=[{label:'Home',to:'/home'},...(exam?[{label:exam.name,to:'/exams/'+exam.slug}]:[]),...(section?[{label:section.label,to:section.to}]:[]),...(subject?[{label:subject}]:[])];
 return <Breadcrumb className="exam-breadcrumbs" data-testid="app-breadcrumb"><BreadcrumbList>{items.map((item,i)=><React.Fragment key={i}>{i>0&&<BreadcrumbSeparator/>}<BreadcrumbItem>{i===items.length-1?<BreadcrumbPage data-testid={'breadcrumb-current-'+i}>{item.label}</BreadcrumbPage>:<BreadcrumbLink asChild><Link to={item.to} data-testid={'breadcrumb-link-'+i}>{item.label}</Link></BreadcrumbLink>}</BreadcrumbItem></React.Fragment>)}</BreadcrumbList></Breadcrumb>;
};

export const NavigationCard=({to,title,description,eyebrow,Icon=ArrowUpRight,testId,children,index})=><Link to={to} className="exam-choice-link" data-nav-tone={index === '02' ? 'green' : index === '03' ? 'red' : 'blue'} data-testid={testId}><Card className="exam-choice-card"><div className="exam-choice-top"><span className="exam-choice-icon"><Icon size={28} strokeWidth={1.5}/></span><span className="exam-choice-index" aria-hidden="true">{index}</span></div>{eyebrow&&<span className="exam-choice-eyebrow" data-testid={testId+'-eyebrow'}>{eyebrow}</span>}<h2 data-testid={testId+'-title'}>{title}</h2><p data-testid={testId+'-description'}>{description}</p>{children}<span className="exam-choice-cta" data-testid={testId+'-action'}>Explore <ArrowUpRight size={19}/></span></Card></Link>;

export const OwnerHiddenNote=({exam})=><p className="owner-preview-note" data-testid="exam-hidden-owner-note"><EyeOff size={16}/>{exam.name} is hidden from students. You are seeing the student view as the owner. Choose Show on Home in Super Admin when it is ready.</p>;

const CustomExamCard=({exam,index})=><article className={'bold-exam-card home-card-surface exam-tone-custom exam-color-'+exam.color} data-testid={'exam-home-exam-card-'+exam.slug}><Link className="home-card-whole-link" to={'/exams/'+exam.slug} aria-label={'Open '+exam.name+' main page'} data-testid={'exam-home-whole-card-'+exam.slug}/><div className="bold-exam-top"><BookMarked size={36} strokeWidth={1.4}/><span>{String(index).padStart(2,'0')} / CHOOSE EXAM</span></div><div><small data-testid={'exam-home-eyebrow-'+exam.slug}>{exam.shown?`YOUR ${exam.short.toUpperCase()} PATHWAY`:'HIDDEN FROM STUDENTS · OWNER PREVIEW'}</small><h2 data-testid={'exam-home-title-link-'+exam.slug}>{exam.name}</h2><p>{exam.subjects.join(' · ')}</p></div><Link className="exam-primary" to={'/exams/'+exam.slug} data-testid={'exam-direct-open-'+exam.slug}>Explore tests<ArrowUpRight size={20}/></Link><nav aria-label={exam.name+' shortcuts'}><Link to={'/exams/'+exam.slug+'/results'} data-testid={'exam-direct-results-'+exam.slug}>My results<ArrowUpRight size={14}/></Link></nav></article>;

export const ExamHomeCards=()=>{
 const [shine,setShine]=useState(true);
 const custom=(useExamList()||[]).filter(e=>!e.builtin);
 const icons=[Atom,Orbit,GraduationCap];
 return <div className="exam-cards-wrap"><div className="exam-card-finish-control"><span data-testid="exam-card-finish-label"><Sparkles size={14}/>YOUR EXAM. YOUR COLOUR.</span><button type="button" className="exam-shine-toggle" data-testid="exam-shine-toggle" aria-pressed={!shine} aria-label={shine?'Pause card shine':'Play card shine'} onClick={()=>setShine(v=>!v)}>{shine?<Pause size={13}/>:<Play size={13}/>} {shine?'Pause shine':'Play shine'}</button></div><div className={'bold-exam-grid '+(!shine?'shine-paused':'')} data-testid="exam-home-exam-card-grid">{EXAMS.map((exam,i)=>{const Icon=icons[i];return <article className={'bold-exam-card home-card-surface exam-tone-'+exam.slug} key={exam.slug} data-testid={'exam-home-exam-card-'+exam.slug}><Link className="home-card-whole-link" to={'/exams/'+exam.slug} aria-label={'Open '+exam.name+' main page'} data-testid={'exam-home-whole-card-'+exam.slug}/><div className="bold-exam-top"><Icon size={36} strokeWidth={1.4}/><span>0{i+1} / CHOOSE EXAM</span></div><div><small>{exam.eyebrow}</small><h2 data-testid={'exam-home-title-link-'+exam.slug}>{exam.name}</h2><p>{exam.subjects.join(' · ')}</p></div><Link className="exam-primary" to={'/exams/'+exam.slug+(exam.slug==='jee-main'?'/pyq':'/mocks')} data-testid={'exam-direct-mocks-'+exam.slug}>{exam.slug==='jee-main'?'Explore PYQ papers':'Explore mock tests'}<ArrowUpRight size={20}/></Link><nav aria-label={exam.name+' shortcuts'}><Link to={'/exams/'+exam.slug+'/chapters'} data-testid={'exam-direct-chapters-'+exam.slug}>Chapter practice</Link><Link to={'/exams/'+exam.slug+'/results'} data-testid={'exam-direct-results-'+exam.slug}>My results<ArrowUpRight size={14}/></Link></nav></article>})}{custom.map((exam,i)=><CustomExamCard key={exam.slug} exam={exam} index={EXAMS.length+i+1}/>)}</div></div>;
};

const FALLBACK={'jee-main':[['pyq','PYQ papers'],['chapters','Chapter tests']],default:[['mocks','Mock tests'],['chapters','Chapter tests']]};
export const ExamDestinations=({exam})=>{
 const {data}=useExamStructure(exam.slug);
 const items=data?data.sections.map(s=>[s.slug,s.name]):exam.custom?[]:(FALLBACK[exam.slug]||FALLBACK.default);
 return <nav className="exam-destinations" aria-label={`${exam.name} practice navigation`} data-testid="exam-destinations">{[...items,['results','My results']].map(([path,label])=><NavLink to={`/exams/${exam.slug}/${path}`} key={path} data-testid={'exam-destination-'+path}>{label}</NavLink>)}</nav>;
};
