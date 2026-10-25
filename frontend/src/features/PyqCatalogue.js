import React, { useEffect, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { ArrowRight, ArrowUpRight, CalendarDays, Clock3, FileCheck2, RotateCcw } from 'lucide-react';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Loading, ErrorBox, Empty } from '../components/Shared';
import { ExamBreadcrumbs, ExamDestinations } from '../components/exams/ExamNavigation';
import { examBySlug } from '../lib/exams';

const dateLabel = date => new Date(date + 'T12:00:00Z').toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

const PaperCard = ({ paper }) => {
  const location = useLocation();
  const state = { returnTo: location.pathname + location.search };
  const active = paper.attempt?.status === 'active';
  const done = paper.attempt?.status === 'completed';
  return <article className="card pyq-paper-card" data-testid={'pyq-paper-' + paper.id}>
    <div className="row-between"><span className="badge" data-testid={'pyq-shift-' + paper.id}>Shift {paper.shift}</span><span className={'badge ' + (active ? 'amber' : '')} data-testid={'pyq-status-' + paper.id}>{active ? 'In progress' : done ? 'Completed' : 'Not attempted'}</span></div>
    <h2 data-testid={'pyq-paper-title-' + paper.id}>{dateLabel(paper.exam_date)}</h2>
    <p className="pyq-paper-meta" data-testid={'pyq-paper-meta-' + paper.id}><span><FileCheck2 size={16}/>{paper.count} questions</span><span><Clock3 size={16}/>{paper.minutes} min</span><span>{paper.maximum} marks</span></p>
    <p data-testid={'pyq-paper-rules-' + paper.id}>Physics · Chemistry · Mathematics<br/>+4 correct · −1 incorrect · Source-matched answers & solutions</p>
    {paper.attempt_count > 0 && <p data-testid={'pyq-attempt-count-' + paper.id}>{paper.attempt_count} full-paper attempt{paper.attempt_count === 1 ? '' : 's'} · Previous results stay available</p>}
    <div className="pyq-paper-actions">
      {paper.latest_result_id && <Button asChild variant="outline"><Link to={'/results/' + paper.latest_result_id} state={state} data-testid={'pyq-result-' + paper.id}>View Result<ArrowUpRight size={16}/></Link></Button>}
      <Button asChild className="btn btn-primary"><Link to={active ? '/attempts/' + paper.attempt.id : '/sets/' + paper.id} state={state} data-testid={'pyq-start-' + paper.id}>{active ? 'Resume Test' : done ? 'Attempt Again' : 'Start Test'}{done && !active ? <RotateCcw size={16}/> : <ArrowRight size={16}/>}</Link></Button>
    </div>
  </article>;
};

export default function PyqCatalogue() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [params, setParams] = useSearchParams();
  useEffect(() => {
    const controller = new AbortController();
    setError('');
    api('/pyq/jee-main', { signal: controller.signal }).then(value => { if (!controller.signal.aborted) setData(value); }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => { controller.abort(); };
  }, [reload]);
  const year = data?.years.includes(Number(params.get('year'))) ? Number(params.get('year')) : data?.years[0];
  const papers = (data?.items || []).filter(p => p.year === year);
  const dates = [...new Set(papers.map(p => p.exam_date))];
  const date = dates.includes(params.get('date')) ? params.get('date') : dates[0];
  function chooseYear(value) { setParams({ year: String(value) }); }
  function chooseDate(value) { setParams({ year: String(year), date: value }); }
  return <div className="container page pyq-page" data-testid="pyq-page">
    <ExamBreadcrumbs exam={examBySlug('jee-main')} section={{label:'PYQ papers'}}/><ExamDestinations exam={examBySlug('jee-main')}/>
    <header className="page-title"><div><span className="eyebrow" data-testid="pyq-eyebrow">JEE MAIN · PREVIOUS YEAR PAPERS</span><h1 data-testid="pyq-title">Real papers. Your next attempt.</h1><p data-testid="pyq-description">Choose a date and shift. Practice the complete paper, then review its matched solutions.</p></div>{data && <span className="badge" data-testid="pyq-total">{data.total} papers available</span>}</header>
    <ErrorBox error={error} retry={() => setReload(x => x + 1)}/>
    {!data && !error && <Loading/>}
    {data?.total === 0 && <Empty title="PYQ papers are being verified">Only papers with checked dates, answer keys and solution mapping appear here.</Empty>}
    {data?.total > 0 && <>
      <div className="pyq-years" role="tablist" aria-label="Paper year" data-testid="pyq-year-tabs">{data.years.map(value => <Button key={value} role="tab" aria-selected={value === year} variant={value === year ? 'default' : 'outline'} onClick={() => chooseYear(value)} data-testid={'pyq-year-' + value}>{value}</Button>)}</div>
      <div className="pyq-dates" role="tablist" aria-label="Exam date" data-testid="pyq-date-tabs">{dates.map(value => <Button key={value} role="tab" aria-selected={value === date} variant={value === date ? 'default' : 'outline'} onClick={() => chooseDate(value)} data-testid={'pyq-date-' + value}><CalendarDays size={16}/>{dateLabel(value)}</Button>)}</div>
      <section className="pyq-paper-list" aria-label="Papers for selected date" data-testid="pyq-paper-list">{papers.filter(p => p.exam_date === date).map(p => <PaperCard key={p.id} paper={p}/>)}</section>
      <p className="import-fineprint" data-testid="pyq-source-note">{data.source_note} Attempt Again starts a new full paper; it does not replace your previous results.</p>
    </>}
  </div>;
}
