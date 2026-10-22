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
 return <div className="exam-choice-grid" data-testid="exam-home-exam-card-grid">{EXAMS.map((exam,i)=><NavigationCard key={exam.slug} to={'/exams/'+exam.slug} title={exam.name} eyebrow={exam.eyebrow} description={exam.description} Icon={icons[i]} index={'0'+(i+1)} testId={'exam-home-exam-card-'+exam.slug}><div className="exam-choice-subjects" data-testid={'exam-home-subjects-'+exam.slug}>{exam.subjects.slice(0,3).join(' · ')}</div></NavigationCard>)}</div>;
};


export const ExamDestinations=({exam})=><nav className="exam-destinations" aria-label={`${exam.name} practice navigation`} data-testid="exam-destinations">{[['mocks','Mock tests'],['chapters','Chapter tests'],['results','My results']].map(([path,label])=><NavLink to={`/exams/${exam.slug}/${path}`} key={path} data-testid={'exam-destination-'+path}>{label}</NavLink>)}</nav>;
