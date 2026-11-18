# JEELIVE.AI: load test + 1–2 lakh capacity report (18 Nov 2026)

Yeh test preview server par chala (jeelive.ai par nahi). Saare load accounts aur unka data test ke baad hata diya gaya.

## Seedhi baat
- Preview server par 2 vCPU hain, ek backend process hai, aur database aur test chalane wali machine bhi usi par hai. Is server ne 1,000 students sambhaale: sab 30 second mein join hue aur 3 minute tak likhte rahe. Koi sign-in, start ya answer save fail nahi hua. 2,000 students par CPU 100% ho gaya aur test apne aap ruk gaya.
- Poore 3 ghante ke JEE paper mein ek student lagbhag **1.2 CPU-second backend** aur **0.43 CPU-second database** leta hai. Yeh number naapa gaya hai, andaaza nahi.
- **1 lakh students**: poore paper mein average ~11 vCPU backend aur ~4 vCPU database. Start ke 15 minute mein ~45 vCPU chahiye, kyunki question pictures server se jaati hain.
- **2 lakh students**: average ~22 vCPU backend aur ~8 vCPU database. Start window mein ~90 vCPU.
- Sabse bade do khatre code mein nahi hain:
  1. **Picture data**: ek poora JEE paper ~7.4 MB pictures ka hai. 1 lakh students = start ke 15 minute mein ~740 GB.
  2. **Cloudflare**: ek hi IP se bahut requests aayi to Cloudflare ne "Just a moment…" challenge (429) de diya. App tak request pahunchi hi nahi. School, coaching ya hostel ke ek Wi-Fi par baithe bahut se students ke saath exam ke din yahi ho sakta hai.

## Test kaise chala
- Paper: JEE Main PYQ 08 Apr 2026 Shift 2. 75 sawaal, 180 minute, picture wale sawaal.
- Har student yeh karta hai: sign-in, paper start, Begin, picture pack, har ~30 second par ek answer save, aadhe saves se pehle ek visit, submit, phir result.
  - Har save ke saath time record bhi jaata hai, bilkul asli player ki tarah: 2 on-screen stretch aur 1 answer change.
  - Asli paper mein ek save ~72 second par hota hai. Is test mein save 2.4 guna tez the.
- Accounts: 9,000 test numbers, sab +91600197 se shuru. Test se pehle database mein bana diye, isliye sign-in rush exam ke din jaisa tha.
- Har stage khud ruk jaata hai agar retry ke baad bhi 2% se zyada calls fail hon, ya p95 5 second se upar chala jaaye.
- Do raaste:
  - (A) Public preview URL se, yaani Cloudflare → load balancer → server.
  - (B) Usi preview server par seedha (127.0.0.1:8001), edge ke bina. Yeh isliye kiya kyunki (A) mein Cloudflare ne hamari ek IP rok di thi.
- CPU har stage mein alag naapa gaya: backend process, MongoDB aur test machine ka.

## Results
### A. Public preview URL se (Cloudflare ke through)
| Students | Kya hua | Latency |
| --- | --- | --- |
| 3 (smoke) | Sab 200 | save p95 0.11 s |
| 20, poora paper (7 picture packs) | 140 mein se 132 packs pehli baar mein aaye, baaki retry se. 1 pack ≈ 1.05 MB | pack ~1 s (network transfer) |
| 200, sab ek saath | 0 failure | sign-in p50 2.4 s (200 ek saath), save p95 0.32 s, visit p95 0.37 s, results p95 0.19 s |
| 500, ek IP se | Cloudflare ne 429 "Just a moment…" diya, request app tak pahunchi hi nahi | – |

### B. Usi preview server par seedha
| Students (30 s mein join) | Kya hua | Latency |
| --- | --- | --- |
| 500 | 0 failure (7,974 calls) | sign-in p95 29 ms, save p50 46 ms / p95 50 ms |
| 1,000 | Sign-in, start, save sab 200 (18,564 calls). 1,000 ne ek saath submit kiya to 298 result checks ko "busy" mila (1.6%), lekin sabko result mil gaya | save p95 51 ms, submit p95 0.26 s |
| 2,000 | Pod CPU 2.0/2.0 cores, sign-in p95 5.8 s, "busy" errors aaye, isliye test apne aap ruk gaya | – |
| 300 × 30 saves (cost alag naapne ke liye) | 0 failure, 8,964 saves | save p95 51 ms |

## Ek student ka kharcha (naapa hua)
| Kaam | Backend CPU | Database CPU |
| --- | --- | --- |
| Sign-in, start, Begin, pehla picture pack, submit, grading, result | 0.074 s | 0.016 s |
| 1 answer save (time record ke saath) + aadha visit | 4.3 ms | 2.7 ms |
| 150 saves (3 ghante ka paper) | 0.65 s | 0.41 s |
| Baaki 6 picture packs (poora paper) | ~0.32 s | ~0 |
| Analysis pehli baar kholna | ≤ 0.18 s | – |
| **Kul, ek student** | **~1.2 s** | **~0.43 s** |

- Class stats (Topper / Top 10% / Average): 2,700 students wale paper par ek rebuild ~13 CPU-second leta hai, yaani ~5 ms per student. 1 lakh students par ek rebuild ~8 minute lega.
- Database storage: ek student ka ek paper ~65 KB. Isme attempt 14 KB, marks ledger 33 KB, peer entry 12.6 KB aur class entry 2.3 KB hain. Time record chhote test mein 2.6 KB tha; poore paper mein yeh zyada hoga.

## 1 lakh aur 2 lakh ka hisaab
Maan ke chala:
- 3 ghante ka paper.
- Har student 150 saves aur 75 visits karta hai.
- Sab 15 minute ke andar start karte hain.
- Zyadatar submit aakhri 5 minute mein hote hain.

| | 1 lakh | 2 lakh |
| --- | --- | --- |
| Answer saves | ~1,390 / s | ~2,780 / s |
| Visits | ~690 / s | ~1,390 / s |
| Sign-in + start (15 min mein) | ~111 / s | ~222 / s |
| Submit (5 min mein) | ~333 / s | ~667 / s |
| Backend, 3 ghante ka average | ~11 vCPU | ~22 vCPU |
| Backend, start window (pictures server se) | ~45 vCPU | ~90 vCPU |
| Backend, start window (pictures CDN se) | ~6 vCPU | ~12 vCPU |
| Database average (2× headroom ke saath) | ~4 (→ 8) vCPU | ~8 (→ 16) vCPU |
| Picture data, start window | ~740 GB (~6.6 Gbit/s) | ~1.5 TB (~13 Gbit/s) |
| Database storage, ek paper | ~7 GB | ~14 GB |

**Server size, 2× headroom ke saath:**
- 1 lakh: ~24 backend workers (jaise 6 pods × 4 vCPU, har pod mein 4 workers) aur ~8 vCPU database.
- 2 lakh: ~48 workers aur ~16 vCPU database.
- Dono mein pictures CDN se jaani chahiye. Bina CDN ke sirf start window ke liye ~45 / ~90 vCPU chahiye.
- Ek Python worker zyada se zyada ~1 core use karta hai. Agar production mein ek pod par ek hi worker chalta hai, to pod ke baaki cores bekaar padhe rehte hain. Platform support se poochna hai ki ek pod par kitne workers chalte hain.

## Kya theek karna zaroori hai
- **P0 (platform support)**: jeelive.ai ki /api calls par Cloudflare ka bot challenge aur rate limit hatwana ya dheela karwana, taaki ek Wi-Fi par baithe bahut se students na rukein. Upar wale size ke pods, workers aur database tier bhi.
- **P0 (code, aapki approval chahiye)**: question pictures CDN se jaayein. Har paper ki pictures fixed aur cache ho sakne wali ho, aur paper ke start time tak locked rahein. Isse start window ka ~85% CPU aur network bachega.
- **P1**: Sign-in lane ek process mein 4 kaam ek saath karti hai (TEJAS_INFLIGHT_AUTH), isliye ~50–60 sign-ins/s per process par ruk jaata hai. Ise cores ke hisaab se badhana hai. Read lane (16) bursts mein "busy" deti hai; website khud retry karti hai.
- **P1**: 1 lakh finishers ke liye class stats ko incremental banana, taaki har rebuild poori class dobara na gine.
- **P1**: Submit rush mein grading queue lambi hoti hai. 1,000 ek saath submit hue to sabke result aaye, lekin kuch checks ko "busy" mila.

## Kya naapa nahi ja saka
- Asli India 4G aur alag-alag IPs se aane wale students. Test machine ek hi thi, ek hi IP.
- Production database aur production pods. Yeh test preview par tha.
- Test machine aur app ek hi 2-vCPU pod par the, isliye test machine ne bhi CPU liya (~13 CPU-s per 1,000 students).
- 1–2 lakh seedha nahi chalaaya. Upar ka hisaab naape hue per-student kharche se nikala gaya hai.

## Safai
Hata diye gaye:
- 9,000 accounts aur 3,889 attempts
- 2,661 marks ledgers aur 5,262 sessions
- 2,673 jobs aur 2,776 time records
- 2,639 peer entries aur 2,639 class entries
- 181 analysis

Preview database wapas pehle jaisa hai: 2 profiles, 8 attempts, 0 orphan.

## Tools aur logs
- `backend/tools/load_live.py`. Env: LOAD_SIGNIN_ONLY, LOAD_PACKS, LOAD_RAMP, LOAD_BASE, LOAD_PIDS, LOAD_ORIGIN.
- `backend/tools/load_accounts.py seed|remove`
- Logs: `/app/test_reports/load197_*.log`
