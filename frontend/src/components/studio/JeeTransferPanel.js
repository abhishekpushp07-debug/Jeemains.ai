import React, { useEffect, useRef, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { api, post } from '../../lib/api';
import { Button } from '../ui/button';

export const JeeTransferPanel = () => {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const running = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    api('/studio/jee-transfer', { signal: controller.signal }).then(setData).catch(e => {
      if (!controller.signal.aborted) setError(e.message);
    });
    return () => { controller.abort(); running.current = false; };
  }, []);
  async function run() {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError('');
    try {
      let result;
      do {
        result = await post('/studio/jee-transfer/step');
        setData(result);
      } while (running.current && result.phase !== 'complete');
    } catch (e) { setError(e.message); }
    finally { running.current = false; setBusy(false); }
  }
  const done = data?.phase === 'complete';
  const progress = data ? data.verified_files + data.processed_records : 0;
  return <section className="import-card mb-6" data-testid="jee-transfer-panel">
    <header><span className="eyebrow"><ShieldCheck size={16} /> VERIFIED JEE CHAPTERS</span>
      <h2 data-testid="jee-transfer-title">Import your 78 reviewed chapter tests</h2>
      <p data-testid="jee-transfer-scope">3,900 questions and supplied solutions. Physics 90 min · Mathematics 120 min · Chemistry 70 min. Marking +4 / −1 / 0. No AI generation.</p>
    </header>
    <p className="mt-3" data-testid="jee-transfer-environment">Applies only to this site's database ({window.location.hostname}). Preview imports do not update your live site. All 81 private PDFs are checked before new chapters are added. Existing records are never overwritten.</p>
    {data && <div className="my-4" aria-live="polite" data-testid="jee-transfer-progress">
      <p>{done ? 'Import complete. Existing content was unchanged at completion.' : data.phase === 'importing' ? 'Adding verified content in resumable batches…' : busy ? 'Checking private source PDFs…' : 'Ready to verify or resume.'}</p>
      <p>{data.verified_files} / 81 PDFs verified · {data.processed_records} / 162 records processed · {data.chapter_tests} / 78 chapter IDs present</p>
      <progress className="w-full h-2" aria-label="JEE chapter import progress" value={progress} max={243} data-testid="jee-transfer-progress-bar" />
    </div>}
    {error && <p role="alert" className="my-3 text-red-700 break-words" data-testid="jee-transfer-error">{error}</p>}
    <div className="flex flex-wrap gap-3 mt-4">
      <Button data-testid="jee-transfer-start" disabled={busy || done || !data} onClick={run}>{done ? 'Import complete' : busy ? 'Import in progress…' : data?.verified_files ? 'Resume verified import' : 'Verify & import 78 chapters'}</Button>
      {busy && <Button variant="outline" data-testid="jee-transfer-pause" onClick={() => { running.current = false; }}>Pause after current step</Button>}
      {!data && error && <Button variant="outline" data-testid="jee-transfer-retry" onClick={() => { setError(''); api('/studio/jee-transfer').then(setData).catch(e => setError(e.message)); }}>Retry connection</Button>}
    </div>
    <p className="import-fineprint mt-3" data-testid="jee-transfer-safety">Closing this page pauses after the current step. Chapters appear in verified batches, so a pause can leave a partial catalogue until you resume. No duplicate chapters are created. A conflicting record or inaccessible source blocks further import.</p>
  </section>;
};
