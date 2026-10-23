# Learner API route inventory

Generated from preview OpenAPI. Root: https://jeelive.ai. Paths below already contain /api; do not prefix /api twice.

Read 01_BACKEND_AND_AUTH.md and 03_TEST_ENGINE_AND_SYNC.md first. OpenAPI response schemas describe inner data; runtime envelope and cookies apply. Blank/general response schema means manually inspect known frontend decoding, not invent a fixed shape.

| Method | Path | Scope | Request body |
|---|---|---|---|
| GET | `/api/health` | public_or_handler_checked | — |
| POST | `/api/auth/login` | public_or_handler_checked | LoginPayload |
| GET | `/api/auth/session` | public_or_handler_checked | — |
| GET | `/api/auth/me` | authenticated_profile | — |
| POST | `/api/auth/refresh` | public_or_handler_checked | EmptyPayload |
| POST | `/api/auth/logout` | public_or_handler_checked | EmptyPayload |
| PATCH | `/api/auth/preferences` | authenticated_profile | PreferencePayload |
| POST | `/api/auth/phone` | public_or_handler_checked | PhonePayload |
| PUT | `/api/attempts/{id}/answers/{qid}` | authenticated_profile | AnswerPayload |
| GET | `/api/my/sets` | authenticated_profile | — |
| GET | `/api/my/sets/{id}` | authenticated_profile | — |
| POST | `/api/sets/{id}/preflight` | authenticated_profile | PreflightPayload |
| POST | `/api/sets/{id}/start` | authenticated_profile | StartPayload |
| GET | `/api/attempts` | authenticated_profile | — |
| GET | `/api/attempts/{id}` | authenticated_profile | — |
| POST | `/api/attempts/{id}/visit` | authenticated_profile | VisitPayload |
| POST | `/api/attempts/{id}/bonus` | authenticated_profile | EmptyPayload |
| POST | `/api/attempts/{id}/submit` | authenticated_profile | EmptyPayload |
| GET | `/api/attempts/{id}/results` | authenticated_profile | — |
| GET | `/api/attempts/{id}/questions/{qid}/asset/{kind}/{index}` | authenticated_profile | — |
| POST | `/api/attempts/{id}/questions/{qid}/solution-open` | authenticated_profile | EmptyPayload |
| POST | `/api/attempts/{id}/retry` | authenticated_profile | RetryPayload |
| POST | `/api/attempts/{id}/report` | authenticated_profile | ReportPayload |
| GET | `/api/competitions` | authenticated_profile | — |
| GET | `/api/competitions/{id}` | authenticated_profile | — |
| PUT | `/api/attempts/{id}/reviews/{qid}` | authenticated_profile | ReviewWrite |
| POST | `/api/attempts/{id}/expected-value` | authenticated_profile | ProbabilityInput |
| GET | `/api/chapter-exams` | public_or_handler_checked | — |
| GET | `/api/my/chapter-exams` | authenticated_profile | — |
| GET | `/api/attempts/{id}/solutions/{qid}` | authenticated_profile | — |
| POST | `/api/attempts/{id}/solutions/{qid}` | authenticated_profile | EmptyPayload |
| GET | `/api/attempts/{id}/cohort` | authenticated_profile | — |
| POST | `/api/attempts/{id}/air-scenario` | authenticated_profile | RankScenario |
| GET | `/api/exam-navigation/{slug}/catalogue` | authenticated_profile | — |
| GET | `/api/exam-navigation/{slug}/history` | authenticated_profile | — |
| GET | `/api/attempts/{id}/ai-solutions` | authenticated_profile | — |
| GET | `/api/attempts/{id}/question-reports` | authenticated_profile | — |
| POST | `/api/attempts/{id}/questions/{qid}/report-wrong` | authenticated_profile | QuestionReportPayload |
| GET | `/api/attempts/{id}/journey` | authenticated_profile | — |
| GET | `/api/my/tests/saved/{id}` | authenticated_profile | — |
| POST | `/api/my/tests/saved/{id}` | authenticated_profile | EmptyPayload |
| DELETE | `/api/my/tests/saved/{id}` | authenticated_profile | EmptyPayload |
| GET | `/api/my/tests` | authenticated_profile | — |
| POST | `/api/my/tests/compare` | authenticated_profile | CompareAttemptsPayload |
| GET | `/api/attempts/{id}/historical-rank` | authenticated_profile | — |
| GET | `/api/bitsat/branch-matches` | authenticated_profile | — |
| GET | `/api/series/all-india-jee` | public_or_handler_checked | — |
| GET | `/api/series/all-india-jee/history` | authenticated_profile | — |
| GET | `/api/series/all-india-jee/streak` | authenticated_profile | — |
