# JEELIVE.AI — Study Notes (pre-build)

## Sources copied locally (read-only reference, NOT run)
- /app/reference/handoff/  → full handoff ZIP (docs 00-07, OpenAPI, postman, web reference components, logo assets)
- /app/reference/github/   → GitHub repo backend (tejas/ 66 modules, server.py), web frontend src, parsed chapter JSON
- /app/reference/api_samples/ → live catalogue responses (JEE Main + BITSAT, all subjects)

## Live backend (source of truth, unchanged)
- Root: https://jeelive.ai/api — health OK, envelope {data,error,meta}
- Auth: POST /auth/phone {phone} → unverified_phone profile, cookies access_token(15m)/refresh_token(7d). No bearer.
- Refresh: single-flight POST /auth/refresh {} on 401, retry once.
- Pilot test profile used for read-only probing: phone 9000000001 (user id db0c62b8-...)
- Server "today" = 2026-10-23; series prelaunch, first day 2026-12-01, 62 slots, last 2027-01-31.

## Live content snapshot
- JEE Main chapters: Physics 29, Chemistry 23, Maths 26 (50 Q each; Phy 90m, Chem 70m, Maths 120m; +4/-1/0; supplied worked solutions)
- BITSAT chapters: Physics 30, Chemistry 32, Maths 32 (50 Q each; +3/-1; answer-key only)
- JEE Main mocks: 0; COMEDK: 0 (honest empty states)
- Catalogue item fields: id,title,rules{correct,wrong,skipped,minutes,numeric_rule,solution_release},count,maximum,types{mcq,integer},chapter_subject,chapter_number,solution_kind,attempt,saved,live_enabled,start_at,end_at

## Key contracts (see handoff/03)
- preflight → start(start_key persisted, reused on retry) → attempt {questions, answers, visited, deadline, server_now, rules, bonus_rule}
- PUT answers/{qid} {value,marked,revision,request_id,confidence?}; ACK correlation by request_id; 409 = conflict, no auto-bump
- visit returns visited list; submit {} → 202 grading; results ?score_version=; jobs/{id}, jobs/{id}/retry
- assets: /attempts/{id}/questions/{qid}/asset/{question|solution}/{index} (PNG, cookie-auth)
- solution-open (consultation) ≠ legacy POST solutions/{qid} (410, never call)
- reviews PUT (categories: concept_gap, calculation, silly_mistake, time_pressure, misread, guess, other; note ≤500)
- report-wrong (category question/key/solution/display; note ≤600)
- my/tests?tab=progress|saved|completed, compare, saved/{id}
- series/all-india-jee, /history, /streak

## Rapid Fire — not in existing backend → our own FastAPI + Mongo (cards + session history, per profile id)

## Deep-dive learnings (backend source)
- Question delivered: id, number, subject, section, type(mcq|integer), text, options{A..D}, topic, render_mode(source|typed), solution_kind, accessible_text, asset_count, bonus. Source-mode questions = original PDF image (options say "See original option A") → MUST render PNG asset.
- Attempt view: id,set_id,title,exam,mode,rules,started_at,deadline,status,answers{qid:{value,marked,revision,request_id,accepted_at}},visited[],questions[],server_now,count,bonus_unlocked_at,series_id,confidence_observations
- Submit → {id,receipt,status,submitted_at,sealed_seq,grading_status}; 202 if not ready
- Results: embargoed {status:'embargoed',release_at} | 202 {status:'grading',job_id,grading_status,retry_after_ms} | full: summary{score,maximum,percentage,correct,incorrect,skipped,dropped,bonus,attempted,accuracy,attempt_rate,penalties,total_seconds,subjects{name:{count,correct,attempted,score}},topics,sections?,main_block?,bonus_block?}, questions[rows: +response,outcome(correct|incorrect|skipped|dropped|bonus),marks,accepted_answers,marked,solution,asset_count,solution_asset_count], analytics, review, insights, grade_versions[], score_version, change_note, review_states
- historical-rank: {state,label,score,maximum,rank_low,rank_high,percentile_low/high,reason,limitation}; only full 300-mark JEE / COMEDK 180 mocks; BITSAT → branch_matches {matches[{programme,campus,cutoff,margin}],next_targets,limitation}
- journey: {state:'unavailable',reason} for chapter tests
- my/tests items: id,set_id,title,exam,status(active|expired|embargoed|completed|grading),mode,remaining_seconds,saved_answers,count,summary,resumable,result_available,compare_eligible
- compare: {left,right,score_delta,accuracy_delta,time_delta,subjects[{name,before,after}],basis}
- BITSAT chapters: source questions, answer_key_only. JEE chapters: supplied_worked.
