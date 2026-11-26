# Part 6 — One account for the website and the app

## 6.1 The rule, and how it already works

The owner (26 Nov 2026): a student who signs up on the website can sign in to the app, and one who signs up in the app can sign in on the website, whenever they like. The two together make **one user list**, and one sign-up gives the student everything on both sides.

**This is already how it works.** It was checked from the app's code and its live answers on {{TODAY}}:

- **The app has no account system of its own.** Signing up, signing in, the session, renewing it, changing the PIN and signing out are all **the website's own doors**. The app's server passes them on unchanged to `https://jeelive.ai/api/…`.
- So **an account made in the app is a website account**, and the same phone number and PIN sign in on jeelive.ai. **An account made on the website signs in to the app** at once. Nothing is copied from one side to the other: there is only one account, the website's.
- **One user list:** the website's. The app's server keeps only the app's own extras (Rapid Fire profile, coins, diamonds, friends, Dream College, Mission) under the **website's own student id**. It reads that id from the website's `GET /api/auth/me` and never makes up an id of its own.
- **The browser Rapid Fire** (Part 5) signs in the same way, with the same id.

[[shots: a01_signin | 18. The app's sign-in screen: the same phone number and PIN as on jeelive.ai]]

## 6.2 Every door the app uses for accounts

All of them go through the app's server, at `…/api/jl/<path>` of the app, to `https://jeelive.ai/api/<path>`, with the website's own cookies. The cookies are kept on the app's server for each device, never on the phone.

| What the student does in the app | The website's door | Sent | What the app needs back |
| --- | --- | --- | --- |
| Sign up | `POST auth/phone/signup` | `phone`, `pin`, `confirm_pin` | the student (with `id`) and the session cookies |
| Sign in | `POST auth/phone` | `phone`, `pin` | the same |
| Open the app | `GET auth/session` | — | `{ "user": … }`, or `user: null` when signed out |
| Session renewal | `POST auth/refresh` | — | new cookies |
| Who am I | `GET auth/me` | — | the student, with the same `id` |
| Change PIN (signed in) | `POST auth/pin` | `phone`, `new_pin`, `confirm_pin` | success. Other sessions end; this one stays, and its `id` must not change |
| Sign out | `POST auth/logout` | — | success |
| Forgot PIN | on the app's server: `POST /api/account/forgot-pin`. The website has no public reset, so the app's server uses the website owner's own reset for that number | — | — |

The exam a student chose, papers, attempts, results, Misfire and the All India series are all read from the website under the same session (Parts 1 to 4).

## 6.3 What the website must keep, so it stays one account

1. **The doors of Part 6.2 and their fields**, as they are. Above all, `user.id` in the answers of `auth/phone`, `auth/phone/signup`, `auth/session` and `auth/me`.
2. **A student's `id` never changes.** Not on a PIN change, not on a phone change, not ever. The app's extras (coins, friends, Rapid Fire ranks, Dream College) hang on it. A new id would leave the student without them.
3. **One phone number = one account.** Signing up again with a number that already has an account must be refused with a plain sentence ("this number already has an account: sign in"), never answered by making a second account.
4. **The same PIN rules on both sides.** The app checks a PIN's shape before sending it and shows the website's own message when the website refuses one.
5. **Never a second user list.** The CEO dashboard joins the two sides on this one `id` (the `uid` of its export); the app's server keeps no copy of phone numbers to edit. It keeps only what it needs for friend search: a one-way hash and the last four digits.
6. A new sign-in door (an OTP, a login with Google…) must give the **same** student id for the same person. Tell the app side before such a door goes live.

## 6.4 What is not automatic

- **Being signed in on one device or browser does not sign another in.** On a new phone, or in the browser Rapid Fire, the student types the same phone and PIN once. Opening the browser Rapid Fire straight from a signed-in website, without typing again, is the plan of Part 5.4: written, not built.
- **Signing out in the app** sends the website's own `auth/logout` for that device's session, and forgets the account on that phone.

## 6.5 Deleting an account

- The app has an in-app "delete my account" request (and a public web page for Google Play). It **erases the app's own extras at once** and signs every device of that account out of the app.
- **The website has no door to delete an account.** The website account is deleted **by the owner on the website by hand**, within 30 days, from the list in the app's owner panel. While a request waits, the app does not sign that account in again.
- If the website ever adds a delete door, tell the app side: the request can then be finished in one step.

## 6.6 How it was checked ({{TODAY}})

- The app's code: sign-up, sign-in, session, renewal, PIN and sign-out are only ever sent to the website's doors above (`frontend/src/auth.tsx`, `frontend/src/api/client.ts`, `backend/jl_proxy.py`). Rapid Fire takes its id from the website's `auth/me` (`backend/rf_access.py`).
- The live answers: the website's `GET /api/auth/session` answers for a signed-out visitor (Part 3.7). The test learner's account is a website account: its papers, results and Misfire are the website's, and it signs in to the app and to the browser Rapid Fire with the same phone and PIN.
- **Not done by the app side:** a brand-new account made in the app and then used on jeelive.ai (it would add a real account to the website's list). The website agent can do it on its test setup: sign up in the app's preview with a throw-away number, sign in on the website with the same number and PIN, and check that `auth/me` gives the same `id` on both.
