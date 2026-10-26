# Native adoption — iteration 36

## Source and boundary
- Owner ZIP downloaded only from `https://campus-search-debug.preview.emergentagent.com/downloads/JEELIVE_App_Integration_2026-10-26.zip`.
- Archive SHA256: `96653542287351d77909fc6052530431f04b160489c4fcc4a7e0ece153c8c2b0`.
- Safely extracted without running contained code; no traversal/symlinks; original export/docs/evidence preserved.
- Canonical academic API remains `https://jeelive.ai/api`. Preview download host is NOT an API/content fallback. Existing authentication and Rapid Fire endpoints/DB/identity integration were not changed.
- New PIN/signup/change-PIN contracts remain **preview-only / NOT activated in this app**. No PIN cutover or automatic phone-only fallback implemented. Native cookie persistence and PIN recovery/rate-hardening remain coordinated rollout gates.

## Implemented visual adoption
- `frontend/assets/website-2026-10-26/design-tokens.json` is a byte-identical copy of owner export. `src/websiteDesign.ts` reads the390px selector values, gradients and stops; `theme.ts` exposes them. Older flattened exam aliases no longer control home cards.
- Home only: JEE royal blue/platinum; BITSAT bright amber/espresso; COMEDK teal/onyx/mint; All India ruby/onyx. Exam hubs and other pages retain black/crimson. RF shared base colours unchanged.
- Native SVG gradient layering preserves CSS layer order, explicit/interpolated stops and aspect-ratio-correct CSS angles. Inner highlights/borders retained.7-second mobile shine with0/1.7/3.4second phase delays; pause/reduced-motion/background/focus handling. All India entrance finish uses1.5seconds/0.2second delay.
- **Native adaptations:** preserve previously requested2×2 grid and mobile navigation; therefore titles/padding/card heights are not the full-width42px/315px website cards. Native shadow rasterisation uses existing platform fallback; browser can render full exported box-shadow. No pixel-perfect/device parity claim.
- Official vector logo is hosted in managed object storage (public branding only) and served through `/api/brand/logo.svg`; response bytes SHA256 `4cec3778c23c429e1be0186c71db65da8ceece01ba736a14ed560623560faff2` matches package exactly. Native renderer removes only browser accessibility metadata (role/aria-labelledby), not vector paths/gradients. Wrapper owns accessible label; loading/retry states supplied.
- Official Atom/Orbit/GraduationCap SVG paths ported with exported stroke1.4. Figtree400–800 and Roboto Mono400–700 packaged/registered, OFL/Lucide licences included. No web-only UI libraries.
- PYQ radius11/cardpadding20; completed library green, saved crimson, active amber; selected academic tabs red/white; result score `rgb(121,13,26)` from measured state. Private original solution backgrounds untouched.
- Series schedule facts now wait for actual canonical response instead of showing fallback dates/counts during errors/loading.

## Contract comparison
- Inspected existing client and attempt controller against APP_INTEGRATION.md: strict response unwrap, single-flight401 refresh/retry, immutable start key, serverUUIDs, acknowledged revisions/request IDs, visible409 conflict handling, deadline anchoring, same-ID Continue,202 results, original solution crops in index order already exist. No auth cutover made.
- Existing account/result/source-image parity baseline:9/9 tests passed before new pilot writes (`test_reports/pytest/iter36_readonly_baseline.xml`). Source student catalogue30 in main browser smoke. Further packaged-ID/2250-count and fresh pilot verification in iteration36 report.
- No student crops sent to object storage. Only the public brand SVG is added there; canonical crop endpoint remains private.
- Tool screenshots are Expo **web preview**, not physical Android/iOS persistence proof. Isolated tests packaged by website team are not counted as native production proof.

## Latest user correction — original card artwork is mandatory
- User paused: "Bhai theme rkhna hai jeelive se lekin card ka icon kyu badal diye ? Screenshot diya hu". Screenshot explicitly shows red target/radar, blue diamond, orange rocket, black/gold crown. This **supersedes** applying exported home-card symbols/gradients to these four cards.
- Restored exact existing `assets/images/tile-{jee,live,bitsat,comedk}.jpg` artwork (no crop rewriting/recolouring/new icon drawing) in the original large image-top/native2×2 layout. Dark/crimson JEELIVE app theme, typography, official logo and remaining academic styles preserved. Lucide ExamGlyph replacement removed.
- Primary images now live in managed public storage behind allowlisted `/api/brand/cards/{kind}.jpg`; byte equality to all4 originals verified. Identical bundled files are offline fallback, not a different icon. Public cache only; no learner crop/data is stored there.
- Card artwork is static; live-series banner retains the exported ruby/onyx treatment and optional sheen. Its switch moved/labeled for the series banner so it no longer implies animation of the4 original pictures.
- Main390/320 screenshot smoke: original4 artworks loaded; JEE card still opens real30-paper PYQ list. No writes during this corrective smoke.