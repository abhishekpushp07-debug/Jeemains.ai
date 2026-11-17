import {Button} from '../components/ui/button';
import {Input} from '../components/ui/input';
import React, { useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  FileCheck2,
  RotateCcw,
  Loader2,
  Phone,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { postWhenFree } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Field, ErrorBox } from "../components/Shared";
export default function Auth({ staff = false }) {
  const { setUser } = useAuth();
  const location = useLocation();
  const signup = !staff && location.pathname === '/signup';
  const reset = !staff && location.pathname === '/forgot-pin';
  const [missing, setMissing] = useState(false);
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setMissing(false);
    if ((signup || reset) && pin !== confirmPin) { setError('PINs must match.'); return; }
    setBusy(true);
    setError("");
    try {
      const [path, body] = staff ? ['/auth/login', { email, password }]
        : signup ? ['/auth/phone/signup', { phone, pin, confirm_pin: confirmPin }]
        : reset ? ['/auth/pin/reset', { phone, new_pin: pin, confirm_pin: confirmPin }]
        : ['/auth/phone', { phone, pin }];
      const u = await postWhenFree(path, body);
      if (staff && !["owner", "reviewer"].includes(u.role))
        throw new Error(
          "This is the staff entrance. Use mobile-number entry for student practice.",
        );
      setUser(u);
      if (reset) toast.success('PIN changed. You are signed in.');
      const next = params.get("next");
      nav(
        next?.startsWith('/') && !next.startsWith('//') && !next.includes('\\') && !/[\u0000-\u001f]/.test(next)
          ? next
          : staff
            ? "/super-admin"
            : "/home",
        {replace:true},
      );
    } catch (e) {
      setError(e.message);
      setMissing(reset && e.status === 404);
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
          Your number.
          <br />
          Your PIN.
        </h1>
        <p>
          Practice, understand your results, and return to your learning—all in
          one place.
        </p>
        {[
          [BookOpen, "One number. Your private practice."],
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
        <h2 data-testid="auth-title">{staff ? 'Super Admin.' : signup ? 'Create your student account.' : reset ? 'Set a new PIN.' : 'Welcome back.'}</h2>
        <p>
          {staff
            ? "Authorized owners and reviewers only."
            : signup ? 'Your mobile number and a 4-digit PIN. No OTP.' : reset ? 'Your mobile number and a new 4-digit PIN. No OTP, no old PIN.' : 'Sign in with your mobile number and 4-digit PIN.'}
        </p>
        <ErrorBox error={error} />
        {missing && <p className="auth-switch"><Link data-testid="forgot-pin-create-account" to="/signup" onClick={()=>{setError('');setMissing(false);setPin('');setConfirmPin('');}}>Create an account with this number</Link></p>}
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
              <Field id={reset ? 'forgot-pin-new-input' : 'student-pin-input'} label={signup ? 'Create 4-digit PIN' : reset ? 'New 4-digit PIN' : '4-digit PIN'} type="password" inputMode="numeric" autoComplete={signup || reset ? 'new-password' : 'current-password'} pattern="[0-9]{4}" minLength={4} maxLength={4} required value={pin} onChange={e=>setPin(e.target.value.replace(/[^0-9]/g,''))}/>
              {!signup && !reset && <Link className="forgot-pin-link" data-testid="forgot-pin-link" to={'/forgot-pin' + (params.toString() ? '?' + params.toString() : '')} onClick={()=>{setError('');setPin('');setConfirmPin('');}}>Forgot PIN?</Link>}
              {(signup || reset) && <Field id={reset ? 'forgot-pin-confirm-input' : 'student-confirm-pin-input'} label="Confirm PIN" type="password" inputMode="numeric" autoComplete="new-password" pattern="[0-9]{4}" minLength={4} maxLength={4} required value={confirmPin} onChange={e=>setConfirmPin(e.target.value.replace(/[^0-9]/g,''))}/>}
              <p
                className="phone-disclosure"
                id="phone-access-note"
                data-testid="student-login-no-otp-notice"
              >
                PIN protects access to your saved practice; it does not verify phone ownership. No OTP is sent.
                {reset && ' Other devices on this number are signed out. Your saved practice and results stay.'}
              </p>
            </>
          )}
          <Button
            type="submit"
            className="btn btn-primary full-width"
            disabled={busy}
            data-testid={
              staff ? "login-submit-button" : reset ? "forgot-pin-submit-button" : "student-login-continue-button"
            }
          >
            {busy ? <Loader2 className="spin" size={18} /> : null}
            {busy
              ? "Opening your space…"
              : staff
                ? "Open Super Admin"
                : signup ? 'Create account' : reset ? 'Save new PIN' : 'Sign in'}
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
            <p className="auth-switch"><Link data-testid="student-auth-switch" to={(signup || reset ? '/login' : '/signup') + (params.toString() ? '?' + params.toString() : '')} onClick={()=>{setError('');setMissing(false);setPin('');setConfirmPin('');}}>{signup ? 'Already have an account? Sign in' : reset ? 'Remembered your PIN? Sign in' : 'New student? Create an account'}</Link></p>
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
