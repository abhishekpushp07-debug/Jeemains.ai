# Student Choice: app jaisa poora, website aur app dono par, ek hi engine se

Student JEE Main ke chapter-wise sawaalon se apna paper khud banata hai: chapters chun kar sawaal tick karke (75 tak), ya sirf ginti bata kar random mock.
Website teen darwaze banati hai; website ke apne naye pages aur app, dono inhi teen darwazon se chalte hain, isliye niyam aur bana hua paper dono jagah ek hi rehta hai.

Abhi koi code nahi likha gaya aur kuch deploy nahi hua. Banana is plan ki manzoori ke baad shuru hota hai. Live par kuch tabhi jata hai jab owner `deploy` likhe.

## Kiske liye

- **Students (website aur app):** apne chapters, apne sawaal, apna paper. Paper ek jagah banta hai aur dono jagah "My Tests" me dikhta hai.
- **Owner (Super Admin):** ek jagah se chalu / band karta hai, niyam rakhta hai aur ginti dekhta hai.
- **App project:** use teen darwaze bilkul usi shape me milte hain jo usne likh kar diya hai. App me kuch badalna nahi padta.

## Kya banega

### Aaj ki haalat

| Cheez | Haalat (28 Nov 2026) |
| --- | --- |
| Website par Student Choice | Bana hi nahi. Live par teeno darwaze 404 dete hain. |
| App me "Chapters chuno, phir us chapter ka poora test" | Chalta hai (website ki chapter-wise list se). |
| App me "Sawaal khud chuno" aur "Random mock" | Screens app ke preview me taiyaar, band hain. Website ke darwazon ka intezaar. |
| Sawaal | Alag bank nahi. Wahi JEE Main chapter-wise sawaal (live par 81 chapter test, 3,750 sawaal). |

### A. Teen darwaze (website ke pages aur app, dono inhi par)

Shape, field ke naam aur har seema wahi jo app ne likhi hai (docs/app_book_v3/BOOK.md Part 1; app ki 28 Nov ki list ki copy plan/app_list_2026-11-28.md me). Website apni taraf se koi field nahi badalti.

| Darwaza | Sawaal | Jawab |
| --- | --- | --- |
| **A** "Chalu hai? Niyam kya hain?" | Kaun sa tareeka khula hai | "Sawaal khud chuno" khula ya band, "Random mock" khula ya band, zyada se zyada sawaal, har subject ka time per sawaal. Dono band hon to "nahi hai" (404). |
| **B** "Is chapter ke sawaal dikhao" | Ek chapter test ke sawaal | Har sawaal ka number, MCQ ya numerical, aur sirf sawaal ka tukda (picture ya likhe shabd). 50 sawaal ek page. |
| **C** "Yeh paper bana do" | Chune hue sawaal, ya sirf ginti | Naye paper ki pehchaan. Uske baad woh paper har paper ki tarah khulta hai. |

Pakke niyam:
- Darwaza B kabhi options, sahi jawab ya solution nahi bhejta. Yeh server se hi nahi nikalte.
- Darwaza A kabhi galti (5xx) nahi deta. Andar koi dikkat ho to "band" kehta hai, taaki app ki chapter list na toote.
- Darwaza C par ek hi maang do baar aaye (double tap, dheema net) to ek hi paper banta hai.
- Sawaal ki picture ke link bina sign-in ke khulte hain aur 24 ghante se zyada chalte hain.
- Teeno darwaze sirf sign-in kiye student ke liye.

### B. Bana hua paper

| Baat | Niyam |
| --- | --- |
| Sawaal | 1 se 75. Random mock me kam se kam 3. |
| Marking | Sahi +4, galat −1, chhoda 0. Poore marks = sawaal × 4. |
| Time | Maths ka har sawaal 3.2 minute, Physics 2.4, Chemistry 1.6. Jod upar ke poore minute tak. (25 + 25 + 25 = 3 ghante; 10 + 10 + 10 = 1 ghanta 12 minute; 25 Maths = 1 ghanta 20 minute.) |
| Kram | Physics, phir Chemistry, phir Maths. Subject ke andar pehle MCQ, phir numerical. |
| Random ka batwara | Teeno subject me barabar; bache hue ek-do pehle Physics, phir Chemistry ko (10 = 4 + 3 + 3; 11 = 4 + 4 + 3; 75 = 25 + 25 + 25). Subject ke andar saare chapters se mila-jula, lagbhag 4 MCQ par 1 numerical. |
| Naam | Apne aap, jaise "Student Choice · 30 Q · 28 Nov". |
| Kiska | Sirf usi student ka. Kisi list, catalogue, Master ya Library me nahi aata. Doosra student use khol nahi sakta ("nahi mila"). |
| Ek din me | Ek student 5 paper (owner ka faisla). Chhathe par saaf line: "Aaj ke 5 paper ban chuke hain. Kal naya paper bana sakte ho." |

Paper banne ke baad woh aam paper hai:
- Wahi paper ka page, wahi taiyaari ki screen, wahi exam screen, autosave, ghadi, submit.
- Wahi result, wahi 8 hisson wala analysis (chapter ke naam ke saath), solutions, PDF report, "dobara do".
- Galat aur chhode sawaal Misfire me jate hain.
- "My Tests" me dikhta hai, website aur app dono par. My Tests ki har row par paper ka prakaar bhi bheja jata hai (app ne maanga hai).
- **Rank, percentile, leaderboard aur compare nahi.** Us jagah screen kehti hai: "Is test par Rank nahi banta".
- **Dream College meter me kabhi nahi ginta**, chahe kitna bhi lamba ho.
- "Sawaal galat hai" ki report asli chapter-wise sawaal tak pahunchti hai.

Mana karne par student ko saral line milti hai (app use jaise ki taise dikhata hai):

| Kab | Line |
| --- | --- |
| 75 se zyada sawaal | "Ek paper me zyada se zyada 75 sawaal ho sakte hain." |
| Koi chuna sawaal ab maujood nahi, ya do baar aaya | "Chune hue sawaalon me se kuch ab available nahi hain. Dobara chuno." |
| Random ki ginti seema se bahar | "3 se 75 ke beech ginti likho." |
| Din ke 5 paper poore | "Aaj ke 5 paper ban chuke hain. Kal naya paper bana sakte ho." |

### C. Super Admin › JEE Main › "Student Choice"

- **Do switch, dono shuru me Off:** "Sawaal khud chuno" aur "Random mock". Alag-alag khulte aur band hote hain.
- **Setting:** zyada se zyada sawaal (1 se 75; shuru me 75), har subject ka time per sawaal (2.4 / 1.6 / 3.2), ek din me paper (shuru me 5), har subject ki seema (shuru me khaali).
- **Pool (sirf dekhne ke liye):** kaun se chapter test shamil hain aur har subject me kitne sawaal. Pool = jo JEE Main chapter-wise test students ke liye Live hain.
- **Ginti:** aaj aur kul kitne paper bane, kitne students ne banaye, kitne chun kar aur kitne random.
- Switch ya setting badalne par website turant, aur app 2 se 4 minute me follow karta hai. Har badlav ka record rehta hai (kisne, kab).
- Kisi chapter ko Student Choice se hatana ho to us chapter test ko Off karna hota hai, jaise aaj.

### D. Website ke apne pages (app jaisa poora)

1. **Home par tile "STUDENT CHOICE"** ("apne chapters chuno", NEW ke nishaan ke saath), aur JEE Main ke page par wahi card. Sirf sign-in kiye student ko, aur sirf tab jab kam se kam ek switch On ho.
2. **Pehli screen:** upar gehra laal card ("Apna paper, apni marzi.", "75 sawaal tak", "+4 / −1", "time subject ke hisaab se"). Neeche card "Sawaal khud chuno" aur "Random mock" (jo khula ho), aur "Banaye hue paper ka time" ka niyam. Aaj kitne paper bane ("2 / 5").
3. **Step 1, "Chapters chuno":** upar search box, Physics / Chemistry / Maths ke teen tab, har chapter ki row ("1. Units, Dimensions and Errors · 68 sawaal · 64 MCQ · 4 numerical"). Tap se tick. Neeche bar: kitne chapter chune.
4. **Chapter search (app jaisa hi):** teeno subject me ek saath, har akshar par, bina server ke. "therm" se Thermodynamics; "goc", "ktg", "wep" jaise pehle akshar; "3d", "shm", "emi", "emw", "nlm", "pnc" jaise chhote naam; galat spelling ("kinametics") par milte-julte naam.
5. **Step 2, "Sawaal chuno":** chune chapters ke sawaal, ek card ek sawaal: tick, "Q 1", MCQ ya NUMERICAL, sawaal. **Options nahi.** Neeche bar: "7 / 75 sawaal", "17 min · 28 marks", "Paper banao". 76va tick nahi lagta.
6. **"Aapka paper" sheet:** subject-wise ginti aur time, poore marks, marking, phir "Haan, paper banao".
7. **"Random mock" sheet:** ginti ka box (30 se shuru), button 15 / 30 / 45 / 60 / 75, subject-wise batwara aur time pehle se dikhta hai, phir "Random mock banao".
8. **"Sawaal khud chuno" band ho aur sirf Random khula ho:** step 2 me chune chapters ke poore chapter test dikhte hain (Start / Resume / Result), jaise app me aaj.

### E. Purana kaam surakshit

Yeh sab nahi chhua jata:
- Chapter-wise tests khud, unke sawaal, key aur time (time Phase 2 me).
- JEE Main PYQ, AITS, `LiveSeries.js`, Rapid Fire, Rank page, Mission, Dream.
- Login, PIN, scoring, rank ki machine.
- PDF upload, cutter aur storage ki machine.
- App ke purane darwaze: sirf naye judte hain.

Aur:
- Dono switch Off rahein to website aur app bilkul aaj jaise chalte hain.
- Koi nayi picture nahi banti. Bana hua paper un chapter tests ki wahi pictures leta hai jo Live hone se pehle saabit ho chuki hain.
- Student ke request me koi AI call nahi.
- Live ke database se kuch hard delete nahi hota.

### F. Bojh (1 lakh students ko dhyan me rakh kar)

- Darwaza A aur B ka jawab har student ke liye ek hi hai, isliye server ise apni yaad me rakh kar deta hai; har request par database nahi padha jata.
- Paper banate samay sirf chune sawaalon ki pehchaan rakhi jati hai. Poore sawaal tabhi jamte hain jab student paper shuru karta hai, jaise har paper me.
- Din ke 5 paper ki seema database ko surakshit rakhti hai.
- Kitne students ek saath chal sakte hain, iska koi number bina load test ke nahi diya jata.

### G. Kaam ka tareeka

Phase 1 paanch chhote hisson me, ek ke baad ek, banta hai:
1. Neenv aur Super Admin ka hissa (dono switch Off).
2. Darwaza A aur B.
3. Darwaza C aur paper ka poora safar (shuru, submit, result bina rank, analysis, Misfire, My Tests).
4. Website ke pages (desktop aur 390 px phone).
5. Kinare ke maamle, app project ke liye jawab ka note, aur saari purani jaanch dobara.

- Aakhir me ek alag jaanch, phir owner ko ek report: kya bana, kya jaancha gaya, kya jaancha nahi ja saka.
- Uske baad kaam rukta hai. Deploy sirf owner ke `deploy` likhne par.

### H. Jo is plan se nahi hota, ya jaancha nahi ja sakta

- **App ke phone tak pahunchna:** app ki "Sawaal khud chuno" aur "Random mock" screens app ke preview me hain. Students ke phone par tab aati hain jab app ka naya version publish ho. Woh app project ka kaam hai; app project ke mutabik uska publish abhi Emergent support ke jawab tak ruka hai.
- **App ke saath asli jaanch:** website ke darwaze app ke likhe namoonon aur niyamon se milaye jate hain. App ke asli server se pehla run tabhi ho sakta hai jab app project website ke preview se jude, ya deploy ke baad live par. App project ko switch On karne se pehle bataya jata hai (yeh unki shart hai).
- **Live par test student nahi hai** (do test student owner ne abhi roke hain). Live par pehla asli paper owner ya pehla student banata hai.
- **Asli phone** par kuch nahi jaancha ja sakta.
- **Solution ki picture me chhapi "Source: AITS Mock …" line:** bane hue paper me wahi solution picture aati hai jo chapter test me hai. Live par yeh line tabhi hatti hai jab owner Super Admin me "Line hatao" daba chuka ho.

## User flow

**Student, website par: sawaal khud chunna**
1. Home › "STUDENT CHOICE".
2. "Sawaal khud chuno" › chapters tick karta hai (search se ya subject ke tab se) › "Sawaal dekho".
3. Har chapter ke sawaal dekhta hai (options ke bina), jo chahiye woh tick karta hai. Bar me ginti, time aur marks badhte hain.
4. "Paper banao" › "Aapka paper" sheet › "Haan, paper banao".
5. Paper ka page khulta hai › "Start attempt" › exam › submit › result (bina Rank) › analysis aur solutions.
6. Paper "My Tests" me rehta hai; wahi paper app me bhi dikhta hai.

**Student, website par: random mock**
1. Home › "STUDENT CHOICE" › "Random mock".
2. Ginti likhta hai ya 15 / 30 / 45 / 60 / 75 dabata hai. Batwara aur time dikhta hai.
3. "Random mock banao" › paper ka page › aage wahi.

**Student, app me**
- Website par switch On hone ke 2 se 4 minute baad, app ki pehli screen par wahi do tareeke khul jate hain (app ke us version me jisme yeh screens hain). Paper website banati hai; baaki sab wahi.

**Owner**
1. Plan manzoor karta hai.
2. Phase 1 banta hai; report milti hai.
3. Owner `deploy` likhta hai. Website live hoti hai; dono switch Off hain, students ko kuch naya nahi dikhta.
4. App project ko khabar jati hai. Owner Super Admin me ek ya dono switch On karta hai.
5. Website par tile aa jata hai; app me tareeke khul jate hain.
6. Kabhi band karna ho: switch Off. Bane hue paper apni jagah rehte hain.

**Jab kuch galat ho**

| Haalat | Student ko kya dikhta hai |
| --- | --- |
| Net dheema, "Paper banao" do baar daba | Ek hi paper. |
| Chune chapter ka test owner ne beech me Off kar diya | Woh chapter list se hat jata hai; uske chune sawaal bhi. Baaki chunav rehta hai. |
| Paper bana, shuru nahi hua, aur uska koi sawaal ab Live nahi | Paper shuru nahi hota: "Is paper ke kuch sawaal ab available nahi hain. Naya paper bana lo." |
| Paper chal raha hai aur chapter test Off hua | Paper poora hota hai; result milta hai. |
| Switch Off hua jab student sawaal chun raha tha | "Paper banana abhi band hai." Chunav browser me rehta hai. |
| Server jawab nahi de raha | "Sawaal abhi load nahi ho paaye. Dobara try karo." Aadhi list kabhi nahi dikhti. |

## UI/UX feel

- **App jaisa** (owner ka faisla): har screen ke upar gehra laal card (result page ke score card jaisa, halki chamak ke saath); Physics / Chemistry / Maths ke chamakte tab (laal, amber, teal); neeche ke card safed, icon laal.
- Tick ki hui row apne subject ka rang pehenti hai: halka rang, rangeen kinara, rangeen tick.
- Neeche tika hua bar: ginti, time, marks aur ek laal button. Jab kuch chuna na ho, button band aur ek line ki wajah.
- Screen par likhe shabd wahi jo app me hain (saral Hinglish: "Chapters chuno", "Sawaal chuno", "Paper banao", "Haan, paper banao", "Random mock banao").
- Sawaal ki picture halki aur tez; list neeche jate hue khud bharti hai.
- Phone (390 px) par ek column, tap ki jagah kam se kam 44 px, sideways scroll nahi. Desktop par wahi screens chaudi jagah me.
- Exam screen, result aur analysis me koi naya look nahi: woh aaj wale hi hain.
- Super Admin ka hissa maujooda Master jaisa hi dikhta hai.

## Phases

**Phase 1 (abhi banta hai): Student Choice poora**
- Teen darwaze, bana hua paper, Super Admin ka hissa, website ke pages: upar "Kya banega" ke A se G tak.

**Phase 2 (alag manzoori; kram owner ka diya hua, sab app ke saath mel me)**
1. **Chapter-wise test ka time ratio se:** sawaal × subject ka time (2.4 / 1.6 / 3.2), upar ke poore minute tak, zyada se zyada 3 ghante. 81 me se 7 test 3 ghante par rukte hain, 11 test 60 minute se chhote ho jate hain (sabse chhota 4 minute). Chal rahe attempt apna purana samay rakhte hain.
2. **"Meri details" phone aur website par ek:** website student ke account ke saath Rank ki details rakhti hai; app aur browser dono wahin se padhte aur likhte hain. Saath me **Class 11 / Class 12 ka nishaan** har chapter par, app ki list ke hisaab se. (App ke likhe poore niyam, memory/APP_REPLY_V5.md, abhi GitHub par nahi mile; app project me "Save to GitHub" ke baad padhe jayenge.)
3. **Poori AITS series ka leaderboard**, website ke series page par bhi. Series 9 Dec 2026 se shuru hai; app ne ise 9 Dec tak maanga hai.

**Phase 3 (alag manzoori)**
- Matched aur AI tagging: har sawaal ke 20 tag (har tag ka wajan 0 se 100), do gate (5 tag se concept ka mixture ek jaisa, aur 70% ya zyada mel), level ke 6 darje (25 tak Easy, 26–40 Easy to medium, 41–55 Medium, 56–72 Medium to hard, 73–83 Hard, 84 se upar Extremely hard), 2027 ke paper ka upload (yaad wala aur NTA wala). JEE Main ki pehli shift (January 2027) se pehle chahiye.
- Student Choice ke aage ke hisse: random mock me pehle naye sawaal; shuru na hue purane paper ko chhupana; Class 11 mock.
- App ki list ke baaki kaam: account delete ka darwaza, do test student, load test aur uske jawab, series me dost se din-ba-din tulna, PYQ pictures pehle se taiyaar.
- Storage ke baaki packet (E ka bacha hissa, F, G): plan/storage_plan.md.

## Assumptions (jo faisle bina pooche liye gaye)

1. Do hi switch hain ("Sawaal khud chuno", "Random mock"), dono Off se shuru. Website ka tile tabhi dikhta hai jab kam se kam ek On ho; dono Off par website aaj jaisi rehti hai. App apna tile hamesha dikhata hai (woh app ka apna hai).
2. Har chapter ke liye alag "Shamil" switch Phase 1 me nahi hai. Pool = saare Live JEE Main chapter-wise test. Wajah: app apni ginti aur seema usi chapter-wise list se nikalta hai; alag pool se app aur website ke number alag ho jate.
3. Bana hua paper 3 ghante par nahi kat-ta (75 Maths = 4 ghante). Owner ka pehle ka niyam "75, aur koi seema nahi" rakha gaya; app student ko yahi time pehle se dikhata hai.
4. Din ke 5 paper: chun kar aur random dono milakar; din India ke samay se (raat 12 baje se); ek hi maang dobara aaye to nahi ginti. 5 ek setting hai; owner badal sakta hai.
5. App student ko "aaj kitne bache" nahi dikha sakta (darwaza A sab ke liye ek hai). App me seema chhathe paper par line se pata chalti hai; website apni screen par "2 / 5" dikhati hai.
6. Random mock Phase 1 me saada random hai. "Pehle woh sawaal jo student ne pehle nahi dekhe" Phase 3 me.
7. Koi subject bina Live chapter test ke ho to random ka batwara bache subjects me barabar hota hai (app ka likha niyam).
8. Tick kiye chapters browser me us account ke liye rehte hain; tick kiye sawaal tab tak, jab tak page khula hai. Yeh phone ke saath saanjha nahi hote (app bhi inhe phone par hi rakhta hai). Bana hua paper dono jagah saanjha hai.
9. Sawaal ki list me naye look wale sawaal ka "sirf sawaal" wala tukda dikhta hai. Purane look wale sawaal: numerical ki poori picture; MCQ ke likhe shabdon me se sirf sawaal wala hissa. Jis sawaal ka na tukda ho na shabd, woh list me nahi aata.
10. Paper bana ho par shuru na hua ho, aur uska koi sawaal ab Live na ho: paper shuru nahi hota. Chalta hua paper poora hota hai; diya hua paper apna result rakhta hai.
11. Kuch delete nahi hota. Shuru na hue paper apni jagah rehte hain (unhe chhupana Phase 3 me).
12. Paper ke sawaal Start par jamte hain, jaise har paper me. Start ke baad chapter-wise sawaal me hua sudhaar chalte paper ko nahi badalta.
13. Paper history me in papers ka prakaar `choice` hai; inke galat sawaal Misfire ke "Sab" me aate hain.
14. Owner ko Super Admin me ginti dikhti hai, kisi student ka bana paper nahi.
15. Har subject ki seema (jaise 25) shuru me khaali hai.
16. Naya kaam kisi exam ke naam se bandha nahi hai; setting har exam ki apni hai. Abhi sirf JEE Main ki setting bhari jati hai; baaki exam ke liye darwaza A "nahi hai" kehta hai.
17. "Ek mock, ek storage" ka niyam Master ke mock ka hai. Bana hua paper alag-alag chapter test ki pictures leta hai; har chapter test apne aap me saabit hota hai.
18. Paanch hisse bina ruke ek ke baad ek bante hain; owner ko report aakhir me ek baar milti hai (owner: "kaam rukna nahi chahiye"). Deploy se pehle kaam rukta hai.
19. Deploy poora preview bhejta hai. Is baar saath jayega: N1 (naam, badi chapter list, Rank ke darwaze, Rapid Fire ka button), B1 (PYQ pictures ka sudhaar), N2 (Rank page app jaisa). N2 ke teen sudhaaron ki testing agent se dobara jaanch deploy se pehle hogi; abhi woh sirf screenshot se dekhe gaye hain.
20. Preview ka database builder nahi badalta. 26–27 Nov ke note ke hisaab se preview par koi chapter-wise test Live nahi hai (aaj dobara nahi dekha gaya); aisa hi ho to owner ko chalti screens ke screenshot alag test setup se milte hain. Preview par khud dekhna ho to owner wahan ek chapter-wise book Live kar sakta hai.
21. Pichhla manzoor storage plan plan/storage_plan.md me rakha gaya hai; uske baaki packet is plan se nahi badalte.
22. App ki 28 Nov ki list plan/app_list_2026-11-28.md me rakhi gayi, kyunki uska link 4 Dec ko band ho jata hai.
23. Owner ke aaj ke faisle (5 paper, Phase 2 ka kram, Matched ke niyam) memory ki files me banana shuru hote hi likhe jayenge; abhi sirf plan ka folder likha ja sakta hai.
