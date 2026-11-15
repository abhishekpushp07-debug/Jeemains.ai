#!/usr/bin/env bash
# Builds the browser arena (the app's web build, Rapid Fire only) into backend/arena_web.
# The backend serves it at /api/arena. Run this after changing app screens, then Publish.
set -euo pipefail
cd /app/frontend
OUT=/tmp/arena_web_build
rm -rf "$OUT"
JEELIVE_ARENA_EXPORT=1 CI=1 npx expo export -p web --output-dir "$OUT" --clear
# Keep only the arena itself: never publish other files that sit in frontend/public.
find "$OUT" -mindepth 1 -maxdepth 1 ! -name index.html ! -name _expo ! -name assets ! -name favicon.ico ! -name metadata.json -exec rm -rf {} +
# Swap in the new build in one step, so the server never serves half a build.
rm -rf /app/backend/arena_web.old
[ -d /app/backend/arena_web ] && mv /app/backend/arena_web /app/backend/arena_web.old
mv "$OUT" /app/backend/arena_web
rm -rf /app/backend/arena_web.old
du -sh /app/backend/arena_web
