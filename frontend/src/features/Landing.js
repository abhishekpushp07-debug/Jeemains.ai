import React from 'react';
import {Link} from 'react-router-dom';
import {ArrowUpRight,ArrowRight,Check,GraduationCap,BookOpen,ClipboardList,ChartNoAxesCombined,Download,Target} from 'lucide-react';
import {useAuth} from '../lib/auth';
import {Button} from '../components/ui/button';
import {Card} from '../components/ui/card';
import {LiveSeriesBanner} from '../components/LiveSeriesBanner';
import {ExamHomeCards} from '../components/exams/ExamNavigation';
import {Accordion,AccordionItem,AccordionTrigger,AccordionContent} from '../components/ui/accordion';

const faqs=[
 ['Is it really 100% free?','Yes. Student access to published practice tests, results and saved solutions is free. No subscription or payment details are required.'],
 ['Do you predict my real-exam rank?','Only an approved, compatible historical dataset can support a range. If evidence is unavailable, we say so. Platform rank, admission cutoffs and national rank are different measures.'],
 ['Are AI solutions available?','Where the owner has explicitly generated and saved an AI explanation, it is labelled AI generated. Owner-provided solutions are kept separately. Student activity never starts AI generation.'],
 ['How do I get started?','Enter your mobile number, choose JEE Main, BITSAT or COMEDK, then open Mock Tests, Chapter-wise Tests or Results. Only published content appears; some exam sections may not have live papers yet.'],
 ['How is my practice saved?','No OTP or password is required. Anyone entering the same number can reopen that profile. Pending answers stay on your device during a disconnect; only server-acknowledged answers before the deadline count.'],
];

export default function Landing(){
 const {user}=useAuth();const entry=user?'/home':'/login';
 return <div className="free-landing" data-testid="free-landing-page">
  <div className="container flagship-home"><LiveSeriesBanner/></div>
  <section className="container direct-home-hero" data-testid="poster-free"><span className="free-label" data-testid="landing-free-label"><GraduationCap size={17}/>100% FREE FOR ALL STUDENTS</span><h1 data-testid="landing-hero-heading">Your exam.<br/><span>Your next big step.</span></h1><p data-testid="landing-hero-description">Go straight to your practice. Full mocks, chapter tests and clear results—one colourful, focused space.</p><ExamHomeCards/></section>
  <section className="free-feature-ribbon" aria-label="Practice features"><div className="container">{[[ClipboardList,'Full mock tests'],[BookOpen,'Chapter-wise practice'],[ChartNoAxesCombined,'Results & answer review'],[Target,'Personal progress']].map(([Icon,label],i)=><span key={label} data-testid={'landing-feature-'+i}><Icon size={19}/>{label}</span>)}</div></section>
  <section className="container free-process-section" id="how-it-works" data-testid="poster-how-it-works"><header className="free-section-heading"><div><span className="eyebrow">LESS NAVIGATION. MORE LEARNING.</span><h2 data-testid="landing-process-title">Pick. Practise. Understand.</h2></div></header><div className="free-process-grid">{[['01','Choose your exam','JEE Main, BITSAT or COMEDK. Your own focused space.'],['02','Find your practice','Live full mocks or subject-wise chapter tests. Check the rules and begin.'],['03','Learn from your attempt','Submit, see your marks and review every question with the available answers and solutions.']].map(([n,title,description])=><article key={n} data-testid={'landing-process-'+n}><span>{n}</span><h3>{title}</h3><p>{description}</p></article>)}</div></section>
  <section className="container free-faq-section"><div><span className="eyebrow">STRAIGHT ANSWERS</span><h2 data-testid="landing-faq-title">Before you begin.</h2></div><Accordion type="single" collapsible className="free-faq-list">{faqs.map(([question,answer],i)=><AccordionItem key={question} value={'faq-'+i}><AccordionTrigger data-testid={'faq-'+i}>{question}</AccordionTrigger><AccordionContent data-testid={'faq-answer-'+i}>{answer}</AccordionContent></AccordionItem>)}</Accordion></section>
  <section className="container free-final-section"><Card className="free-final-card"><div><span className="free-label" data-testid="landing-final-free">100% FREE. FOR ALL STUDENTS.</span><h2 data-testid="landing-final-title">Your effort is the only investment.</h2></div><Button asChild className="btn btn-primary btn-large"><Link to={entry} data-testid="landing-final-cta">Let's get started<ArrowUpRight size={19}/></Link></Button></Card></section>
 </div>;
}
