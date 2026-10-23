import {Button} from '../components/ui/button';
import {Input} from '../components/ui/input';
import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  FileCheck2,
  RotateCcw,
  Loader2,
  Phone,
  ShieldCheck,
} from "lucide-react";
import { post } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Field, ErrorBox } from "../components/Shared";
export default function Auth({ staff = false }) {
  const { setUser } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const u = await post(
        staff ? "/auth/login" : "/auth/phone",
        staff ? { email, password } : { phone },
      );
      if (staff && !["owner", "reviewer"].includes(u.role))
        throw new Error(
          "This is the staff entrance. Use mobile-number entry for student practice.",
        );
      setUser(u);
      const next = params.get("next");
      nav(
        staff && next?.startsWith("/") && !next.startsWith("//")
          ? next
          : staff
            ? "/studio"
            : "/home",
        {replace:true},
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="container auth-layout">
      <div className="auth-story">
        <span className="free-label" data-testid="auth-free-label">100% FREE FOR ALL STUDENTS</span>
        <h1>
          Your next step.
          <br />
          Just one number
          <br />
          away.
        </h1>
        <p>
          Practice, understand your results, and return to your learning—all in
          one place.
        </p>
        {[
          [BookOpen, "One number. Straight into practice."],
          [FileCheck2, "Original questions. Clear answer review."],
          [RotateCcw, "Come back and pick up where you left off."],
        ].map(([Icon, t]) => (
          <div className="auth-point" key={t}>
            <Icon size={20} />
            {t}
          </div>
        ))}
        <span className="auth-footnote">
          No score guarantees. Just a clearer way forward.
        </span>
      </div>
      <div className="auth-card phone-auth-card">
        <span className="auth-icon">
          {staff ? <ShieldCheck size={25} /> : <Phone size={24} />}
        </span>
        <h2>{staff ? "Content Studio." : "Let’s get you started."}</h2>
        <p>
          {staff
            ? "Authorized owners and reviewers only."
            : "Your mobile number is all you need."}
        </p>
        <ErrorBox error={error} />
        <form onSubmit={submit}>
          {staff ? (
            <>
              <Field
                id="login-email-input"
                label="Staff email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Field
                id="login-password-input"
                label="Password"
                type="password"
                autoComplete="current-password"
                minLength={8}
                maxLength={64}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </>
          ) : (
            <>
              <label className="field" htmlFor="student-login-phone-input">
                <span>Mobile number</span>
                <div className="phone-input-shell">
                  {!phone.trim().startsWith("+") && (
                    <span className="country-prefix">+91</span>
                  )}
                  <Input
                    className="border-0 rounded-none shadow-none"
                    id="student-login-phone-input"
                    data-testid="student-login-phone-input"
                    type="tel"
                    inputMode="tel"
                    autoComplete="tel"
                    placeholder="98765 43210"
                    maxLength={32}
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    aria-describedby="phone-access-note"
                  />
                </div>
                <small>
                  Outside India? Include your country code, starting with +.
                </small>
              </label>
              <p
                className="phone-disclosure"
                id="phone-access-note"
                data-testid="student-login-no-otp-notice"
              >
                No OTP or password. Anyone entering this number can access its
                saved practice and results.
              </p>
            </>
          )}
          <Button
            type="submit"
            className="btn btn-primary full-width"
            disabled={busy}
            data-testid={
              staff ? "login-submit-button" : "student-login-continue-button"
            }
          >
            {busy ? <Loader2 className="spin" size={18} /> : null}
            {busy
              ? "Opening your space…"
              : staff
                ? "Open Content Studio"
                : "Continue"}
            <ArrowRight size={18} />
          </Button>
        </form>
        {staff ? (
          <p className="auth-switch">
            Here to practice?{" "}
            <Link data-testid="student-entry-link" to="/login">
              Use your mobile number
            </Link>
          </p>
        ) : (
          <>
            <p className="phone-consent">
              By continuing, you agree to store this number and your practice
              records as described in our{" "}
              <Link data-testid="phone-privacy" to="/privacy">
                privacy notice
              </Link>
              .
            </p>
            <Link
              className="staff-login-link"
              data-testid="staff-login-link"
              to="/owner-login"
            >
              Staff login <ArrowRight size={12} />
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
