# Raat ki report (24-25 Nov) — owner ke uthne par padhne ke liye

Aapne kaha tha: "sota hoon, banate raho, kuch mat poochho, publish ke liye mat ruko". Maine yahi kiya.
**Kuch bhi deploy nahi hua.** Live par wahi purana code hai. Deploy tabhi hoga jab aap "deploy" likhenge.
Har packet ke baad rukne ki jagah maine yahan us packet ki chhoti report likhi hai.

## Packet A — Pocket 1 + 2 ki alag jaanch (poora)
- Testing agent (iteration_224): koi galti nahi mili. Usne 25 nayi jaanch likhi (tests/storage_stuck_edge232.py), sab paas.
- Alag code review: koi critical ya high galti nahi. Ek "medium" baat thi; uska poora text mere paas nahi bacha (tool ka jawab kat gaya tha). Isliye deploy se pehle poore badle code ka review dobara chalega aur is baar nateeja file me likha jayega.
- Browser jaanch 30/32: jo 2 "fail" dikhe woh jaanch ki apni ghadi thi (test server 21 minute purana tha, to 15-minute wali chetavni sahi dikh rahi thi). App ki galti nahi.
- Live ko sirf padh kar dekha (login ke bina): live par 23 Nov raat tak ka code hai, Pocket 2 ka kuch nahi. To agla deploy sirf storage ka kaam bhejega (aur jo aaj raat bana).

## Packet B — latke kadam ki rok (bana, jaancha)
- Kya bana: PDF ka koi kadam 10 minute tak bina harkat ke rahe to machine use chhod deti hai, likh leti hai ki kahan latka tha, lock khol deti hai aur 20 second baad save hui jagah se dobara chalati hai. Lagataar 3 baar latke to sirf wahi PDF "Atki hai" kehti hai (har ghante apne aap koshish, ya "Dobara chalao"). Machine panel me nayi line: "Latke kadam (24 ghante): N".
- Sirf PDF wali line par. Grading, score, report ko nahi chhua.
- Nayi file: backend/tejas/step_guard.py. Chhote badlav: jobs.py, book_worker.py, book_store.py, book_publish.py, machine.py, master.py, book_imports.py, db.py; screen: UploadProgress.js, MachinePanel.js, MockList.js.
- Jaanch: nayi suite tests/step_guard233.py 29/29. Purani 20 suite dobara, ek-ek karke: sab paas (kul 937 jaanch, 0 fail).
- Jo jaancha NAHI ja saka:
  - 10 minute sach me ruk kar nahi; jaanch me yeh had 1.2 second rakhi gayi.
  - 24 Nov wale asli latkaav ki wajah ab bhi nahi mili. Yeh rok uske asar ko sambhalti hai, wajah ko nahi. Agli baar latke to wajah database me (tejas_step_hangs) likhi milegi.
  - Screen ki nayi line browser me abhi nahi dekhi gayi (testing agent ki jaanch Packet C ke saath hogi).
- Do purani suite jo is kaam se pehle se hi nahi chalti (aaj ke code se pehle wale code par bhi wahi nateeja, maine chala kar dekha):
  - get_ready_iso188: 35/36 (uski apni test PDF ab "held" rehti hai).
  - maths_bookmarks_iso190: aapki 640-page PDF (/tmp/maths.pdf) is machine par nahi hai, isliye chal hi nahi sakti.

## Packet C — "Is PDF ko delete karo" (bana, jaancha)
- Kya bana: jis upload se kabhi koi test students tak nahi pahuncha (na Live, na Scheduled, na Off, na Library) use owner hamesha ke liye hata sakta hai. Button do jagah: Uploads ki row par "Delete", aur Draft mock ke Status menu me "Is PDF ko delete karo…". AITS ke din wali screen par bhi chhota dustbin.
- Dabane par ek box khulta hai: pehle "Kya hatega" (kitne Draft mock, kitne me aapke fix, kitne page, original PDF kahan hai, kitni pictures), phir "Kya nahi hatega" (doosre upload, bane hue test, students ke score, JEE Main PYQ). Jab tak aap bade aksharon me DELETE nahi likhte, laal button band rehta hai.
- Jo upload students tak pahunch chuka hai uske liye button dikhta hi nahi, aur server bhi mana karta hai (409) chahe koi seedha API se koshish kare. Reviewer ko 403.
- Delete dabate hi row list se hat jaati hai aur wahi PDF turant dobara upload ho sakti hai. Safai peeche chalti hai is kram me: (1) us PDF ka chalta kadam rukta hai, (2) Supabase me sirf us upload ka apna folder khali hota hai, (3) uske record, (4) sabse aakhir me upload ka apna record. Beech me server band ho ya Supabase na mile to 15-minute wali jaanch wahin se poora karti hai. Machine panel me nayi line: "Delete ki safai baaki: N" (wajah ke saath).
- Suraksha ki do taale: storage ka code sirf `jeelive/books/<us upload ki id>/` ke andar ki file hata sakta hai, koi bhi doosra path code khud mana kar deta hai; aur agar Delete ke usi pal us upload ka koi mock students ke liye ban gaya, to delete radd ho jata hai aur kuch nahi hatta.
- Emergent me rakhi file hatai nahi jaati (Emergent me hatana hota hi nahi): sirf uska record hatta hai. Box yeh saaf likhta hai.
- Nayi file: backend/tejas/book_delete.py, frontend/src/components/master/DeleteUploadDialog.js. Chhote badlav: tejas_storage.py (sb_list, sb_remove, sb_empty, sb_end_upload), master.py, series_admin.py, machine.py, jobs.py, route_contracts.py, request_contracts.py, db.py; screen: MasterType.js, MockList.js, SeriesDays.js, MachinePanel.js, master.css.
- Jaanch:
  - tests/upload_delete234.py 31/31 (alag test database, nakli Supabase).
  - tests/storage_delete_real234.py 9/9 ASLI Supabase par (preview bucket, do TEST folder): folder khali hua, padosi folder ki file byte-ba-byte wahi rahi, galat path mana hua, aadha bheja upload khatam hua. Ant me dono test folder me 0 file bachi.
  - Browser, desktop + 390px mobile: tests/ui_delete234.py 33/33, koi fail API call nahi. Mobile par box ke button pehle 36px ke the; ab 44px (ungli ke liye) kar diye.
  - Purani 24 suite ek-ek karke dobara: sab paas (kul 1,100+ jaanch). get_ready_iso188 35/36 pehle jaisa (Packet B se pehle wale code par bhi yahi).
  - Packet B ki nayi lines ("Latke kadam", latki PDF ki row) bhi isi browser jaanch me dekhi gayin.
- Review wali "medium" baat mil gayi aur theek ho gayi: badi PDF jo bina "jagah yaad rakhne" ke bheji jaaye aur Supabase use lauta de, woh pehle hamesha "intezaar" me rehti; ab do koshish ke baad "Atki hai" ban jaati hai. tests/storage_nocallback234.py 7/7.
- Jo jaancha NAHI ja saka:
  - Live par kuch nahi (deploy nahi hua).
  - 15-minute wali jaanch ko asli ghadi se nahi; jaanch me use haath se chalaya gaya.
  - Bahut bade upload (hazaaron pictures) ka delete asli Supabase par nahi; asli jaanch 4 file ki thi, nakli par 1,000+ ka panna-dar-panna rasta chala.



## Packet B + C — alag jaanch aur alag code review ke baad (25 Nov, 01:15 UTC)
- Testing agent (iteration_225): koi galti nahi mili. Usne 21 nayi jaanch likhi (tests/upload_delete_edge235.py): DELETE ke 17 galat roop (chhote akshar, space, nayi line, doosri lipi, khaali, faltu khaane) sab mana; doosre owner ka upload "mila hi nahi" (404); do Delete ek saath dabe to ek hi chala; storage ke 13 aur galat path mana hue.
- Alag code review: koi critical ya high galti nahi, aur koi aisa raasta nahi mila jisse kisi doosre upload, bane hue test, student ke score ya PYQ ka kuch hat sake. Do baatein mili, dono theek kar di:
  1. (Medium) "Latke kadam ki rok" ek sehatmand par lambe kaam ko bhi latka maan sakti thi: 100 page ek saath padhte samay ya ek mock ki saari pictures kaat-te samay beech me koi "main zinda hoon" ka ishaara nahi jata tha. Ab har 10 page / 10 picture ke baad ishaara jata hai. Nayi jaanch: bina ishaare wala lamba kaam chhoota (jaisa pehle hota), ishaare ke saath wahi kaam poora hua (100 page padhe gaye). step_guard233 ab 33/33.
  2. (Low) Delete ka box: ek upload ka box band karke turant doosre ka kholne par ek pal ke liye pehle wale ki ginti dikh sakti thi. Ab der se aaya jawab phenk diya jata hai. (Galat upload kabhi delete nahi ho sakta tha; server har baar khud jaanchta hai.)
- AITS wali screen ka dustbin (jo pehle browser me nahi dekha gaya tha) ab dekha gaya, desktop + mobile: jis PDF se kabhi test nahi bana uske paper par dustbin hai, jisse bana uske paper par nahi; DELETE likhne par paper list se hata. Mobile par dustbin 36px ka tha, ab 44px. Browser jaanch ab 41/41.
- In sudhaaron ke baad dobara, ek-ek karke: step_guard233 33, upload_delete234 31, upload_delete_edge235 21, phase1_iso221 17, storage_book229 22, storage_stuck231 49, storage_stuck_edge232 25, pictures_iso220 66, chapters_iso182 58, master_iso181 124, library_aits_iso180 125, series_dates_iso187 47, structure_imports_iso174 51. Sab 0 fail.
- Ek purani suite jo is kaam se pehle se nahi chalti: book_scale_iso171 (uske upload me "exam aur mock type" nahi hai, isliye server 422 deta hai; aaj ke badlav se pehle bhi yahi).
- Review ke do khule sawaal (jaanche nahi ja sake, isliye likh raha hoon):
  - Agar kisi PDF ka ek hi kadam 20 minute se zyada chalta rahe aur usi beech Delete dabe, to us upload ke apne folder me kuch pictures bach sakti hain; agli 15-minute jaanch unhe hata deti hai. Kisi doosre upload par asar nahi.
  - Do server hon to har server sirf apne kadam par nazar rakhta hai. Yeh theek hai, par do server par chala kar nahi dekha gaya (preview me ek hi server hai).
- Deploy 2 ki teeno shartein poori: testing agent paas, alag code review ho gaya, badlavon ki list is file ke ant me "Deploy se pehle" me hai. Deploy tabhi jab aap "deploy" likhen.


## Packet D — sach bolne wala storage badge (bana, jaancha) — 25 Nov, 07:25 UTC
- Kya bana: storage ki haalat ab database ke ek hi record me rehti hai, isliye har server ek hi baat dikhata hai. Badge me teen line: "Supabase · Pictures (chhoti file)", "Supabase · PDF (badi file)", "Emergent (fallback)". Har line ke saath: kab jaanchi gayi, kaise, kitna samay laga.
- Rang: hara (dono raaste theek, kuch ruka nahi), peela (dheema, koi file atki, 10 minute se ruki, badi file ka raasta fail ya kabhi jaancha nahi, ya Emergent chup), laal (Supabase jawab nahi de raha ya project par rok).
- Har jaanch naye naam ki test file se: likhi, wapas padhi, hatayi. Isse "Read back different bytes" wali galat chetavni nahi aati.
- "Badi file ka test" button: lagbhag 7 MB ki test file asli tukdon wale raaste se jati hai, wapas padhi jati hai, hata di jati hai. Yahi test apne aap bhi chalta hai (kabhi jaancha na ho, koi PDF us raaste par ruki ho, aur din me ek baar).
- Machine panel me aakhri 20 storage galtiyan (kab, kaun si file, kaun sa storage, kaun sa raasta, wajah) aur dono storage ki aakhri 20 reading ki speed.
- Nayi/badli file: backend/tejas/storage_health.py (dobara likhi), tejas_storage.py, jobs.py, machine.py, ceo.py, server.py; screen: StorageBadge.js, MachinePanel.js, master.css.
- Jaanch:
  - tests/storage_badge236.py 64/64 (alag test database, nakli Supabase).
  - tests/storage_badge_real236.py 9/9 ASLI Supabase par (preview bucket, sirf app ki apni jaanch file; koi file peeche nahi bachi).
  - Browser, desktop + 390px mobile: tests/ui_badge236.py 29/29, koi fail API call nahi.
  - Testing agent (iteration_226): koi galti nahi mili; usne 14 nayi jaanch likhi (tests/storage_badge_edge237.py), sab paas.
  - Purani 26 suite ek-ek karke dobara (07:12 se 07:19 UTC): 1,111 jaanch, 0 fail.
- Jo jaancha NAHI ja saka:
  - Live par kuch nahi (deploy nahi hua).
  - Do server ka ek record baantna ek hi process ke andar jaancha gaya; preview me ek hi server hai.
  - 10 minute, 15 minute aur 24 ghante ghadi aage badha kar jaanche gaye, sach me ruk kar nahi.
  - Packet D ke code ka alag code review us samay nahi hua tha. Woh 25 Nov 10:15 UTC ko ho gaya (neeche "Deploy ke liye taiyaar" dekhiye).
- Ek jaanch pehli baar 44/45 aayi thi: us jaanch ko ek test PDF chahiye thi jo us folder me thi hi nahi. PDF bana kar dobara chalayi: 48/48. App ki galti nahi thi.

## Packet E, F, G
- Shuru nahi hue. E ke liye sirf code padha gaya; koi code nahi likha gaya. Padhne me jo mila woh memory/HANDOFF_2026-11-25_SUPER_ADMIN_STORAGE.md ke section 8 me hai.

## Deploy se pehle (pichhle deploy, 23 Nov raat, ke baad preview me kya badla)
Upar likha tha ki yeh list is file me hai, par woh likhi nahi gayi thi. Ab yeh hai.
- Students ke liye: koi screen nahi badli. Picture bhejne ka raasta wahi hai.
- Super Admin me naya:
  1. Badi PDF 0% par nahi atakti (Pocket 1).
  2. Ek file atke to sirf wahi rukti hai: "Atki hai", wajah, "Dobara chalao", har 15 minute apne aap koshish (Pocket 2).
  3. PDF ka koi kadam 10 minute chup rahe to machine use chhod kar dobara chalati hai (B).
  4. "Is PDF ko delete karo": DELETE likh kar, sirf us upload ke liye jisse kabhi koi test nahi bana (C).
  5. Badge teen line aur sahi rang ke saath; "Badi file ka test"; aakhri 20 galtiyan (D).
- Kul 31 file badli (21 server, 10 screen). Poori list: HANDOFF file ka section 7.
- Deploy ki teen shartein: testing agent paas (A se D tak ho gaya); alag code review (A, B, C, D sabka ho gaya); yeh list (ab hai).
- Deploy tabhi jab aap "deploy" likhen.

## Deploy ke liye taiyaar — 25 Nov, 10:25 UTC
- Packet D ka alag code review ho gaya: koi blocker nahi, koi critical ya high galti nahi. Poora nateeja: test_reports/code_review_packet_D.md.
- Ek "medium" baat mili, theek NAHI ki gayi (jaan-boojh kar): Emergent ya Supabase latak jaye to badge ya Machine panel kholne par woh screen kuch minute tak ghoomti reh sakti hai. Sirf owner ki screen; upload, kaam aur students par asar nahi. Pichhle deploy ke code me bhi badge isi tarah jaanch ka intezaar karta tha, yaani yeh is deploy se nahi bigadta. Sudhaar agle packet me, jaanch ke saath; deploy se theek pehle bina jaanch ka naya code nahi dala.
- Teen "low" baatein usi file me hain; theek nahi ki gayi.
- Regression ke baad koi app code nahi badla: aakhri badlav 06:02 UTC, regression 07:12 se 07:19 UTC. Packet E ka koi code nahi likha gaya.
- Production build ban gaya (yarn build, 31 second, koi galti nahi).
- Live ke Secrets me zaroori naam set hain: SUPABASE_URL, SUPABASE_SECRET_KEY, WEBHOOK_CRON_SECRET, FRONTEND_URL. Is deploy ko koi nayi key, nayi library ya naya cron nahi chahiye.
- Deploy-jaanch tool ne ek baat uthayi: .gitignore me ".env" likha hai. Yeh line 17 Oct se hai aur 23 Nov ke deploy wale code me bhi thi; keys Secrets me rakhi hain. Isliye ise nahi badla (badalne se secret wali file git me chali jati). Agar deployer isi par ruke to uska message builder ko bhejiye.
- Jaancha NAHI gaya: live par kuch nahi; asli do server; store ke latakne par asli samay.
- 25 Nov, lagbhag 12:20 UTC: owner ne deploy panel se deploy kar diya (Packet A se D live par).
- Deploy ke baad live ko ek baar sirf padha gaya (deployer ki read-only report, 25 Nov):
  - Dono pod theek chal rahe hain, 0 restart, koi crash ya memory ki galti nahi; 24 ghante ke log me koi galti ki line nahi.
  - Atki PDF "mathematics chapterwise": ab 0% par nahi hai. Poori padhi ja chuki hai: 27 me se 26 mock ready, 1 mock "Attention Needed" me (use Fix me dekhna owner ka kaam hai).
  - Storage record: Supabase aur Emergent theek, galtiyon ki list khali. Galat laal line ki wajah (har 409 par sabke liye aaram) ab code me nahi hai.
  - Koi kaam queue me ruka nahi; latke kadam 0; 15 minute wali jaanch har baar 200 de rahi hai.
  - Jo is report me NAHI tha: badi file (7 MB) ke test ka nateeja alag se nahi likha tha; badge ka rang owner ki screen par hi dikhega.
- 25 Nov, 10:35 UTC: owner ne "deploy" likha. Builder ne deployer ko bheja; deployer ne deploy NAHI kiya aur kaha ki yeh deploy panel (UI) se hi hoga, jahan "purani app replace" ya "nayi app" chunna hota hai. Owner ko yahi bataya gaya. Jab tak owner "deploy ho gaya" na likhe, app ka koi code nahi badlega (Packet E shuru nahi hoga), taaki aadha kaam deploy me na jaye.


## Packet E — picture ka saboot: kadam 1 aur 2 (25 Nov, deploy ke baad; SIRF preview me)
- **Deploy nahi hua.** Live par Packet A se D hi hain. E abhi adhoora hai (neeche "abhi nahi bana" dekhiye).
- Kadam 1, saboot ka function (nayi file backend/tejas/picture_proof.py): ek paper ki har picture (sawaal, solution aur option ke tukde) ek hi storage me hai ya nahi.
  - Supabase: picture Supabase ki apni list me ho, aur size wahi ho jo save karte samay tha. Emergent: har picture wapas padh kar fingerprint se milayi jati hai.
  - Yeh function sirf padhta hai: kuch save, copy ya delete nahi karta. Verified JEE Main PYQ par chalta hi nahi.
- Kadam 2, PDF se bana mock jab Live ya Scheduled hota hai (book_publish.py, book_worker.py):
  - Test banne se pehle saboot liya jata hai. Jo picture na mile ya badli hui mile, sirf wahi ek baar dobara save hoti hai, phir jaanch dobara.
  - Phir bhi saabit na ho: mock Draft rehta hai, koi test nahi banta. Row: "Atki hai: iski pictures storage mein saabit nahi hui ... Wajah: 28 pictures storage me nahi mili", saath me "Dobara chalao"; har 15 minute apne aap koshish. Baaki mock aur kitaabein chalti rehti hain.
  - Supabase khud jawab na de (503) to kisi picture ko "gayab" nahi kaha jata: kitaab Supabase ka intezaar karti hai, pehle jaisa.
  - Pictures do storage me bati hon to mock Live nahi hota aur row batati hai.
  - Scheduled mock ki jaanch schedule karte samay hoti hai, khulne ke samay nahi.
  - Nayi save hui picture ke record me ab size bhi likha jata hai (purane record me size nahi hai; unke liye sirf "list me hai" dekha jata hai).
- Screen par: saabit mock ki row par "Pictures: 28 / 28 · Storage: Supabase". Uploads ki row, Mocks ki row, Machine panel aur badge "saabit nahi hui" kehte hain (pehle wali line "picture Supabase mein nahi ja rahi" nahi).
- Jaanch (sab ek-ek karke, test database par):
  - tests/picture_proof238.py 26/26 (function akela).
  - tests/picture_gate239.py 40/40 (app ke apne route + asli worker, nakli Supabase).
  - tests/picture_proof_real239.py 12/12 asli Supabase par, sirf preview bucket, sirf TEST_ files (ant me hata di gayi, 0 bachi). 1,011 file wale folder me bhi list poori padhi gayi.
  - Browser: tests/ui_picture239.py 43/43 (desktop + 390 px; pehle 33 thi, ab All India Test Series wala page bhi isi me hai).
  - Testing agent (test_reports/iteration_227.json): meri do suite dobara chalayi (26/26, 40/40) aur apni nayi tests/picture_gate_edge240.py likhi, 14/14. Koi galti nahi mili. App ka code usne nahi badla.
  - AITS (14:20 se 14:32 UTC): tests/picture_aits241.py 26/26. Uske baad 11 suite ek-ek karke dobara: picture_gate239 40/40, picture_gate_edge240 14/14, picture_proof238 26/26, storage_stuck231 49/49, master_iso181 124/124, library_aits_iso180 125/125, series_dates_iso187 47/47, storage_badge236 64/64, step_guard233 33/33, storage_wait224 27/27, structure_iso173 133/133. 0 fail.
  - Purani 32 suite dobara (13:27 se 13:35 UTC): 1,210 jaanch, 1 fail. Woh ek (media_cdn_iso198 "paper built") Packet E se pehle wale code par bhi waise hi fail hoti hai; maine pichhle commit ki copy par chala kar dekha.
  - Chaar aur purani suite jo E se pehle bhi isi tarah fail hoti hain (copy par dekha): publish_fail_iso211 4/5, media_warm_iso217 35/36, get_ready_iso188 35/36, get_ready_iso189 8/9.
  - Do purani suite me ek-ek line badalni padi kyunki unka apna nakli Supabase list nahi deta tha / unka wrapper naya argument nahi leta tha: storage_wait224 (27/27), step_guard233 (33/33). tests/storage_wait_bridge224.py me bhi wahi ek line badli; woh bridge dobara chalaya NAHI gaya.
- Abhi NAHI bana (E ke baaki kadam): (3) chuna hua samay nikal jaye to der se na khule; (4) Likha hua mock, Off se Live, Library se wapas; (5) purani Emergent pictures ki Supabase me copy; (6) "Pictures ki poori jaanch" button.
- AITS (All India Test Series) ka din wala paper, ab jaancha hua:
  - PDF mock ko din diya aur Supabase ne uski pictures nahi rakhi: us din ka paper NAHI banta, mock ka din bana rehta hai, PDF "Atki hai" kehti hai, doosri PDF ka din ban jata hai.
  - Naya (chhota badlav): Master me us din ki row par ab wajah dikhti hai: "Atki hai: iski pictures storage mein saabit nahi hui, isliye is din ka paper abhi taiyaar nahi hua. Wajah: 28 pictures storage me nahi mili ..." Pehle wahan hamesha "taiyaar ho raha hai" likha rehta tha. Students ko is bare me kuch nahi dikhta (jaancha: student aur bina login, dono).
  - Supabase pictures rakhne lage + "Dobara chalao": paper usi din ke liye ban jata hai, bina page reload ke row badal jati hai.
  - Intezaar ke dauran din khul jaye: paper der se NAHI banta; mock ka din hat jata hai aur woh "bina din wale paper" ki list me laut aata hai; kuch "Atki hai" nahi rehta.
  - Badli hui files: backend/tejas/master.py (ek padhne wala function alag kiya, kaam wahi), backend/tejas/series_admin.py, frontend SeriesDays.js, MockList.js, MasterShared.js, master.css. LiveSeries.js nahi chhui.
- Jaancha NAHI gaya: asli do server; live par kuch nahi; tests/storage_wait_bridge224.py dobara nahi chalaya.
- **Deploy ki salaah: E poora hone se pehle deploy na karein.** Wajah: agar kisi purani kitaab ke Draft mock ki kuch pictures Emergent me aur kuch Supabase me hain, to woh mock ab Live nahi hoga aur use theek karne wala kadam (5) abhi bana nahi hai.

