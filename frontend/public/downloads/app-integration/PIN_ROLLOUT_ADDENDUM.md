# PIN rollout addendum — 2026-10-26

This supersedes the previous handoff's statement that the longer-window PIN budget is pending. No endpoint path, body, response schema, session-cookie format, learner ID or attempt contract changes.

Prepared website/backend now also retains an atomic per-number maximum of **20 incorrect PIN checks per fixed clock hour**. A successful sign-in releases only its own reserved check; it does not erase earlier failures from that hour. The existing five-attempt/15-minute guard remains. Concurrent checks occupy a reservation before verification. At the hourly limit, even the correct PIN must wait: honour the server's `Retry-After`, avoid automatic retry loops and do not fall back to legacy phone-only login.

Public-peer IP throttling runs first, so already IP-blocked traffic cannot consume a target number's quota. Shared private ingress still needs operator-configured trusted client-IP forwarding before any per-client IP protection is claimed; raw forwarded headers are not trusted. An attacker knowing a number can cause temporary account lockout with wrong guesses; this is the rate-limiting trade-off for the chosen short PIN, not full identity verification.

Known limiter database failures fail closed with HTTP503 and Retry-After3; no session is issued. A failed/incomplete verification can retain its reservation conservatively until the budget expires.

**Not deployed:** the live canonical backend remains unchanged pending coordinated native PIN client rollout. Do not publish the prepared PIN backend while the native app still depends on phone-only login. No payments, OTP or Rapid Fire changes. Existing accounts/history are preserved. Existing profiles set their first PIN from an existing authenticated session; no public takeover/reset flow was added.

Validation: isolated real-backend tests cover failures interleaved with successes, concurrent guesses, budget rollover, phone normalization, independent accounts and existing owner/student permissions. No production test accounts or attempts were created.
