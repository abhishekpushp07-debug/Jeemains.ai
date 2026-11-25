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

