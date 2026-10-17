import React from 'react';
import {ExamHomeCards} from '../components/exams/ExamNavigation';
export default function Home(){
 return <div className="container page exam-home" data-testid="exam-home-page"><header className="exam-simple-heading"><span className="eyebrow" data-testid="exam-home-eyebrow">YOUR AMBITION. YOUR NEXT STEP.</span><h1 data-testid="exam-home-title">Choose your exam.</h1><p data-testid="exam-home-description">Mock tests, chapter-wise practice and your results. All in one place.</p><span className="free-label" data-testid="exam-home-free">100% free for all students</span></header><ExamHomeCards/></div>;
}
