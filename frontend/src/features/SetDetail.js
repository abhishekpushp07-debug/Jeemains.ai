import { examPath, safeExamReturn, seriesPath, JEE_SERIES } from '../lib/exams';
import React, { useEffect, useState, useRef } from 'react';
import { Link, useParams, useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Clock3, ShieldCheck, Loader2, FileQuestion, Flag, PlayCircle, BookOpenCheck, Rocket } from 'lucide-react';
import { api, postWhenFree } from '../lib/api';
import { rememberStartedAttempt } from '../lib/privateResources';
import { useAuth } from '../lib/auth';
import { PageTitle, Loading, ErrorBox } from '../components/Shared';
import { Button } from '../components/ui/button';
import { SavePaperButton } from '../components/SavePaperButton';
import { Card } from '../components/ui/card';

const STEPS = [
  [PlayCircle, 'Press Start test.'],
  [BookOpenCheck, 'Read 6 quick rules for 60 seconds while your whole paper loads.'],
  [Rocket, 'Press Begin now, or wait. Your clock starts only then.'],
];

function SeriesNote({ s }) {
  if (!s.series_id) return null;
  return <div className="series-preflight-note" data-testid="series-preflight-rules">
    <strong>{s.series_id === JEE_SERIES ? 'All India JEE Mains' : 'All India series'} · {s.series_date} (IST)</strong>
    <p>{s.series_id === JEE_SERIES ? 'Live starts 12:01 AM–8:59 PM. ' : ''}One live attempt today; resuming keeps your deadline. Score and solutions open right after you submit. Your All India rank joins when the day closes at 11:59 PM.</p>
  </div>;
}

function Facts({ s }) {
  const count = s.count ?? s.questions?.length, minutes = s.rules.minutes;
  return <>
    <div className="instruction-facts" data-testid="set-facts">
      <div><FileQuestion size={18} /><strong data-testid="set-question-count">{count}</strong><span>Questions</span></div>
      <div><Clock3 size={18} /><strong data-testid="set-duration">{minutes ? (minutes < 1 ? minutes * 60 : minutes) : 'No limit'}</strong><span>{minutes ? (minutes < 1 ? 'Seconds' : 'Minutes') : 'Untimed practice'}</span></div>
      <div><Flag size={18} /><strong data-testid="set-maximum-marks">{s.maximum ?? count * s.rules.correct}</strong><span>Maximum marks</span></div>
    </div>
    <div className="marks-rule" data-testid="set-marking-rule"><span>+{s.rules.correct} correct</span><span>{s.rules.wrong} incorrect</span><span>0 unanswered</span></div>
  </>;
}

export default function SetDetail() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const preview = params.get('preview') === 'true';
  const { user, checking } = useAuth();
  const userId = user?.id;
  const nav = useNavigate();
  const location = useLocation();
  const backParam = params.get('back');
  const previewBack = location.state?.previewBack || (backParam && backParam.startsWith('/super-admin') ? backParam : null);
  const [s, setS] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const key = useRef(null);
  const autoStarted = useRef(false);
  const returnTo = safeExamReturn(location.state?.returnTo, s ? s.series_id ? seriesPath(s.series_id) : s.catalog_path ? s.catalog_path+((s.chapter_book_id||s.test_kind==='chapter')&&s.chapter_subject?'?subject='+encodeURIComponent(s.chapter_subject):'') : examPath(s.exam)+(s.chapter_book_id||s.test_kind==='chapter'?'/chapters'+(s.chapter_subject?'?subject='+encodeURIComponent(s.chapter_subject):''):s.test_kind==='pyq'?'/pyq':'/mocks') : '/home');
  useEffect(() => {
    const controller = new AbortController();
    setS(null); setError('');
    if (!checking) {
      key.current = sessionStorage.getItem('tejas-start-' + id) || crypto.randomUUID();
      sessionStorage.setItem('tejas-start-' + id, key.current);
      const path = preview ? '/studio/sets/' + id : (userId ? '/my/sets/' : '/sets/') + id;
      api(path, { signal: controller.signal })
        .then(d => { if (!controller.signal.aborted) setS(d); })
        .catch(e => { if (!controller.signal.aborted) setError(e.message); });
    }
    return () => controller.abort();
  }, [id, preview, userId, checking, retry]);
  async function start() {
    setBusy(true); setError('');
    try {
      const a = await postWhenFree('/sets/' + id + '/start', { preview, start_key: key.current, get_ready: true });
      sessionStorage.removeItem('tejas-start-' + id);
      rememberStartedAttempt(userId, a);
      nav(a.status === 'completed' ? '/results/' + a.id : '/attempts/' + a.id, { state: { returnTo } });
    } catch (e) { setError(e.message); setBusy(false); }
  }
  // A tap on a finished, unattempted series day starts its paper straight away (once).
  useEffect(() => {
    if (!s || !userId || preview || autoStarted.current || !location.state?.autoStart) return;
    autoStarted.current = true;
    nav(location.pathname + location.search, { replace: true, state: { ...location.state, autoStart: false } });
    start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [s, userId]);
  if (!s) return <div className="container page"><ErrorBox error={error} retry={() => setRetry(v => v + 1)} />{!error && <Loading />}</div>;
  return (
    <div className="container page set-detail set-simple" data-testid="set-detail-page">
      <Link className="breadcrumb" data-testid="set-back" to={preview ? previewBack || '/studio/' + id : returnTo}><ArrowLeft size={15} /> {preview ? (previewBack ? 'Back to Master' : 'Back to Content Studio') : s.series_id ? 'Back to All India series' : 'Back to '+s.exam+' tests'}</Link>
      <PageTitle eyebrow={preview ? 'PRIVATE REVIEW · NOT APPROVED CONTENT' : s.series_id ? `${s.exam.toUpperCase()} · ALL INDIA TEST SERIES` : `${s.exam.toUpperCase()} · INDEPENDENT PRACTICE`} title={s.title} description={s.test_kind === 'pyq' ? 'A complete dated JEE Main paper. Original supplied solutions unlock after you submit.' : s.source} action={!preview&&user?<SavePaperButton setId={id}/>:null} />
      {preview && <div className="notice amber" data-testid="private-preview-notice">Private draft preview. Questions and solutions still require review. Starting does not approve or publish this paper.</div>}
      <SeriesNote s={s} />
      <Card className="card set-start-card" data-testid="set-instructions">
        <Facts s={s} />
        <h2 data-testid="set-before-start-heading">How it works</h2>
        <ol className="set-steps" data-testid="set-steps">{STEPS.map(([Icon, text], i) => <li key={i}><span className="set-step-icon"><Icon size={18} aria-hidden="true" /></span><span>{text}</span></li>)}</ol>
        {user
          ? <Button className="btn btn-primary full-width set-start-button" data-testid="set-preflight-start-button" disabled={busy} onClick={start}>{busy ? <Loader2 className="spin" size={18} /> : null}Start {preview ? 'private preview' : 'test'}<ArrowRight size={18} /></Button>
          : <Button asChild className="btn btn-primary full-width"><Link data-testid="preflight-login" to={'/login?next=' + encodeURIComponent('/sets/' + id)}>Sign in to start<ArrowRight size={17} /></Link></Button>}
        <ErrorBox error={error} />
        <small className="preflight-clock-note" data-testid="preflight-clock-notice"><Clock3 size={14} /> The clock starts only when your paper opens.</small>
        <small data-testid="preflight-profile-notice"><ShieldCheck size={14} /> Saved to this number’s practice profile.</small>
      </Card>
    </div>
  );
}
