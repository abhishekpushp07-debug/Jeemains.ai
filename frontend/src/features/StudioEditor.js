import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Upload,
  FileText,
  CheckCircle2,
  ShieldCheck,
  Eye,
  Save,
  Plus,
  RefreshCw,
  ArrowRight,
  Scissors,
  Trash2,
  Loader2,
  History,
  Layers,
  LockKeyhole,
} from "lucide-react";
import { api, post, put, API, downloadFile } from "../lib/api";
import { questionPayload, settingsPayload } from "../lib/studioContracts";
import { useAuth } from "../lib/auth";
import {
  PageTitle,
  Badge,
  Loading,
  ErrorBox,
  Field,
  SelectField,
  Confirm,
  Empty,
} from "../components/Shared";
import { QuestionContent, MathText } from "../components/QuestionContent";
import { ManualSolve } from '../components/studio/ManualSolve';
import { useSearchParams } from 'react-router-dom';
import { toast } from "sonner";
const tabs = [
  "Sources",
  "Questions",
  "Publication",
  "Rules & rights",
  "Change history",
];
const tabLabels = {
  Sources: "1. Upload",
  Questions: "2. Review",
  Publication: "3. Publish",
  "Rules & rights": "Rules & rights",
  "Change history": "History",
};
export default function StudioEditor() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const requestedQuestion = searchParams.get('question');
  const nav = useNavigate();
  const { user } = useAuth();
  const [s, setS] = useState(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("Questions");
  const [i, setI] = useState(0);
  const [q, setQ] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [settings, setSettings] = useState(null);
  const [busy, setBusy] = useState(false);
  const [profiles, setProfiles] = useState([]);
  const [job, setJob] = useState(null);
  const [file, setFile] = useState(null);
  const [kind, setKind] = useState("questions");
  const [confirm, setConfirm] = useState("");
  const [reason, setReason] = useState("");
  const [subset, setSubset] = useState("");
  const [subsetTitle, setSubsetTitle] = useState("");
  const [checks, setChecks] = useState({});
  const [crop, setCrop] = useState(false);
  const selection = useRef({ dirty, index: i });
  selection.current = { dirty, index: i };
  const load = useCallback(async (keep = true) => {
    const d = await api("/studio/sets/" + id);
    if (!keep && requestedQuestion) {
      const target = d.questions.findIndex(q => q.id === requestedQuestion);
      if (target >= 0) { selection.current.index = target; setI(target); }
    }
    setS(d);
    setSettings(d);
    if (!keep || !selection.current.dirty)
      setQ(
        d.questions[Math.min(selection.current.index, Math.max(d.questions.length - 1, 0))] || null,
      );
    return d;
  }, [id, requestedQuestion]);
  useEffect(() => {
    if (tab === "Change history")
      api("/studio/profiles")
        .then(setProfiles)
        .catch((e) => setError(e.message));
  }, [tab]);
  useEffect(() => {
    load(false).catch((e) => setError(e.message));
  }, [load]);
  useEffect(() => {
    if (!job || ["done", "failed"].includes(job.status)) return;
    const t = setInterval(
      () =>
        api("/jobs/" + job.id)
          .then((j) => {
            setJob(j);
            if (j.status === "done") {
              setDirty(false);
              load(false);
              toast.success(j.message);
            }
            if (j.status === "failed") setError(j.error);
          })
          .catch((e) => setError(e.message)),
      1800,
    );
    return () => clearInterval(t);
  }, [job, load]);
  function change(k, v) {
    setQ({ ...q, [k]: v });
    setDirty(true);
    setChecks({});
  }
  async function perform(fn, message) {
    setBusy(true);
    setError("");
    try {
      await fn();
      if (message) toast.success(message);
      setConfirm("");
      return true;
    } catch (e) {
      setError(e.message);
      toast.error(e.message);
      return false;
    } finally {
      setBusy(false);
    }
  }
  async function saveQuestion() {
    return perform(async () => {
      const saved = await put(`/studio/sets/${id}/questions/${q.id}`, { ...questionPayload(q), expected_revision: s.revision });
      setQ(saved);
      setDirty(false);
      const d = await api("/studio/sets/" + id);
      setS(d);
      setChecks({});
    }, "Question draft saved. It needs fresh approval.");
  }
  async function saveSettings() {
    return perform(async () => {
      await put("/studio/sets/" + id, { ...settingsPayload(settings), expected_revision: settings.revision });
      await load();
    }, "Rules and rights saved. Publication is a separate action.");
  }
  async function upload() {
    if (!file) {
      setError("Select a PDF first.");
      return;
    }
    const form = new FormData();
    form.append("kind", kind);
    form.append("file", file);
    await perform(async () => {
      await api("/studio/sets/" + id + "/files", {
        method: "POST",
        body: form,
      });
      setFile(null);
      await load();
    }, "Original PDF stored privately.");
  }
  async function action() {
    if (confirm === "regrade")
      await perform(async () => {
        setJob(await post("/studio/sets/" + id + "/regrade", { note: reason }));
      }, "Correction versions queued; original scores remain unchanged.");
    if (confirm === "publish")
      await perform(async () => {
        await post("/studio/sets/" + id + "/publish", { confirm: true });
        await load();
      }, "Set published to its permitted audience.");
    if (confirm === "withdraw")
      await perform(async () => {
        await post("/studio/sets/" + id + "/withdraw", { reason });
        await load();
      }, "Set withdrawn. Historical attempts are unchanged.");
    if (confirm === "extract")
      await perform(async () => {
        setJob(
          await post("/studio/sets/" + id + "/extract", {
            replace_drafts: true,
          }),
        );
      }, "Extraction queued. Keep reviewing the process state.");
    if (confirm === "subset")
      await perform(async () => {
        const nums = subset.split(/[,\s]+/).map(Number);
        const next = await post("/studio/sets/" + id + "/subset", {
          title: subsetTitle || s.title + " — Revision",
          question_ids: s.questions
            .filter((q) => nums.includes(q.number))
            .map((q) => q.id),
        });
        nav("/studio/" + next.id);
      }, "Created a separate untimed revision draft.");
  }
  if (!s)
    return (
      <div className="container page">
        <ErrorBox error={error} />
        {!error && <Loading />}
      </div>
    );
  const approved = s.questions.filter((q) => q.approved).length;
  const unresolved = s.questions.length - approved;
  return (
    <div className="container page studio-editor">
      <Link className="breadcrumb" data-testid="studio-back" to="/studio">
        <ArrowLeft size={14} /> All practice sets
      </Link>
      <PageTitle
        eyebrow={`CONTENT STUDIO · ${s.status.toUpperCase()} · VERSION ${s.version}`}
        title={s.title}
        description={`${s.exam} · ${s.questions.length} draft questions · ${approved} reviewed`}
        action={
          <Link
            className="btn btn-secondary"
            data-testid="studio-preview-attempt"
            to={"/sets/" + id + "?preview=true"}
          >
            <Eye size={17} /> Private student preview
          </Link>
        }
      />
      <ManualSolve setId={id}/>
      <div className="studio-stage">
        <span>
          <CheckCircle2 size={17} /> Prepare
        </span>
        <i />
        <span className={unresolved ? "stage-current" : ""}>
          <ShieldCheck size={17} /> Review {approved}/{s.questions.length}
        </span>
        <i />
        <span className={s.status === "published" ? "stage-complete" : ""}>
          <LockKeyhole size={17} /> Publish separately
        </span>
      </div>
      <div className="studio-tabs">
        {tabs.map((t) => (
          <button
            data-testid={"studio-tab-" + t.toLowerCase().replace(/\W+/g, "-")}
            className={
              (tab === t ? "active " : "") +
              (["Rules & rights", "Change history"].includes(t)
                ? "secondary-tab"
                : "")
            }
            key={t}
            onClick={() => setTab(t)}
          >
            {tabLabels[t]}
          </button>
        ))}
      </div>
      <ErrorBox error={error} />
      {job && (
        <div
          className={"notice " + (job.status === "failed" ? "amber" : "")}
          role="status"
        >
          {job.status === "running" || job.status === "queued" ? (
            <Loader2 className="spin" size={18} />
          ) : (
            <CheckCircle2 size={18} />
          )}
          <div>
            <strong>
              {job.status === "done"
                ? "Processing complete"
                : job.status === "failed"
                  ? "Processing needs a retry"
                  : "Processing source documents…"}
            </strong>
            <p>
              {job.message ||
                job.error ||
                "Your sources are preserved. Extracted content remains a suggestion until reviewed."}
            </p>
            {job.status === "failed" && (
              <button
                className="text-button"
                data-testid="studio-job-retry"
                onClick={() =>
                  perform(async () =>
                    setJob(await post("/jobs/" + job.id + "/retry")),
                  )
                }
              >
                Retry processing
              </button>
            )}
          </div>
        </div>
      )}
      {tab === "Questions" && (
        <>
          {s.questions.length ? (
            <div className="editor-layout">
              <aside className="card editor-question-list">
                <div className="row-between">
                  <strong>Questions</strong>
                  <button
                    className="icon-button"
                    title="Add question"
                    aria-label="Add question"
                    data-testid="studio-add-question"
                    onClick={() =>
                      perform(async () => {
                        await post("/studio/sets/" + id + "/questions");
                        await load();
                      })
                    }
                  >
                    <Plus size={18} />
                  </button>
                </div>
                <div className="editor-number-grid">
                  {s.questions.map((item, j) => (
                    <button
                      data-testid={"studio-q-" + item.number}
                      key={item.id}
                      className={
                        (q?.id === item.id ? "current " : "") +
                        (item.approved ? "approved" : "")
                      }
                      aria-label={`Question ${item.number}, ${item.approved ? "approved" : "needs review"}`}
                      onClick={() => {
                        if (dirty) {
                          setError(
                            "Save your draft edits before switching questions.",
                          );
                          return;
                        }
                        setI(j);
                        setQ(item);
                        setChecks({});
                        setError("");
                      }}
                    >
                      {item.number}
                      {item.approved && <CheckCircle2 size={9} />}
                    </button>
                  ))}
                </div>
                <small>
                  Checked = approved
                  <br />
                  Unmarked = needs review
                </small>
                <button
                  className="btn btn-secondary full-width"
                  data-testid="studio-subset"
                  onClick={() => setConfirm("subset")}
                >
                  <Layers size={15} /> Build revision set
                </button>
              </aside>
              {q && (
                <div className="editor-main">
                  <div className="card editor-preview">
                    <div className="row-between">
                      <h2>Question {q.number}</h2>
                      <Badge tone={q.approved ? "green" : "amber"}>
                        {q.approved ? "Approved" : "Needs review"}
                      </Badge>
                    </div>
                    <p className="input-hint">
                      Source-based preview. Extracted text is not proof of
                      faithful notation.
                    </p>
                    <QuestionContent
                      question={q}
                      base={`/studio/sets/${id}/questions/${q.id}`}
                    />
                    <details className="solution-preview" open>
                      <summary data-testid="studio-solution-preview">
                        Matched solution · source Q
                        {q.solution_number || "not confirmed"}
                      </summary>
                      <QuestionContent
                        question={q}
                        solution
                        base={`/studio/sets/${id}/questions/${q.id}`}
                      />
                    </details>
                  </div>
                  <section className="card question-edit-form">
                    <h3>Identity, answer & pairing</h3>
                    <div className="form-grid">
                      <Field
                        id="edit-number"
                        label="Question number"
                        type="number"
                        min={1}
                        value={q.number}
                        onChange={(e) =>
                          change("number", Number(e.target.value))
                        }
                      />
                      <Field
                        id="edit-solution-number"
                        label="Matched source solution number"
                        type="number"
                        min={1}
                        value={q.solution_number || ""}
                        onChange={(e) =>
                          change("solution_number", Number(e.target.value))
                        }
                      />
                      <Field
                        id="edit-subject"
                        label="Subject"
                        value={q.subject}
                        onChange={(e) => {
                          setQ({
                            ...q,
                            subject: e.target.value,
                            section: e.target.value,
                          });
                          setDirty(true);
                          setChecks({});
                        }}
                      />
                      <Field
                        id="edit-section"
                        label="Section identity"
                        value={q.section || ""}
                        onChange={(e) => change("section", e.target.value)}
                      />
                      <SelectField
                        id="edit-type"
                        label="Response format"
                        value={q.type}
                        onChange={(v) => change("type", v)}
                        options={[
                          { value: "mcq", label: "Single-correct MCQ" },
                          {
                            value: "integer",
                            label: "Integer (JEE Main only)",
                          },
                        ]}
                      />
                      <Field
                        id="edit-answer"
                        label="Verified answer key"
                        value={q.answer}
                        onChange={(e) => change("answer", e.target.value)}
                        hint={
                          q.type === "integer"
                            ? "Exact integer; five-digit values accepted"
                            : "Enter the option identifier, not the option text"
                        }
                      />
                      <Field
                        id="edit-topic"
                        label="Author / reviewer topic"
                        value={q.topic}
                        onChange={(e) => change("topic", e.target.value)}
                      />
                      <Field
                        id="edit-difficulty"
                        label="Author-assigned difficulty"
                        value={q.difficulty}
                        onChange={(e) => change("difficulty", e.target.value)}
                      />
                    </div>
                    <SelectField
                      id="edit-disposition"
                      label="Scoring disposition"
                      value={q.disposition || "standard"}
                      onChange={(v) => change("disposition", v)}
                      options={[
                        { value: "standard", label: "Standard reviewed key" },
                        {
                          value: "multiple_accepted",
                          label: "Any one of the accepted answers",
                        },
                        {
                          value: "dropped",
                          label: "Dropped: zero marks, excluded from maximum",
                        },
                        {
                          value: "bonus_all",
                          label: "Bonus correct marks to everyone",
                        },
                        {
                          value: "under_review",
                          label: "Under review: cannot publish",
                        },
                      ]}
                    />
                    {q.disposition === "multiple_accepted" && (
                      <Field
                        id="edit-accepted-answers"
                        label="Verified accepted answers, comma-separated"
                        value={(q.accepted_answers || []).join(", ")}
                        onChange={(e) =>
                          change(
                            "accepted_answers",
                            e.target.value
                              .split(",")
                              .map((v) => v.trim())
                              .filter(Boolean),
                          )
                        }
                      />
                    )}
                    <SelectField
                      id="edit-render-mode"
                      label="Student presentation"
                      value={q.render_mode}
                      onChange={(v) => change("render_mode", v)}
                      options={[
                        {
                          value: "source",
                          label:
                            "Faithful source regions + reviewed accessible text",
                        },
                        { value: "typed", label: "Reviewed text / LaTeX" },
                      ]}
                    />
                    <Field
                      id="edit-question-text"
                      label="Question text (extraction suggestion)"
                    >
                      <textarea
                        data-testid="edit-question-text"
                        id="edit-question-text"
                        rows={5}
                        value={q.text}
                        onChange={(e) => change("text", e.target.value)}
                      />
                    </Field>
                    {q.type === "mcq" && (
                      <div className="form-grid">
                        {Object.entries(q.options || {}).map(([key, v]) => (
                          <Field
                            key={key}
                            id={"edit-option-" + key}
                            label={"Option " + key}
                          >
                            <textarea
                              id={"edit-option-" + key}
                              data-testid={"edit-option-" + key}
                              rows={2}
                              value={v}
                              onChange={(e) =>
                                change("options", {
                                  ...q.options,
                                  [key]: e.target.value,
                                })
                              }
                            />
                          </Field>
                        ))}
                      </div>
                    )}
                    <Field
                      id="edit-solution-text"
                      label="Matched solution text (preserve original English/Hinglish)"
                    >
                      <textarea
                        id="edit-solution-text"
                        data-testid="edit-solution-text"
                        rows={7}
                        value={q.solution}
                        onChange={(e) => change("solution", e.target.value)}
                      />
                    </Field>
                    {q.render_mode === "source" && (
                      <>
                        <div className="row-between">
                          <h3>Source regions</h3>
                          <button
                            className="btn btn-secondary"
                            data-testid="open-crop-editor"
                            onClick={() => setCrop(true)}
                          >
                            <Scissors size={15} /> Select a source region
                          </button>
                        </div>
                        {["q_refs", "s_refs"].map((key) => (
                          <div className="region-list" key={key}>
                            <strong>
                              {key === "q_refs" ? "Question" : "Solution"}{" "}
                              regions
                            </strong>
                            {q[key]?.map((ref, j) => (
                              <div key={j}>
                                <span>
                                  Page {ref.page} ·{" "}
                                  {ref.rect
                                    .map((n) => Math.round(n))
                                    .join(", ")}
                                </span>
                                <button
                                  className="icon-button"
                                  aria-label="Remove source region"
                                  data-testid={key + "-remove-" + j}
                                  onClick={() =>
                                    change(
                                      key,
                                      q[key].filter((_, k) => k !== j),
                                    )
                                  }
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            ))}
                          </div>
                        ))}
                        <Field
                          id="edit-accessible-question"
                          label="Verified accessible question description"
                          hint="Include options, notation and meaningful diagram details. Use $LaTeX$ where useful."
                        >
                          <textarea
                            id="edit-accessible-question"
                            data-testid="edit-accessible-question"
                            rows={5}
                            value={q.accessible_text || ""}
                            onChange={(e) =>
                              change("accessible_text", e.target.value)
                            }
                          />
                        </Field>
                        <Field
                          id="edit-accessible-solution"
                          label="Verified accessible solution description"
                        >
                          <textarea
                            id="edit-accessible-solution"
                            data-testid="edit-accessible-solution"
                            rows={5}
                            value={q.solution_accessible_text || ""}
                            onChange={(e) =>
                              change("solution_accessible_text", e.target.value)
                            }
                          />
                        </Field>
                      </>
                    )}
                    <Field
                      id="edit-review-note"
                      label="Correction / pairing evidence note"
                      hint="Explain numbering differences, corrections or source evidence. Required when changing published content."
                    >
                      <textarea
                        id="edit-review-note"
                        data-testid="edit-review-note"
                        rows={2}
                        value={q.review_note || ""}
                        onChange={(e) => change("review_note", e.target.value)}
                      />
                    </Field>
                    {q.issues?.length > 0 && (
                      <div className="notice amber">
                        <ul>
                          {q.issues.map((x) => (
                            <li key={x}>{x}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className="editor-save">
                      <span>
                        {dirty ? "Unsaved draft changes" : "Draft saved"}
                      </span>
                      <button
                        className="btn btn-primary"
                        data-testid="studio-save-question"
                        disabled={busy}
                        onClick={saveQuestion}
                      >
                        <Save size={17} /> Save draft
                      </button>
                    </div>
                  </section>
                  <section className="card approval-card">
                    <h3>Review is a separate decision.</h3>
                    <p>
                      Compare the original question, options and solution before
                      approving. Author claims do not replace your verification.
                    </p>
                    {[
                      "Question, notation and figures render faithfully",
                      "The answer key and option meaning are correct",
                      "Source identity and solution pairing are verified",
                      "Accessible descriptions faithfully represent both regions",
                    ].map((text, k) => (
                      <label className="checkbox-label" key={text}>
                        <input
                          type="checkbox"
                          data-testid={"review-check-" + k}
                          checked={checks[k] || false}
                          onChange={(e) =>
                            setChecks({ ...checks, [k]: e.target.checked })
                          }
                        />
                        <span>{text}</span>
                      </label>
                    ))}
                    <button
                      className="btn btn-secondary"
                      data-testid="studio-approve-question"
                      disabled={
                        busy ||
                        dirty ||
                        Object.values(checks).filter(Boolean).length !== 4
                      }
                      onClick={() =>
                        perform(async () => {
                          await post(
                            `/studio/sets/${id}/questions/${q.id}/approve`,
                          );
                          const d = await load(false);
                          setQ(d.questions[i]);
                          setChecks({});
                        }, "Question approved. Publication remains separate.")
                      }
                    >
                      <ShieldCheck size={17} /> Approve this question
                    </button>
                  </section>
                </div>
              )}
            </div>
          ) : (
            <Empty
              title="No questions extracted yet."
              action={
                <button
                  className="btn btn-primary"
                  data-testid="studio-manual-first-question"
                  onClick={() =>
                    perform(async () => {
                      await post("/studio/sets/" + id + "/questions");
                      await load(false);
                    })
                  }
                >
                  <Plus size={17} /> Add question manually
                </button>
              }
            >
              Upload your PDFs in Sources, then run assisted extraction. Scanned
              and complex content can be entered manually with source regions.
            </Empty>
          )}
        </>
      )}
      {tab === "Sources" && (
        <div className="source-tab">
          <div className="card">
            <h2>Keep the originals. Review the interpretation.</h2>
            <p>
              Up to 50 MB and 300 pages per PDF. Encrypted files must be
              supplied unlocked. No automated OCR or AI-generated answers are
              used.
            </p>
            <div className="upload-grid">
              <SelectField
                id="upload-kind"
                label="Document type"
                value={kind}
                onChange={setKind}
                options={[
                  { value: "questions", label: "Question paper" },
                  { value: "solutions", label: "Solutions PDF" },
                  { value: "key", label: "Separate answer key" },
                  {
                    value: "combined",
                    label: "Combined questions & solutions",
                  },
                ]}
              />
              <Field id="source-upload" label="Select original PDF">
                <input
                  data-testid="source-upload"
                  id="source-upload"
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                />
              </Field>
            </div>
            <button
              className="btn btn-primary"
              data-testid="studio-upload-button"
              disabled={busy || !file}
              onClick={upload}
            >
              {busy ? (
                <Loader2 className="spin" size={17} />
              ) : (
                <Upload size={17} />
              )}{" "}
              {busy ? "Validating & privately storing…" : "Upload privately"}
            </button>
            {!s.rights_upload && (
              <p className="warning-text">
                Confirm permission to upload under Rules & rights first.
              </p>
            )}
          </div>
          <div className="source-files">
            {s.files.map((f) => (
              <div className="card source-file" key={f.id}>
                <FileText size={25} />
                <div>
                  <strong>{f.name}</strong>
                  <p>
                    {f.kind} · {f.pages} pages ·{" "}
                    {(f.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <code>SHA-256: {f.sha256?.slice(0, 18)}…</code>
                </div>
                <button
                  className="btn btn-secondary"
                  data-testid={"download-source-" + f.kind}
                  onClick={() =>
                    downloadFile(
                      "/studio/files/" + f.id + "/download",
                      f.name,
                    ).catch((e) => toast.error(e.message))
                  }
                >
                  Open original PDF
                </button>
              </div>
            ))}
          </div>
          <div className="card">
            <h3>Assisted extraction, never automatic approval.</h3>
            <p>
              Numbered text-based questions are matched using paper identity,
              subject/section, question number and source references. A combined
              PDF follows the same review path. Scanned pages may yield no text;
              use manual question entry and region selection instead.
            </p>
            <button
              className="btn btn-secondary"
              data-testid="studio-extract"
              disabled={
                busy || job?.status === "running" || job?.status === "queued"
              }
              onClick={() => setConfirm("extract")}
            >
              <RefreshCw size={17} /> Extract & suggest pairings
            </button>
          </div>
        </div>
      )}
      {tab === "Rules & rights" && (
        <div className="card settings-form">
          <h2>Define the practice. Record the permission.</h2>
          <p>
            These values are frozen for each attempt. Editing a published set
            returns it to draft; existing student records do not change.
          </p>
          <div className="form-grid">
            <Field
              id="settings-title"
              label="Set title"
              value={settings.title}
              onChange={(e) =>
                setSettings({ ...settings, title: e.target.value })
              }
            />
            <SelectField
              id="settings-exam"
              label="Exam"
              value={settings.exam}
              onChange={(v) => setSettings({ ...settings, exam: v })}
              options={["JEE Main", "BITSAT"]}
            />
            <Field
              id="settings-year"
              label="Source year (if known)"
              value={settings.year || ""}
              onChange={(e) =>
                setSettings({ ...settings, year: e.target.value })
              }
            />
            <Field
              id="settings-minutes"
              label="Time allowance (0 = untimed)"
              type="number"
              min={0}
              max={1440}
              value={settings.rules.minutes}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  rules: { ...settings.rules, minutes: Number(e.target.value) },
                })
              }
            />
            <Field
              id="settings-correct"
              label="Marks for correct answer"
              type="number"
              value={settings.rules.correct}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  rules: { ...settings.rules, correct: Number(e.target.value) },
                })
              }
            />
            <Field
              id="settings-wrong"
              label="Marks for wrong answer (negative or zero)"
              type="number"
              value={settings.rules.wrong}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  rules: { ...settings.rules, wrong: Number(e.target.value) },
                })
              }
            />
          </div>
          <p className="notice">
            Unanswered = 0. Maximum marks = question count × correct marks.
            Numerical responses use exact integer equivalence; no assumed
            official digit limit.
          </p>
          <Field id="settings-source" label="Source and provenance">
            <textarea
              id="settings-source"
              data-testid="settings-source"
              value={settings.source}
              rows={3}
              onChange={(e) =>
                setSettings({ ...settings, source: e.target.value })
              }
            />
          </Field>
          <Field
            id="settings-attribution"
            label="Required attribution"
            value={settings.attribution}
            onChange={(e) =>
              setSettings({ ...settings, attribution: e.target.value })
            }
          />
          <div className="form-grid">
            <SelectField
              id="settings-audience"
              label="Permitted audience"
              value={settings.audience}
              onChange={(v) => setSettings({ ...settings, audience: v })}
              options={[
                { value: "all", label: "All registered students" },
                {
                  value: "restricted",
                  label: "Only specified registered students",
                },
              ]}
            />
            <Field
              id="settings-expiry"
              label="Permission expiry (optional, YYYY-MM-DD)"
              placeholder="YYYY-MM-DD"
              value={settings.expires || ""}
              onChange={(e) =>
                setSettings({ ...settings, expires: e.target.value })
              }
            />
          </div>
          {settings.audience === "restricted" && (
            <>
              <Field
                id="settings-allowed-phones"
                label="Permitted mobile numbers, comma-separated (+ country code)"
              >
                <textarea
                  id="settings-allowed-phones"
                  data-testid="settings-allowed-phones"
                  value={(settings.allowed_phones || []).join(", ")}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      allowed_phones: e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </Field>
              <Field
                id="settings-allowed-emails"
                label="Staff / legacy account emails (optional), comma-separated"
              >
                <textarea
                  id="settings-allowed-emails"
                  data-testid="settings-allowed-emails"
                  value={(settings.allowed_emails || []).join(", ")}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      allowed_emails: e.target.value
                        .split(",")
                        .map((s) => s.trim().toLowerCase()),
                    })
                  }
                />
              </Field>
            </>
          )}
          <h3>Separate permissions, separate responsibilities</h3>
          {[
            [
              "rights_upload",
              "I have permission to upload and privately process these source documents.",
            ],
            [
              "rights_publish",
              "I have permission to present the reviewed content to the audience specified above.",
            ],
            [
              "rights_report",
              "I have permission to include questions and solutions in downloadable personal student reports.",
            ],
          ].map(([key, l]) => (
            <label className="checkbox-label" key={key}>
              <input
                type="checkbox"
                data-testid={"settings-" + key}
                checked={settings[key] || false}
                onChange={(e) =>
                  setSettings({ ...settings, [key]: e.target.checked })
                }
              />
              <span>{l}</span>
            </label>
          ))}
          <Field
            id="settings-change-reason"
            label="Reason for this change"
            value={settings.change_reason || ""}
            onChange={(e) =>
              setSettings({ ...settings, change_reason: e.target.value })
            }
          />
          <button
            className="btn btn-primary"
            data-testid="studio-save-settings"
            disabled={busy}
            onClick={saveSettings}
          >
            <Save size={17} /> Save rules & rights
          </button>
        </div>
      )}
      {tab === "Publication" && (
        <div className="card publication-card">
          <ShieldCheck size={36} />
          <h2>Ready is a verified state.</h2>
          <p>
            Publishing is the final owner decision, not a side effect of
            uploading or extraction.
          </p>
          <div className="publication-checks">
            {[
              [
                s.questions.length > 0,
                `${s.questions.length} questions in the set`,
              ],
              [
                unresolved === 0 && s.questions.length > 0,
                `${approved} approved · ${unresolved} still need review`,
              ],
              [s.rights_upload, "Private upload permission recorded"],
              [s.rights_publish, "Publication permission recorded"],
              [s.rights_report, "Personal report redistribution allowed"],
              [s.source && s.attribution, "Source and attribution recorded"],
            ].map(([ok, t]) => (
              <div key={t} className={ok ? "complete" : ""}>
                <CheckCircle2 size={19} />
                {t}
              </div>
            ))}
          </div>
          <p>
            Audience:{" "}
            <strong>
              {s.audience === "all"
                ? "All registered students"
                : "Only specified accounts"}
            </strong>{" "}
            · Expiry: {s.expires || "Not specified"}
          </p>
          <p>
            Future corrections are logged. Completed attempts retain their
            original questions, keys, options and marking rules.
          </p>
          {user.role === "owner" ? (
            <div className="button-row">
              <button
                className="btn btn-primary"
                data-testid="studio-publish-button"
                disabled={busy || unresolved > 0 || !s.questions.length}
                onClick={() => setConfirm("publish")}
              >
                Publish reviewed set <ArrowRight size={17} />
              </button>
              <button
                className="btn btn-secondary"
                data-testid="studio-regrade-button"
                disabled={s.status !== "published"}
                onClick={() => setConfirm("regrade")}
              >
                Create corrected score versions
              </button>
              <button
                className="btn btn-secondary"
                data-testid="studio-withdraw-button"
                disabled={s.status !== "published"}
                onClick={() => setConfirm("withdraw")}
              >
                Withdraw set
              </button>
            </div>
          ) : (
            <div className="notice">
              Only the owner can publish or withdraw. Your approvals are ready
              for their review.
            </div>
          )}
          <small>
            Withdrawal revokes new access through the application; it is not
            certified physical erasure from storage.
          </small>
        </div>
      )}
      {tab === "Change history" && (
        <div className="card audit-card">
          <h2>Changes leave a record.</h2>
          <details className="profile-details">
            <summary data-testid="studio-profile-registry">
              Immutable exam profile registry ({profiles.length})
            </summary>
            <p>
              These are recorded custom-practice profiles—not official-year
              verification. A new definition is sealed whenever the rules or
              included questions change.
            </p>
            {profiles.length ? (
              profiles.map((p) => (
                <div className="profile-row" key={p.id}>
                  <strong>
                    {p.definition.exam} ·{" "}
                    {p.definition.duration_minutes || "Untimed"}{" "}
                    {p.definition.duration_minutes ? "minutes" : ""}
                  </strong>
                  <code>{p.id}</code>
                  <p>
                    {p.definition.sections
                      .map((s) => s.name + ": " + s.count)
                      .join(" · ")}
                    <br />
                    Navigation: {p.definition.navigation} · Release:{" "}
                    {p.definition.solution_release}
                    <br />
                    Evidence: {p.definition.source_evidence.approval_state}
                  </p>
                </div>
              ))
            ) : (
              <p>
                A profile is created when a reviewed set is published or an
                attempt is started.
              </p>
            )}
          </details>
          <p>
            Latest 40 content actions. Existing attempt snapshots are never
            silently overwritten.
          </p>
          {s.audit.map((a) => (
            <div className="audit-row" key={a.id}>
              <span>
                <History size={17} />
              </span>
              <div>
                <strong>{a.action}</strong>
                <p>{a.detail}</p>
                <small>
                  {new Date(a.at * 1000).toLocaleString()} · Actor{" "}
                  {a.actor.slice(0, 8)}
                </small>
              </div>
            </div>
          ))}
        </div>
      )}
      <Confirm
        open={!!confirm}
        onClose={() => setConfirm("")}
        title={
          confirm === "regrade"
            ? "Create a labelled score correction?"
            : confirm === "publish"
              ? "Publish this reviewed set?"
              : confirm === "withdraw"
                ? "Withdraw from new practice?"
                : confirm === "subset"
                  ? "Build a separate revision set"
                  : "Replace drafts with new extraction?"
        }
        button={
          confirm === "regrade"
            ? "Create score versions"
            : confirm === "publish"
              ? "Publish set"
              : confirm === "withdraw"
                ? "Withdraw set"
                : confirm === "subset"
                  ? "Create revision draft"
                  : "Run extraction"
        }
        busy={busy}
        onConfirm={action}
      >
        {confirm === "regrade" ? (
          <>
            <p>
              Create a new score version for compatible completed attempts using
              the published correction. Original responses, ledgers and PDFs
              remain untouched. Changed question stems or marking rules are not
              silently regraded.
            </p>
            <Field
              id="regrade-note"
              label="Student-facing correction explanation"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </>
        ) : confirm === "publish" ? (
          <p>
            This makes the reviewed content available to the permitted audience
            with personal reports enabled. Confirm that the rights and academic
            review records are accurate.
          </p>
        ) : confirm === "withdraw" ? (
          <>
            <p>
              New attempts will stop. Saved and completed attempts keep their
              frozen version.
            </p>
            <Field
              id="withdraw-reason"
              label="Reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </>
        ) : confirm === "subset" ? (
          <>
            <Field
              id="subset-title"
              label="Revision set title"
              value={subsetTitle}
              onChange={(e) => setSubsetTitle(e.target.value)}
            />
            <Field
              id="subset-questions"
              label="Question numbers, separated by commas"
              placeholder="1, 5, 22"
              value={subset}
              onChange={(e) => setSubset(e.target.value)}
            />
            <p>
              The new set is untimed, with its own maximum marks. Original
              question order and source links are preserved.
            </p>
          </>
        ) : (
          <p>
            Assisted extraction replaces current draft edits and approvals.
            Original PDFs and completed attempts remain unchanged. Uncertain
            matches stay unpublished.
          </p>
        )}
      </Confirm>
      {crop && q && (
        <CropEditor
          files={s.files}
          onClose={() => setCrop(false)}
          onAdd={(target, ref) => {
            change(target, [...(q[target] || []), ref]);
            setCrop(false);
          }}
        />
      )}
    </div>
  );
}
function CropEditor({ files, onClose, onAdd }) {
  const [fid, setFid] = useState(files[0]?.id || "");
  const [page, setPage] = useState(1);
  const [target, setTarget] = useState("q_refs");
  const [info, setInfo] = useState(null);
  const [rect, setRect] = useState([40, 50, 550, 400]);
  const [corner, setCorner] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!fid) return;
    api(`/studio/files/${fid}/text/${page}`)
      .then((d) => {
        setInfo(d);
        setError("");
      })
      .catch((e) => setError(e.message));
  }, [fid, page]);
  const f = files.find((f) => f.id === fid);
  function select(e) {
    if (!info) return;
    const b = e.currentTarget.getBoundingClientRect();
    const x = Math.round(((e.clientX - b.left) / b.width) * info.width);
    const y = Math.round(((e.clientY - b.top) / b.height) * info.height);
    if (!corner) setCorner([x, y]);
    else {
      setRect([
        Math.min(x, corner[0]),
        Math.min(y, corner[1]),
        Math.max(x, corner[0]),
        Math.max(y, corner[1]),
      ]);
      setCorner(null);
    }
  }
  return (
    <Confirm
      open
      onClose={onClose}
      title="Select a faithful source region"
      button="Add this region"
      onConfirm={() => {
        if (
          rect[2] <= rect[0] ||
          rect[3] <= rect[1] ||
          rect[0] < 0 ||
          rect[1] < 0 ||
          rect[2] > info?.width ||
          rect[3] > info?.height
        ) {
          setError("Choose a valid rectangle inside the page.");
          return;
        }
        onAdd(target, { file_id: fid, page, rect });
      }}
    >
      <ErrorBox error={error} />
      <SelectField
        id="crop-file"
        label="Original document"
        value={fid}
        onChange={(v) => {
          setFid(v);
          setPage(1);
        }}
        options={files.map((f) => ({ value: f.id, label: f.name }))}
      />
      <div className="form-grid">
        <Field
          id="crop-page"
          label={`Page (1–${f?.pages || 0})`}
          type="number"
          min={1}
          max={f?.pages}
          value={page}
          onChange={(e) => setPage(Number(e.target.value))}
        />
        <SelectField
          id="crop-target"
          label="Attach to"
          value={target}
          onChange={setTarget}
          options={[
            { value: "q_refs", label: "Question" },
            { value: "s_refs", label: "Matched solution" },
          ]}
        />
      </div>
      <p>
        Click two opposite corners, or enter coordinates below. Include every
        essential sign, figure and option. Add more regions for multi-page
        solutions.
      </p>
      <div
        className="crop-image-wrap"
        onClick={select}
        data-testid="crop-source-image"
      >
        {fid && (
          <img
            src={`${API}/studio/files/${fid}/page/${page}`}
            alt="Source page for region selection. Coordinate inputs below provide keyboard access."
          />
        )}
        {info && (
          <div
            className="crop-selection"
            style={{
              left: (rect[0] / info.width) * 100 + "%",
              top: (rect[1] / info.height) * 100 + "%",
              width: ((rect[2] - rect[0]) / info.width) * 100 + "%",
              height: ((rect[3] - rect[1]) / info.height) * 100 + "%",
            }}
          />
        )}
      </div>
      <small>
        {corner
          ? "First corner selected; select the opposite corner."
          : `Page size: ${Math.round(info?.width || 0)} × ${Math.round(info?.height || 0)} PDF points.`}
      </small>
      <div className="form-grid four">
        {["Left", "Top", "Right", "Bottom"].map((t, i) => (
          <Field
            key={t}
            id={"crop-" + t.toLowerCase()}
            label={t}
            type="number"
            value={rect[i]}
            onChange={(e) =>
              setRect(
                rect.map((v, j) => (i === j ? Number(e.target.value) : v)),
              )
            }
          />
        ))}
      </div>
    </Confirm>
  );
}
