import React from 'react';
import {Link,NavLink} from 'react-router-dom';
import {ArrowUpRight,Atom,Orbit,GraduationCap} from 'lucide-react';
import {Card} from '../ui/card';
import {Breadcrumb,BreadcrumbList,BreadcrumbItem,BreadcrumbLink,BreadcrumbPage,BreadcrumbSeparator} from '../ui/breadcrumb';
import {EXAMS} from '../../lib/exams';

export const ExamBreadcrumbs=({exam,section,subject})=>{
 const items=[{label:'Home',to:'/home'},...(exam?[{label:exam.name,to:'/exams/'+exam.slug}]:[]),...(section?[{label:section.label,to:section.to}]:[]),...(subject?[{label:subject}]:[])];
 return <Breadcrumb className="exam-breadcrumbs" data-testid="app-breadcrumb"><BreadcrumbList>{items.map((item,i)=><React.Fragment key={i}>{i>0&&<BreadcrumbSeparator/>}<BreadcrumbItem>{i===items.length-1?<BreadcrumbPage data-testid={'breadcrumb-current-'+i}>{item.label}</BreadcrumbPage>:<BreadcrumbLink asChild><Link to={item.to} data-testid={'breadcrumb-link-'+i}>{item.label}</Link></BreadcrumbLink>}</BreadcrumbItem></React.Fragment>)}</BreadcrumbList></Breadcrumb>;
};

export const NavigationCard=({to,title,description,eyebrow,Icon=ArrowUpRight,testId,children,index})=><Link to={to} className="exam-choice-link" data-testid={testId}><Card className="exam-choice-card"><div className="exam-choice-top"><span className="exam-choice-icon"><Icon size={28} strokeWidth={1.5}/></span><span className="exam-choice-index" aria-hidden="true">{index}</span></div>{eyebrow&&<span className="exam-choice-eyebrow" data-testid={testId+'-eyebrow'}>{eyebrow}</span>}<h2 data-testid={testId+'-title'}>{title}</h2><p data-testid={testId+'-description'}>{description}</p>{children}<span className="exam-choice-cta" data-testid={testId+'-action'}>Explore <ArrowUpRight size={19}/></span></Card></Link>;

export const ExamHomeCards=()=>{
 const icons=[Atom,Orbit,GraduationCap];
 return <div className="bold-exam-grid" data-testid="exam-home-exam-card-grid">{EXAMS.map((exam,i)=>{const Icon=icons[i];return <article className={'bold-exam-card exam-tone-'+exam.slug} key={exam.slug} data-testid={'exam-home-exam-card-'+exam.slug}><div className="bold-exam-top"><Icon size={36} strokeWidth={1.4}/><span>0{i+1} / CHOOSE EXAM</span></div><div><small>{exam.eyebrow}</small><h2><Link to={'/exams/'+exam.slug+'/mocks'} data-testid={'exam-home-title-link-'+exam.slug}>{exam.name}</Link></h2><p>{exam.subjects.join(' · ')}</p></div><Link className="exam-primary" to={'/exams/'+exam.slug+'/mocks'} data-testid={'exam-direct-mocks-'+exam.slug}>Explore mock tests<ArrowUpRight size={20}/></Link><nav aria-label={exam.name+' shortcuts'}><Link to={'/exams/'+exam.slug+'/chapters'} data-testid={'exam-direct-chapters-'+exam.slug}>Chapter practice</Link><Link to={'/exams/'+exam.slug+'/results'} data-testid={'exam-direct-results-'+exam.slug}>My results<ArrowUpRight size={14}/></Link></nav></article>})}</div>;
};


export const ExamDestinations=({exam})=><nav className="exam-destinations" aria-label={`${exam.name} practice navigation`} data-testid="exam-destinations">{[['mocks','Mock tests'],['chapters','Chapter tests'],['results','My results']].map(([path,label])=><NavLink to={`/exams/${exam.slug}/${path}`} key={path} data-testid={'exam-destination-'+path}>{label}</NavLink>)}</nav>;
