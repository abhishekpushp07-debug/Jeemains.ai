# Handoff 2026-11-25 (07:25 UTC): Super Admin "storage machine"

For the next (forked) agent. Scope: only the Super Admin file-save machine (upload PDF → read → Draft → Live), worked on 23–25 Nov.
Dates and times are the pod clock, UTC. Owner-facing reports are written in simple Roman Hinglish (`memory/NIGHT_REPORT.md`).

---

## 0. Read this first

1. **Nothing is deployed.** jeelive.ai still runs the code of 23 Nov 23:00 (commit `7e9e3ab`; inferred by reading the live site without login, not from a deploy log). Deploy only when the owner writes the exact word **"deploy"**.
2. **Packets A, B, C, D are built and tested in preview. Packets E, F, G are not started.** For E only code was read; no code was written.
3. **Before any deploy, one thing is still missing:** a separate code review of the Packet D code (rule I.3 of the plan). Testing-agent checks are done for A–D.
4. The approved plan is `/app/plan/plan.md` (Roman Hinglish, 404 lines). It is the source of truth for what E, F and G must do. Its status table was updated in this session.
5. Tests: **one isolated suite or one bridge at a time**, and raise the mongod open-file limit first (section 9). Parallel runs crash the preview MongoDB.
6. Never touch `frontend/src/features/LiveSeries.js`. Never touch verified JEE Main PYQ. No email/SMS/external alerts.
7. The owner is awake again. The night-time permission "build without asking" was for that night. The plan's own rule is: stop after every packet, report, wait for the owner's yes (section 12 lists the decisions he has to take).

---

## 1. Was the last 24 hours only Super Admin?

Screens: yes. Since the live commit, every changed screen file is under `components/master/`, `features/admin/master/` or `master.css`, plus one label in `components/admin/AdminShared.js` ("Atki hai" status chip). No student screen changed. `LiveSeries.js` was last changed 23 Nov 22:53, before the live commit; its diff since then is empty.

Server: mostly Super Admin modules, but three shared files changed, which student flows also use:
- `backend/tejas_storage.py`: the upload side was rebuilt. The read side (`get_object`, used when students get pictures) only gained an error note before the same error is raised; behaviour is the same.
- `backend/tejas/jobs.py`: the storage-wait branch is shared by every job kind (report PDFs included): a file Supabase keeps returning now waits 15 minutes at a time instead of the 30 s–5 min ladder.
- `backend/server.py`: starts the storage watcher, mounts the delete routes, and words the admin-only storage message differently. The student message is unchanged.

Student-path regression suites pass after these changes (section 6).

---

## 2. Owner's standing rules

1. Deploy only on the exact word "deploy".
2. Do not modify `LiveSeries.js` (not even its warning).
3. No email, SMS or outside alert. Warnings live only inside Super Admin rows and panels.
4. One bad file must never pause other uploads, books or mocks.
5. Nothing new applies to verified JEE Main PYQ.
6. One mock, one storage: a mock's pictures are all in Supabase or all in Emergent, never split.
7. No general hard delete. The only approved exception is Packet C (owner types DELETE; upload never reached students). App code never drops a collection or database.
8. A packet is not "done" without test evidence. What could not be tested is written as "not tested".
9. Each packet: write the test first, then the code, then re-run the older suites, one at a time.
10. Real-Supabase tests: preview bucket only, `TEST_` files only, removed afterwards. The live bucket is read-only for the builder.
11. Before every deploy: testing agent pass, a separate code review of the changed code, and a list for the owner of what changed since the last deploy.
12. Do not break existing flows: student player, reader, cutter, scoring, login, PIN, rank, JEE Main PYQ, live exams, AITS hub.

---

## 3. What we were fixing

Live symptoms (owner's screenshots, 24–25 Nov):
- The PDF "mathematics chapterwise" (51,535,181 bytes) stayed at 0 % for hours.
- The badge said "890 minute se Supabase jawab nahi de raha" although Supabase answered in 1.3 s at that moment.
- Other uploads paused on and off.

Root cause (proven by reading the live bucket `jeelive-jeelive-ai`, nothing written):
- The same PDF already sat at that path since 21 Nov (same size, same sha256). The old code sent upload pieces without `x-upsert`, so Supabase answered 409 at byte 0 every time.
- The old code read that 409 as "Supabase is away" and rested Supabase for everyone (15 s to 5 min), again and again. That produced the false red badge and paused other work.
- "Read back different bytes": the old health check wrote the same file name every time. Likely cause (not proven): two live servers write the same name and Supabase may serve the older copy for up to 60 s.

Wider gaps found on the way: a silent PDF step could block all PDF work on a server until restart; a stuck upload could not be removed; the badge kept its state per server process; nothing proves a picture exists before a mock goes Live; there is no fallback when Supabase refuses a mock.

---

## 4. Plan and status

| Packet | What | Status |
| --- | --- | --- |
| Pocket 0 | Proof of the live cause | Done |
| Pocket 1 | Big-file (TUS) route fixed | Built, tested, testing agent `iteration_223`. Preview only |
| Pocket 2 | One file's fault stays with that file ("Atki hai") | Built, tested. Preview only |
| A | Independent check of Pocket 1 + 2 | Done: testing agent `iteration_224`, separate code review (no critical/high; one medium, fixed in C) |
| B | Guard against a silent PDF step | Built, tested, testing agent `iteration_225`, code review done (one medium fixed) |
| C | "Is PDF ko delete karo" (permanent delete of an upload that never reached students) | Built, tested, testing agent `iteration_225`, code review done (one low fixed) |
| D | Storage badge that tells the truth (shared database record) | Built, tested, testing agent `iteration_226`. **Separate code review not done** |
| E | Picture proof before Live/Scheduled | **Not started** (code read only; notes in section 8) |
| F | Fallback: whole mock to Emergent | Not started |
| G | Owner button: bring an Emergent mock into Supabase | Not started |

The plan had four deploy points (after A, C, E, G). None happened, so the next deploy carries everything built so far.

---

## 5. What was built

### Pocket 1: big-file route (`backend/tejas_storage.py`)
- Every piece carries `x-upsert`.
- `_same_there`: before sending and after every failed try, Supabase is asked whether it already holds exactly this file (size, then full read and sha256). If yes, nothing is sent.
- A stall counts only when no piece moved. After 2 stalls (`STALL_LIMIT`): a fresh upload, then the one-request route.
- 423 (locked) waits. `_sized` checks the stored size after both routes. A finished upload is never "carried on". A piece whose answer was lost counts as progress.
- A failing progress listener (the caller's own database write) is logged and the upload carries on.
- Upload place is saved after every 6 MB piece (`payload.transfer`) and trusted for 20 h.

### Pocket 2: "Atki hai"
- `StorageStuck` (scope `stuck`, retry every 900 s). Network trouble, 408, 429, 5xx stay "Supabase away" (`StorageWaiting`, scope `away`); 401/402/403/540 are `blocked`; an ordinary 4xx/409 is that one file's fault.
- A big PDF is tried on both routes before it is stuck; a small picture is stuck at once. Supabase is never rested for one file.
- `book_worker.publish_batch`: a stuck mock is tried once per round (`payload.stuck_round`); the book's other mocks still go Live.
- `book_worker.step` writes `payload.storage_wait` {since, at, error, kind, code, reason, next, stuck, mock, mock_id, mocks}.
- `jobs.py`: a stuck job stays queued (`stuck: true`), next try in 15 min, tries not used up; "Supabase is back" does not wake it; `/api/cron/maintenance` (every 15 min) does.
- Imports and chapter books: same stuck handling (`imports.py`, `chapter_books.py`).
- Screens: `UploadProgress.js` (reason, Supabase code, mock name, 15-minute alert inside the row), `MachinePanel.js` (stuck list + "Dobara chalao"), `MockList.js`, `MasterShared.js`, `MasterType.js` (a stuck mock is not counted as busy; polling is shared so many rows make one request).
- "Dobara chalao" = `POST /api/admin/books/{id}/control` with `{revision, action: 'retry'}`.

### Packet B: step guard (`backend/tejas/step_guard.py`, new)
- `jobs.run_job` runs a PDF step through `step_guard.guarded(job)`.
- No sign of life for 600 s (`SILENCE`): the step is let go, the place is written to `tejas_step_hangs`, the lock is freed, the job runs again after 20 s from the saved place.
- 3 silent steps in a row (`HANG_LIMIT`): only that PDF says "Atki hai" (`storage_wait.kind = 'hang'`), retried hourly or on "Dobara chalao".
- Signs of life (`beat`): lock checked/saved/renewed (`book_store.py`), every 10 pages read, every group of pictures cut (`book_pdf.inspect_many(..., alive)`), every picture saved (`book_publish.py`).
- Only the PDF lane. Grading, score and report jobs are not guarded.
- Machine panel: "Latke kadam (24 ghante): N" and the last hung step.

### Packet C: permanent delete (`backend/tejas/book_delete.py`, `DeleteUploadDialog.js`, new)
- Routes: `GET` and `POST /api/admin/master/uploads/book/{id}/delete`. Body `{"confirm": "DELETE"}` (strict, no extra fields). Owner only; another owner's upload answers 404.
- Allowed only when no test was ever made from the upload (`reached_students`). Otherwise 409 and no button.
- The row leaves at once; the same PDF can be uploaded again immediately. Clean-up runs behind: stop the running step → empty the upload's own Supabase folder → its records → last, the upload's own record. Maintenance finishes an interrupted clean-up.
- `tejas_storage`: `sb_list`, `sb_remove`, `sb_empty`, `sb_end_upload`. `_removable` refuses every path that is not `jeelive/books/<uuid>/`.
- Emergent files are never physically removed (Emergent has no delete); only the record goes.
- If a mock of that upload became a test in the same moment, the delete is called off and nothing is removed.
- Buttons: Uploads row "Delete", Draft mock Status menu "Is PDF ko delete karo…", AITS day screen dustbin (`SeriesDays.js`). Tap targets 44 px on mobile.
- Machine panel: "Delete ki safai baaki: N".

### Packet D: truthful badge (`backend/tejas/storage_health.py`, rewritten)
- One record `tejas_storage_state` `{_id: 'state'}`: `small`, `big`, `emergent`, `errors` (last 20), `readings` (last 20 per store), `checked_at`, `ok_at`, `check_lease`, `big_lease`, `big_test_at`, `swept_at`, `rev`. Every server shows the same.
- Three lines: Supabase pictures (small file), Supabase PDF (big file), Emergent (fallback), each with when, how and how long.
- Colour: green = both Supabase routes fine and nothing held. Yellow = slow (> 5000 ms), a file stuck, a file held over 10 min, big route failed or never tried, Emergent not answering. Red = Supabase not answering or project blocked.
- Supabase check: a new name each time (`health/check-<epoch>-<hex>.bin`), written, read back, removed. Emergent check: one name (`jeelive/health/check.bin`).
- "Badi file ka test": 7,340,032 bytes by the real piece route, read back, removed. Runs by itself when never proven, when a PDF waits on that route (every 15 min), and once a day. A real PDF save also counts as proof.
- One server checks at a time (`CHECK_LEASE` 120 s, `BIG_LEASE` 600 s). The button answers within 45 s even if the test is slow; the test carries on and writes its result.
- `watch()` starts with the server (`app.state.storage_watch`) and runs every 30 s: writes this server's notes, and when any server found Supabase well it ends this server's rest and wakes its lanes (`jobs.wake_local`).
- Left-behind check files are swept daily; the sweep only removes names that match its own pattern. The older `health/check.bin` in the bucket is not touched.
- Routes (owner only): `GET /api/admin/storage/health[?fresh=true]`, `POST /api/admin/storage/retry`, `POST /api/admin/storage/big-test`. `GET /api/admin/machine/status` gained `storage_errors`.
- `ceo.py` now reads the shared record (`storage_health.current()`), not the old in-process state.
- Screens: `StorageBadge.js`, `MachinePanel.js` (last 20 storage errors), `master.css`.

### New or changed data
- Collections: `tejas_storage_state`, `tejas_step_hangs`, `tejas_publish_progress` (picture count while a mock goes Live).
- `tejas_books`: `payload.storage_wait`, `payload.stuck_round`, `payload.hang`, `payload.transfer`, `payload.again`, `deleting`.
- `tejas_jobs`: `stuck`, `storage_waits`, `storage_wait_since`, `busy_waits`. Imports and chapter books: `stuck`, `storage_wait`, `storage_wait_since`.

---

## 6. Evidence

Last app-code change: `storage_health.py` at 06:02 UTC. Everything below ran after it unless a time says otherwise. Logs are copied to `/app/test_reports/handoff_2026-11-25/`.

**Full regression, 25 Nov 07:12–07:19 UTC, one suite at a time: 26 suites, 1,111 checks, 0 failed.**

| Suite | Result | Suite | Result |
| --- | --- | --- | --- |
| storage_wait224 | 27/27 | step_guard233 | 33/33 |
| storage_dual216 | 37/37 | upload_delete234 | 31/31 |
| storage_fail215 | 13/13 | upload_delete_edge235 | 21/21 |
| storage_before229 | 9/9 | phase1_iso221 | 17/17 |
| storage_big229 | 28/28 | pictures_iso220 | 66/66 |
| storage_book229 | 22/22 | chapters_iso182 | 58/58 |
| storage_edge230 | 23/23 | master_iso181 | 124/124 |
| storage_stuck231 | 49/49 | library_aits_iso180 | 125/125 |
| storage_stuck_edge232 | 25/25 | series_dates_iso187 | 47/47 |
| storage_nocallback234 | 7/7 | structure_imports_iso174 | 51/51 |
| storage_move225 | 24/24 | structure_iso173 | 133/133 |
| storage_move_edge225 | 6/6 | typed_delete_iso185 | 54/54 |
| storage_move_fix226 | 17/17 | storage_badge236 | 64/64 |

Other runs:
- `storage_badge_edge237` (testing agent's suite): 14/14 at 06:59. In this session 3 unused imports were removed from that test file; it was re-run afterwards.
- `storage_badge_real236` on the real Supabase (preview bucket, the app's own check files only): 9/9 at 07:10.
- Browser walks on bridges (disposable database, fake Supabase at the wire), desktop + 390 px:
  - After the last code change: Packet D `ui_badge236` 29/29 (06:16); Supabase-wait `ui_storage_wait_qa224` 48/48 (06:33), `ui_storage_wait224` 10/10 and `storage_wait_api_qa224` 10/10 (06:24).
  - Before it (the only later change was one named constant in `storage_health.py`): Packets B + C `ui_delete234` 41/41 (05:46); Pocket 2 `ui_storage_stuck231` 32/32 (05:43).
- Earlier real-Supabase runs (not repeated today): `storage_real229` at 7, 50 and 100 MB, 6/6 each; `storage_stuck_real231` 8/8; `storage_delete_real234` 9/9.
- Preview app after all this: `/api/health` 200, frontend compiles, ruff F/E9 clean on the changed backend files, no failed jobs, no waiting or stuck book; the storage record shows both Supabase routes and Emergent fine with 0 errors.

One failure seen and explained: the first `ui_storage_wait_qa224` run was 44/45 ("desk: down walk", FileNotFoundError). The test needs a fixture PDF at `/tmp/uibridge224/qa_variant.pdf` that nothing creates. With the fixture made (section 9) it passed 48/48. Not an app fault.

Limits of this evidence:
- Nothing was checked on live.
- 15 minutes, 10 minutes, 1 hour and 24 hours were tested by moving clocks or lowering thresholds, not by waiting.
- The real Supabase cannot be asked to "return" a file; those cases use the fake.
- Two servers sharing the record were tested inside one process; preview has one server.
- No record of a browser walk of the real preview app under an owner login for Packet D; the walks ran on bridges.
- The cause of the 24 Nov hang (a Live step silent for 10 minutes, picture count 0/21, 50 s after a database restart) was never found. Packet B handles its effect only.

Older suites that fail for reasons that predate this work: `get_ready_iso188` 35/36; `maths_bookmarks_iso190` (needs `/tmp/maths.pdf`, the owner's 640-page PDF, not on this machine); `book_scale_iso171` and one check of `book_publishing_iso170` (upload without section gets 422).

---

## 7. What a deploy would send (changes since `7e9e3ab`)

31 app files, +1,691 / −207 lines, 8 commits, plus one small uncommitted edit (`storage_health.py`, a named constant) that the platform will commit. 26 new test files (25 committed, `storage_badge_edge237.py` not yet).

Backend: `server.py`, `tejas_storage.py`, and in `tejas/`: `book_delete.py` (new), `step_guard.py` (new), `storage_health.py`, `storage_move.py`, `jobs.py`, `book_worker.py`, `book_imports.py`, `book_publish.py`, `book_pdf.py`, `book_store.py`, `machine.py`, `master.py`, `series_admin.py`, `imports.py`, `chapter_books.py`, `ceo.py`, `db.py`, `route_contracts.py`, `request_contracts.py`.

Frontend: `components/master/` (`StorageBadge.js`, `MachinePanel.js`, `UploadProgress.js`, `MockList.js`, `MasterShared.js`, `SeriesDays.js`, `DeleteUploadDialog.js` new), `features/admin/master/MasterType.js`, `components/admin/AdminShared.js`, `master.css`.

`NIGHT_REPORT.md` promised a "Deploy se pehle" list that was never written. It was added to that file in this session.

Three more backend files differ since the live commit by one line each (`backend_test.py`, `backend_test_additional.py`, `tools/export_app_analysis_samples.py`); the server does not import them.

---

## 8. Packet E (next): picture proof before Live/Scheduled

### What the plan asks (plan.md section E; read it in full)
- A paper is shown to students (Live or Scheduled) only when every picture in it is proven to exist in one and the same storage.
- Supabase paper: every picture is in Supabase's list, and a newly saved picture has the size it had when saved. Emergent paper: every picture is read back and matched by fingerprint. A missing picture is saved once more, then checked again.
- Applies to: a PDF Draft mock going Live/Scheduled (AITS day papers too), a Written mock, an Off test switched Live/Scheduled again, a test coming back from the Library (stays Off until proven, then returns to its old state). A Scheduled mock is checked when it is scheduled, not when it opens.
- On failure: not Live; the row says why ("3 pictures storage me nahi mili") with "Dobara chalao"; automatic retry every 15 min; other mocks carry on.
- Old Emergent pictures: on Live the machine first copies them to Supabase, each read back and matched, and switches only when all are copied. Row: "Pictures Supabase me copy ho rahi hain · 120 / 312". If the chosen time passed meanwhile, the mock does not open late.
- Row line after proof: "Pictures: 312 / 312 · Storage: Supabase". Owner button "Pictures ki poori jaanch" (full read + fingerprint, in the background). In Phase 1 the full check only reports; it never switches a Live mock Off.
- Verified JEE Main PYQ: no check, no copy, no button.

### Where a paper becomes visible today (read in code on 25 Nov)
| Path | Code | Storage touched? |
| --- | --- | --- |
| PDF mock → Live/Scheduled | `master.change_status` → `mock_status` → `book_imports.request_publication` → `book_worker.publish_batch` → `book_publish.publish_ready` → `source_questions` / `crop_ref` → `content.publish_validated` | Yes |
| Same, other doors | `structure.publish_ready_items` (`POST /api/admin/publish-ready`), `book_imports.control` (`publish_ready`, `release_now`, `resume_mock`) | Yes / flag only for `resume_mock` |
| AITS PDF mock gets a day | `series_admin.assign_mocks` → worker → `publish_ready` | Yes |
| Written mock | `master.publish_written`, `series_admin.assign_written`, `written.save_questions` / `update_written` (re-publish) → `publish_validated` | Read only |
| Off → Live | `master.set_status` (non-draft branch), `structure.update_test` (`PATCH /api/admin/catalog/tests/{id}`), `series_admin.paper_live`, `chapter_books.chapter_live`, `imports.py` live toggle | No: database flag only |
| Library → back | `library.restore_sets`, `library.restore_uploads` | No: database flag only |
| Built set gets an AITS day | `series_admin.assign_built` | No |
| Old chapter book | `master.chapter_books_live` → `chapter_books.publish_book` | No |
| Older Studio doors (found by grep, not read in full) | `imports.py` (paper import publish, about lines 272–286), `smart_imports.py` (about 404–412), `live_series.py` (old All-India assign, about line 296) | Not checked |

### Findings from reading the code (not reproduced by a test; verify each before relying on it)
1. `crop_ref` trusts the file record. If `tejas_files` has the id, the picture is not saved again and storage is never asked whether the object is there.
2. `publish_validated` → `validate_refs` reads back and sha-checks `q_refs` and `s_refs` (through `render_crop` → `get_object`), but **not `c_refs`**, the question and option pieces students see in the new look. `get_object` may also answer from its in-process cache.
3. So a new PDF mock already pays one full read-back of question and solution pictures at Live. The plan (assumption 19) assumed a full read would double the Live time and wanted only "exists + size" there.
4. A missing or wrong picture today makes the mock `held` with an English reason (`book_worker.hold`: "Source region is invalid…" or the storage error text). That is not the "reason + Dobara chalao + retry every 15 min" the plan wants.
5. Picture records store `sha256` but no size. "Same size as when saved" needs a new field at save time; old records will not have it.
6. A mock scheduled from Master carries its own `release_at`. In `publish_ready`, the missed-release check looks only at the book-level `release_at`. If the per-mock time has passed while the mock waited, `start` is that past time and the mock is published at once. The plan says it must not open late.
7. Picture ids are per book (`identity(book.id, raw_sha, role)`), so two mocks of one book can share a record. In the preview data 3 file records (old-style records, not book pictures) are used by more than one set. This matters for "one mock, one storage" when old files are copied (E) and when a mock's pictures are cleaned up (F).
8. Old sets (file kind `combined` or none, path `tejas/…`) have no saved pictures: crops are rendered on demand from a source PDF. "Every picture proven" for them means the source file exists and matches its hash. Whether every such record has a `sha256` was not checked.
9. Verified PYQ in code = `structure.locked(s)` (`test_kind == 'pyq'` and not `master_pyq`).

### Pieces that already exist and can be reused
- `tejas_storage.sb_list(folder)` returns names and sizes, 1000 per call. PDF pictures live under `jeelive/books/<book id>/crops/`, Written pictures under `jeelive/written/<set id>/`.
- `tejas_storage.sb_size`, `_same_there` (size, then full read + sha256).
- `storage_move.copy(old, sha, resume, progress)`: Emergent bytes → hash check → Supabase → read back → hash compare. `storage_move.one` shows the guarded switch with `moved_from`.
- Per-mock stuck state for PDF mocks: `payload.storage_wait.mocks`, `stuck_round`, 15-minute retry, "Dobara chalao", row text. Sets (Written, Off, Library) have no worker and need their own state.
- `tejas_publish_progress` already drives the "Picture 180/300 save hui" row text.

### Rules that bite when adding routes or fields
- Every new API route needs an entry in `tejas/route_contracts.py` `SPEC`, and every route with a body needs its model in `request_contracts.MODELS`. Otherwise the server refuses to start.
- App responses may only gain fields; none may change or disappear (the mobile app reads them).
- Picture bytes must stay identical, so ETag and `asset_revision` do not change.

### Suggested order (builder's suggestion; the owner approved the plan text, not this breakdown)
1. One proof function for a set: which storage, which pictures are missing, sizes. Skip `locked` sets. Test it alone on an isolated database with the fake Supabase.
2. Gate the PDF-mock path (`publish_ready`), including `c_refs`, re-save of a missing picture, and the per-mock stuck state on failure.
3. Fix the late-open case (finding 6) with its own test.
4. Gate Written, Off → Live and Library restore.
5. Legacy copy before Live.
6. Row line, "Pictures ki poori jaanch" button, browser walk on a bridge.
7. Full regression, then the testing agent.

---

## 9. How to run tests safely

**Before anything:** `prlimit --pid $(pgrep -x mongod | head -n1) --nofile=65536:1048576`
The default limit is 1024 open files and returns after every mongod restart or new pod. Today's one-at-a-time regression left mongod holding 895 open files when it finished (95 a few minutes later); parallel runs go over 1024 and mongod aborts (it happened on 20 Nov and 24 Nov).

Rules:
- One isolated suite at a time, plus at most one bridge. Never lanes side by side.
- Stop a bridge with `pkill -INT -f tests/<bridge>.py` so its `finally` drops its own database. Never SIGTERM/SIGKILL.
- Every harness database is named `tejas_isolated_*`. Tests assert that prefix before dropping. The app database is `test_database`.
- Real-Supabase tests assert `'preview' in bucket_name()`.

Commands (from `/app/backend`):
- A suite: `python tests/<name>.py` (prints `TOTAL n PASS n FAIL 0`; `chapters_iso182` prints `58/58 passed`).
- Runner scripts are kept in `/app/backend/tests/runners/`. They log to `/root/p2`, which may not exist after a fork: `mkdir -p /root/p2 && cp /app/backend/tests/runners/*.sh /root/p2/ && chmod +x /root/p2/*.sh`.
  - `bash /root/p2/d_regress.sh suite1 suite2 …` → `/root/p2/d_regress.log`
  - `bash /root/p2/d_ui.sh` → Packet D bridge + walk → `/root/p2/ui236.log`
  - `bash /root/p2/c_ui.sh` → Packets B + C bridge + walk → `/root/p2/ui234.log`
- Bridges (real app on 127.0.0.1, disposable database, fake Supabase): `storage_wait_bridge224` :8774, `storage_stuck_bridge231` :8775, `delete_bridge234` :8776, `badge_bridge236` :8777. Switch files and cookies are described in `memory/test_credentials.md`.
- Fixture for `ui_storage_wait_qa224.py`, after its bridge prints READY:
  `python -c "import sys; sys.path.insert(0,'tests'); from cut_bridge207 import cut_pdf; open('/tmp/uibridge224/qa_variant.pdf','wb').write(cut_pdf('QAVAR', long=True))"`
- Test helpers worth knowing: `tests/iso_harness_book170.py` (isolated database, in-memory Emergent, removes `SUPABASE_URL`), `tests/fake_supabase229.py` and `fake_supabase231.py` (Supabase at the wire, with knobs), `tests/storage_book229.py` (`upload`, `finish`, `pump`, `again`, `row`, `job`, `listed`), `tests/cut_bridge207.py` (`cut_pdf`).

Long runs: anything over 2 minutes goes in the background with a log file; poll the log.

---

## 10. Environment facts (preview, 25 Nov 07:20 UTC)

- Services: backend, frontend, mongodb running. `/api/health` 200.
- Cron: `.emergent/crons.yml` calls `POST /api/cron/maintenance` every 15 min. It is running: the last run was 6 minutes old when checked at 07:14.
- Supabase: `SUPABASE_URL` and `SUPABASE_SECRET_KEY` come from the platform secrets (not in `backend/.env`). Preview and live use the same Supabase project with separate buckets.
- Preview bucket: `jeelive-book-pipeline-fix-1-7ttfegq6-preview-emergentagent-com`. The name is derived from `FRONTEND_URL`. **If the fork gets a new preview address, the app will make and use a new empty bucket.** Nothing is lost: the preview database has no file in Supabase.
- Preview database `test_database`: 1 book ("Chemistry chapter-wise (boxed) — engine test", 2,527 pages, 24 ready mocks, original on Emergent); 252 sets = 30 verified PYQ (published) + 222 others, all in the Library (172 chapter-book, 50 mock-book); 164 file records, all on Emergent.
- Those 164 files: 30 belong to verified PYQ sets, 131 to the Library sets, 3 to no set. So in preview the badge's "Purani files Emergent mein: 164 › copy" button would also copy the 30 PYQ files. The owner was told not to press it. Live counts are unknown.
- Storage record: small route fine, big route fine (7 MB test file), Emergent fine, 0 errors.
- Two old test databases are still there and were not dropped (not made by this session): `tejas_isolated_book170_19f082e9` (seed rows only) and `tejas_isolated_window177_66e69d` (30 sets, 30 files, 30 versions, from 23 Nov).
- Scratch logs and probes: `/root/p2` (outside the repo).

---

## 11. Mistakes and lessons

- 9 parallel test databases crashed mongod (20 Nov); it happened again under test load on 24 Nov. Hence section 9.
- A rollback on 21 Nov lost a night of work that had no checkpoint. The platform commits after each step; do not rely on anything outside `/app`.
- An earlier handoff called work "done" that had no screen. Rule since then: a packet is done only with test evidence, and untested parts are named.
- A code-review answer was once cut off by the tool and its "medium" point was lost for a while. Write review results into a file.
- Importing a module that only tests use into app code, or leaving stale `noqa` marks, made lint noisy. Run `ruff check --select F,E9` on changed files.
- Running eslint directly fails (ESLint 9 with an old config). Trust the webpack "Compiled successfully" line.

---

## 12. Decisions waiting for the owner

1. **Deploy now or after Packet E?** A–D are ready except the Packet D code review. A deploy sends everything in section 7. If yes: run the code review, give him the change list, wait for the word "deploy", then read live once and report (did the stuck PDF move, did the false red line go).
2. **How to proceed:** stop and report after each packet (the plan's rule), or keep building E → F → G without stopping.
3. **Old test databases** (section 10): drop them or leave them.
4. Still open from the plan (section J, his side): Supabase spend cap ON or OFF before 9 Dec; do not re-upload a once-deleted PDF over 6 MB on live before the deploy; leave the stuck "mathematics chapterwise" alone until the deploy; do not press "Purani files › copy"; ask Emergent support whether the 21 Nov storage HTTP 500 was fixed at the root.

---

## 13. After E: F and G in one paragraph each

**F (fallback).** A mock that cannot get into Supabase for 5 minutes, or on the owner's "Abhi Emergent me save karo", is saved whole into Emergent: its Supabase pictures from this try are removed (never a picture another paper uses), every Emergent picture is read back and matched, then Live. If Emergent also refuses: "Atki hai: dono storage ne nahi liya". Applies to PDF mocks and the original PDF; not to Written mocks, old Studio screens or PYQ. Before building: test in preview whether Emergent takes a 50 MB and a 100 MB PDF in one request (about 160 MB of test files stay in Emergent for ever). `_removable` must be widened carefully for the mock's own pictures.

**G (bring to Supabase).** Owner button "Supabase me lao" on an Emergent mock: copy every picture, read back, match, switch only when all match; bytes stay the same; the Emergent copy stays; disabled while that paper's live exam runs; never automatic.

---

## 14. File index

| What | Where |
| --- | --- |
| Approved plan | `/app/plan/plan.md` |
| Owner's night report (Hinglish) | `/app/memory/NIGHT_REPORT.md` |
| This handoff | `/app/memory/HANDOFF_2026-11-25_SUPER_ADMIN_STORAGE.md` |
| Test rules and lessons | `/app/memory/LEARNINGS.md` |
| Bridges, cookies, switches | `/app/memory/test_credentials.md` |
| Product history | `/app/memory/PRD.md`, `CHANGELOG.md`, `ROADMAP.md`, `HISTORY.md` |
| Testing-agent reports | `/app/test_reports/iteration_223.json` … `iteration_226.json` |
| Today's logs | `/app/test_reports/handoff_2026-11-25/` |
| Runner scripts | `/app/backend/tests/runners/` |
| Storage core | `/app/backend/tejas_storage.py` |
| Health, guard, delete, copy | `/app/backend/tejas/storage_health.py`, `step_guard.py`, `book_delete.py`, `storage_move.py` |
| PDF worker and publish | `/app/backend/tejas/book_worker.py`, `book_publish.py`, `book_imports.py`, `book_store.py`, `jobs.py` |
| Master API | `/app/backend/tejas/master.py`, `machine.py`, `series_admin.py`, `structure.py`, `library.py`, `written.py`, `content.py` |
| Master screens | `/app/frontend/src/components/master/`, `/app/frontend/src/features/admin/master/`, `/app/frontend/src/master.css` |
| Do not touch | `/app/frontend/src/features/LiveSeries.js` |
