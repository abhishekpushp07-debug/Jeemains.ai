import { examPath, safeExamReturn } from '../lib/exams';
import React, { useEffect, useState, useRef } from 'react';
import { Link, useParams, useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ArrowRight, CheckCircle2, Wifi, Clock3, ShieldCheck, Loader2, FileQuestion, Flag, Save, FileDown } from 'lucide-react';
import { api, post } from '../lib/api';
import { useAuth } from '../lib/auth';
import { PageTitle, Badge, Loading, ErrorBox, Field } from '../components/Shared';
import { MathText } from '../components/QuestionContent';
import { Button } from '../components/ui/button';
import { Checkbox } from '../components/ui/checkbox';
import {SavePaperButton} from '../components/SavePaperButton';
import { Card } from '../components/ui/card';

export default function SetDetail() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const preview = params.get('preview') === 'true';
  const { user, checking } = useAuth();
  const userId = user?.id;
  const nav = useNavigate();
  const location = useLocation();
  const [s, setS] = useState(null);
  const [error, setError] = useState('');
  const [checked, setChecked] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const key = useRef(null);
  const returnTo = safeExamReturn(location.state?.returnTo, s ? s.series_id ? '/series/all-india-jee' : examPath(s.exam)+(s.chapter_book_id||s.test_kind==='chapter'?'/chapters'+(s.chapter_subject?'?subject='+encodeURIComponent(s.chapter_subject):''):s.test_kind==='pyq'?'/pyq':'/mocks') : '/home');
  useEffect(() => {
    const controller = new AbortController();
    setS(null); setError(''); setChecked(false); setConfirmed(false);
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
  async function check() {
    setBusy(true); setError('');
    try {
      localStorage.setItem('tejas-device-check', 'ok');
      if (localStorage.getItem('tejas-device-check') !== 'ok') throw new Error('Enable browser storage to protect pending answer drafts.');
      localStorage.removeItem('tejas-device-check');
      await post('/sets/' + id + '/preflight', { preview, test_response: value });
      setChecked(true);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function start() {
    setBusy(true); setError('');
    try {
      const a = await post('/sets/' + id + '/start', { preview, device_checked: confirmed, start_key: key.current });
      sessionStorage.removeItem('tejas-start-' + id);
      nav(a.status === 'completed' ? '/results/' + a.id : '/attempts/' + a.id, {state:{returnTo}});
    } catch (e) { setError(e.message); setBusy(false); }
  }
  if (!s) return <div className="container page"><ErrorBox error={error} retry={() => setRetry(v => v + 1)} />{!error && <Loading />}</div>;
  const count = s.count ?? s.questions?.length;
  const minutes = s.rules.minutes;
  return (
    <div className="container page set-detail" data-testid="set-detail-page">
      <Link className="breadcrumb" data-testid="set-back" to={preview ? '/studio/' + id : returnTo}><ArrowLeft size={15} /> {preview ? 'Back to Content Studio' : 'Back to '+s.exam+' tests'}</Link>
      <PageTitle eyebrow={preview ? 'PRIVATE REVIEW · NOT APPROVED CONTENT' : `${s.exam.toUpperCase()} · INDEPENDENT PRACTICE`} title={s.title} description={s.test_kind === 'pyq' ? 'A complete dated JEE Main paper. Review the rules, check your device and begin; original supplied solutions unlock after submission.' : s.source} action={!preview&&user?<SavePaperButton setId={id}/>:null} />
      {preview && <div className="notice amber" data-testid="private-preview-notice">Private draft preview. Questions and solutions still require review. Starting does not approve or publish this paper.</div>}
      {s.series_id&&<div className="series-preflight-note" data-testid="series-preflight-rules"><strong>All India JEE Mains · {s.series_date} (IST)</strong><p>Live starts: 12:01 AM–8:59:00 PM. One live attempt; the original 180-minute deadline continues on resume. Live results and solutions release at 11:59 PM. From the following day, starts become separate archive-practice attempts.</p></div>}
      <div className="preflight-grid">
        <Card className="card instructions" data-testid="set-instructions">
          <div className="preflight-step-label" data-testid="preflight-rules-step"><span>01</span> Get familiar</div>
          <h2 data-testid="set-instructions-heading">Your practice, at a glance.</h2>
          <Badge>{s.exam} · Practice for {s.year || 'your preparation'}</Badge>
          <div className="instruction-facts" data-testid="set-facts">
            <div><FileQuestion size={18} /><strong data-testid="set-question-count">{count}</strong><span>Questions</span></div>
            <div><Clock3 size={18} /><strong data-testid="set-duration">{minutes ? (minutes < 1 ? minutes * 60 : minutes) : 'No limit'}</strong><span>{minutes ? (minutes < 1 ? 'Seconds' : 'Minutes') : 'Untimed practice'}</span></div>
            <div><Flag size={18} /><strong data-testid="set-maximum-marks">{s.maximum ?? count * s.rules.correct}</strong><span>Maximum marks</span></div>
          </div>
          <div className="marks-rule" data-testid="set-marking-rule"><span>+{s.rules.correct} correct</span><span>{s.rules.wrong} incorrect</span><span>0 unanswered</span></div>
          <h3 data-testid="set-before-start-heading">A few things to know</h3>
          <ul data-testid="set-instructions-list">
            <li data-testid="set-response-format">{s.test_kind === 'pyq' ? 'Select one listed option, or enter an integer where stated. Source-marked multiple accepted answers and withdrawn questions retain their supplied scoring treatment.' : 'One correct option per question, or an integer entry where stated.'} Mark for review and return to any question.</li>
            {s.rules.numeric_rule&&<li>{s.rules.numeric_rule}</li>}
            <li>{minutes ? 'The timer keeps running during a disconnect. Only answers received before the deadline are scored.' : 'This is untimed practice. Come back to your saved attempt whenever you need.'}</li>
            <li>{s.series_id?'Live results and solutions are sealed until 11:59 PM IST. Archive practice results unlock after submission.':s.solution_kind==='answer_key_only'?'Submitting is final. Your score and supplied answer keys become available after grading. This book has no worked solutions.':'Submitting is final. Your result and matched solutions become available afterward.'}</li>
          </ul>
          <div className="notice preflight-recovery" data-testid="preflight-offline-recovery-notice"><Save size={19} /><span><strong>Your drafts stay on this device.</strong> Offline edits remain pending until the server acknowledges them. Check the save status before submitting.</span></div>
          <details className="profile-details"><summary data-testid="practice-profile-details">About this practice profile</summary><p>Free navigation · Original question order · Exact integers · Solutions after submission. This custom profile is not an official-year exam simulation. Review includes every question, regardless of review filters.</p></details>
        </Card>
        <Card className="card device-check" data-testid="set-preflight-checklist">
          <div className="preflight-step-label" data-testid="preflight-device-step"><span>02</span> Check & begin</div>
          <h2 data-testid="device-check-heading">Ready when you are.</h2>
          <p data-testid="device-check-description">Check that the notation and diagram look clear, then try an answer below.</p>
          <div className="device-sample" data-testid="device-check-sample">
            <MathText text={'$x^2 + y^2 = r^2$'} />
            <svg viewBox="0 0 180 65" role="img" aria-label="Device check: a right triangle with sides a, b and c"><path d="M35 10v45h110Z" fill="none" stroke="var(--brand-text)" strokeWidth="2" /><text x="17" y="38">a</text><text x="84" y="51">b</text><text x="90" y="27">c</text></svg>
            <small>Display check only, not a practice question.</small>
          </div>
          <Field id="device-test-answer" label="Try entering an integer" placeholder="For example, 25" value={value} onChange={e => setValue(e.target.value)} />
          {user ? <>
            <Button variant="outline" className="btn btn-secondary full-width" data-testid="preflight-run-check" disabled={busy} onClick={check}>{busy ? <Loader2 className="spin" size={17} /> : checked ? <CheckCircle2 size={17} /> : <Wifi size={17} />}{checked ? 'Device check passed' : 'Check my device'}</Button>
            {checked && <p className="device-check-success" role="status" data-testid="preflight-check-success">Connection check passed and browser storage is available. You can enlarge original source images during the attempt.</p>}
            <label className="checkbox-label" htmlFor="preflight-consent"><Checkbox id="preflight-consent" className="preflight-checkbox" data-testid="preflight-acknowledge" checked={confirmed} onCheckedChange={v => setConfirmed(v === true)} /><span>I can read the content and understand the rules and offline saving policy.</span></label>
            <ErrorBox error={error} />
            <p className="import-fineprint" data-testid="preflight-source-image-disclosure">If a required source image fails to load during the attempt, answering pauses until it loads. This check does not certify every formula’s readability.</p>
            <div className={checked&&confirmed?'preflight-start-ready':''} data-testid="preflight-start-actionbar"><Button className="btn btn-primary full-width" data-testid="set-preflight-start-button" disabled={!checked || !confirmed || busy} onClick={start}>{busy ? <Loader2 className="spin" size={18} /> : null}Start {preview ? 'private preview' : 'attempt'}<ArrowRight size={18} /></Button></div>
          </> : <Button asChild className="btn btn-primary full-width"><Link data-testid="preflight-login" to={'/login?next=' + encodeURIComponent('/sets/' + id)}>Sign in to start<ArrowRight size={17} /></Link></Button>}
          <small className="preflight-clock-note" data-testid="preflight-clock-notice"><Clock3 size={14} /> The clock starts only when your attempt opens.</small>
          <small data-testid="preflight-profile-notice"><ShieldCheck size={14} /> Saved to this number’s practice profile.</small>
        </Card>
      </div>
    </div>
  );
}
