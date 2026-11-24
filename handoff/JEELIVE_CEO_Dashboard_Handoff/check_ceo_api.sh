#!/usr/bin/env bash
# Proves the app's CEO API answers. The token is typed here by the owner; it is never written into a file.
#   BASE=https://jeelive-mobile.emergent.host/api  TOKEN=...  bash check_ceo_api.sh
set -u
: "${BASE:?set BASE to the app server address ending in /api}"
: "${TOKEN:?set TOKEN to the CEO_API_TOKEN value}"
code() { curl -s -o /dev/null -w "%{http_code}" "$@"; }
echo "no token          -> $(code "$BASE/ceo/overview")   (401 = closed, as it should be; 503 = token not set on that server; 404 = that server is not published yet)"
echo "wrong token       -> $(code -H "Authorization: Bearer wrong" "$BASE/ceo/overview")   (401)"
echo "overview          -> $(code -H "Authorization: Bearer $TOKEN" "$BASE/ceo/overview")   (200)"
echo "users, 5 a page   -> $(code -H "Authorization: Bearer $TOKEN" "$BASE/ceo/users?limit=5")   (200)"
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/ceo/overview"; echo
