import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Plus,
  ArrowUpRight,
  FileStack,
  ShieldCheck,
  CheckCircle2,
  BookOpen,
  Users,
} from "lucide-react";
import { api, post } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  PageTitle,
  Loading,
  Empty,
  ErrorBox,
  Badge,
  Confirm,
  Field,
  SelectField,
} from "../components/Shared";
import { StudioImportHub } from './StudioImport';
import { MockBookPanel } from '../components/studio/MockBookPanel';
import { ManualSolvePanel } from '../components/studio/ManualSolve';
import { QuestionReportsPanel } from '../components/studio/QuestionReportsPanel';
import { AiReviewPanel } from '../components/studio/AiReviewPanel';
import { Button } from '../components/ui/button';
import { toast } from "sonner";
export default function Studio() {
  const [sets, setSets] = useState(null);
  const [error, setError] = useState("");
  const [create, setCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [exam, setExam] = useState("JEE Main");
  const [busy, setBusy] = useState(false);
  const [team, setTeam] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("reviewer");
  const [initialPassword, setInitialPassword] = useState("");
  const { user } = useAuth();
  const nav = useNavigate();
  useEffect(() => {
    api("/studio/sets")
      .then(setSets)
      .catch((e) => setError(e.message));
  }, []);
  async function add() {
    setBusy(true);
    try {
      const s = await post("/studio/sets", { title, exam });
      nav("/studio/" + s.id);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function grant() {
    setBusy(true);
    try {
      await post("/studio/reviewers", {
        email,
        role,
        initial_password: initialPassword,
      });
      toast.success("Reviewer access updated.");
      setTeam(false);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="container page">
      <PageTitle
        eyebrow="PRIVATE · CONTENT OPERATIONS"
        title="Your content. Their next breakthrough."
        description="PDF or Excel → organised test → choose a start time. All in one place."
        action={
          <Button
            className="btn btn-primary"
            data-testid="studio-upload-files"
            onClick={() => { document.querySelector('[data-testid="studio-import-hub"]')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); document.querySelector('[data-testid="studio-create-test-import-mode-pdf"]')?.focus({ preventScroll: true }); }}
          >
            <Plus size={18} /> Upload PDF / Excel
          </Button>
        }
      />
      <ManualSolvePanel />
      <QuestionReportsPanel />
      <StudioImportHub />
      <MockBookPanel />
      <AiReviewPanel />
      <div className="flex flex-wrap items-center justify-between gap-4 mt-10 mb-6"><h2 data-testid="legacy-studio-heading">Advanced Studio sets</h2><Button variant="outline" data-testid="studio-new-set" onClick={() => setCreate(true)}><Plus size={16} /> Manual editor</Button></div>
      <div className="studio-stats">
        {[
          [
            FileStack,
            "Drafts & review",
            sets?.filter((s) => s.status !== "published").length,
          ],
          [
            CheckCircle2,
            "Published sets",
            sets?.filter((s) => s.status === "published").length,
          ],
          [
            ShieldCheck,
            "Reviewer approvals",
            sets?.reduce((n, s) => n + s.approved_count, 0),
          ],
        ].map(([Icon, l, v]) => (
          <div className="card" key={l}>
            <Icon size={22} />
            <div>
              <span>{l}</span>
              <strong>{v ?? "—"}</strong>
            </div>
          </div>
        ))}
      </div>
      <div className="notice">
        <ShieldCheck size={20} />
        <div>
          <strong>Advanced editorial workspace</strong>
          <p>
            Use this workspace for manually authored sets. Imported tests use the
            organiser above, with frozen content and separate Live/Unlive controls.
          </p>
        </div>
      </div>
      <ErrorBox error={error} />
      {!sets && !error ? (
        <Loading />
      ) : sets?.length ? (
        <div className="studio-list">
          {sets.map((s) => (
            <Link
              to={"/studio/" + s.id}
              className="card studio-row"
              key={s.id}
              data-testid="studio-set-row"
            >
              <span className="icon-tile">
                <BookOpen size={25} />
              </span>
              <div className="studio-set-name">
                <div>
                  <Badge>{s.exam}</Badge>
                  <Badge tone={s.status === "published" ? "green" : "amber"}>
                    {s.status}
                  </Badge>
                </div>
                <h3>{s.title}</h3>
                <p>
                  {s.count} questions · {s.approved_count} approved ·{" "}
                  {s.rules.minutes ? s.rules.minutes + " minutes" : "Untimed"} ·{" "}
                  {s.maximum} marks
                </p>
              </div>
              <div className="studio-review-progress">
                <span>
                  {s.approved_count} / {s.count} reviewed
                </span>
                <div>
                  <i
                    style={{
                      width:
                        (s.count ? (100 * s.approved_count) / s.count : 0) +
                        "%",
                    }}
                  />
                </div>
              </div>
              <ArrowUpRight size={22} />
            </Link>
          ))}
        </div>
      ) : (
        !error && (
          <Empty title="Bring a paper into the process.">
            Create a practice set, record its source permissions, and upload the
            original PDFs.
          </Empty>
        )
      )}
      <div className="studio-bottom">
        <p>
          <strong>Supported now:</strong> JEE Main single-correct and numerical
          practice; BITSAT single-correct practice. Scanned or complex pages
          require source-region selection and manual verification.
        </p>
        {user.role === "owner" && (
          <button
            className="btn btn-secondary"
            data-testid="studio-reviewers"
            onClick={() => setTeam(true)}
          >
            <Users size={17} /> Reviewer access
          </button>
        )}
      </div>
      <Confirm
        open={create}
        onClose={() => setCreate(false)}
        title="Create a practice set"
        button="Create draft"
        busy={busy}
        onConfirm={add}
      >
        <Field
          id="new-set-title"
          label="Paper or set title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Name your source paper"
        />
        <SelectField
          id="new-set-exam"
          label="Exam"
          value={exam}
          onChange={setExam}
          options={["JEE Main", "BITSAT"]}
        />
        <p>
          New sets are private drafts with no publication permissions. You will
          define timing, marks and rights next.
        </p>
        <ErrorBox error={error} />
      </Confirm>
      <Confirm
        open={team}
        onClose={() => setTeam(false)}
        title="Manage reviewer access"
        button="Update role"
        busy={busy}
        onConfirm={grant}
      >
        <p>
          Create a password-protected staff account here, or update an existing
          reviewer. Phone-only student profiles can never receive staff
          privileges.
        </p>
        <Field
          id="reviewer-email"
          label="Staff email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Field
          id="reviewer-initial-password"
          label="Initial password (new staff only)"
          type="password"
          autoComplete="new-password"
          value={initialPassword}
          onChange={(e) => setInitialPassword(e.target.value)}
          hint="At least 10 characters. Existing accounts keep their password."
        />
        <SelectField
          id="reviewer-role"
          label="Access"
          value={role}
          onChange={setRole}
          options={[
            { value: "reviewer", label: "Authorized reviewer" },
            { value: "student", label: "Remove reviewer access" },
          ]}
        />
      </Confirm>
    </div>
  );
}
