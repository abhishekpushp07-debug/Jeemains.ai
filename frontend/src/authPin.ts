import { useEffect, useRef, useState } from "react";
import { ApiError } from "./api/client";

export const validPin = (pin: string) => /^[0-9]{4}$/.test(pin);
export const cleanPhone = (phone: string) => phone.trim().replace(/[\s()-]/g, "");
// Canonical API owns normalization/account lookup; don't hash or invent an ID.
export const validPhone = (phone: string) => /^\+?[0-9]{8,15}$/.test(cleanPhone(phone));
export function pinFormError(phone: string, pin: string, confirm?: string) {
  if (!validPhone(phone)) return "Enter your mobile number, including country code if needed.";
  if (!validPin(pin)) return "Your PIN must be exactly 4 digits (0–9).";
  if (confirm !== undefined && !validPin(confirm)) return "Confirm your PIN using 4 digits.";
  if (confirm !== undefined && confirm !== pin) return "PINs do not match. Please check both fields.";
  return "";
}

/** Clear words for a failed sign-in / PIN step. The server's own words stay when they already guide the student. */
export function authErrorText(e: unknown) {
  if (!(e instanceof ApiError)) return e instanceof Error ? e.message : "Couldn't finish. Please try again.";
  if (e.status === 422 && /operation.s contract/.test(e.message)) return "Mobile number ya PIN sahi format mein nahi hai. 10 digit ka mobile number aur 4 digit ka PIN daalo.";
  if (e.status === 0 && !/server address/.test(e.message)) return "Internet nahi mil raha. Net check karke dobara try karo — aapka account aur saved kaam safe hai.";
  if (e.status >= 500) return "Server abhi busy hai — bahut students ek saath aa rahe hain. Aapka account safe hai, kuch second baad dobara try karo.";
  return e.message;
}
/** "45s" or "14 min" for the wait after too many tries. */
export const waitText = (seconds: number) => seconds > 90 ? `${Math.ceil(seconds / 60)} min` : `${seconds}s`;

/** No automatic PIN retries. Honor server Retry-After with a visible countdown. */
export function useAuthSubmit() {
  const pending = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [retryAt, setRetryAt] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!retryAt) return;
    const timer = setInterval(() => { const time = Date.now(); setNow(time); if (time >= retryAt) setRetryAt(0); }, 1000);
    return () => clearInterval(timer);
  }, [retryAt]);
  async function run(validate: () => string, action: () => Promise<void>) {
    if (pending.current || retryAt > Date.now()) return;
    const validation = validate();
    setError(validation);
    if (validation) return;
    pending.current = true; setBusy(true);
    try { await action(); } catch (e) {
      setError(authErrorText(e));
      if (e instanceof ApiError && (e.retryAfterMs > 0 || e.status === 429)) {
        const time = Date.now(); setNow(time); setRetryAt(time + Math.max(e.retryAfterMs, e.status === 429 ? 30000 : 0));
      }
    } finally { pending.current = false; setBusy(false); }
  }
  return { busy, error, setError, retrySeconds: Math.max(0, Math.ceil((retryAt - now) / 1000)), run };
}