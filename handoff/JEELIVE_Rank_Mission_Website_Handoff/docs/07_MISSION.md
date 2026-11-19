# 07 · Mission

Mission is the product's promise and its growth loop on one page: a letter from the maker, a personal share link for
every student, and a live thank-you count of the friends that link brought in.

Screenshots: `MISSION/screenshots/` (fresh from the app). Code: `MISSION/code/`.

## 1. The idea in four lines

1. JEELIVE.AI is 100 % free. The maker built it with AI, at his own cost, and asks one thing: share it.
2. Each student gets a personal link (`…/api/j/AB2CDEF`).
3. When a friend opens it in a real browser, the student's count goes up by one, once per friend.
4. After a test, the result opens with one share ("Share to view results").

## 2. The page (`app_tabs_mission.tsx`)

Top to bottom (screenshots `01`–`03`):

1. Eyebrow `JEELIVE.AI · OUR MISSION`, title **"Ek share, kisi ki free taiyari"**.
2. **Impact panel** (§5).
3. Big red button **"Please share karo"** / "aur free education ko support karo" with the WhatsApp mark.
4. **The Mission card** (§6).
5. The same red button again, and a quiet "Doosre app mein share karo".
6. **Poori baat**: six points with an icon each (`copy.ts` `POINTS`), word for word.
7. The fine print (word for word):
   "200+ marks ek practice target hai, guarantee nahi. “PYQ DNA”, “institute se better” aur “100% made by AI Astra”
   creator ka design approach aur daava hai, koi independent audit nahi. Supplied solutions hi original source hain. NTA se affiliated nahi."

Pull to refresh reloads the count. Page background is the light app surface; the panel and card are royal night blue
with gold.

## 3. API

| Call | Sign-in | Answer |
|---|---|---|
| `GET /api/mission/me` (website, through the connector) | the student's website session | `{code, helped, week, link}` |
| `GET /api/rf/mission/me` (app server, what the connector calls) | 15-minute pass | `{code, helped, week}` |
| `GET /api/j/{code}` | none (the friend's browser) | `302` to `https://jeelive.ai` |

- `code`: 7 characters from `ABCDEFGHJKMNPQRSTUVWXYZ23456789` (no 0/O, 1/I/L). Created the first time the student asks; never changes.
- `helped`: friends counted, all time. `week`: counted in the last 7 days.
- `link`: added by the connector, `JEELIVE_SHARE_LINK_BASE + "/" + code`.
- The `/rf/` in the app-server path is only a historical prefix shared by the app's signed-in calls. The website only
  sees `/api/mission/me`.
- Samples (values masked): `MISSION/api_examples/`.

## 4. The counting rule

`GET /api/j/{code}`, every time:

1. The browser gets a `302` to `https://jeelive.ai` with `Cache-Control: no-store` and `Referrer-Policy: no-referrer`.
   A browser without the visitor cookie `jlv` gets one (random, 1 year, HttpOnly, Secure, SameSite=Lax, path `/api/j`).
2. Not counted, but still redirected: an unknown or malformed code; an empty browser name; link-preview robots and
   scripts (WhatsApp, Telegram, Facebook, Slack, Discord, Google and every "bot", curl, wget, python, headless browsers,
   Postman, …). CUBOT phones are real phones and are counted.
3. Counted (+1 to `helped`) only when **both** are new for this link: the visitor cookie, and a hash of
   (address + browser name). Opening again from the same browser, or clearing cookies on the same phone and network, does not count again.
4. No name, number or address is stored, only the hash.

Consequences for the website:

- The link must be opened by the friend's own browser. Never fetch `/api/j/…` from a server: the server's address
  and name would be seen, and nobody would be counted. The connector's optional `/api/j/{code}` route only **redirects**.
- The student's address for counting is read from the forwarding headers by the app server (`client_ip.py`).

## 5. Impact panel (`ImpactPanel.tsx`)

Royal night blue gradient (`#1A36B8 → #0B1C6B → #071241`), gold rim `rgba(242,193,78,0.45)`, a gold glow at the top left.

| State | Shows |
|---|---|
| loading | a 128 px skeleton |
| not signed in / unreachable | nothing (the share buttons stay) |
| `helped = 0` | a gold hand-heart medal, `AAPKA IMPACT`, "Aapka pehla share kisi ki free taiyari shuru karega" — never a made-up number |
| `helped ≥ 1` | a gold ring medal with the count (counts up once in 0.9 s, ease-out) and `DOST`; `THANK YOU! 🙏`; "Aapne **12 logon** ki free education mein help ki" ("1 dost" for one); `+K is hafte` chip when `week > 0`; "Agla padaav: 25 dost" with `12/25` and a thin gold track |
| always | "Jab koi dost aapke link se JEELIVE.AI kholta hai, wo yahan gina jaata hai. Har dost sirf ek baar." |

Milestones: 1, 5, 10, 25, 50, 100, 250, 500, 1,000, 2,500, 5,000, 10,000, then every 10,000.
Short count: under 10,000 Indian grouping (`1,234`); from 10,000 `25k+`. Helpers: `nextStep`, `shortCount` in `jeeliveApp.ts`.

## 6. The Mission card (`MissionCard.tsx`)

4 : 5 card (shared as 1080 × 1350 PNG), royal blue, a corner ribbon `100% MADE BY AI ASTRA`.

- Gold thank-you band at the top when `helped ≥ 1`: "Thank you Rahul 🙏 — aapne **12** logon ki free education mein help ki"
  (first name only; empty when the name is a phone number). Otherwise the eyebrow `EK CHHOTI SI BAAT`.
- The quote in serif: "Maine ise AI ke saath, apne kharche par, bahut mehnat se banaya hai. Taaki har JEE student
  **100% free** mein padh sake." Signature **Abhishek Pushp**, "Creator, JEELIVE.AI", gold `AP` seal.
- Four promise tiles (`copy.ts` `SEGMENTS`), word for word.
- Foot: `100% FREE` · "🙏 Please share karo · jeelive.ai".

Colours: blue `#1A36B8`, deep `#0B1C6B`, night `#071241`, gold `#F2C14E` (light `#FFE6A3`, deep `#A8761C`), ink `#DCE5FF`.

## 7. Sharing

What goes out: the card picture + the caption (`copy.ts` `caption(link)`, word for word) ending with
`Abhi kholo 👉 <the student's own link>`. Before the link is known, the plain `https://jeelive.ai`.

On the website (`shareCard.ts` web branch):

1. If the browser can share files (`navigator.canShare({files})`), share the PNG with the caption. A cancelled sheet
   (`AbortError`) = not shared.
2. Else, for the WhatsApp button, open `https://api.whatsapp.com/send?text=<caption>` (not `wa.me`: it breaks some emoji).
3. Else the system share with the text; if that fails, copy the caption and say
   "Message copy ho gaya. Kahin bhi paste karke bhej do."

Every Rank share also carries the student's link, so friends from a rank card count too.

## 8. "Share to view results" gate (`ShareGate.tsx`, `gate.ts`)

Only if the website shows test results. Screenshot `04`.

- After a test is submitted, the result is locked on that device for that attempt (`share_gate.<attemptId>` in local storage).
- The gate: royal night blue page, gold check badge, `TEST SUBMIT HO GAYA`, title by stage
  ("Aapka result taiyaar hai 🎉" / "Aapka result ban raha hai ⏳" / "Aapka result jald khulega 🔒"),
  the lock chip "Score, rank aur solutions bas ek share door", red **Share to view results** above and below the card,
  "Doosre app se share karo".
- **When it opens:** a share that left the page (WhatsApp in another tab or app) opens the result when the student comes
  back (`visibilitychange` on the web); if the page never left, 3 seconds after the share. A cancelled share sheet keeps
  it locked with "Share pura nahi hua. Result dekhne ke liye ek baar share karo." While waiting:
  "WhatsApp par bhej kar wapas aao, result yahin khul jaayega." Then a green "Shukriya! Result khul raha hai…" for 0.9 s.
  Leaving during the thank-you still unlocks.
- No device can prove a message was sent; coming back is the signal. This is a product decision.

## 9. Data on the app server

| Collection | Fields | Notes |
|---|---|---|
| `mission_links` | `uid`, `code`, `helped`, `created_ts` | unique `uid`, unique `code` |
| `mission_visits` | `code`, `key` (`c:<cookie>` or `d:<hash>`), `ts`, `counted` | unique (`code`, `key`) |

`uid` is the student's permanent website id (from the website's `GET /api/auth/me`), so app and website share one
count.

## 10. About the words "Rapid Fire" here

The card's third promise tile, the third point and one caption line name Rapid Fire as one of the product's promises.
That is the app's marketing copy, kept word for word so the app and the website say the same thing. No Rapid Fire code,
data, art or screen is in this pack.
