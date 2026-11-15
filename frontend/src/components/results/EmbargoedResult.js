import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../ui/button';
import { PageTitle } from '../Shared';
import { seriesPath, JEE_SERIES } from '../../lib/exams';

const ist = n => new Date(n * 1000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' }) + ' IST';
const slug = v => v.toLowerCase().replace(/\W+/g, '-');

function LiveScore({ s }) {
  const subjects = Object.entries(s.subjects || {});
  return <section className="import-card" data-testid="results-live-score">
    <div className="import-section-label">YOUR SCORE</div>
    <h2 className="mt-2" data-testid="results-live-score-value">{s.score} / {s.maximum}</h2>
    <p className="import-muted" data-testid="results-live-score-counts">{s.correct} correct · {s.incorrect} wrong · {s.skipped} skipped{s.accuracy != null ? ` · ${s.accuracy}% accuracy` : ''}</p>
    {subjects.length > 1 && <ul className="flex flex-wrap gap-3 mt-4" data-testid="results-live-subjects">{subjects.map(([name, g]) => <li key={name} className="import-status" data-testid={'results-live-subject-' + slug(name)}>{name}: {g.score}</li>)}</ul>}
  </section>;
}

export function EmbargoedResult({ pending, onRefresh }) {
  const open = pending.score_released, score = pending.summary;
  return <div className="container page" data-testid="results-embargoed">
    <PageTitle eyebrow="SUBMISSION RECEIVED" title={score ? 'Your score is ready.' : open ? 'Calculating your score…' : 'Your answers are sealed.'} description={pending.title} />
    {score && <LiveScore s={score} />}
    <section className={'import-card' + (score ? ' mt-6' : '')}>
      <h2>A fair window for everyone.</h2>
      <p className="import-muted" data-testid="results-release-time">{open ? 'Answers, solutions and ranks' : 'Your results and solutions'} unlock at {ist(pending.release_at)}, {open ? 'when every student’s time is up.' : 'after the competition closes.'}</p>
      <p className="import-fineprint mt-4 [overflow-wrap:anywhere]" data-testid="results-embargo-receipt">Submission receipt: {pending.receipt}</p>
      <div className="flex flex-wrap gap-3 mt-6">
        <Button data-testid="results-release-refresh" onClick={onRefresh}>Check results</Button>
        <Button asChild variant="outline"><Link data-testid="results-competition-hub" to={pending.series_id ? seriesPath(pending.series_id)+(pending.series_id===JEE_SERIES?'?tab=results':'') : '/competitions'}>{pending.series_id ? 'All India series hub' : 'Competition hub'}</Link></Button>
      </div>
    </section>
  </div>;
}
