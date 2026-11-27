# Offline Solutions — parked plan (23 Nov 2026). BUILT on 27 Nov 2026 in another shape: read `OFFLINE_KEPT.md` first.
# Changed by the owner's later words (27 Nov): papers are kept by themselves (no "Offline save" button), and the room is
# 512 MB with the oldest-used copy giving way (no pinning). The rest below was followed.

Goal: a student keeps a finished paper's questions + solutions on the phone and revises without internet.

## Owner's decisions (final)
- Build ONLY after the website's light pictures (format=webp) and finished-attempt packs (kind=solution) are live and the
  app side of them is built and tested (see APP_PICTURES_REPLY.md, WEBSITE_PICTURES_REPLY.md). Not before.
- The student saves a paper by pressing a button. The button's name is exactly "Offline save".
- Without internet the app opens ONLY the saved papers, for 7 days after the last server-confirmed sign-in.
  After that the student must connect once. Sign out removes the saved papers.

## Facts found (code read + read-only checks on jeelive.ai, QA learner, one finished JEE Main PYQ)
- The app does not open without internet today. src/auth.tsx: checkSession() calls /auth/session first; "A cached profile is
  not proof of authentication; never render it first." Offline -> entry screen with sessionError. app/_layout.tsx sends
  anyone without `user` to /entry.
- Result JSON (337 KB) is not kept: useCached's persisted copy is used for 10 minutes only; app/result/[id].tsx loads it
  with loadResult(id, version).
- Pictures: per-account AES-encrypted store (src/assets/deviceCache: store.ts native, store.web.ts), DISK_BUDGET 256 MB,
  oldest-used evicted, key in SecureStore, purged on sign out. A copy older than 3 days needs the network
  (imageDownload.ts REUSE_MS) -> unusable offline. No "pinned" notion exists.
- The result screen already warms the open paper in the background (usePaperAssets(..., solutions=true) ->
  privateAssets.preload), but only until the 48 MB memory budget is 90 % full, so a paper is not fully on disk.
- Size today: 80 question + 117 solution pictures = 197 one-picture calls; question pictures avg 561 KB (36 sampled),
  solution pictures avg 394 KB (30 sampled) -> about 92 MB per paper. At WebP quality 90 (12 %): about 11 MB (computed).
- The Solutions view inside app/result/[id].tsx also calls the network (ai-solutions via useCached, consult, report):
  an offline reader must not depend on them.

## Packets (small, in this order, each checked before the next)
1. Shelf store: saved result JSON + list of saved papers, encrypted per account like the picture store; pictures of a saved
   paper are pinned (never evicted, usable offline whatever their age). Native store.ts can only be fully checked on a
   real phone build; store.web.ts on the preview.
2. Downloader: from the finished-attempt part links / packs (question, piece and solution items), straight to disk (not
   through the memory queue), progress "n / total", pause / resume, skip what is already saved, one-picture route as fallback.
3. "Offline save" button on the result screen: shows the size first, then progress; "Saved on phone" state; remove button.
4. Offline door: on the entry screen, when the session check fails for lack of network (not a 401) and a shelf exists for
   the saved account and the last confirmed sign-in is under 7 days old -> "Saved papers" opens a read-only route that
   lists and reads saved papers only. The signed-in app tree and its auth rules stay untouched.
5. Offline reader: question, your answer, right answer, solution pictures / text from the shelf; no AI consult, no report,
   no network calls. Plain line when something is missing.
Then: testing agent (frontend), a real phone build check for the native store, one Publish.

## Do not
- Do not build the downloader on today's one-picture route (197 calls and ~92 MB per paper per student).
- Do not render the signed-in app from a cached profile.
