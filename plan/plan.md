# JEELIVE.AI — Student Login aur Simple, Powerful Superadmin

Students ke liye phone number aur 4-digit PIN se login, verified email se recovery aur free/paid test series ka clear access.
Owner ke liye ek easy control panel: students, papers, series, prices, payments, posters aur thumbnails ek jagah manage honge.

## Who it's for

- JEE Main, BITSAT aur COMEDK ki preparation karne wale students.
- Owner/superadmin, jo bina technical knowledge ke platform operate karna chahta hai.
- Experience itna straightforward hoga ki 10th-class level ki computer understanding wala person clear instructions follow karke use kar sake.

## Core features and experience

### Student signup, login aur recovery

- Signup mein exactly chaar main fields: **Phone number, Email ID, Create 4-digit PIN, Confirm 4-digit PIN**.
- Agle step mein email par **4-digit OTP**. Website par OTP verify karne ke baad account activate hoga.
- Regular login: **Phone number + 4-digit PIN**; har login par OTP nahi.
- “PIN bhool gaye?”: registered phone enter → linked email par 4-digit OTP → website par OTP enter → naya PIN aur confirmation.
- OTP short-lived aur single-use hoga. Resend countdown aur repeated incorrect PIN/OTP par temporary lock rahega.
- Reset ke baad purane logged-in sessions band honge. PIN kisi student list, email ya admin screen mein nahi dikhega.
- Duplicate phone/email, PIN mismatch aur invalid details par simple field-level messages.
- SMS OTP ka connection-ready provision rahega, lekin abhi SMS send nahi hoga. Admin mein **“SMS not connected”** status; student ko fake “SMS sent” message nahi milega.

### Superadmin account aur dashboard

- Designated superadmin login ID: **7004186276**. Selected preference ke mutabik phone number aur 4-digit PIN se login, extra login OTP nahi.
- Superadmin identity normal student signup se claim nahi ho sakegi. Existing owner access retain rahega.
- PIN public page ya plan mein repeat nahi hoga; secure account setup mein configure hoga.
- Dashboard: actual students, active/blocked accounts, draft/published series, successful payment totals aur attention-needed items. Invented numbers nahi.
- Main sections: **Dashboard, Students, Test Series, Papers, Posters & Thumbnails, Payments, Settings**.
- Direct actions: **Add Series, Add Paper, Upload PDF, Create Poster**.
- Important changes ki history: kisne student block kiya, price badla, paper publish kiya ya access diya.
- Short inactivity timeout aur sensitive actions se pehle clear confirmation.

### Student management

- Phone/email se search; Active, Blocked aur Pending verification filters.
- Student detail mein enrolled series, validity, payment history aur existing attempts/results ka read-only overview.
- Activate, block aur reactivate. Blocking se login/protected access rukega, saved attempts delete nahi honge.
- Account status aur individual series access alag controls honge.
- Complimentary access dena, expiry badalna ya access revoke karna, reason aur history ke saath. Complimentary access ko paid transaction nahi dikhaya jayega.
- PIN dekhne ki jagah safe reset help. Verified email na hone par owner-reviewed recovery; sirf number batane se purana account handover nahi hoga.
- Is phase mein permanent bulk student/result deletion nahi hogi.

### New test-series management

- Series name, exam, description, instructions, start/end dates, paper order aur access validity.
- Har series par **Free / Paid**, selling price, poster, thumbnail aur visibility controls.
- Existing paper choose karna ya naya paper banana; appropriate series mein assign karna.
- Duration, marks, negative marking, availability aur result/solution release rules.
- **Draft → Preview → Publish → Archive**. Draft public nahi dikhega.
- Publish se pehle missing questions, answers, dates ya price ki readable checklist.
- Student-view preview mein actual card, price, instructions aur included papers.
- Published paper edit se already-started attempts ya purane marks silently nahi badlenge.
- Existing JEE PYQ/chapter content preserve rahega. Existing All India schedule/rules automatically replace nahi honge; nayi series separately manage hongi.

### PDF upload aur manual paper editor — dono

- Existing papers ka searchable chooser.
- PDF upload progress, processing status aur question-wise review.
- Original question, diagram, answer aur solution crops inspect/correct karke map karna.
- Incomplete paper ya missing source answers ko publish-ready nahi dikhaya jayega; missing content invent nahi hoga.
- Manual editor: subject, question, options, MCQ/numerical answer, marks aur solution; maths notation aur diagram/image support.
- Question reorder, draft save aur student preview.
- Solutions sirf appropriate result/review stage par; active attempt mein answers reveal nahi honge.
- Naya automatic AI-solving flow included nahi hai.

### Razorpay payments aur rates

- Free series seedhe accessible; paid series ka price aur validity purchase se pehle clear.
- Razorpay checkout; available payment methods merchant account approval par depend karenge.
- Confirmed successful payment ke baad automatic series access. Sirf browser ke success message se paid access nahi milega.
- Pending, failed aur cancelled payments ke honest status aur retry. Duplicate payment confirmation se duplicate purchase/access nahi banega.
- Admin payment list: student, series, amount, status aur payment reference. Student ko apni purchase history.
- Existing purchase ka paid amount aur agreed validity future price change se nahi badlenge.
- Phase 1 mein refunds Razorpay dashboard se initiate honge; app confirmed refund status reflect karega. Full refund par us purchase ka access revoke hoga, separate valid/complimentary access preserve rahega. Partial refund se automatic access removal nahi.
- Live payments ke liye activated Razorpay account aur secure connection required. Connection incomplete ho toh paid purchase disabled rahegi, fake success nahi.
- Existing free material free rahega. Paid offerings publish hone par blanket “sab kuch 100% free” claims ko accurate free/paid wording mein badla jayega; actual free-content labels retain rahenge.

### Posters aur thumbnails

- Ready-made brand-matched templates: series name, image, price, dates aur short text edit karna.
- Apna image/poster upload, crop, preview aur series par assign karna.
- Poster image download aur saved media reuse.
- Phone/desktop card preview; approved promotional media related content publish hone par public hoga.
- Original question/solution files promotional media ki tarah public nahi honge.
- Yeh focused template editor hoga, full Canva-style application ya AI image generator nahi.

## User flow

**Naya student:** Chaar signup fields → email ka 4-digit OTP → account ready → phone + PIN login → series choose → free access ya Razorpay purchase → Start Test → Resume / Result / Solutions.

**PIN recovery:** Registered phone → linked email OTP → website par verification → naya PIN confirm → fresh login.

**Superadmin:** Phone + PIN login → dashboard → student search → details dekhein → activate/block ya series access change → confirmation.

**Nayi series:** Add Series → details aur price → existing/PDF/manual papers → schedule/rules → poster/thumbnail → student preview → Publish.

**Purana student profile:** Existing verified email se ownership confirm karke PIN setup. Verified recovery email na ho toh owner-reviewed recovery. Sirf phone aur nayi email bhar kar purana profile claim nahi hoga.

## UI/UX feel

- Existing premium black/blood-red brand aur current logo retain rahenge.
- Approved colours unchanged: **JEE blue–platinum, All India ruby–onyx, BITSAT amber, COMEDK teal**, opening page aur logged-in Home dono par consistent.
- Readable text, clearly named buttons, limited primary actions aur plain-language instructions; technical jargon nahi.
- Long forms chhote steps mein. **Save Draft, Preview, Publish** clearly distinct.
- Mobile-friendly forms, PIN ke liye number keypad, show/hide control aur clear errors.
- Risky actions par exact effect: “Student ka access block hoga; results delete nahi honge.”
- Daily operations mein complicated charts ke bajay searchable lists aur useful status labels ko priority.

## Implementation phases

### Phase 1 — MVP: daily-use platform, abhi banega

Student signup/login, email verification, 4-digit email OTP recovery, designated superadmin, student/account/access management, new-series creation and prices, Razorpay purchases, PDF review/import, manual question editor, poster/thumbnail templates, draft/preview/publish aur action history. SMS connection-ready status rahega; real SMS disabled.

### Phase 2 — SMS activation aur support expansion, later approval par

SMS service/account aur required sender/message approvals milne par real SMS OTP aur phone ownership verification activate karna. Team add karni ho toh limited-access support/content staff accounts; sabko superadmin rights nahi.

### Phase 3 — Advanced operations, later approval par

Series-wise sales/engagement reports, larger content batches ke guided bulk controls aur richer reusable poster templates. Yeh Phase 1 approval ka automatic extension nahi hai.

## Assumptions

- “Rate wate” ka matlab new-series pricing aur paid access maana gaya hai. Prices INR mein, primary audience India; per-series one-time purchase, recurring subscription nahi.
- Safe email recovery ke liye signup par email OTP verification included hai. Regular student/superadmin login selected phone + PIN hi rahega.
- **4-digit PIN, especially superadmin ke liye, longer password aur extra verification se kam secure hai.** Chosen simple login retain hoga, attempt limits aur locks ke saath; equivalent security ka claim nahi hoga.
- Chat mein share hua PIN permanent secret ke liye recommended nahi hai. Secure account setup mein PIN enter hoga; public page, email ya plan mein expose nahi hoga.
- SMS activate hone tak email verified hogi, phone ownership verified nahi maana jayega. Phone login identifier hoga; false phone-verification badge nahi lagega.
- Ek phone aur ek email se ek student account. Existing unverified profiles ka automatic takeover nahi; owner-reviewed recovery.
- PIN/email OTP ke five failed attempts par 15-minute temporary lock; OTP lifetime 5 minutes aur resend wait 60 seconds. Superadmin inactivity timeout 15 minutes.
- Email JEELIVE.AI display name se managed sending address se aayegi. Custom jeelive.ai sender address assume nahi kiya gaya. Email service availability/usage balance par depend karegi; delivery failure par verification bypass nahi hoga.
- Payment connection secrets secure settings se liye jayenge, chat se nahi. Real collection merchant activation aur required business details/policies ke bina enable nahi hogi. Tax registration aur refund terms invent nahi honge.
- Existing owner access, free academic content, saved solutions aur student history preserve rahenge. Is plan mein data reset ya existing exams ka redesign nahi hai.
- Primary owner/superadmin ka complete daily workflow Phase 1 mein hai. Permanent bulk deletion, promotional email blasts aur new AI generation included nahi hain.
- Yeh proposal hai: abhi account creation, PIN change, payment activation ya application coding nahi ki gayi hai.
