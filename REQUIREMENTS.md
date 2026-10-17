# Requirements update — new Volume 02 and latest user decisions

Authority: original approved `/app/plan/plan.md` remains baseline. Latest user changes supersede blue palette and student email/password/privacy assumptions.

## Latest approved decisions
- Teal-blue theme, primary #0F766E, navy #071A2B, page #F4FBFF. Existing simple role-aware navigation retained.
- Students enter only a phone number; no OTP, password, email, or name required. A number is an unverified lookup, not proof of identity. Anyone entering the same normalized number can access that profile's saved attempts and reports. User explicitly accepted this trade-off. State it on entry and in privacy notice.
- Owner/reviewer Content Studio remains password-protected and separate. Phone profiles cannot become staff.
- Capacity target remains >500,000 concurrent students, unproven pending provisioned infrastructure and measured workload tests.

## New source
`Tejas_Emergent_02_Exam_Formats_Scoring_Player.pdf`, 24 pages, saved `/app/sources/exam_formats.pdf` with complete extracted text.

### Apply to current MVP
1. Separate feature/API domains; reject unsupported/missing scoring and navigation policies.
2. Immutable content-addressed exam-profile registry: exam/year, source evidence, sections, duration, scoring, types, release mode; snapshot reference in each attempt.
3. Preserve supplied practice fixture: 75 questions, 180 min,20MCQ+5integer per subject =60MCQ+15integer. +4/-1/0 is owner-supplied custom scoring, not an official2027claim. There is NO conflict between these counts and new PDFp3.
4. Server grading with exact score ledger; reason codes, answer/key/content/profile versions, acknowledgement timestamps, release state. Show raw percentage without cohort percentile inference.
5. Explicit integer normalization (zero, negative,03, whitespace, Unicode minus); preserve exact raw entry. Decimal3.0 invalid under integer policy; no implicit rounding.
6. Visited/unvisited, saved answer, review/answered+review, pendingdraft and submitted states remain separate. CAS monotonically increasing answer revisions and idempotent acknowledgement.
7. Server deadline authoritative. Browser monotonic countdown; reconnect/refresh and clock changes do not extend server acceptance or cause premature voluntary submission.
8. Submission counts include pending drafts, permanent idempotent receipt.
9. Reviewed dispositions and explicitly versioned score corrections; never overwrite historical response records or original reports. A corrected score must be selected and labelled as a new version.
10. Source-text accessibility, keyboard controls, reduced motion, compact-mobile-practice label. Do not claim a formal screen-reader certification or taggedPDF guarantee.
11. Answer keys and unreleased solutions are absent from active API payloads. Session-level record separation still applies; same-number reopening is intentionally not identity-secure.
12. Deterministic score, persistence, timing, privacy, report and correction tests; handoff registry, APIcontracts, screenshots, unresolveddecisions.

### Retained future / blocked scope (do not advertise as available)
- Official year-verified simulation profiles: require actualselectedyearbulletinURL/retrievaldate/checksum/reviewerapproval. Authority homepages alone are not verifiedruleevidence.
- BITSAT conditionalbonus stage/irreversiblemainlock: no suppliedBITSATpaper or verifiedyearprofile; regularsingle-correctpracticeonlywhenreviewedcontentexists.
- WBJEE digitalOMR multi-select/2k/N rational partial credit and two sessions; COMEDK+1/0 official mode: remain approvedfuturephase2.
- Arbitrarydecimal/tolerance policy not enabled for the supplied integer fixture. Unsupportedformats failvalidation ratherthanborrowingJEErules.
- Cohortpercentiles/officialranks/proctoredexamclaims are not available. Insufficient realdata is notfilledwithinventedmetrics.
- Four-exam productiondemo, fullrestore/load/concurrencydrills, rolloutownerapproval remain releasegates, NOT fulfilled by this two-exam MVP.

## Source reading correction
The file-analysis tool initially hallucinated conflicts (60+15 vs20+5persubject) and incorrectly called the actualsuppliedpaperhypothetical. Those conclusions were rejected against the original PDFtext; actualsource reading governs.

## QA caution
Earlier testing imported/published a70-questionQA subset despite instructions to keep QA restricted. It was immediately withdrawn and all QAsets marked restricted/hidden. This is NOT the initialpaper, notacademicapproval and not75-questioncompletionevidence. All75originaldrafts remainpresent andunpublished. Final75-questiontestmust coverALL75—not omit5diagram-richitems.
