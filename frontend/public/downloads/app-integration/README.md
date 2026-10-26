# App-agent handoff

Start with APP_INTEGRATION.md, then design-tokens.json.

Canonical API: https://jeelive.ai/api
Rapid Fire: excluded; do not migrate it.
Data policy: same database, same learner IDs, same question/paper/attempt IDs. No resets, no duplicate accounts, no private student exports.

The live PYQ import now contains 30 reviewed papers / 2250 questions. Evidence distinguishes the live authorised-owner catalogue check from isolated two-session student tests. Recheck the same catalogue in the EXISTING native learner session; do not register another account to make an empty list disappear.

The new PIN and owner-only student-list revision is preview-only and tested, NOT published yet. Coordinate native client support before backend cutover. Current production login is still the legacy phone-only contract. Do not silently try legacy login after a failed PIN login.

Visuals are exact live website measurements plus original logo, font and icon assets and complete reference CSS. Home: JEE blue/platinum, All India ruby/onyx, BITSAT bright amber, COMEDK teal. Other pages retain the black/blood-red theme. Mobile references are 390x844. Native layout/shadow/font fidelity still requires on-device comparison.

No cookies, credentials, private source PDFs, answer keys, learner IDs or real student results are included. The isolated proof deliberately omits synthetic learner/attempt IDs as well.
