# Exam profile registry status

| Exam/profile | Status | Active implementation | Evidence boundary |
|---|---|---|---|
| Tejas200 Paper01 / JEE Main practice for2027 | Owner-supplied reviewdraft | 75Q =60singleMCQ+15integer;180min;+4/-1/0;free navigation | SuppliedpaperPDFandkeyPDF, notofficial2027rules; rights andacademicreviewpending |
| Custom JEE Main practice | Supported | Explicitreviewer timing/scoring;MCQ+exactinteger;postsubmit solutions | Everyset mustdefine approvedcontentandrules |
| Custom BITSAT practice | Categorysupported;nocontentsupplied | Single-correctpractice, explicittiming/scoring;noautomaticbonusstage | Mustreceive andreview actualBITSATcontent |
| JEE Main official-year simulation | Notactivated | Futureverifiedprofile | SpecificofficialbulletinURL,retrievaldate,reviewerapprovalandchecksummissing |
| BITSAT official-year simulation | Notactivated | Futureverifiedbonusgate/mainlockpolicy | Noapprovedyear-specificauthorityevidence orcontent |
| WBJEE digitalOMR | ApprovedfuturePhase2 | Requires2k/N rational partialcredit andseparatesessions | Notadvertisedasavailable |
| COMEDK officialmode | ApprovedfuturePhase2 | Requiresverifiedyear/count and+1/0 engineprofile | Notadvertisedasavailable |

Live immutable profiles are stored in `tejas_profiles`, keyed by SHA256 of canonical JSON. `/api/studio/profiles` exposes their factual registry to authorized staff; each attempt contains the sealed definition/reference. The registry includes year,sections,types,timer,scoring,numeric/navigation/releasepolicies and evidence fields. Noauthority homepage is treated as a verified examrule.

Scoring dispositions now supported forreviewedcorrections: standard, multipleaccepted(single-response acceptance set), dropped(excludedmaximum), bonus-to-all. Underreview is rejected. This is NOT multi-selectWBJEEpartialcredit; that format remainsunpublished.
