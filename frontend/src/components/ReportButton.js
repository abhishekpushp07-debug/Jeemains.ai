import React, { useState, useEffect, useRef } from 'react';
import { Download, Loader2, RefreshCw } from 'lucide-react';
import { api, post, downloadFile } from '../lib/api';
import { toast } from 'sonner';
import { Button } from './ui/button';

export const ReportButton = ({ id, compact = false, scoreVersion = 'original', answerKeyOnly = false }) => {
  const filename = answerKeyOnly ? 'jeemains-ai-results-and-answer-keys.pdf' : 'jeemains-ai-results-and-solutions.pdf';
  const [job, setJob] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [cycle, setCycle] = useState(0);
  const downloaded = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  const jobId = job?.id;
  const status = job?.status;
  useEffect(() => {
    if (!jobId || ['done', 'failed'].includes(status)) return;
    let stopped = false, timer, polls = 0, failures = 0;
    const poll = async () => {
      try {
        const next = await api('/jobs/' + jobId);
        if (stopped || !mounted.current) return;
        if (next.status === 'done') {
          if (!downloaded.current) {
            await downloadFile('/jobs/' + next.id + '/download', filename);
            downloaded.current = true;
          }
          if (!stopped && mounted.current) { setJob(next); setError(''); setBusy(false); }
          return;
        }
        setJob(next);
        failures = 0;
        setError('');
        if (next.status === 'failed') {
          setError(next.error || 'Report preparation needs another try.');
          setBusy(false);
          return;
        }
        if (++polls >= 90) {
          setError('Your report is still queued. Check again shortly; your result is safe.');
          setBusy(false);
          return;
        }
        timer = setTimeout(poll, Math.min(10000, 1800 + polls * 250) + Math.random() * 1200);
      } catch (e) {
        if (stopped || !mounted.current) return;
        setError(e.message);
        if (++failures >= 5) { setBusy(false); return; }
        timer = setTimeout(poll, Math.max(e.retryAfterMs || 0, Math.min(30000, 1000 * 2 ** failures) + Math.random() * 1000));
      }
    };
    timer = setTimeout(poll, 1600 + Math.random() * 600);
    return () => { stopped = true; clearTimeout(timer); };
  }, [jobId, status, cycle, filename]);

  const start = async () => {
    setBusy(true); setError(''); downloaded.current = false;
    try {
      let next = await post('/attempts/' + id + '/report', { score_version: scoreVersion });
      if (!mounted.current) return;
      if (next.status === 'failed') next = await post('/jobs/' + next.id + '/retry');
      if (!mounted.current) return;
      setJob(next); setCycle(v => v + 1);
      if (next.status === 'done') {
        downloaded.current = true;
        await downloadFile('/jobs/' + next.id + '/download', filename);
        if (mounted.current) setBusy(false);
      }
    } catch (e) {
      if (!mounted.current) return;
      setError(e.message); toast.error(e.message); setBusy(false);
    }
  };
  return <div className="report-button-wrap">
    <Button variant={compact ? 'ghost' : 'default'} className={'btn ' + (compact ? 'btn-quiet' : 'btn-primary')} data-testid="results-download-report-button" disabled={busy} onClick={start}>
      {busy ? <Loader2 size={18} className="spin" /> : error ? <RefreshCw size={18} /> : <Download size={18} />}
      {busy ? `Preparing report${job ? ' · ' + job.progress + '%' : ''}` : error ? 'Retry PDF download' : compact ? 'Download PDF' : answerKeyOnly ? 'Download results & answer keys PDF' : 'Download results & solutions PDF'}
    </Button>
    {error && <small className="error-text" role="alert" data-testid="report-download-error">{error}</small>}
    {busy && <div className="report-progress" role="progressbar" data-testid="report-download-progress" aria-label="Report generation" aria-valuenow={job?.progress || 5} aria-valuemin={0} aria-valuemax={100}><span style={{ width: (job?.progress || 5) + '%' }} /></div>}
  </div>;
};
