#!/usr/bin/env bash
# Builds the browser arena (the app's web build, Rapid Fire only) into backend/arena_web.
# The backend serves it at /api/arena. Run this after changing app screens, then Publish.
# Nothing is deleted: the copy that was being served is kept in /tmp/arena_web_previous.<time> (to go back, move it back).
set -euo pipefail
cd /app/frontend
STAMP=$(date -u +%Y%m%d-%H%M%S)
OUT=$(mktemp -d /tmp/arena_web_build.XXXXXX)
SHIP=$(mktemp -d /tmp/arena_web_ship.XXXXXX)
chmod 755 "$SHIP"
# EXPO_PUBLIC_BACKEND_URL empty: the arena always talks to the server it came from (src/api/client.ts), so the address
#   of the workspace that builds it must not travel into the copy students get.
# METRO_CACHE_ROOT of its own: the build never clears or fills the cache of the running preview.
EXPO_PUBLIC_BACKEND_URL= METRO_CACHE_ROOT=/tmp/arena_metro_cache JEELIVE_ARENA_EXPORT=1 CI=1 npx expo export -p web --output-dir "$OUT" --clear
# Keep only the arena itself: never publish other files that sit in frontend/public.
for part in index.html _expo assets favicon.ico metadata.json; do
  if [ -e "$OUT/$part" ]; then mv "$OUT/$part" "$SHIP/$part"; fi
done
# git never carries a folder named node_modules, so the icon font the build keeps there never reached production
# (seen 27 Nov 2026: empty boxes in place of icons). It ships under another name; backend/arena_web.py answers the
# old name from it.
if [ -d "$SHIP/assets/node_modules" ]; then mv "$SHIP/assets/node_modules" "$SHIP/assets/_modules"; fi
# A build without its page or its entry file, or one that carries a workspace address, is never put in place.
ENTRY=$(grep -o '_expo/static/js/web/entry-[0-9a-f]*\.js' "$SHIP/index.html" | head -1 || true)
if [ -z "$ENTRY" ] || [ ! -s "$SHIP/$ENTRY" ]; then
  echo "The build is not complete; the copy being served was left as it is (see $OUT and $SHIP)." >&2
  exit 1
fi
if grep -rlE 'preview\.emergentagent\.com' "$SHIP" >/dev/null; then
  echo "The build carries a workspace address; the copy being served was left as it is (see $SHIP)." >&2
  exit 1
fi
# A file git leaves out would be missing in production: such a build is never put in place either.
git -C /app rev-parse --git-dir >/dev/null
LEFT_OUT=$(cd "$SHIP" && find . -type f -printf 'backend/arena_web/%P\n' | git -C /app check-ignore --no-index --stdin || true)
if [ -n "$LEFT_OUT" ]; then
  echo "git would leave these files out of a Publish; the copy being served was left as it is (see $SHIP):" >&2
  echo "$LEFT_OUT" | head -20 >&2
  exit 1
fi
# Swap in the new build in one step, so the server never serves half a build.
if [ -d /app/backend/arena_web ]; then mv /app/backend/arena_web "/tmp/arena_web_previous.$STAMP"; fi
mv "$SHIP" /app/backend/arena_web
du -sh /app/backend/arena_web
echo "the copy served before is kept in /tmp/arena_web_previous.$STAMP"
