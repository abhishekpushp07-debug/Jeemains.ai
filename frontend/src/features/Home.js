import React from 'react';
import {Link} from 'react-router-dom';
import {Button} from '../components/ui/button';
import {Bookmark,ArrowUpRight} from 'lucide-react';
import {LiveSeriesBanner} from '../components/LiveSeriesBanner';
import {ExamHomeCards} from '../components/exams/ExamNavigation';
export default function Home(){
 return <div className="container page exam-home polished-home" data-testid="exam-home-page"><LiveSeriesBanner/><header className="exam-simple-heading"><span className="eyebrow" data-testid="exam-home-eyebrow">YOUR AMBITION. YOUR NEXT STEP.</span><h1 data-testid="exam-home-title">Choose your exam.</h1><p data-testid="exam-home-description">PYQs, mock tests, chapter-wise practice and your results. All in one place.</p><div className="home-quick-actions"><Button asChild variant="outline"><Link to="/profile" data-testid="home-my-tests"><Bookmark size={17}/>My Tests<ArrowUpRight size={16}/></Link></Button><span className="free-label" data-testid="exam-home-free">100% free for all students</span></div></header><ExamHomeCards/></div>;
}
