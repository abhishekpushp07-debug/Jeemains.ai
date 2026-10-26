import React, { useEffect, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { ArrowRight, ArrowUpRight, CalendarDays, Clock3, FileCheck2, RotateCcw } from 'lucide-react';
import { api } from '../lib/api';
import { Button } from '../components/ui/button';
import { Loading, ErrorBox, Empty } from '../components/Shared';
import { ExamBreadcrumbs, ExamDestinations } from '../components/exams/ExamNavigation';
import { examBySlug } from '../lib/exams';

const dateLabel = date => new Date(date + 'T12:00:00Z').toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

const PaperCard = ({ paper, tone }) => {
  const location = useLocation();
  const state = { returnTo: location.pathname + location.search };
  const active = paper.attempt?.status === 'active';
  const done = paper.attempt?.status === 'completed';
  return <article className={'card pyq-paper-card pyq-tone-' + tone} data-state={active ? 'active' : done ? 'completed' : 'new'} data-testid={'pyq-paper-' + paper.id}>
    <div className="pyq-paper-heading"><span className="badge pyq-shift-badge" data-testid={'pyq-shift-' + paper.id}>Shift {paper.shift}</span><span className="badge pyq-status-badge" data-testid={'pyq-status-' + paper.id}>{active ? 'In progress' : done ? 'Completed' : 'Not attempted'}</span></div>
    <div className="pyq-paper-body"><div className="pyq-paper-summary">
    <h2 data-testid={'pyq-paper-title-' + paper.id}><CalendarDays size={19} aria-hidden="true"/>{dateLabel(paper.exam_date)}</h2>
    <p className="pyq-paper-meta" data-testid={'pyq-paper-meta-' + paper.id}><span><FileCheck2 size={16}/>{paper.count} questions</span><span><Clock3 size={16}/>{paper.minutes} min</span><span>{paper.maximum} marks</span></p>
    <p data-testid={'pyq-paper-rules-' + paper.id}>Physics · Chemistry · Mathematics<br/>+4 correct · −1 incorrect · Source-matched answers & solutions</p>
    {paper.attempt_count > 0 && <p data-testid={'pyq-attempt-count-' + paper.id}>{paper.attempt_count} full-paper attempt{paper.attempt_count === 1 ? '' : 's'} · Previous results stay available</p>}
    </div><div className="pyq-paper-actions">
      {paper.latest_result_id && <Button asChild variant="outline"><Link to={'/results/' + paper.latest_result_id} state={state} data-testid={'pyq-result-' + paper.id}>View Result<ArrowUpRight size={16}/></Link></Button>}
      <Button asChild className="btn btn-primary"><Link to={active ? '/attempts/' + paper.attempt.id : '/sets/' + paper.id} state={state} data-testid={'pyq-start-' + paper.id}>{active ? 'Resume Test' : done ? 'Attempt Again' : 'Start Test'}{done && !active ? <RotateCcw size={16}/> : <ArrowRight size={16}/>}</Link></Button>
    </div></div>
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
  useEffect(() => {
    if (params.has('date')) {
      const next = new URLSearchParams(params);
      next.delete('date');
      setParams(next, { replace: true });
    }
  }, [params, setParams]);
  function chooseYear(value) { setParams({ year: String(value) }); }
  return <div className="container page pyq-page" data-testid="pyq-page">
    <ExamBreadcrumbs exam={examBySlug('jee-main')} section={{label:'PYQ papers'}}/><ExamDestinations exam={examBySlug('jee-main')}/>
    <header className="page-title"><div><span className="eyebrow" data-testid="pyq-eyebrow">JEE MAIN · PREVIOUS YEAR PAPERS</span><h1 data-testid="pyq-title">Real papers. Your next attempt.</h1><p data-testid="pyq-description">Choose a year. Every paper is listed below—pick a date and shift to begin.</p></div>{data && <span className="badge" data-testid="pyq-total">{data.total} papers available</span>}</header>
    <ErrorBox error={error} retry={() => setReload(x => x + 1)}/>
    {!data && !error && <Loading/>}
    {data?.total === 0 && <Empty title="PYQ papers are being verified">Only papers with checked dates, answer keys and solution mapping appear here.</Empty>}
    {data?.total > 0 && <>
      <div className="pyq-filter-bar"><div className="pyq-years" role="group" aria-label="Filter papers by year" data-testid="pyq-year-tabs">{data.years.map(value => <Button key={value} aria-pressed={value === year} aria-controls="pyq-year-paper-list" variant={value === year ? 'default' : 'outline'} onClick={() => chooseYear(value)} data-testid={'pyq-year-' + value}>{value}</Button>)}</div><p className="pyq-year-count" aria-live="polite" data-testid="pyq-year-count">{papers.length} paper{papers.length === 1 ? '' : 's'} <span aria-hidden="true">·</span> {year}</p></div>
      <section id="pyq-year-paper-list" className="pyq-paper-list" aria-label={'All ' + year + ' papers'} data-testid="pyq-paper-list">{papers.map((p, index) => <PaperCard key={p.id} paper={p} tone={index % 4}/>)}</section>
      <p className="import-fineprint" data-testid="pyq-source-note">{data.source_note} Attempt Again starts a new full paper; it does not replace your previous results.</p>
    </>}
  </div>;
}
