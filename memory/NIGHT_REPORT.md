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
