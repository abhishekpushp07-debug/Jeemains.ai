import React, { useEffect, useRef } from 'react';
import { Atom, FlaskConical, Calculator, BookOpen, Brain, Check, X, Minus, Flag } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/tabs';

export const matchesOutcome = (q, filter) => filter === 'all' || (filter === 'marked' ? q.marked : filter === 'bonus-section' ? q.bonus : q.outcome === filter);
export const subjectSlug = subject => subject.toLowerCase().replace(/[^a-z0-9]+/g, '-');
const subjectIcons = { Physics: Atom, Chemistry: FlaskConical, Mathematics: Calculator, 'Logical Reasoning': Brain, English: BookOpen };

export const SolutionNavigator = ({ subjects, subject, questions, allQuestions, filter, selected, onSubject, onQuestion }) => {
  const rail = useRef(null);
  useEffect(() => {
    const row = rail.current, button = row?.querySelector('[aria-current="true"]');
    if (button) row.scrollTo({ left: button.offsetLeft - row.offsetLeft - row.clientWidth / 2 + button.offsetWidth / 2, behavior: 'instant' });
  }, [subject, selected]);
  return <div className="solution-navigator" data-testid="solution-question-navigation">
    <div className="solution-nav-heading"><span data-testid="solution-navigation-label">CHOOSE A SUBJECT</span><span data-testid="solution-navigation-count">{questions.length} {questions.length === 1 ? 'question' : 'questions'}{filter !== 'all' ? ' in this filter' : ''}</span></div>
    <Tabs value={subject} onValueChange={onSubject} className="solution-subject-tabs">
      <TabsList aria-label="Solution subjects" data-testid="solution-subject-tabs">{subjects.map(name => {
        const Icon = subjectIcons[name] || BookOpen;
        const count = allQuestions.filter(q => q.subject === name && matchesOutcome(q, filter)).length;
        return <TabsTrigger value={name} key={name} className={'subject-tone-' + subjectSlug(name)} data-testid={'solution-subject-' + subjectSlug(name)}><Icon size={16}/>{name}<span className="subject-tab-count" data-testid={'solution-subject-count-' + subjectSlug(name)}>{count}</span></TabsTrigger>;
      })}</TabsList>
      <TabsContent value={subject} className="solution-number-panel" data-testid="solution-subject-question-panel">
        <div className="solution-rail-label"><strong data-testid="solution-active-subject">{subject}</strong><span data-testid="solution-swipe-hint">Choose a number · scroll sideways for more</span></div>
        <nav ref={rail} className="solution-question-rail" aria-label={subject + ' question numbers'} data-testid="solution-question-rail">{questions.map(q => {
          const Status = q.marked ? Flag : q.outcome === 'correct' ? Check : q.outcome === 'incorrect' ? X : Minus;
          return <button type="button" key={q.id} className={'solution-number outcome-' + q.outcome} aria-current={selected === q.id ? 'true' : undefined} aria-label={`Question ${q.number}, ${q.subject}, ${q.outcome}${q.marked ? ', marked for review' : ''}`} title={`Q${q.number} · ${q.outcome}${q.marked ? ' · Marked' : ''}`} data-testid={'solution-question-' + q.number} onClick={() => onQuestion(q.id)}><span>{q.number}</span><Status size={11} aria-hidden="true"/></button>;
        })}</nav>
        {!questions.length && <p className="solution-no-numbers" data-testid="solution-empty-subject">No questions match this filter in {subject}.</p>}
      </TabsContent>
    </Tabs>
    <div className="solution-legend" data-testid="solution-navigation-legend"><span><Check size={12}/>Correct</span><span><X size={12}/>Incorrect</span><span><Minus size={12}/>Skipped / other</span><span><Flag size={12}/>Marked</span></div>
  </div>;
};
