#!/usr/bin/env bash
# Every Rank and Mission call as a plain curl, against the live JEELIVE.AI app server.
# Usage:  bash curl_examples.sh            (or copy any single line)
#         APP=https://<other-host>/api bash curl_examples.sh
APP="${APP:-https://jeelive-mobile.emergent.host/api}"
J='Content-Type: application/json'
show() { echo; echo "### $1"; shift; "$@" | head -c 700; echo; }

# ---------------------------------------------------------------- Rank (public, no sign-in)
show "GET /rank/meta"              curl -s "$APP/rank/meta"
show "POST /rank/estimate (JEE)"   curl -s -X POST "$APP/rank/estimate"   -H "$J" -d '{"exam":"jee","marks":180,"level":"normal","category":"OBC-NCL","pwd":false}'
show "POST /rank/estimate (COMEDK)" curl -s -X POST "$APP/rank/estimate"  -H "$J" -d '{"exam":"comedk","marks":110,"level":"normal","category":"GEN","pwd":false}'
show "POST /rank/percentile"       curl -s -X POST "$APP/rank/percentile" -H "$J" -d '{"percentile":97.4567,"category":"GEN","pwd":false}'
show "POST /rank/predict"          curl -s -X POST "$APP/rank/predict"    -H "$J" -d '{"marks":180,"level":"normal","category":"GEN","female":false,"pwd":false,"state":"Bihar","branches":[],"segment":"all","page":1}'
show "POST /rank/college"          curl -s -X POST "$APP/rank/college"    -H "$J" -d '{"marks":180,"level":"normal","category":"GEN","female":false,"pwd":false,"state":"Bihar","branches":[],"inst":22,"prog":230,"quota":"OS","gender":"N","seat":"open"}'
show "POST /rank/bitsat"           curl -s -X POST "$APP/rank/bitsat"     -H "$J" -d '{"score":280,"campus":"all","degree":"all"}'
show "POST /rank/comedk"           curl -s -X POST "$APP/rank/comedk"     -H "$J" -d '{"marks":110,"branches":[],"area":"all","page":1}'
show "POST /rank/comedk/college"   curl -s -X POST "$APP/rank/comedk/college" -H "$J" -d '{"marks":110,"branches":[],"code":"E095","course":"CY"}'
show "GET /rank/colleges"          curl -s "$APP/rank/colleges"
show "POST /rank/target/jee"       curl -s -X POST "$APP/rank/target/jee"    -H "$J" -d '{"inst":22,"category":"GEN","female":false,"pwd":false,"state":"Bihar"}'
show "POST /rank/target/comedk"    curl -s -X POST "$APP/rank/target/comedk" -H "$J" -d '{"code":"E095"}'
show "GET /rank/target/bitsat"     curl -s "$APP/rank/target/bitsat"
show "POST /rank/compare"          curl -s -X POST "$APP/rank/compare"    -H "$J" -d '{"items":[{"exam":"jee","id":"jee-230","prog":230,"quota":"OS","gender":"N","path":"Other state · Open"},{"exam":"comedk","id":"E095|CY"},{"exam":"bitsat","id":"Pilani-cs"}]}'
show "POST /rank/compare/colleges" curl -s -X POST "$APP/rank/compare/colleges" -H "$J" -d '{"items":[{"exam":"jee","id":"22"},{"exam":"comedk","id":"E095"},{"exam":"bitsat","id":"Pilani"}],"category":"GEN","female":false,"pwd":false,"state":"Bihar"}'

# ---------------------------------------------------------------- Cut off (NEW) and the scorecard rank (public)
# key = exactly what GET /rank/cutoff/options gave: JEE college = institute number as text, branch = group name;
# COMEDK college = code; BITSAT college = campus, branch = program key. A score is optional.
show "GET /rank/cutoff/options (the pickers)"         curl -s "$APP/rank/cutoff/options"
show "POST /rank/cutoff (JEE college, every round)"   curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"jee","by":"college","key":"25"}'
show "POST /rank/cutoff (JEE college, 200 marks)"     curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"jee","by":"college","key":"25","marks":200,"level":"normal","category":"GEN","female":false,"pwd":false,"state":null}'
show "POST /rank/cutoff (JEE branch, top 100)"        curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"jee","by":"branch","key":"Computer Science"}'
show "POST /rank/cutoff (JEE branch, rank, OBC-NCL)"  curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"jee","by":"branch","key":"Computer Science","rank":7500,"category":"OBC-NCL","female":false,"pwd":false,"state":"Tamil Nadu"}'
show "POST /rank/cutoff (COMEDK branch, rank)"        curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"comedk","by":"branch","key":"Computer Science","rank":30000}'
show "POST /rank/cutoff (COMEDK college, marks)"      curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"comedk","by":"college","key":"E095","marks":150}'
show "POST /rank/cutoff (BITSAT campus, score)"       curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"bitsat","by":"college","key":"Pilani","marks":280}'
show "POST /rank/cutoff (BITSAT program)"             curl -s -X POST "$APP/rank/cutoff" -H "$J" -d '{"exam":"bitsat","by":"branch","key":"cs"}'
show "POST /rank/predict (scorecard rank)"            curl -s -X POST "$APP/rank/predict" -H "$J" -d '{"rank":7500,"level":"normal","category":"GEN","female":false,"pwd":false,"state":null,"branches":[],"segment":"all","page":1}'

# ---------------------------------------------------------------- Rank PDFs (public, application/pdf)
echo; echo "### POST /rank/pdf/jee  ->  jee_top50.pdf"
curl -s -X POST "$APP/rank/pdf/jee" -H "$J" -o jee_top50.pdf -w "HTTP %{http_code}, %{size_download} bytes\n" \
  -d '{"marks":180,"level":"normal","category":"GEN","female":false,"pwd":false,"state":"Bihar","branches":[],"segment":"all"}'
# the other six:  /rank/pdf/comedk  /rank/pdf/bitsat  /rank/pdf/target/jee  /rank/pdf/target/comedk  /rank/pdf/target/bitsat  /rank/pdf/saved
# (request bodies: RANK/sample_pdfs/*.request.json)

# ---------------------------------------------------------------- Mission
echo; echo "### GET /j/{code}  (a friend opens a student's link; an unknown code is simply not counted)"
curl -s -o /dev/null -D - -A "Mozilla/5.0" "$APP/j/AAAAAAA" | grep -i -E "^HTTP|^location|^set-cookie|^cache-control|^referrer-policy" | sed -E 's/(jlv=)[^;]+/\1<visitor id>/'

echo; echo "### Signed-in calls (only with a real session of a signed-in student; the cookie value is never echoed)"
if [ -n "$JEELIVE_ACCESS_COOKIE" ]; then
  TOKEN=$(curl -s -X POST "$APP/rf/access" -H "$J" -d "{\"access_cookie\":\"$JEELIVE_ACCESS_COOKIE\"}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')
  curl -s "$APP/rf/mission/me" -H "Authorization: Bearer $TOKEN"; echo
  curl -s "$APP/rf/dream"      -H "Authorization: Bearer $TOKEN" | head -c 400; echo
  curl -s -X POST "$APP/rf/access/revoke" -H "Authorization: Bearer $TOKEN"; echo
else
  echo "skipped: export JEELIVE_ACCESS_COOKIE='<access_token cookie of a signed-in student>' to run them"
fi
