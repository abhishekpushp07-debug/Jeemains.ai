import { examPath, safeExamReturn } from '../lib/exams';
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Flag,
  Check,
  CheckCircle2,
  CloudOff,
  Clock3,
  Send,
  Loader2,
  RotateCcw,
  ChevronDown,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import { Logo, Loading, ErrorBox, Badge, Confirm } from "../components/Shared";
import { QuestionContent, MathText } from "../components/QuestionContent";
import { useAttempt } from "./practice/useAttempt";
import { PlayerConfidencePanel } from '../components/player/PlayerConfidencePanel';
import { BonusGate, BonusConfirm } from '../components/player/BonusGate';
import {QuestionReport, QuestionReportsProvider} from '../components/QuestionReport';
import { useLocation, useNavigate } from 'react-router-dom';
import {Button} from '../components/ui/button';
import {Input} from '../components/ui/input';

export default function Player() {
  const { id } = useParams();
  const nav = useNavigate();
  const location = useLocation();
  const [exitOpen, setExitOpen] = useState(false);
  const { user } = useAuth();
  const {
    attempt: a,
    pending,
    error,
    setError,
    saving,
    online,
    seconds,
    conflict,
    load,
    edit,
    confidencePreferences,
    chooseConfidence,
    visit,
    discard,
    submit,
    enterBonus,
  } = useAttempt(id, user);
  const [index, setIndex] = useState(0),
    [confirm, setConfirm] = useState(false),
    [submitting, setSubmitting] = useState(false),
    [navOpen, setNavOpen] = useState(false),
    [blocked, setBlocked] = useState({}),
    [bonusConfirm, setBonusConfirm] = useState(false),
    [enteringBonus, setEnteringBonus] = useState(false);
  const bonusRule = a?.rules?.bonus_rule;
  const bonusOpen = !!a?.bonus_unlocked_at;
  const qs = !a ? [] : bonusRule ? a.questions.filter((x) => !!x.bonus === bonusOpen) : a.questions;
  const q = qs[index] || qs[0];
  const questionId = q?.id;
  useEffect(() => {
    if(!a)return;
    try { setIndex(Math.max(0,Math.min(qs.length-1,Number(sessionStorage.getItem(`test-question-${id}-${bonusOpen}`))||0))); }
    catch { setIndex(0); }
  }, [a?.id, bonusOpen]);
  useEffect(()=>{if(a&&qs.length)try{sessionStorage.setItem(`test-question-${id}-${bonusOpen}`,String(index))}catch{}},[id,a?.id,bonusOpen,index]);
  useEffect(() => {
    if (questionId) visit(questionId);
  }, [questionId, visit, online]);
  useEffect(() => {
    if (!a || !q) return;
    function shortcut(e) {
      if (e.repeat || e.altKey || e.ctrlKey || e.metaKey || e.isComposing || confirm || bonusConfirm || navOpen || document.querySelector('[role="dialog"]')) return;
      if (e.target.closest('input, textarea, select, button, a, canvas, [contenteditable="true"], [role="slider"], [role="radio"], [role="tab"]')) return;
      const key=e.key.toUpperCase();
      if (key==='ARROWRIGHT' || key==='ARROWLEFT') {
        e.preventDefault();setIndex(i=>Math.max(0,Math.min(qs.length-1,i+(key==='ARROWRIGHT'?1:-1))));return;
      }
      if (seconds===0 || conflict || Object.keys(blocked).some(k=>k.startsWith(q.id+':'))) return;
      const response=pending[q.id]||a.answers[q.id]||{};
      if (q.type==='mcq' && Object.hasOwn(q.options||{},key)) {e.preventDefault();edit(q.id,{value:key});}
      if (key==='M') {e.preventDefault();edit(q.id,{marked:!response.marked});}
    }
    document.addEventListener('keydown',shortcut);
    return()=>document.removeEventListener('keydown',shortcut);
  },[a,q,qs.length,pending,seconds,conflict,blocked,confirm,bonusConfirm,navOpen,edit]);

  async function doEnterBonus() {
    setEnteringBonus(true);
    try {
      await enterBonus();
      setBonusConfirm(false);
    } catch (e) {
      setError(e.message);
      setBonusConfirm(false);
    } finally {
      setEnteringBonus(false);
    }
  }

  async function doSubmit() {
    setSubmitting(true);
    try {
      await submit();
    } catch (e) {
      setError(e.message);
      setConfirm(false);
    } finally {
      setSubmitting(false);
    }
  }
  if (!a || !q)
    return (
      <div className="container page">
        <ErrorBox error={error} retry={load} />
        {!error && <Loading />}
      </div>
    );
  const current = pending[q.id] || a.answers[q.id] || {},
    all = { ...a.answers, ...pending };
  const committed = a.questions.filter((x) =>
    String(a.answers[x.id]?.value || "").trim(),
  ).length;
  const mainCommitted = bonusRule ? a.questions.filter((x) => !x.bonus && String(a.answers[x.id]?.value || "").trim()).length : 0;
  const sectionCommitted = qs.filter((x) => String(a.answers[x.id]?.value || "").trim()).length;
  const gate = bonusRule && <BonusGate rule={bonusRule} open={bonusOpen} answered={mainCommitted} pending={nPendingCount(pending)} ended={seconds === 0} online={online} onEnter={() => setBonusConfirm(true)} />;
  const marked = qs.filter((x) => all[x.id]?.marked).length,
    nPending = Object.keys(pending).length;
  const time =
    seconds === null
      ? "Untimed"
      : `${Math.floor(seconds / 3600)
          .toString()
          .padStart(2, "0")}:${Math.floor((seconds % 3600) / 60)
          .toString()
          .padStart(2, "0")}:${(seconds % 60).toString().padStart(2, "0")}`;
  const assetBlocked = Object.keys(blocked).some((k) =>
    k.startsWith(q.id + ":"),
  );
  const locked = seconds === 0 || conflict || assetBlocked;
  function assetState(i, failed) {
    setBlocked((old) => {
      const b = { ...old };
      if (failed) b[q.id + ":" + i] = true;
      else delete b[q.id + ":" + i];
      return b;
    });
  }
  return (
    <QuestionReportsProvider attemptId={id}><div className="player-layout">
      <header className="player-header">
        <div onClickCapture={e=>{e.preventDefault();setExitOpen(true)}}><Logo testId="player-logo" /></div>
        <div className="player-title">
          <strong>{a.title}</strong>
          <span>
            {a.exam} ·{" "}
            {a.mode === "preview"
              ? "Unapproved private preview"
              : a.mode === "retry"
                ? "Untimed revision · repeated exposure"
                : "Nonofficial practice"}
          </span>
        </div>
        <span className="player-light-label" data-testid="player-light-mode">Light exam view</span>
        <div
          className={
            "player-timer " +
            (seconds !== null && seconds < 300 ? "urgent" : "")
          }
        >
          <Clock3 size={18} />
          <span data-testid="player-timer">{time}</span>
        </div>
      </header>
      <div className="player-savebar">
        <Button variant="link" onClick={()=>setExitOpen(true)} data-testid="player-home">
          <ArrowLeft size={14} /> Leave test
        </Button>
        <span
          data-testid="player-save-state-indicator"
          role="status"
          className={nPending ? "pending" : "saved"}
        >
          {!online ? (
            <CloudOff size={16} />
          ) : saving ? (
            <Loader2 size={16} className="spin" />
          ) : (
            <CheckCircle2 size={16} />
          )}{" "}
          {!online
            ? `Offline · ${nPending} pending`
            : saving
              ? "Saving…"
              : nPending
                ? `${nPending} pending · not yet acknowledged`
                : "All responses saved"}
        </span>
        <span className="player-progress">
          {bonusRule ? `${sectionCommitted} / ${qs.length} saved answers · ${bonusOpen ? "Bonus section" : "Main section"}` : `${committed} / ${a.count} saved answers`}
        </span>
      </div>
      <p className="compact-practice-note">
        Compact mobile practice · Server time controls the deadline
      </p>
      <div className="player-body">
        <aside className={"question-navigator " + (navOpen ? "open" : "")}>
          <Button variant="ghost"
            className="navigator-heading"
            data-testid="player-navigator-toggle"
            onClick={() => setNavOpen(!navOpen)}
            aria-expanded={navOpen}
          >
            <strong>Question navigator</strong>
            <ChevronDown size={18} />
          </Button>
          <div className="navigator-content">
            {Array.from(new Set(qs.map((x) => x.subject))).map(
              (subject) => (
                <div className="nav-subject" key={subject}>
                  <h4>{subject}</h4>
                  <div className="number-grid">
                    {qs.map((x, i) =>
                      x.subject !== subject ? null : (
                        <Button variant="ghost"
                          key={x.id}
                          data-testid={"player-question-nav-" + x.number}
                          className={
                            (index === i ? "current " : "") +
                            (all[x.id]?.value?.trim() ? "answered " : "") +
                            (all[x.id]?.marked ? "marked " : "") +
                            (a.visited?.includes(x.id) ? "visited " : "") +
                            (pending[x.id] ? "pending-answer" : "")
                          }
                          aria-label={`Question ${x.number}, ${all[x.id]?.value?.trim() ? "answered" : a.visited?.includes(x.id) ? "visited, unanswered" : "not visited"}${all[x.id]?.marked ? ", marked for review" : ""}${pending[x.id] ? ", pending save" : ""}`}
                          aria-current={index === i ? "step" : undefined}
                          onClick={() => {
                            setIndex(i);
                            setNavOpen(false);
                          }}
                        >
                          {x.number}
                          {all[x.id]?.marked ? (
                            <Flag size={8} />
                          ) : all[x.id]?.value?.trim() ? (
                            <Check size={9} />
                          ) : null}
                        </Button>
                      ),
                    )}
                  </div>
                </div>
              ),
            )}
            <div className="nav-legend">
              <span>
                <i />
                Not visited
              </span>
              <span>
                <i className="legend-visited" />
                Visited · blank
              </span>
              <span>
                <i className="legend-answered" />✓ Answered
              </span>
              <span>
                <i className="legend-marked" />⚑ For review
              </span>
              <span>
                <i className="legend-both" />✓ + ⚑ Both
              </span>
              <span>
                <i className="legend-pending" />
                Pending save
              </span>
            </div>
            {gate}
            <Button variant="ghost"
              className="btn btn-primary full-width"
              data-testid="player-submit-button"
              onClick={() => setConfirm(true)}
              disabled={seconds === 0 || !online}
            >
              <Send size={17} /> Review & submit
            </Button>
            <p className="navigator-note">
              Free navigation · Original order preserved. Skipped questions
              receive 0 marks.
            </p>
          </div>
        </aside>
        <section className="player-question-area">
          <ErrorBox error={error} />
          {bonusRule && <div className="bonus-gate-inline">{React.cloneElement(gate, { testId: 'player-bonus-gate-inline' })}</div>}
          {conflict && (
            <div className="notice amber">
              <span>
                Another saved version exists. Local drafts are retained until
                you choose to discard them.
              </span>
              <Button variant="ghost"
                className="btn btn-secondary"
                data-testid="discard-conflicting-drafts"
                onClick={discard}
              >
                Use server-saved answers
              </Button>
            </div>
          )}
          {seconds === 0 && (
            <div className="notice amber">
              Time has ended. Pending drafts cannot be scored. Reconnect to
              retrieve your result.
            </div>
          )}
          <article className="card question-card">
            <div className="question-topline">
              <Badge>{q.subject}</Badge>
              <span>
                {q.type === "integer" ? "Integer answer" : "Single correct"} · +
                {a.rules.correct} / {a.rules.wrong}
              </span>
            </div>
            <div className="question-heading">
              <h2 data-testid="player-question-heading">Question {q.number}</h2>
              <Button variant="ghost"
                className={
                  "btn btn-quiet " + (current.marked ? "review-active" : "")
                }
                data-testid="player-mark-review-toggle"
                aria-pressed={!!current.marked}
                disabled={locked}
                onClick={() => edit(q.id, { marked: !current.marked })}
              >
                <Flag size={17} />
                {current.marked ? "Marked for review" : "Mark for review"}
              </Button>
            </div>
            <div data-testid="player-question-stem">
              <QuestionContent
                question={q}
                readable
                base={`/attempts/${id}/questions/${q.id}`}
                onAssetError={(i) => assetState(i, true)}
                onAssetLoad={(i) => assetState(i, false)}
              />
            </div>
            {assetBlocked && (
              <div className="notice amber">
                A required source image did not load. Retry it above before
                answering; do not guess missing content.
              </div>
            )}
            {q.type==='mcq'&&q.render_mode==='source'&&<p className="source-options-hint" data-testid="player-source-options-hint">Read options A–D in the original image above, then select the matching letter.</p>}
            <fieldset disabled={locked} className="answer-fieldset">
              <legend>
                {q.type === "mcq"
                  ? "Select one answer"
                  : "Enter your integer answer"}
              </legend>
              {q.type === "mcq" ? (
                <div className={'answer-options ' + (q.render_mode==='source'?'answer-options-source':'')}>
                  {Object.entries(q.options || {}).map(([key, value]) => (
                    <label
                      key={key}
                      className={
                        "answer-option " +
                        (current.value === key ? "selected" : "")
                      }
                    >
                      <input
                        type="radio"
                        name={q.id}
                        value={key}
                        checked={current.value === key}
                        onChange={() => edit(q.id, { value: key })}
                        data-testid={"player-option-" + key}
                      />
                      <span className="option-index">{key}</span>
                      <div className="option-copy" data-testid={'player-option-math-' + key}>
                        {q.render_mode === 'source'
                          ? `Option ${key} (as shown above)`
                          : <MathText text={value} />}
                      </div>
                      {current.value === key && (
                        <span className="selected-tick">
                          <Check size={16} />
                        </span>
                      )}
                    </label>
                  ))}
                </div>
              ) : (
                <>
                  <Input
                    className="numerical-input"
                    type="text"
                    inputMode="text"
                    aria-label="Integer answer"
                    data-testid="player-numerical-input"
                    placeholder="e.g. 13440"
                    maxLength={30}
                    value={current.value || ""}
                    onChange={(e) => edit(q.id, { value: e.target.value })}
                  />
                  <p className="input-hint">
                    Exact integer. Zero, negatives, leading zeros and five-digit
                    answers are accepted. No decimal rounding.
                  </p>
                </>
              )}
            </fieldset>
            <Button variant="ghost"
              className="text-button clear-answer"
              data-testid="player-clear-response-button"
              disabled={!current.value || locked}
              onClick={() => edit(q.id, { value: "" })}
            >
              <RotateCcw size={14} /> Clear response
            </Button>
            <QuestionReport key={"report-"+q.id} attemptId={id} questionId={q.id} number={q.number} context="attempt" />
            <PlayerConfidencePanel
              key={q.id}
              questionId={q.id}
              preference={confidencePreferences[q.id]}
              observation={a.confidence_observations?.[q.id]}
              changed={a.confidence_changed_questions?.includes(q.id)}
              answerChosen={!!String(current.value || '').trim()}
              disabled={locked}
              onSave={chooseConfidence}
              online={online}
            />
            <div className="question-navigation">
              <Button variant="ghost"
                className="btn btn-secondary"
                data-testid="player-previous"
                disabled={index === 0}
                onClick={() => setIndex(index - 1)}
              >
                <ArrowLeft size={17} /> Previous
              </Button>
              <span>
                {index + 1} of {qs.length}
              </span>
              {index < qs.length - 1 ? (
                <Button variant="ghost"
                  className="btn btn-primary"
                  data-testid="player-next"
                  onClick={() => setIndex(index + 1)}
                >
                  Next question <ArrowRight size={17} />
                </Button>
              ) : (
                <Button variant="ghost"
                  className="btn btn-primary"
                  data-testid="player-finish"
                  disabled={seconds === 0 || !online}
                  onClick={() => setConfirm(true)}
                >
                  Review & submit <Send size={17} />
                </Button>
              )}
            </div>
            <div className="player-shortcuts" data-testid="player-shortcuts-help"><span><kbd>←</kbd> <kbd>→</kbd> Navigate</span><span><kbd>A–D</kbd> Answer</span><span><kbd>M</kbd> Mark for review</span><span>Shortcuts pause while a control has focus.</span></div>
          </article>
          <p className="practice-note">
            Focus on the question. This is home practice, not a proctored
            examination or an official readiness prediction.
          </p>
        </section>
      </div>
      <Confirm
        open={confirm}
        onClose={() => setConfirm(false)}
        title="Ready to submit your attempt?"
        button="Submit & see results"
        busy={submitting}
        onConfirm={doSubmit}
      >
        <p>
          Submission is final. {a.mode==='series_live'?'Your result and solutions unlock at 11:59 PM IST after today’s live window closes.':'Your result and available solutions are released afterward.'}
        </p>
        <div className="submission-stats">
          <span>
            <strong>{committedOrDraft(a, all)}</strong>Answered
          </span>
          <span>
            <strong>{a.count - committedOrDraft(a, all)}</strong>Unanswered
          </span>
          <span>
            <strong>{marked}</strong>For review
          </span>
        </div>
        <p>
          <strong>{nPending}</strong> unsaved draft(s). {committed} answers are
          currently acknowledged by the server.
        </p>
        {nPending > 0 && (
          <p className="warning-text">
            Pending responses must be acknowledged before submission. Invalid
            integer drafts need correction.
          </p>
        )}
        <p>
          Unanswered questions earn 0 marks. Marked questions are scored using
          their saved response.
        </p>
      </Confirm>
      {bonusRule && <BonusConfirm open={bonusConfirm} onClose={() => setBonusConfirm(false)} onConfirm={doEnterBonus} busy={enteringBonus} rule={bonusRule} marking={a.rules} />}
      <Confirm open={exitOpen} onClose={()=>setExitOpen(false)} title="Leave this test for now?" button="Leave test" onConfirm={()=>nav(safeExamReturn(location.state?.returnTo,a.series_id?'/series/all-india-jee':examPath(a.exam)+'/results'))}>
        <p>Your original timer keeps running. Server-saved answers remain; {nPending} local draft(s) are not yet acknowledged. Resume this same attempt from My Tests.</p>
      </Confirm>
    </div></QuestionReportsProvider>
  );
}

const nPendingCount = (pending) => Object.keys(pending).length;
const committedOrDraft = (a, all) => a.questions.filter((x) => String(all[x.id]?.value || "").trim()).length;
