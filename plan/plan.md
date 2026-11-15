# JEELIVE.AI: Simple PIN, One Account, Exam-Day Readiness

A student who forgets the PIN sets a new one in three steps, with no OTP, on the website and in the app.
The same number and PIN work on both, and the site is checked and prepared for a first live exam of 20,000 to 1 lakh students.

## Who it's for

- **Students:** sign up once, use the same number and PIN on the website and the app, and reset a forgotten PIN themselves.
- **Owner:** no more PIN reset requests, a plain report of what is wrong on the live site, and a clear list of what 1 lakh students need.
- **App agent:** one short message that says exactly which server calls the app must use.

## What was found before writing this plan

Read from the code, not yet run:

- The website login has no "Forgot PIN". It tells the student to ask the owner. A student who forgot the PIN cannot get back in alone.
- A PIN can be changed only from inside Profile, after signing in.
- Older students who never set a PIN cannot sign in at all unless they are still signed in somewhere.
- Not yet checked: whether the Change PIN button inside Profile itself fails. It is tested first, and fixed if it does.

Website and app, by design:

- Both use one server and one student list. A student who signs up on the website can sign in on the app with the same number and PIN, and the other way round.
- This holds only if the app calls the same server with the same sign-up and sign-in calls. The app's code cannot be seen from here, so this is not confirmed.
- Rapid Fire has its own separate accounts. That stays as it is.

## Core features and experience

### 1. Forgot PIN (website)

- A "Forgot PIN?" link under the PIN box on the login screen.
- One screen: mobile number, new 4-digit PIN, confirm PIN.
- A "PIN changed" confirmation. The student is signed in and continues to Home.
- No OTP, no old PIN, no owner approval.
- Works for every student number, including older accounts that never had a PIN.
- A number with no account shows "No account with this number" and a link to create one.
- The line "There is no public PIN reset" is removed from the login screen.

### 2. Change PIN inside Profile

- Stays where it is: new PIN, confirm, save.
- Tested first. If it fails, the cause is found and fixed.

### 3. One account on website and app

- The same Forgot PIN call is opened for the app, so the app's Forgot Password screen can use it.
- The app guide is updated.
- The read-only look at the live site (item 5) shows whether the app's sign-ups arrive at the same server as the website's.
- The message for the app agent:

```
Use one server for everything: https://jeelive.ai/api
Do not keep a separate student list. Rapid Fire stays separate, as today.

Sign up:            POST /auth/phone/signup   phone, pin, confirm_pin
Sign in:            POST /auth/phone          phone, pin
Change PIN (signed in): POST /auth/pin        phone, new_pin, confirm_pin
Forgot PIN (not signed in): POST /auth/pin/reset   phone, new_pin, confirm_pin
   -> signs the student in, same reply as Sign in
   -> works on jeelive.ai only after the next deploy

PIN is text of exactly 4 digits. Keep leading zeros.
Keep the cookies the server sends and send them on every call. There is no bearer token.
Identify the student by the server's user.id, never by a local id.
After any PIN change, other devices are signed out. Saved answers and results stay.

Check: sign up on the website, sign in on the app with the same number and PIN,
and My Tests must show the same attempts. Then repeat the other way round.
```

### 4. Sign-in rush before a live exam

- Seen in the code, not measured: every sign-in checks the PIN with a deliberately slow lock. On the two small live servers this could allow only a few hundred sign-ins per minute.
- 20,000 students signing in within 15 minutes need about 1,300 per minute.
- The real number is measured first. If it is too low, the student PIN check is made lighter. Staff passwords are not changed. Existing PINs keep working.

### 5. Read-only look at the live site

Nothing is changed and no test account is created. A plain report covers:

- whether the earlier deploys and the first nightly data repair actually completed
- error and slow-request counts, including the 30-second hangs seen earlier
- whether the live server allows the safe PDF reader
- database size, the lookups that are slow, and whether a backup is visible
- whether sign-ups from the app reach this server

Any fix on live waits for the word "deploy".

### 6. Server size for 1 lakh

- Measured earlier, not re-measured: the live site runs on 2 small servers. That is about 10,000 exam starts per minute and roughly 16,000 to 22,000 students writing at once.
- 1 lakh at once needs about 10 to 12 CPUs and a database that takes about 1,400 answer saves per second.
- This cannot be fixed in code. A ready request for platform support is prepared with these numbers, for the owner to send.

### 7. Three small known faults

- A tab left open across a deploy shows "We couldn't open this screen" on the next click. It will reload itself once instead.
- The clean source line could lose the exam name just after a server restart. Confirmed first, then fixed.
- A PDF restored from the Library after it was read does not come back in the Uploads panel. It will.

## User flow

1. A student opens Login and taps "Forgot PIN?".
2. The student enters the mobile number, a new PIN, and the PIN again.
3. "PIN changed" appears and the student is on Home, signed in.
4. The student opens the app and signs in with the same number and the new PIN. My Tests shows the same attempts.
5. A signed-in student can still change the PIN from Profile.
6. The owner reads the live report and sends the server-size request to platform support.

## UI/UX feel

- Same dark theme and the same login card.
- One link, one screen, one confirmation. No extra steps or warnings.
- Large number boxes that open the number keypad on a phone.
- Short, plain English messages.
- Works fully at phone width.

## Implementation phases

**Phase 1 (built now):** the seven items above. Forgot PIN, Change PIN check, one account with the app message and guide, sign-in rush, read-only live report, server-size request, three small faults.

**Phase 2 (separate approval):**
- One staged load test at exam size after the servers are enlarged.
- A short waiting line under overload, so answer saves are not turned away.
- 100 MB PDFs uploaded without holding the whole file in memory, and one real 100 MB storage test.
- Faster reading of very large PDFs.
- Decimal numerical answers.
- Browser checks still open: replacing mocks with a new PDF, a series day while it is open, photo and Excel upload.
- A check of student-history lookups at 1-lakh size.

**Phase 3 (separate approval):**
- Scanned (photo) PDFs.
- A database backup and restore drill.
- The 30-second hangs at the network edge, taken up with platform support.
- Series cards for new exams in the app.
- The earlier Master Phase 2 and 3 items.

## Assumptions

1. "Forgot Password" is labelled "Forgot PIN?" because students have a PIN, not a password.
2. Anyone who knows a student's mobile number can set a new PIN for it, open that student's tests and results, and sign that student out. This follows the owner's words: "Anyone can change any phone number or password, and it's okay."
3. This also applies during a live exam. Someone can sign another student out in the middle of a ranked paper, or submit it. No guard for this is included. One can be added on request: no outside reset while that student's live paper is running.
4. A limit stays: 5 PIN resets per number in 15 minutes, then a wait message.
5. After a reset, every other device on that number is signed out. Saved answers, attempts and results stay. A running attempt continues after signing in again.
6. A number with no account is not created by Forgot PIN. The student is sent to sign-up.
7. Owner and reviewer logins (email and password) cannot be reset this way.
8. The owner's reset in Super Admin › Students stays.
9. The privacy page gets one honest line: a PIN can be reset by anyone who knows the number.
10. "It is there in the app" is read as: the app already has a Forgot Password screen. The app's code is not visible from here, so the app side is done by the app agent.
11. Rapid Fire accounts and server are not touched.
12. The student PIN check is made lighter only if the measurement shows sign-in is too slow.
13. The live look is read-only. The 100 MB storage test is not run, as it was not chosen.
14. The capacity numbers are from earlier measurements. Phase 1 does not include a new load test.
15. The server request is sized for 1 lakh, the top of the range given.
16. One deploy carries everything built in preview. Forgot PIN reaches jeelive.ai together with the one-time cleanup: old non-PYQ tests go to the Library and the JEE Main series loses its papers but keeps its dates. Nothing goes live until the owner says "deploy".
17. The note "Deprecated. The not code" was not understood. Nothing is removed or changed because of it.
18. Screen labels stay in simple English.
