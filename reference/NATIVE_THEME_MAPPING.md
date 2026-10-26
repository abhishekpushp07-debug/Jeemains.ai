# Academic website → native theme mapping

## Sources used
- Owner handoff: `reference/handoff/reference/learning-workspace.css` (exam tone definitions, card finish, learning segments, library/results rules).
- Current public repository: `https://raw.githubusercontent.com/abhishekpushp07-debug/Jeemains.ai/main/frontend/src/pyq.css`, retrieved during iteration 35.
- Repository `frontend/tailwind.config.js` was also checked. Its generic font defaults do not override the explicit Figtree academic stylesheet; keep Figtree 400–800 already bundled in the app.
- Existing charcoal/red semantic theme remains unchanged. CSS files are reference material, never imported into React Native.

## Native mapping
| Website rule | Native implementation |
| --- | --- |
| JEE `#B00000`, white CTA, `#8A0000` CTA text | `examCardColors('jee')`, ExamTile and ExamHub |
| BITSAT `#FF9933`, dark `#2B1600` text, `#3D1D0A` CTA | `examCardColors('bitsat')` |
| COMEDK `#101115`, `#E5D5AF` accent, `#ECEEF2` CTA | `examCardColors('comedk')` |
| 18px mobile exam corners, glass/orbit decoration, 48px CTA | ExamTile StyleSheet; native press-scale instead of hover |
| 4.8s mobile shine, reduced-motion, pause control | ExamCardFinish Animated/LinearGradient; pauses when unfocused/backgrounded; Home switch |
| PYQ mobile padding 20px, heading 18px, 24px action gap | PyqPaperCard; original year/shift direct list/actions retained |
| Active amber, completed sky blue, saved sapphire top borders | My Tests and PYQ state styles; LearningBadge always includes text |
| Maroon score panel | Results Analysis score card |
| Analysis maroon / Progress amber / Confidence sky blue / Rank sapphire / Solutions crimson | LearningTab soft surfaces, dark matching text and 3px active underline |

Native adaptation is intentional: preserve the app's requested 2×2 home grid, mobile navigation, safe areas, scrolling and >=44px touch targets. Titles wrap instead of truncating on narrow phones. This is token/style alignment, **not a claim of pixel-identical desktop/mobile layouts or complete website feature parity**.

## Data boundary
No authentication, academic API, canonical origin, question/solution transformations, learner IDs, or Rapid Fire backend/content changes in this theme pass. All academic requests still use the canonical `jeelive.ai/api` (native directly; preview via `/api/jl`). Rapid Fire stays separate, including its palette and ChapterSheet.

## Live data observation
Iteration 35 initial canonical learner probe now returns 30 papers for years 2026 and 2025, each with 75 questions. The old zero-papers blocker is no longer reproduced. Full same-source flow/parity verification follows in the test report; no paper import or website admin action was performed here.