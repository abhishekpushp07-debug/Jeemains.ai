import { examPath } from '../lib/exams';
import React, { useEffect, useState } from "react";
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
  ChevronDown,
  ShieldCheck,
  ArrowUpRight,
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
import { Button } from '../components/ui/button';
export default function Results() {
  const { id } = useParams();
  const { user } = useAuth();
  const [params] = useSearchParams();
  const scoreVersion = params.get("score_version") || "original";
  const nav = useNavigate();
  const [r, setR] = useState(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [retryOpen, setRetryOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [expanded, setExpanded] = useState({});
  const [page, setPage] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [pending, setPending] = useState(null);
  const [focusQuestion,setFocusQuestion] = useState(null);
  const [solutionState,setSolutionState] = useState({});
  const [confidenceThreshold,setConfidenceThreshold] = useState(0.2);
  useEffect(()=>{
    if (!focusQuestion) return;
    const timer=setTimeout(()=>{document.getElementById('review-question-'+focusQuestion)?.scrollIntoView({block:'start',behavior:'instant'});setFocusQuestion(null)},220);
    return()=>clearTimeout(timer);
  },[focusQuestion]);
  async function refreshAnalytics(threshold = confidenceThreshold) {
    const result=await api('/attempts/'+id+'/results?score_version='+encodeURIComponent(scoreVersion)+'&confidence_threshold='+threshold);
    if(result.analytics) { setR(result); setConfidenceThreshold(threshold); }
    return result;
  }
  async function recordSolution(qid) {
    setSolutionState(old=>({...old,[qid]:'pending'}));
    try { await post(`/attempts/${id}/questions/${qid}/solution-open`,{}); setSolutionState(old=>({...old,[qid]:'saved'})); }
    catch { setSolutionState(old=>({...old,[qid]:'error'})); }
  }
  function openQuestion(qid) {
    if(!r)return;
    setFilter('all');setPage(Math.ceil((r.questions.findIndex(q=>q.id===qid)+1)/10));setExpanded(old=>({...old,[qid]:true}));setFocusQuestion(qid);
    recordSolution(qid);
  }
  useEffect(() => {
    const controller = new AbortController();
    let timer, polls = 0;
    setR(null); setPending(null); setError(''); setExpanded({}); setPage(1);
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
  if (pending?.status === 'embargoed') return <div className="container page" data-testid="results-embargoed"><PageTitle eyebrow="SUBMISSION RECEIVED" title="Your answers are sealed." description={pending.title} /><section className="import-card"><h2>A fair window for everyone.</h2><p className="import-muted" data-testid="results-release-time">Your results, solutions and PDF report unlock at {new Date(pending.release_at * 1000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST, after the competition closes.</p><p className="import-fineprint mt-4" data-testid="results-embargo-receipt">Submission receipt: {pending.receipt}</p><div className="flex flex-wrap gap-3 mt-6"><Button data-testid="results-release-refresh" onClick={() => setRefresh(v => v + 1)}>Check results</Button><Button asChild variant="outline"><Link data-testid="results-competition-hub" to="/competitions">Competition hub</Link></Button></div></section></div>;
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
  const qs = r.questions.filter(
    (q) =>
      filter === "all" ||
      (filter === "marked" ? q.marked : filter === "bonus-section" ? q.bonus : q.outcome === filter),
  );
  const lateKey = `tejas-draft-${user.id}-${id}`;
  let late = {};
  try {
    late = JSON.parse(localStorage.getItem(lateKey) || "{}");
  } catch {}
  return (
    <div className="container page results-page">
      <Link className="breadcrumb" to={examPath(r.exam)+'/results'} data-testid="results-home">
        <ArrowLeft size={14} /> All {r.exam} results
      </Link>
      <PageTitle
        eyebrow={`${r.exam} · ${r.mode === "preview" ? "UNAPPROVED PRIVATE PREVIEW" : "COMPLETED PRACTICE"}`}
        title="Every answer has a next step."
        description={r.title}
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
              onClick={() => nav("/results/" + id)}
            >
              Original score
            </button>
            {r.grade_versions.map((g) => (
              <button
                key={g.id}
                className="btn btn-secondary"
                data-testid={"score-version-" + g.key_version}
                disabled={scoreVersion === g.id}
                onClick={() =>
                  nav(
                    "/results/" +
                      id +
                      "?score_version=" +
                      encodeURIComponent(g.id),
                  )
                }
              >
                Key version {g.key_version} ·{" "}
                {new Date(g.created_at * 1000).toLocaleDateString()}
              </button>
            ))}
          </div>
        </section>
      )}
      <div className="results-review-shortcuts" data-testid="results-review-shortcuts"><p data-testid="results-attempt-immutable-notice"><ShieldCheck size={16}/> Your submitted answers are sealed. Review notes won’t change your score.</p><Button variant="outline" data-testid="results-jump-review" onClick={()=>document.getElementById('results-review-heading')?.scrollIntoView({behavior:'instant'})}>Review answers <ArrowUpRight size={16}/></Button></div>
      {r.questions.every(q=>q.solution_kind==='answer_key_only')&&<p className="results-key-notice" data-testid="results-answer-keys-only-disclosure">Answer keys only. Original questions and supplied keys are available below; worked solutions were not provided.</p>}
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
      <MockSectionScores s={s} />
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
      <div className="results-actionbar">
        <div>
          <h3>Your full attempt, yours to keep.</h3>
          <p>
            {r.questions.every(q=>q.solution_kind==='answer_key_only')?'The PDF includes every original question, your response and its supplied answer key. No worked solutions were provided.':'The PDF includes every question and solution—even if you filter the review below.'}
          </p>
        </div>
        <ReportButton key={`${id}-${scoreVersion}`} id={id} scoreVersion={scoreVersion} answerKeyOnly={r.questions.every(q=>q.solution_kind==='answer_key_only')} />
      </div>
      <p className="report-privacy">
        <ShieldCheck size={14} /> A downloaded copy is outside jeemains.ai access
        controls. Use it for permitted personal study only.
      </p>
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
      <ResultsAnalyticsWorkspace key={`${id}-${scoreVersion}`} analysis={r.analytics} questions={r.questions} userId={user.id} attemptId={id} onOpenQuestion={openQuestion} onRefresh={refreshAnalytics} confidenceThreshold={confidenceThreshold} review={r.review} />
      <div className="review-heading" id="results-review-heading">
        <div>
          <span className="eyebrow">UNDERSTAND THE WHY</span>
          <h2>Your question-by-question review.</h2>
        </div>
        <span>{qs.length} questions</span>
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
            onClick={() => {
              setFilter(v);
              setPage(1);
            }}
          >
            {l}
          </button>
        ))}
      </div>
      {qs.length ? (
        qs.slice(0, page * 10).map((q) => (
          <article
            className="card review-question"
            id={'review-question-'+q.id}
            data-testid="results-question-review-item"
            key={q.id}
          >
            <button
              className="review-question-toggle"
              data-testid={"results-expand-" + q.number}
              aria-expanded={!!expanded[q.id]}
              onClick={() => expanded[q.id] ? setExpanded({...expanded,[q.id]:false}) : openQuestion(q.id)}
            >
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
              <ChevronDown
                className={expanded[q.id] ? "rotate" : ""}
                size={18}
              />
            </button>
            {expanded[q.id] && (
              <div className="review-expanded">
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
                <div className="matched-solution">
                  <div className="solution-title">
                    <FileIcon />
                    <h3>{q.solution_kind==='answer_key_only'?'Supplied answer key':'Matched solution'} · Q{q.solution_number}</h3>
                    {q.solution_kind==='answer_key_only'&&<p className="import-fineprint" data-testid={'no-worked-solution-'+q.number}>The source provides this key only. No worked solution was supplied or generated.</p>}
                    <Badge>Matched to this frozen version</Badge>
                  </div>
                  <QuestionContent
                    question={q}
                    solution
                    base={`/attempts/${id}/questions/${q.id}`}
                    gradeVersion={scoreVersion}
                  />
                </div>
              </div>
            )}
          </article>
        ))
      ) : (
        <Empty title="No questions in this filter.">
          Try another outcome to continue your review.
        </Empty>
      )}
      {qs.length > page * 10 && (
        <button
          className="btn btn-secondary full-width"
          data-testid="results-load-more"
          onClick={() => setPage(page + 1)}
        >
          Show 10 more questions
        </button>
      )}
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
    </div>
  );
}
function FileIcon() {
  return <CheckCircle2 size={19} />;
}
