import { examPath, safeExamReturn } from '../lib/exams';
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Link,
  useParams,
  useSearchParams,
  useNavigate,
} from "react-router-dom";
import {
  ArrowLeft,
  RotateCcw,
  CheckCircle2,
  XCircle,
  MinusCircle,
  Flag,
  ShieldCheck,
} from "lucide-react";
import { api, post } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  PageTitle,
  Badge,
  Loading,
  ErrorBox,
  Empty,
  Confirm,
} from "../components/Shared";
import { QuestionContent, MathText } from "../components/QuestionContent";
import { ResultsAnalyticsWorkspace } from '../components/results/ResultsAnalyticsWorkspace';
import { ResultsReflectionStrip } from '../components/results/ResultsReflectionStrip';
import { ReportButton } from "../components/ReportButton";
import { MockSectionScores } from '../components/results/MockSectionScores';
import {BitsatBranchView} from '../components/results/BitsatBranchView';
import {useLearningMeters,MeterShortcuts,JourneyView,ConfidenceView,HistoricalRankView} from '../components/results/LearningMeters';
import { BarChart3,TrendingUp,Target,Trophy,BookOpen } from 'lucide-react';
import { ResultAnalysis } from '../components/results/ResultAnalysis';
import { AiSolution, PeerQuestionStat } from '../components/results/AiSolution';
import { useResultExtras } from '../components/results/useResultExtras';
import {QuestionReport, QuestionReportsProvider} from '../components/QuestionReport';
import {Tabs, TabsList, TabsTrigger} from '../components/ui/tabs';
import { SolutionNavigator, matchesOutcome } from '../components/results/SolutionNavigator';
import {useLocation} from 'react-router-dom';
import { Button } from '../components/ui/button';
export default function Results() {
  const { id } = useParams();
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const location = useLocation();
  const view = ['analysis','progress','accuracy','rank','solutions'].includes(params.get('view')) ? params.get('view') : 'analysis';
  const scrollPositions = useRef({analysis:0,progress:0,accuracy:0,rank:0,solutions:0});
  function changeView(next, question) {
    scrollPositions.current[view] = window.scrollY;
    const nextParams = new URLSearchParams(params);
    if (next === 'analysis') nextParams.delete('view'); else nextParams.set('view', next);
    if (question) nextParams.set('question', question);
    setParams(nextParams, {state:location.state});
    requestAnimationFrame(()=>window.scrollTo(0, scrollPositions.current[next] || 0));
  }
  function changeScoreVersion(version) {
    const next = new URLSearchParams(params);
    if (version === 'original') next.delete('score_version'); else next.set('score_version', version);
    setParams(next, {state:location.state});
  }
  const scoreVersion = params.get("score_version") || "original";
  const nav = useNavigate();
  const [r, setR] = useState(null);
  const [error, setError] = useState("");
  const filter = ['all','marked','bonus-section','incorrect','skipped','correct','dropped','bonus'].includes(params.get('filter')) ? params.get('filter') : 'all';
  function setFilter(value) {
    const next = new URLSearchParams(params); next.set('filter', value);
    const matching = allQuestions.filter(q => q.subject === activeSubject && matchesOutcome(q, value));
    const question = matching.find(q => q.id === selectedQuestion) || matching[0];
    if (question) next.set('question', question.id); else next.delete('question');
    setParams(next, {state:location.state});
  }
  const [retryOpen, setRetryOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [pending, setPending] = useState(null);
  const recordedSolutions = useRef(new Set());
  const [solutionState,setSolutionState] = useState({});
  const [confidenceThreshold,setConfidenceThreshold] = useState(0.2);
  const recordSolution = useCallback(async (qid) => {
    setSolutionState(old=>({...old,[qid]:'pending'}));
    try { await post(`/attempts/${id}/questions/${qid}/solution-open`,{}); setSolutionState(old=>({...old,[qid]:'saved'})); }
    catch { setSolutionState(old=>({...old,[qid]:'error'})); }
  }, [id]);
  const extras = useResultExtras(id, !!r, !!r?.questions?.length && r.questions.every(q => q.solution_kind === 'supplied_worked'));
  const meters = useLearningMeters(id,scoreVersion,!!r);
  const resultAttemptId = r?.id;
  const allQuestions = r?.questions || [];
  const selectedQuestion = params.get('question');
  const subjects = [...new Set(allQuestions.map(q => q.subject))];
  const requestedSubject = params.get('subject');
  const activeSubject = allQuestions.find(q => q.id === selectedQuestion)?.subject || (subjects.includes(requestedSubject) ? requestedSubject : subjects[0]) || '';
  const qs = allQuestions.filter(q => q.subject === activeSubject && matchesOutcome(q, filter));
  const activeQuestion = qs.find(q => q.id === selectedQuestion) || qs[0];
  useEffect(() => {
    if (!r || view !== 'solutions' || !activeSubject) return;
    const next = new URLSearchParams(params);
    next.set('subject', activeSubject);
    if (params.has('filter')) next.set('filter', filter);
    if (activeQuestion) next.set('question', activeQuestion.id); else next.delete('question');
    if (next.toString() !== params.toString()) setParams(next, {replace:true, state:location.state});
  }, [r, view, activeSubject, activeQuestion, filter, params, setParams, location.state]);
  useEffect(() => {
    if (view !== 'solutions' || !activeQuestion || resultAttemptId !== id) return;
    const key = id + ':' + activeQuestion.id;
    if (!recordedSolutions.current.has(key)) {
      recordedSolutions.current.add(key);
      recordSolution(activeQuestion.id);
    }
  }, [id, view, activeQuestion, resultAttemptId, recordSolution]);
  async function refreshAnalytics(threshold = confidenceThreshold) {
    const result=await api('/attempts/'+id+'/results?score_version='+encodeURIComponent(scoreVersion)+'&confidence_threshold='+threshold);
    if(result.analytics) { setR(result); setConfidenceThreshold(threshold); }
    return result;
  }
  function openQuestion(qid) {
    if(!r)return;
    const question=r.questions.find(q=>q.id===qid);
    if(!question)return;
    const matches = matchesOutcome(question, filter);
    const next=new URLSearchParams(params);next.set('view','solutions');next.set('question',qid);next.set('subject',question.subject);
    if(!matches)next.set('filter','all');
    if(view==='analysis')scrollPositions.current.analysis=window.scrollY;
    setParams(next,{state:location.state});
    if (view !== 'solutions') requestAnimationFrame(() => document.querySelector('[data-testid="solution-question-navigation"]')?.scrollIntoView({block:'start',behavior:'instant'}));
  }
  function chooseSubject(subject) {
    const next = new URLSearchParams(params); next.set('subject', subject);
    const question = allQuestions.find(q => q.subject === subject && matchesOutcome(q, filter));
    if (question) next.set('question', question.id); else next.delete('question');
    setParams(next, {state:location.state});
  }
  useEffect(() => {
    const controller = new AbortController();
    let timer, polls = 0;
    setR(null); setPending(null); setError('');
    const load = async () => {
      try {
        const result = await api('/attempts/' + id + '/results?score_version=' + encodeURIComponent(scoreVersion), { signal: controller.signal });
        if (controller.signal.aborted) return;
        if (result.status === 'embargoed') { setPending(result); }
        else if (result.status === 'grading') {
          setPending(result);
          if (result.grading_status !== 'failed' && ++polls < 45) {
            timer = setTimeout(load, Math.min(10000, Math.max(2000, result.retry_after_ms || 2000) * (1 + polls / 5)) + Math.random() * 1000);
          }
        } else { setPending(null); setR(result); }
      } catch (e) { if (!controller.signal.aborted) setError(e.message); }
    };
    load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [id, scoreVersion, refresh]);
  async function retry() {
    setBusy(true);
    try {
      const next = await post("/attempts/" + id + "/retry", {
        start_key: crypto.randomUUID(),
        score_version: scoreVersion,
      });
      nav("/attempts/" + next.id);
    } catch (e) {
      setError(e.message);
      setRetryOpen(false);
    } finally {
      setBusy(false);
    }
  }
  if (pending?.status === 'embargoed') return <div className="container page" data-testid="results-embargoed"><PageTitle eyebrow="SUBMISSION RECEIVED" title="Your answers are sealed." description={pending.title} /><section className="import-card"><h2>A fair window for everyone.</h2><p className="import-muted" data-testid="results-release-time">Your results and solutions unlock at {new Date(pending.release_at * 1000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST, after the competition closes.</p><p className="import-fineprint mt-4" data-testid="results-embargo-receipt">Submission receipt: {pending.receipt}</p><div className="flex flex-wrap gap-3 mt-6"><Button data-testid="results-release-refresh" onClick={() => setRefresh(v => v + 1)}>Check results</Button><Button asChild variant="outline"><Link data-testid="results-competition-hub" to={pending.series_id?'/series/all-india-jee?tab=results':'/competitions'}>{pending.series_id?'All India series hub':'Competition hub'}</Link></Button></div></section></div>;
  if (pending) return <div className="container page" data-testid="results-grading-pending">
    <PageTitle eyebrow="SUBMISSION RECEIVED" title="Your answers are safely submitted." description="Your sealed answers are being graded in the background. You can leave this page and return from your exam’s Results section." />
    <div className="card">
      <p data-testid="grading-status" role="status">{pending.grading_status === 'failed' ? 'Grading needs another try. Your submitted answers have not changed.' : 'Preparing your results and review…'}</p>
      <p data-testid="submission-receipt">Receipt: {pending.receipt}</p>
      <ErrorBox error={error} />
      <div className="form-actions">
        <Button className="btn btn-primary" data-testid="grading-retry" disabled={busy} onClick={async () => {
          setBusy(true);
          try { if (pending.grading_status === 'failed') await post('/jobs/' + pending.job_id + '/retry', {}); setRefresh(v => v + 1); }
          catch (e) { setError(e.message); } finally { setBusy(false); }
        }}>{pending.grading_status === 'failed' ? 'Retry grading' : 'Check progress'}</Button>
        <Button asChild variant="outline" className="btn btn-secondary"><Link data-testid="grading-back-home" to="/home">Home</Link></Button>
      </div>
    </div>
  </div>;
  if (!r)
    return (
      <div className="container page">
        <ErrorBox error={error} retry={() => setRefresh(v => v + 1)} />
        {!error && <Loading text="Opening your completed attempt…" />}
      </div>
    );
  const s = r.summary;
  const lateKey = `tejas-draft-${user.id}-${id}`;
  let late = {};
  try {
    late = JSON.parse(localStorage.getItem(lateKey) || "{}");
  } catch {}
  return (
    <QuestionReportsProvider attemptId={id}><div className="container page results-page">
      <Link className="breadcrumb" to={safeExamReturn(location.state?.returnTo,r.series_id?'/series/all-india-jee?tab=results':examPath(r.exam)+'/results')} data-testid="results-home">
        <ArrowLeft size={14} /> {r.series_id?'Back to All India series':location.state?.returnTo?.startsWith('/profile')?'Back to My Tests':`Back to ${r.exam} ${location.state?.returnTo?.includes('/results')?'results':'tests & results'}`}
      </Link>
      <PageTitle
        eyebrow={`${r.exam} · ${r.mode === "preview" ? "UNAPPROVED PRIVATE PREVIEW" : r.mode === 'series_live' ? 'ALL INDIA SERIES · LIVE ATTEMPT' : r.mode === 'series_practice' ? 'ALL INDIA SERIES · ARCHIVE PRACTICE' : "COMPLETED PRACTICE"}`}
        title={r.title}
        description="Your score, analysis and saved explanations—in one place."
      />
      {r.mode === "preview" && (
        <div className="notice amber">
          Private content preview—not an approved academic result.
          Author-provided keys and solutions still require human verification.
        </div>
      )}
      {Object.keys(late).length > 0 && (
        <div className="notice amber" data-testid="late-draft-notice" role="status">
          <div>
            <strong>
              Late or unacknowledged local drafts were not scored.
            </strong>
            <p>
              {Object.keys(late).length} draft response(s) remain on this
              device. The result below uses only accepted server responses.
            </p>
            <details>
              <summary data-testid="late-drafts-view">
                View unaccepted drafts
              </summary>
              {Object.entries(late).map(([qid, v]) => (
                <p key={qid}>
                  Question {r.questions.find((q) => q.id === qid)?.number}:{" "}
                  {v.value || "Cleared response"} — not accepted
                </p>
              ))}
            </details>
          </div>
        </div>
      )}
      <ErrorBox error={error} />
      {r.grade_versions?.length > 0 && (
        <section className="grade-history">
          <h3>A reviewed scoring correction is available.</h3>
          <p>
            {r.change_note} Your original result and report remain unchanged.
            Select a version explicitly.
          </p>
          <div className="button-row">
            <button
              className="btn btn-secondary"
              data-testid="score-version-original"
              disabled={scoreVersion === "original"}
              onClick={() => changeScoreVersion('original')}
            >
              Original score
            </button>
            {r.grade_versions.map((g) => (
              <button
                key={g.id}
                className="btn btn-secondary"
                data-testid={"score-version-" + g.key_version}
                disabled={scoreVersion === g.id}
                onClick={() => changeScoreVersion(g.id)}
              >
                Key version {g.key_version} ·{" "}
                {new Date(g.created_at * 1000).toLocaleDateString()}
              </button>
            ))}
          </div>
        </section>
      )}
      <div className="results-review-shortcuts" data-testid="results-review-shortcuts"><p data-testid="results-attempt-immutable-notice"><ShieldCheck size={16}/> Your submitted answers are sealed. Review notes won’t change your score.</p></div>
      {r.questions.every(q=>q.solution_kind==='answer_key_only')&&<p className="results-key-notice" data-testid="results-answer-keys-only-disclosure">The source supplies official keys, not worked solutions. Saved owner or AI explanations appear in Solutions where available.</p>}
      <div className="results-summary" data-testid="results-summary-tiles">
        <div className="score-card">
          <span>Your score</span>
          <strong data-testid="results-score-total">
            {s.score}
            <small> / {s.maximum}</small>
          </strong>
          <span className="score-percentage">
            {s.percentage === null
              ? "Percentage unavailable"
              : s.percentage + "%"}{" "}
            · not a percentile
          </span>
          <p>
            +{r.rules.correct} correct · {r.rules.wrong} wrong · 0 skipped
          </p>
        </div>
        <div className="result-stat">
          <span>
            <CheckCircle2 size={18} /> Correct
          </span>
          <strong>{s.correct}</strong>
          <small>Matched the frozen supplied key</small>
        </div>
        <div className="result-stat">
          <span>
            <XCircle size={18} /> Incorrect
          </span>
          <strong>{s.incorrect}</strong>
          <small>Opportunities to review</small>
        </div>
        <div className="result-stat">
          <span>
            <MinusCircle size={18} /> Skipped
          </span>
          <strong>{s.skipped}</strong>
          <small>Worth another look</small>
        </div>
      </div>
      <Tabs value={view} onValueChange={changeView} className="result-destinations" data-testid="result-view-navigation"><TabsList aria-label="Result sections">{[['analysis','Analysis',BarChart3,'maroon'],['progress','Progress',TrendingUp,'amber'],['accuracy','Confidence',Target,'emerald'],['rank',r.exam==='BITSAT'?'Branch matches':'Real-exam rank',Trophy,'sapphire'],['solutions','Solutions',BookOpen,'crimson']].map(([value,label,Icon,tone])=><TabsTrigger key={value} value={value} className={'tone-'+tone} data-testid={'result-view-'+value}><Icon size={16}/>{label}</TabsTrigger>)}</TabsList><ReportButton key={`${id}-${scoreVersion}`} id={id} scoreVersion={scoreVersion} answerKeyOnly={r.questions.every(q=>q.solution_kind==='answer_key_only')} /></Tabs>
      <section className="result-view-panel" hidden={view!=='analysis'} data-testid="result-analysis-panel" aria-label="Result analysis">
      <MeterShortcuts exam={r.exam} journey={meters.journey} rank={meters.rank} onView={changeView}/>
      <MockSectionScores s={s} />
      <ResultAnalysis r={r} cohort={extras.cohort} peer={extras.peer} onOpen={openQuestion} />
      <div className="result-metrics">
        <div>
          <span>Attempt rate</span>
          <strong>
            {s.attempt_rate === null ? "Not applicable" : s.attempt_rate + "%"}
          </strong>
          <small>
            {s.attempted} / {s.eligible_count ?? r.count} eligible questions
          </small>
        </div>
        <div>
          <span>Attempted accuracy</span>
          <strong>
            {s.accuracy === null ? "Not applicable" : s.accuracy + "%"}
          </strong>
          <small>Correct ÷ attempted (excludes dropped/bonus)</small>
        </div>
        <div>
          <span>Penalty marks</span>
          <strong>{s.penalties}</strong>
          <small>Marks lost to wrong answers</small>
        </div>
        <div>
          <span>Total elapsed time</span>
          <strong>
            {Math.floor(s.total_seconds / 60)}m {s.total_seconds % 60}s
          </strong>
          <small>Includes time away; per-question timing unavailable</small>
        </div>
      </div>
      <div className="summary-tables">
        <section className="card">
          <h3>By subject</h3>
          {Object.entries(s.subjects).map(([name, d]) => (
            <div className="subject-result" key={name}>
              <span>{name}</span>
              <strong>{d.score} marks</strong>
              <small>
                {d.correct} correct / {d.attempted} attempted
              </small>
              <div className="subject-track">
                <span style={{ width: (100 * d.correct) / d.count + "%" }} />
              </div>
            </div>
          ))}
        </section>
        <section className="card">
          <h3>A clearer next step.</h3>
          <p>
            {r.questions.every(q=>q.solution_kind==='answer_key_only')?'Compare each missed question with the supplied key; this book has no worked explanations.':'Review the explanation beside each missed question.'} Then try a separate, untimed revision attempt.
          </p>
          <button
            className="btn btn-secondary"
            data-testid="results-retry-mistakes"
            disabled={!s.incorrect && !s.skipped}
            onClick={() => setRetryOpen(true)}
          >
            <RotateCcw size={17} /> Retry incorrect & skipped
          </button>
          <small>
            Repeated exposure is revision—not a new readiness estimate.
          </small>
          <details>
            <summary data-testid="topic-summary-toggle">
              Topic summary ({Object.keys(s.topics).length})
            </summary>
            {Object.entries(s.topics).map(([name, d]) => (
              <p className="topic-result" key={name}>
                <span>{name}</span>
                <strong>
                  {d.correct}/{d.count} correct · {d.score} marks
                </strong>
              </p>
            ))}
          </details>
        </section>
      </div>
      {r.insights && <section className="import-card mb-8" data-testid="results-evidence-insights"><div className="import-section-label">YOUR NEXT STUDY SESSION</div><h2>Start where this attempt points.</h2><div className="insight-grid">{r.insights.priorities.length ? r.insights.priorities.map((g,i) => <article className="import-issue" data-testid={'results-priority-' + i} key={g.label}><strong>{g.label}</strong><p>{g.incorrect} incorrect · {g.skipped} skipped · {g.count} questions</p><p>Attempted accuracy: {g.accuracy === null ? 'Not available' : g.accuracy + '%'} ({g.correct}/{g.attempted})</p><p>{g.action}</p><small>{g.evidence} · Review Q{g.questions.join(', Q')}</small></article>) : <p data-testid="results-no-priorities">No incorrect or skipped eligible questions in this attempt. Use fresh questions to gather more evidence.</p>}</div><p className="import-fineprint mt-4" data-testid="results-insights-basis">{r.insights.basis}</p></section>}
      <details className="advanced-analysis" data-testid="advanced-result-analysis"><summary data-testid="advanced-result-analysis-toggle">Deeper review tools · decisions, revision & study plan</summary><ResultsAnalyticsWorkspace key={`${id}-${scoreVersion}`} analysis={r.analytics} questions={r.questions} userId={user.id} attemptId={id} onOpenQuestion={openQuestion} onRefresh={refreshAnalytics} confidenceThreshold={confidenceThreshold} review={r.review} /></details>
      </section>
      {view==='progress'&&<JourneyView data={meters.journey} retry={meters.retry}/>}
      {view==='accuracy'&&<ConfidenceView data={meters.journey} retry={meters.retry} latestAccuracy={s.accuracy}/>}
      {view==='rank'&&(r.exam==='BITSAT'?<BitsatBranchView key={`${id}-${scoreVersion}`} data={meters.rank} retry={meters.retry}/>:<HistoricalRankView data={meters.rank} cohort={extras.cohort} retry={meters.retry}/>)}
      {view === 'solutions' && <section className="result-view-panel" data-testid="result-solutions-panel" aria-label="Question solutions">
      <SolutionNavigator subjects={subjects} subject={activeSubject} questions={qs} allQuestions={allQuestions} filter={filter} selected={activeQuestion?.id} onSubject={chooseSubject} onQuestion={openQuestion}/>
      <div className="review-heading" id="results-review-heading">
        <div>
          <span className="eyebrow">UNDERSTAND THE WHY</span>
          <h2 data-testid="solution-review-heading">One question. A clearer understanding.</h2>
        </div>
        <span data-testid="solution-current-question-label">{activeQuestion ? `${activeSubject} · Question ${activeQuestion.number}` : 'Choose another filter'}</span>
      </div>
      <div className="filter-tabs" data-testid="results-filter-tabs">
        {[
          ["all", "All questions"],
          ["incorrect", "Incorrect"],
          ["skipped", "Skipped"],
          ["correct", "Correct"],
          ["marked", "Marked for review"],
          ["dropped", "Dropped"],
          ["bonus", "Bonus-to-all"],
          ...(s.sections ? [["bonus-section", "Bonus section"]] : []),
        ].map(([v, l]) => (
          <button
            data-testid={"results-filter-" + v}
            className={filter === v ? "active" : ""}
            key={v}
            aria-pressed={filter === v}
            onClick={() => setFilter(v)}
          >
            {l}
          </button>
        ))}
      </div>
      {activeQuestion ? (
        [activeQuestion].map((q) => (
          <article
            className="card review-question focused-solution-card"
            id={'review-question-'+q.id}
            data-testid="results-question-review-item"
            key={q.id}
          >
            <div className="review-question-toggle" data-testid={'solution-question-heading-' + q.number}>
              <span className={"outcome-icon " + q.outcome}>
                {q.outcome === "correct" ? (
                  <CheckCircle2 />
                ) : q.outcome === "incorrect" ? (
                  <XCircle />
                ) : (
                  <MinusCircle />
                )}
              </span>
              <span>
                <strong>Question {q.number}</strong>
                <small>
                  {q.subject} ·{" "}
                  {q.type === "integer" ? "Integer answer" : "Single correct"}
                </small>
              </span>
              <Badge
                tone={
                  q.outcome === "correct"
                    ? "green"
                    : q.outcome === "incorrect"
                      ? "red"
                      : "neutral"
                }
              >
                {q.outcome}
              </Badge>
              <strong className="review-marks">
                {q.marks > 0 ? "+" : ""}
                {q.marks} marks
              </strong>
            </div>
              <div className="review-expanded" data-testid="selected-question-solution-panel" aria-label={'Question ' + q.number + ' and solution'}>
                <QuestionContent
                  question={q}
                  base={`/attempts/${id}/questions/${q.id}`}
                  gradeVersion={scoreVersion}
                />
                {q.render_mode !== "source" && q.type === "mcq" && (
                  <div className="review-options">
                    {Object.entries(q.options).map(([k, v]) => (
                        <div key={k} className="review-option-math" data-testid={'review-option-' + q.number + '-' + k}>
                          <strong>{k}.</strong> <MathText text={v} />
                        </div>
                    ))}
                  </div>
                )}
                <div className="response-comparison">
                  <div>
                    <span>Your response</span>
                    <strong>{q.response || "Unanswered"}</strong>
                  </div>
                  <div>
                    <span>Accepted answer(s)</span>
                    <strong>
                      {(q.accepted_answers || [q.answer]).join(", ")}
                    </strong>
                  </div>
                  <div>
                    <span>Awarded marks</span>
                    <strong>{q.marks}</strong>
                  </div>
                  {q.marked && (
                    <Badge>
                      <Flag size={13} /> Marked for review
                    </Badge>
                  )}
                </div>
                <section data-testid={'solution-content-'+q.number} aria-label={'Solution for question '+q.number}>
                {(q.solution_kind==='answer_key_only'||q.solution||q.s_refs?.length||q.solution_accessible_text)&&<div className="matched-solution">
                  <div className="solution-title"><FileIcon/><h3>{q.solution_kind==='answer_key_only'?'Supplied answer key':q.solution_kind==='ai_generated'?'AI-generated explanation':'Supplied solution'} · Q{q.solution_number??q.number}</h3><Badge>Matched to this frozen version</Badge></div>
                  {q.solution_kind==='answer_key_only'&&<p className="import-fineprint" data-testid={'no-worked-solution-'+q.number}>{extras.ai[q.id]?.state==='ready'?'The source provides this key only. An AI generated step-by-step solution is shown below.':'The source provides this key only. No worked solution was supplied.'}</p>}
                  <QuestionContent question={q} solution base={`/attempts/${id}/questions/${q.id}`} gradeVersion={scoreVersion}/>
                </div>}
                {(!['ai_generated','supplied_worked'].includes(q.solution_kind)||(!q.solution&&!q.s_refs?.length)||extras.ai[q.id]?.state==='ready')&&<AiSolution item={extras.ai[q.id]} number={q.number}/>}
                </section>
                <PeerQuestionStat p={extras.peer[q.id]} number={q.number} />
                <div className="ledger-meta">
                  Scoring reason: {q.reason_code} · Exact marks: {q.marks_exact}{" "}
                  · Key version: {q.key_version}
                  <br />
                  {q.accepted_at
                    ? "Response acknowledged " +
                      new Date(q.accepted_at * 1000).toLocaleString()
                    : "No response acknowledged"}
                  {q.review_note && <p>Reviewer note: {q.review_note}</p>}
                </div>
                {solutionState[q.id]==='error'&&<div className="import-error" role="alert" data-testid={'solution-record-error-'+q.number}>Your solution is visible, but the review step could not be recorded. <Button variant="outline" onClick={()=>recordSolution(q.id)} data-testid={'solution-record-retry-'+q.number}>Retry review tracking</Button></div>}
                <ResultsReflectionStrip key={`${q.id}-${scoreVersion}`} attemptId={id} question={q} scoreVersion={scoreVersion}
                  state={r.review?.states?.[q.id]} categories={r.review?.categories} assigned={r.review?.assigned?.includes(q.id)}
                  confidence={r.confidence_observations?.[q.id]?.probability} excluded={r.confidence_changed_questions?.includes(q.id)}
                  solutionPending={solutionState[q.id]!=='saved'} onSaved={refreshAnalytics}/>
                <QuestionReport key={"solution-report-"+q.id} attemptId={id} questionId={q.id} number={q.number} context="solutions" />
              </div>
          </article>
        ))
      ) : (
        <Empty title="No questions in this filter.">
          Try another outcome to continue your review.
        </Empty>
      )}
      </section>}
      <div className="receipt">
        <CheckCircle2 size={17} />
        <span>
          Submission receipt: <code>{r.receipt}</code>
          <br />
          {new Date(r.submitted_at * 1000).toLocaleString()} ·{" "}
          {r.reason === "time_limit"
            ? "Time limit reached"
            : "Submitted by you"}{" "}
          · Content version {r.version}
        </span>
      </div>
      <Confirm
        open={retryOpen}
        onClose={() => setRetryOpen(false)}
        title="Turn mistakes into revision."
        button="Start untimed retry"
        onConfirm={retry}
        busy={busy}
      >
        <p>
          Create a separate attempt with {s.incorrect + s.skipped} incorrect or
          skipped questions. Your original score and report will not change.
        </p>
        <p>
          This set is untimed. Its maximum marks reflect only the selected
          questions; it is not another full-paper simulation.
        </p>
      </Confirm>
    </div></QuestionReportsProvider>
  );
}
function FileIcon() {
  return <CheckCircle2 size={19} />;
}
