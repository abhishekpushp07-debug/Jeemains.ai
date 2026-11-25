# Storage machine ka baaki kaam: ek mock ek storage, atki file akeli ruke, Delete button, sachcha badge, picture ka saboot

Super Admin ki file-save machine poori ki jati hai: ek file ki galti usi file tak rehti hai, atka upload ek button se hatta hai, har mock poora ek hi storage me rehta hai (Supabase pehli pasand, Emergent fallback), badge sach batata hai, aur mock tabhi Live hota hai jab uski har picture saabit ho.
Students ka player, reader, cutter, scoring, login aur JEE Main PYQ nahi chhue jate. Live par kuch bhi tabhi jata hai jab owner "deploy" likhe.

## Owner ke sawaalon ke jawab

**1. "Book zero se aage nahi badh rahi thi": kya yahi hua tha?**

Haan. Live ke bucket ko sirf padh kar yeh saabit hua: "mathematics chapterwise" ke pate par wahi PDF (51,535,181 bytes, wahi fingerprint) 21 Nov se padi thi. Purana code tukdon ke saath "upar likhne ki ijazat" nahi bhejta tha, isliye Supabase pehla hi tukda har baar lautata raha (409).

Yeh sudhaar (Pocket 1) preview me bana aur jaancha hua hai. Live par abhi purana code hai.

**2. "File lautayi" ka matlab kya hai, aur kya koi sawaal Supabase tak pahunche bina reh sakta hai?**

"Lautayi" ka matlab: Supabase chal raha hai aur doosri files le raha hai, par isi ek file ko lene se mana kar raha hai. Yeh badi PDF ke saath bhi ho sakta hai aur kisi ek picture ke saath bhi.

| Kya ho sakta hai | Preview ke code me aaj | Is plan ke baad |
| --- | --- | --- |
| Supabase ek picture lautata hai | Woh mock Live nahi hota, "Atki hai" banta hai; baaki mock chalte hain | 5 minute baad ya button se poora mock Emergent me jata hai |
| Supabase der tak jawab hi nahi deta | Mock intezaar karta hai | Wahi fallback |
| Supabase "haan" kehta hai, par picture wahan nahi hai ya adhoori hai | Pakdi nahi jati | Live se pehle jaanch; kami ho to mock Live nahi hota |
| Picture ka record hai, par file storage se hat chuki hai | Pakdi nahi jati | Wahi jaanch pakadti hai; picture dobara save hoti hai |

**3. Live par "890 minute se Supabase jawab nahi de raha" kyun likha hai?**

- 25 Nov ke screenshot me usi samay Supabase ne 1.3 second me jawab diya. Supabase band nahi tha; laal line galat hai.
- Wajah live ka purana code hai. Atki hui 51 MB PDF ki har koshish par 409 aata hai, aur purana code ise "Supabase chala gaya" maan kar Supabase ko sabke liye 15 second se 5 minute tak aaram par daal deta hai. Isi se badge kabhi hara, kabhi laal hota hai aur baaki uploads bhi beech-beech me rukte hain. Ilaaj: Pocket 1 + 2 ka deploy.
- "Read back different bytes": jaanch har baar ek hi naam ki file likh kar turant padhti hai. Anumaan (saabit nahi): live ke do server ek hi file par likhte hain, aur Supabase upar likhi gayi file ki purani copy 60 second tak lauta sakta hai. Ilaaj: har jaanch naye naam ki file se (Pocket 3).

**4. Emergent ya Supabase: kaun behtar?**

| Baat | Supabase | Emergent |
| --- | --- | --- |
| File hatana | Hai | Nahi hai |
| Badi PDF | Tukdon me; ruk kar wahin se aage | Ek hi request; 100 MB kabhi jaanchi nahi gayi |
| Jagah | Pro plan me 100 GB, uske upar lagbhag $0.02 per GB har mahine | 250 GB (owner le chuka hai); bhar jaye to support ke badhane tak naya save band |
| Rok ka jokhim | Spend cap ON ho to usage paar hote hi | Quota bharne par |
| Live par purani galti | 0% wala atkaav hamare code ki galti thi | 21 Nov ko save par HTTP 500 aaya aur kitaabein fail hui; 22 Nov ki report me 24 ghante me 0 baar. Jad se theek hui ya nahi, pata nahi |

Speed ke do naap hain aur dono ulte hain (nanhi file likhna + padhna):
- Live, 25 Nov, ek reading: Supabase 1.3 second, Emergent 6.0 second.
- Preview, 21 Nov: Supabase 1.6 se 2.1 second, Emergent 0.15 second.

Isliye "kaun tez" abhi tay nahi hai. Pocket 3 dono ki aakhri 20 reading dikhayega; faisla un number se hoga.

Faisla (owner ka): Supabase pehli pasand rahe. Emergent fallback bane, is niyam ke saath ki ek mock poora ek hi storage me rahe.

**5. Picture chhoti karne ke do raaste: bane hain ya nahi?**

Dono bane hain. Raasta 2 live par chal raha hai. Raasta 1 23 Nov ke deploy ke saath gaya hoga (deploy poora preview bhejta hai), par live par woh sach me chal raha hai ya nahi, yeh naapa nahi gaya.

Picture ka safar:
1. Upload me sirf PDF storage me jati hai. Us samay koi picture nahi banti.
2. Mock Live hone lagta hai tab machine PDF se har sawaal aur option ki picture kaat-ti hai.
3. Raasta 1: save se theek pehle picture chhoti ki jati hai.
4. Chhoti picture storage me save hoti hai. Supabase ho ya Emergent, wahi bytes jate hain.
5. Student paper kholta hai: server storage se picture leta hai aur raasta 2 se bhejta hai.

| | Raasta 1 (website ka) | Raasta 2 (app ka sujhaav) |
| --- | --- | --- |
| Kya karta hai | Save se pehle picture ko bina ek pixel badle chhota karta hai | Kam call, dobara download nahi, halki copy |
| Kitna | Poore page jaisi picture lagbhag 14% chhoti, chhote option tukde 38 se 48%, mila-jula 13 se 22% | 12 picture ek call me (ek paper: 197 ki jagah lagbhag 17 call); phone "badli hai kya?" pooch kar wahi picture dobara nahi utarta; maangne par WebP copy, pixel wahi: website ke namoonon par 51 se 63% kam bytes, app ke apne 12 namoonon par 37% kam |
| Haalat | 23 Nov ke deploy me gaya hoga; live par naapa nahi gaya. Na chale to picture apne asli size me save hoti hai, kharab nahi hoti | 23 Nov se live, har student ke liye |
| Seema | Sirf nayi save hone wali picture par. JEE Main PYQ ki pictures shayad har maang par PDF se banti hain, to un par yeh nahi lagta | Halki copy aur bundle pehli maang par bante hain aur server ki yaad me rehte hain; restart par dobara bante hain |

- App in naye raaston ko kitna istemaal kar raha hai, yeh app team batayegi.
- "200%" do alag baatein hain. App ne halki picture ko 200% zoom par aankh se dekha tha: woh jaanchne ka tareeka tha, koi setting nahi. Aur picture pehle se PDF ke 2 guna (200%) size par banti hai.
- Jo abhi nahi bana: WebP quality 90 (lagbhag 8 guna kam bytes, par pixel thode badalte hain; diagram, graph aur chemistry structure ki aankh se jaanch baaki hai); halki copy aur bundle ko file ki tarah rakhna; alag CDN. Yeh sab Phase 2 me hai.

## Kiske liye

- **Owner (Super Admin):** PDF upload karta hai aur mock Live karta hai. Use sach chahiye: file gayi ya nahi, kahan gayi, kyun ruki, ab kya karna hai.
- **Students:** Super Admin nahi dekhte, par wahi paper pate hain jo yahan se nikalta hai. Adhoori pictures wala paper un tak nahi pahunchna chahiye, aur paper jaldi khulna chahiye.
- **App team:** unke liye kuch nahi badalta. Server ke jawab me sirf naye khaane judte hain; picture ke bytes wahi rehte hain.

## Aaj ki haalat

| Hissa | Haalat |
| --- | --- |
| Live par chal raha code | Pocket 1 se pehle ka. 0% wala atkaav aur galat laal line wahin hai. |
| Pocket 0: asli wajah ka saboot | Poora |
| Pocket 1: badi file ka raasta | Bana aur jaancha hua (testing agent sahit). Sirf preview me. |
| Pocket 2: ek file ki galti us file tak, "Atki hai", 15 minute ki chetavni row ke andar | Bana hua. Builder ki apni jaanch paas: 19 suite me 883 jaanch, browser 32/32, asli Supabase par test file se 8/8. Testing agent ki alag jaanch baaki. Sirf preview me. |
| Packet A: Pocket 1 + 2 ki alag jaanch (25 Nov) | Poora: testing agent (iteration_224) aur alag code review paas. Upar ki line ka "Testing agent ki alag jaanch baaki" ab purana hai. Sirf preview me. |
| Packet B: latke kadam ki rok | Bana aur jaancha hua (testing agent iteration_225 + alag code review). Sirf preview me. |
| Packet C: Delete button | Bana aur jaancha hua (testing agent iteration_225 + alag code review). Sirf preview me. |
| Packet D: Pocket 3, sachcha badge | Bana aur jaancha hua (testing agent iteration_226 + alag code review 25 Nov: koi blocker nahi; ek medium aur teen low baaki, test_reports/code_review_packet_D.md). Sirf preview me. |
| Packet E (picture ka saboot) | Adhoora, sirf preview me, deploy nahi hua. Bana aur jaancha hua (25 Nov): saboot ka function, aur PDF se bane mock ke Live/Scheduled par rok (na mile to ek baar dobara save, phir bhi nahi to Draft + "Atki hai" + wajah + Dobara chalao), row par "Pictures: n / n · Storage". Der se na khulna bhi bana aur jaancha hua (25 Nov shaam): chuna hua samay nikal jaye to mock Draft rehta hai aur row batati hai. Likha hua mock bhi bana aur jaancha hua (25 Nov raat): photo saabit na ho to sirf wahi mock Draft rehta hai aur sawaal ka number batata hai; uske liye row par tiki wajah, "Dobara chalao" aur "Pictures: n / n" line abhi nahi hai. Abhi nahi bana: Off se Live, Library se wapas, purani Emergent pictures ki copy, "Pictures ki poori jaanch" button. Poora haal: memory/NIGHT_REPORT.md |
| Packet F, G (fallback, Supabase me lana) | Shuru nahi. |
| Deploy | 25 Nov ko owner ne deploy kiya: Packet A se D ab live par hain. Live ko sirf padh kar dekha gaya: atki PDF aage badh gayi (27 me se 26 mock ready), storage ki galtiyon ki list khali, koi crash nahi. Upar ki lines ka "Sirf preview me" aur "Live par ... purana code" ab purana hai. Poora haal: memory/NIGHT_REPORT.md |

Pocket 2 ki jaanch ki seema:
- 15 minute sach me ruk kar nahi, ghadi aage badha kar jaanche gaye.
- Asli Supabase ko "yeh file lautao" nahi kaha ja sakta. Us jaanch me ek test file ke liye 409/400 ka jawab jaanch ne khud diya; baaki sab asli Supabase tak gaya.
- Browser ki jaanch nakli Supabase par hui.

Ek khuli baat: preview me ek baar "Live ho raha hai" wala kadam 10 minute latka raha (picture ginti 0/21), database ke restart ke 50 second baad. Uske baad wahi jaanch 175 se zyada baar chali aur har baar paas hui. Wajah nahi mili. Neeche B iske asar ko sambhalta hai, wajah ko nahi.

## Kya banega

### A. Pocket 1 + 2 ko live karna (pehla deploy)

1. Testing agent ki alag jaanch (server aur screen dono). Jo mile woh theek hota hai, phir dobara jaanch.
2. Badle hue code ka alag code review.
3. Owner ko list milti hai: pichhle deploy ke baad preview me kya-kya badla. Deploy poore preview ko live karta hai, sirf storage ko nahi.
4. Owner "deploy" likhta hai, tabhi deploy hota hai.
5. Deploy ke baad live ko sirf padh kar report: atki PDF aage badhi ya nahi, galat laal line gayi ya nahi.

Atki PDF ki isi haalat ki nakal preview me jaanchi gayi hai aur wahan woh aage badhi. Live par yeh deploy ke baad hi pakka hoga.

### B. Latke hue kadam ki rok

- Aaj agar PDF ka koi kadam bina galti diye latak jaye, to us server par PDF ka saara kaam server ke restart tak ruka rehta hai.
- Naya niyam: kisi kadam me 10 minute tak koi harkat na ho (na page badhe, na tukda, na picture), to machine use chhod kar save hui jagah se dobara shuru karti hai.
- Chhodne se pehle machine likh leti hai ki kadam kahan latka tha, taaki agli baar wajah pakdi ja sake.
- Lagataar 3 baar latke to row "Atki hai" kehti hai, wajah ke saath.
- Machine panel me ek line: "Latke kadam (24 ghante): N".
- Yeh rok sirf PDF wali line par lagti hai. Grading, score aur report ki line nahi chhedi jati.

### C. Delete button

**Kahan dikhta hai**
- Master › mock type › "Uploads" ki har row par: 0% par atki, "Atki hai", fail, ruki hui, adhoori bheji hui, ya padhi ja rahi PDF.
- Draft mock ki row ke Status menu me "Is PDF ko delete karo…": un PDF ke liye jo padhi ja chuki hain aur Uploads me nahi dikhti.
- Sirf tab, jab us upload se students ke liye kabhi koi test nahi bana (na Live, na Scheduled, na Off, na Library).
- Jis upload ka ek bhi mock students tak pahunch chuka hai, us par yeh button nahi hota. Uske Draft mock pehle ki tarah Library me bheje ja sakte hain.

**Dabane par**
- Ek box khulta hai jo ginti ke saath batata hai ki kya hatega: kitne Draft mock, unme se kitno me owner ke fix hain, kitne page, storage me kitni files.
- Owner box me DELETE likhta hai. Tabhi "Hamesha ke liye delete karo" button chalta hai.

**Kya hatta hai**

| Cheez | Hatti hai? |
| --- | --- |
| Upload ka record (naam, padhe hue page, page ke nishaan) | Haan |
| Server par pade PDF ke hisse | Haan |
| Us upload ke saare Draft mock aur unke fix | Haan |
| "Try as student" ki private copy | Haan |
| Supabase me us upload ki original PDF aur uski saari pictures | Haan |
| Us upload ke ruke hue kaam | Haan |
| Emergent me padi us upload ki files | Record hatta hai; file wahan rehti hai (Emergent me hatana hota hi nahi) |
| Koi doosra upload, koi bana hua test, kisi student ka score, JEE Main PYQ | Nahi |

**Kaise chalta hai**
1. Row turant list se hat jati hai. Us PDF par chal raha kaam apne agle kadam par ruk jata hai.
2. Safai peeche chalti hai. Pehle Supabase: us upload ke apne folder ki list li jati hai, wahi naam hataye jate hain, phir dobara list dekh kar pakka kiya jata hai ki folder khali hai. Uske baad database ke record; sabse aakhir me upload ka record.
3. Beech me server band ho ya Supabase jawab na de, to safai adhoori nahi chhooti: har 15 minute wali jaanch use wahin se poora karti hai. Tab tak Machine panel me "Delete ki safai baaki: N" dikhta hai.
4. Wahi PDF turant dobara upload ki ja sakti hai, safai chal rahi ho tab bhi. Woh bilkul naye sire se padhi jati hai.

**Suraksha**
- Sirf owner yeh kar sakta hai.
- Supabase se file hatane ki taaqat code me gini-chuni jagah ke liye hai: is upload ka apna folder, storage test ki file (D), aur fallback me us mock ki adhoori pictures (F). Kisi aur pate par hatane ki koshish code khud rok deta hai.
- Database me sirf isi upload ke record hatte hain; poora collection kabhi nahi.
- Kisne, kab, kya hataya: ek line record me rehti hai.
- Agar yeh upload kisi purane mock ko replace karne wala tha, woh nishaan hat jata hai; purana mock jaisa tha waisa rehta hai. AITS me jis Draft ko din diya gaya tha, woh din khali ho jata hai.

### D. Pocket 3: sach bolne wala badge

1. Storage ki haalat database me rakhi jati hai, har server ki apni yaad me nahi. Dono server ek hi baat dikhate hain.
2. Badge me teen line: "Supabase · Pictures (chhoti file)", "Supabase · PDF (badi file)", "Emergent (fallback)". Har line ke saath: kab aur kaise jaanchi gayi, aur kitna samay laga.
3. Rang:
   - Hara: Supabase ke dono raaste theek, koi file atki nahi, koi file 10 minute se ruki nahi.
   - Peela: Supabase dheema hai, ya koi file "Atki hai", ya koi file 10 minute se ruki hai, ya badi file ka raasta pichhli baar fail hua, ya Emergent (fallback) jawab nahi de raha.
   - Laal: Supabase jawab nahi de raha, ya project par rok hai (billing, paused, galat key).
4. Supabase ki har jaanch naye naam ki test file se hoti hai: likhi jati hai, wapas padh kar milayi jati hai, phir hata di jati hai. Isse "Read back different bytes" wali galat chetavni nahi aati. Emergent me hatana nahi hota, isliye wahan jaanch ek hi naam ki file par rehti hai.
5. "Badi file ka test" button: lagbhag 7 MB ki test file asli tukdon wale raaste se jati hai, wapas padhi jati hai, phir hata di jati hai. Samay ya wajah dikhti hai.
6. Yahi test apne aap bhi chalta hai: jab badi file ka raasta kabhi jaancha na gaya ho, jab koi PDF us raaste par ruki ho, aur 24 ghante me ek baar. Har asli PDF ka save hona bhi is raaste ka saboot gina jata hai.
7. Machine panel me aakhri 20 storage galtiyon ki list: kab, kaun si file, kaun sa storage, kaun sa raasta, kya wajah.
8. Dono storage ki aakhri 20 reading ki speed, taaki "kaun tez" asli number se dikhe.
9. Kisi bhi server ki safal jaanch ke baad ruka hua kaam dono server par ek minute ke andar jagta hai.

### E. Pocket 4: picture ka saboot

**Niyam:** koi paper students ko tabhi dikhta hai (Live ya Scheduled) jab usme lagi har picture ek hi storage me maujood saabit ho.

**Jaanch kya dekhti hai**
- Paper ki har picture usi ek storage me hai.
- Supabase wala paper: har picture Supabase ki list me hai, aur nayi save hui picture ka size wahi hai jo save karte samay tha.
- Emergent wala paper: har picture wapas padh kar fingerprint se milayi jati hai.
- Jo picture na mile, woh ek baar dobara save hoti hai, phir jaanch dobara hoti hai.

**Kahan lagti hai**
- PDF se bana Draft mock jab Live ya Scheduled hota hai (AITS ke din wala paper bhi).
- Likha hua (Write) mock jab Live ya Scheduled hota hai.
- Koi Off test jab dobara Live ya Scheduled kiya jata hai.
- Library se wapas aane wala test: pictures saabit hone tak Off rehta hai, phir apni purani haalat me lautta hai.
- Scheduled mock ki jaanch schedule karte samay hi hoti hai, khulne ke samay nahi.

**Jaanch fail ho to**
- Mock Live nahi hota. Row wajah batati hai ("3 pictures storage me nahi mili"), saath me "Dobara chalao".
- Har 15 minute me apne aap phir koshish hoti hai. Baaki mock aur kitaabein chalti rehti hain.

**Purani Emergent pictures (Supabase lagne se pehle ki)**
- Jis mock ki kuch pictures purani hain aur Emergent me hain, use Live dabane par machine pehle woh pictures Supabase me copy karti hai. Har copy wapas padh kar fingerprint se milayi jati hai. Poori copy mil jaye tabhi switch hota hai.
- Us dauran row dikhati hai: "Pictures Supabase me copy ho rahi hain · 120 / 312". Copy aur jaanch poori hote hi mock apne aap Live (ya chune hue samay par Scheduled) ho jata hai.
- Chuna hua samay tab tak nikal chuka ho, to mock Live nahi hota aur row batati hai. Der se apne aap nahi khulta.

**Row par**
- Jaanch se guzre mock par ek line: "Pictures: 312 / 312 · Storage: Supabase" (ya Emergent).
- "Pictures ki poori jaanch" (owner): us paper ki har picture storage se padhi jati hai aur fingerprint se milayi jati hai. Peeche chalti hai; row ginti dikhati hai, phir nateeja.
- Phase 1 me poori jaanch sirf batati hai. Kisi Live mock ko machine khud Off nahi karti.

**JEE Main PYQ**
- Verified JEE Main PYQ par yeh jaanch, copy aur "poori jaanch" button nahi lagte. Unka Live/Off pehle jaisa chalta hai.

### F. Fallback: ek mock, ek storage

**Sunehra niyam:** ek mock ki har picture ek hi storage me hoti hai: ya poori Supabase me, ya poori Emergent me. Aadhi-aadhi kabhi nahi. Mock students ko tabhi dikhta hai jab yeh saabit ho (E).

**Kaise chalta hai**
1. Mock Live hone lage to machine pehle Supabase me save karti hai, aaj jaisa.
2. Fallback do tarah se shuru hota hai:
   - **Apne aap:** mock 5 minute se Supabase me nahi ja pa raha (Supabase jawab nahi de raha, project par rok hai, ya uski koi picture do baar lautayi gayi).
   - **Button se:** row par "Abhi Emergent me save karo". 5 minute ka intezaar nahi. Dabane par ek chhota box poochta hai, phir kaam shuru hota hai.
3. Fallback shuru hote hi:
   - Us mock ka Supabase wala save ruk jata hai.
   - Is koshish me us mock ki jo pictures Supabase me ja chuki thin, woh wahan se hata di jati hain. Jo picture kisi aur paper me lagi hai, woh nahi hatti.
   - Poora mock shuru se Emergent me save hota hai. Har picture wapas padh kar fingerprint se milayi jati hai.
   - Sab mil jaye tabhi mock Live (ya Scheduled) hota hai.
4. Emergent bhi na le: mock Draft rehta hai aur row kehti hai "Atki hai: dono storage ne nahi liya", wajah ke saath. 15 minute baad phir koshish hoti hai, pehle Supabase se.
5. Emergent me save shuru ho jaye to woh mock Emergent me hi poora hota hai, chahe Supabase beech me laut aaye. Beech raaste storage nahi badalta.

**Niyam kaise nahi toot-ta**
- Emergent wali picture ka apna alag record hota hai. Emergent wala mock sirf unhi record se juda hota hai, isliye kisi doosre paper ki picture apni jagah se nahi hilti.
- Live se theek pehle saboot ki jaanch (E) dekhti hai ki mock ki har picture ek hi storage me hai. Na ho to mock Live nahi hota.
- Supabase band hone se safai us samay na ho paye, to woh files "safai baaki" list me jati hain aur Supabase lautte hi hatti hain. Mock unse juda nahi hota.
- Mock ka har naya version (correction) apna faisla naye sire se karta hai: pehle Supabase. Purana version jahan tha wahin rehta hai.

**Original PDF**
- PDF ek hi file hai; jis storage me gayi, poori wahin rehti hai. Students ke paper ko PDF nahi chahiye, sirf pictures.
- PDF ka fallback bhi unhi do tarah se chalta hai (5 minute ya button). Button par Supabase ka adhoora upload band karke hata diya jata hai.
- Banane se pehle preview me jaanch: Emergent 50 aur 100 MB ki PDF ek request me leta hai ya nahi. Jis size tak le, usi tak PDF ka fallback; usse badi PDF Supabase ka intezaar karti hai. Is jaanch ki lagbhag 160 MB test files Emergent se hat nahi sakti aur 250 GB me ginti rahengi.

**Kis par lagta hai**
- PDF se bane mock (AITS ke din wala paper bhi) aur original PDF.
- Write mock ki pictures aur purani Studio screens par nahi: woh pehle ki tarah sirf Supabase me jati hain (band ho to intezaar), isliye hamesha ek hi storage me rehti hain.
- JEE Main PYQ par nahi.

**Seemayein**
- Mock ki pictures PDF se banti hain. PDF Supabase me ho, Supabase band ho aur server par us PDF ki copy na bachi ho, to fallback bhi intezaar karta hai.
- Emergent me file hatayi nahi ja sakti. Fallback ki adhoori ya bekaar files wahan rehti hain aur 250 GB me ginti hain; kisi paper se judi nahi hoti.
- Live par Emergent 21 Nov ko khud fail hua tha. Isliye fallback har picture ko wapas padh kar hi maanta hai.
- Paper jis storage me hai, exam ke din uski pictures usi par nirbhar hain. Is jokhim ke liye Phase 2 ki dhaal hai.

### G. Emergent wale mock ko Supabase me lana

- Row par "Supabase me lao" (owner). Peeche chalta hai; row ginti dikhati hai.
- Machine us mock ki har picture Supabase me copy karti hai aur wapas padh kar fingerprint se milati hai. Sab mil jayein tabhi poora mock Supabase par switch hota hai. Ek bhi na mile to mock Emergent par hi rehta hai.
- Switch ke samay mock dono storage me poora maujood hota hai.
- Bytes wahi rehte hain, isliye phone kuch dobara download nahi karta.
- Emergent wali copy rehti hai (hat nahi sakti).
- Jis paper ka live exam chal raha ho, us par yeh button us dauran band rehta hai.
- Yeh apne aap nahi chalta; sirf owner ke button se.
- Badge ki "Purani files › Copy" machine fallback wale mock ki pictures ko nahi chhuti.

### H. Kya nahi chhua jata

- PDF reader, cutter, chapter split, answer key, Fix tool.
- Students ka player, results, analysis, AITS hub, Rank, Mission, CEO dashboard, contacts.
- Students ko picture bhejne ka raasta aur picture chhoti karne ke dono raaste (Phase 2 tak waise hi).
- Login, PIN, scoring, rank.
- JEE Main PYQ.
- LiveSeries.js (uski warning bhi nahi).
- Library ka purana "delete": jaisa hai waisa.
- App ke liye server ke jawab: sirf naye khaane judte hain.

### I. Kaam ke niyam

1. Har packet ke baad kaam rukta hai aur owner ko chhoti report milti hai: kya bana, kya jaancha gaya, kya jaancha nahi ja saka. Agla packet owner ki haan par.
2. Deploy sirf tab, jab owner "deploy" likhe.
3. Har deploy se pehle teen cheezein: testing agent ki jaanch paas, badle hue code ka alag code review, aur owner ko list ki pichhle deploy ke baad kya-kya badla.
4. Koi email, SMS ya bahar ka alert nahi. 15 minute wali chetavni sirf Super Admin ki upload row ke andar.
5. Ek file ki galti se poori line kabhi nahi rukti.
6. Ek mock, ek storage: yeh niyam kisi bhi packet me nahi tod-a jata.
7. Har packet me pehle jaanch likhi jati hai, phir code. Uske baad purani saari jaanch dobara chalti hai, ek samay me ek hi suite.
8. Asli Supabase par builder ki jaanch sirf preview ke bucket me, "TEST_" naam ki files se, jo baad me hata di jati hain. Live ke bucket me builder kuch nahi likhta; live par builder sirf padhta hai.
9. Jo cheez jaanchi na ja sake, woh "jaanchi nahi gayi" likhi jati hai, "ho gaya" nahi.
10. Jawab saral Roman Hinglish me.

### J. Owner ke kaam (yeh builder nahi kar sakta)

1. **Deploy tak savdhani:** jo PDF pehle upload hui thi aur Library se hamesha ke liye delete hui, use (6 MB se badi ho to) live par dobara upload na karein. Woh bhi 0% par atkegi.
2. **Supabase › Billing › Spend cap:** ON ho to included usage paar hote hi Supabase project par rok laga deta hai. 9 Dec se pehle ek faisla: OFF (zyada usage ka bill aata hai, rok nahi lagti) ya ON (bill tay, rok ka jokhim).
3. Supabase ke email jis inbox me aate hain, woh roz dekha jata ho.
4. Live par atki "mathematics chapterwise" ko abhi na chhedein. Deploy ke baad woh apne save hue hisson se aage badhti hai; na badhe to naye Delete button se hata kar dobara upload ki ja sakti hai.
5. Badge ka "Purani files Emergent mein: 164 › Supabase mein copy karo" button abhi na dabayein. Yeh 164 files shayad JEE Main PYQ ki hain (ginti preview ke PYQ se milti hai; pakka nahi), aur PYQ ko chhedna nahi hai.
6. Ho sake to Emergent support se poochh lein: 21 Nov ko live par storage ka HTTP 500 jad se theek hua ya nahi. Fallback usi storage par tikega.

### K. Poora kab maana jayega

- Ek file jaan-boojh kar fail karayi jaye, tab bhi doosri kitaab bina ruke Live hoti hai.
- Latka hua kadam 10 minute baad khud chhoot kar dobara chalta hai, aur us server par agli PDF bhi chalti hai.
- Atka upload DELETE likh kar hatane ke baad: Supabase me uska folder khali, database me uska koi record nahi, aur wahi PDF dobara upload hokar naye sire se padhi jati hai.
- Jis upload ka koi mock students tak pahunch chuka hai, us par Delete button nahi dikhta aur server bhi mana karta hai.
- Koi file 10 minute se ruki ho to badge hara nahi dikhta; dono server ek hi haalat dikhate hain; Supabase theek ho to "jawab nahi de raha" kabhi nahi likha aata.
- Jis mock ki ek picture storage se gayab ho, woh Live nahi hota.
- Supabase band karke Live dabaya jaye: 5 minute baad (ya button par turant) poora mock Emergent me jata hai aur Live hota hai; Supabase me us mock ki koi adhoori picture nahi bachti.
- Kisi bhi jaanch me aisa Live mock nahi milta jiski pictures do storage me bati hon. Button beech me dabane, server band hone aur dono storage ke fail hone par bhi nahi.
- "Supabase me lao" ke baad mock poora Supabase me hota hai aur har picture ke bytes wahi rehte hain.
- JEE Main PYQ me koi badlav nahi.
- Upload › Draft › Fix › Live ka purana raasta pehle jaisa chalta hai.

## User flow

**Is kaam ke dauran (owner)**
1. Plan manzoor karta hai.
2. Pehle Pocket 1 + 2 ki jaanch aur code review hota hai; owner ko badlavon ki list milti hai; owner "deploy" likhta hai.
3. Baaki packet ek-ek karke preview me bante hain. Har packet ke baad report milti hai aur kaam rukta hai.
4. Har deploy ke baad live ka nateeja ek baar sirf padh kar bataya jata hai.

**Roz ka upload**
1. Upload PDF › "Server par pahunchi X%".
2. "Original Supabase mein X%".
3. "Padhi ja rahi hai · X / Y page" › Draft.
4. Live dabane par: pictures bani › chhoti hui › save › jaanch › "Pictures: N / N · Storage: Supabase" › Live.

**Jab Supabase na le**
1. Row: "Supabase ka intezaar · 3 min · 5 min par apne aap Emergent me jayega", saath me "Abhi Emergent me save karo".
2. 5 minute poore hon ya button dabe: "Emergent me save ho raha hai · 120 / 312".
3. Jaanch paas: "Pictures: 312 / 312 · Storage: Emergent" › Live.
4. Baad me, jab chahein: "Supabase me lao".

**Jab dono na lein**
- Row "Atki hai: dono storage ne nahi liya" kehti hai, wajah, "Dobara chalao" aur "Delete" ke saath. Baaki kitaabein chalti rehti hain. 15 minute ho jayein to usi row ke andar chetavni ki line aa jati hai.

**Atka upload hatana aur dobara bhejna**
1. Uploads ki row par "Delete" dabata hai.
2. Box me dekhta hai ki kya-kya hatega, DELETE likhta hai, button dabata hai.
3. Row hat jati hai.
4. Upload PDF se wahi PDF dobara chunta hai. Woh naye sire se chalti hai.

## UI/UX feel

- Koi nayi screen nahi. Wahi badge, wahi panel, wahi upload row, wahi mock row.
- Delete laal rang ka, baaki button se alag; bina DELETE likhe nahi chalta. Box me pehle "kya hatega", phir "kya nahi hatega".
- "Abhi Emergent me save karo" ek chhote box ke baad chalta hai, jo ek line me batata hai ki mock poora Emergent me jayega aur Supabase ki adhoori pictures hatengi.
- Har Live mock par saaf likha hota hai ki woh kis storage me hai.
- Badge ke rang: hara, peela, laal; har rang ke saath ek line ki wajah.
- Wajah ki line chhoti aur saral Roman Hinglish me; storage ka code bracket me.
- "Apne aap aage chalega" sirf tab likha aata hai jab woh sach ho.
- Phone (390 px) par row ki line aur button ek ke neeche ek; tap ki jagah kam se kam 44 px.
- Maujooda JEELIVE look; koi naya style nahi. Jame hue shabd (Master, Draft, Live, Library, Upload PDF) wahi rehte hain.

## Phases

**Phase 1 (abhi banta hai): storage machine poori**

| Kram | Packet | Uske baad |
| --- | --- | --- |
| 1 | A: Pocket 1 + 2 ki jaanch aur code review | **Deploy 1** (owner ke "deploy" par) |
| 2 | B: latke kadam ki rok | Ruk kar report |
| 3 | C: Delete button | Ruk kar report. **Deploy 2** |
| 4 | D: Pocket 3, sachcha badge | Ruk kar report |
| 5 | E: Pocket 4, picture ka saboot | Ruk kar report. **Deploy 3** |
| 6 | F: fallback, ek mock ek storage | Ruk kar report |
| 7 | G: Emergent wale mock ko Supabase me lana | Ruk kar report. **Deploy 4** |

- Deploy 1 sabse pehle isliye hai ki live par ek PDF abhi baaki kaam ko rok rahi hai aur uska sudhaar taiyaar hai.
- Fallback aakhir me isliye hai ki woh Live karne wale raaste ko sabse zyada chhoota hai. Us se pehle Delete (safai ki taaqat), badge (dono storage ki asli reading) aur saboot (niyam ki jaanch) ban chuke honge, aur fallback inhi teeno par tikta hai.

**Phase 2 (alag manzoori): paper turant khule, exam ke din ki dhaal, cut ki jaanch**
- Paper Live hote hi uske picture-bundle (12-12 ke; PNG aur halki WebP dono) ek baar bante hain aur file ki tarah rakhe jate hain, server ki disk par bhi. Pehla student bhi intezaar nahi karta, aur server restart par dobara banana nahi padta.
- Storage ki chhoti rukavat un students tak nahi pahunchti jinka paper server par aa chuka hai. Storage chup ho to picture ki request kuch second me saaf jawab deti hai, latakti nahi.
- Tay samay wale exam aur AITS ke din se pehle har server par us paper ki saari pictures taiyaar; Super Admin me ek line: "Aaj ka paper: pictures 100% taiyaar".
- WebP quality 90 (lagbhag 8 guna kam bytes): pehle owner ke liye ek jaanch screen, jahan diagram, graph aur chemistry structure ki asli aur halki picture saath-saath 200% zoom par dikhti hain. Owner ki haan ke baad hi app ke liye chalu.
- Jaanch ki asli bundle link jeelive.ai ke aage wale cache (Cloudflare) par rukti hain ya nahi; na rukti hon to owner ko bataya jata hai ki kya set karna hai.
- AITS paper ko din dete hi uski poori jaanch apne aap; bane hue paper ki gayab picture ke liye "Dobara save karo".
- Cut report: har mock ke har sawaal aur option ki chhoti picture ek hi screen par, shak wale sabse upar. Shak wala sawaal bina dekhe Live nahi hota.

**Phase 3 (alag manzoori): machine ki speed, aur kada compression, bada paimana**
- Speed: pehle har kadam ka samay naapa aur Super Admin me dikhaya jata hai (padhai, cut, pictures ka save). Phir sabse lamba intezaar hataya jata hai.
- Compression: bina pixel badle aur kade tareeke kitna aur bachate hain aur kitna samay lete hain, pehle naap; faisla us report ke baad.
- Pictures ke aage alag CDN, taaki 1 lakh students ka pehla load server aur storage par na pade.
- Supabase me padi bekaar files ki safai (pehle list, phir owner ki haan), aur purani Emergent files ko poori tarah Supabase me lana.

## Assumptions (jo faisle bina pooche liye gaye)

1. Owner ne kaha "technical faisle tum lo". Is file ke saare technical faisle usi bharose par liye gaye hain.
2. "Republish code review" ka matlab: har deploy se pehle badle hue code ka alag code review.
3. Char deploy ke mauke rakhe gaye, taaki har baar live par chhota badlav jaye. Charon owner ke "deploy" likhne par hi.
4. Fallback Phase 1 ke aakhir me rakha gaya (wajah Phases me).
5. Apne aap fallback ki had 5 minute; "picture do baar lautayi gayi" bhi isi 5 minute ke andar gina jata hai.
6. Fallback sirf PDF se bane mock aur original PDF par. Write mock aur purani Studio screens sirf Supabase par rehte hain.
7. Emergent me save shuru hone ke baad us mock ka storage beech me nahi badalta, Supabase laut aaye tab bhi.
8. Emergent wala mock Supabase me apne aap nahi lautta; sirf owner ke button se, aur live exam ke dauran nahi.
9. Mock ka purana version (jo students de chuke hain) jahan tha wahin rehta hai; niyam har version par alag lagta hai.
10. "PYQ ko touch nahi karna" ka matlab: verified JEE Main PYQ par saboot ki jaanch, copy, fallback aur "poori jaanch" button, koi nahi lagta.
11. JEE Main PYQ ki pictures shayad aaj bhi har maang par PDF se banti hain (app ka naap: ek picture lagbhag 561 KB; pakka nahi kiya gaya). Un par raasta 2 lagta hai, raasta 1 nahi. Wahan speed ka bada faayda ho sakta hai, par owner ke niyam ki wajah se PYQ ke liye is plan me kuch nahi hai.
12. Delete button fully padhi hui PDF ke liye bhi diya gaya (Draft mock ke menu se), kyunki aaj wahi PDF usi type me dobara upload karne par naye sire se nahi padhi jati.
13. "Students tak kabhi nahi pahuncha" ki pehchaan: us upload se kabhi koi test bana hi nahi. Ek bhi bana ho to poora upload Delete nahi hota.
14. Delete turant row hatata hai aur safai peeche chalti hai.
15. Purane tareeke ki "chapter book" rows par Delete nahi; un par "Library mein bhejo" pehle jaisa rehta hai.
16. Library ka purana delete Supabase ki files nahi hatata; yeh waisa hi chhoda gaya. Uski safai Phase 3 me hai.
17. Latke kadam ki had 10 minute, sirf PDF wali line par; 3 baar lagataar par "Atki hai".
18. Saboot ki jaanch har us raaste par lagti hai jisse paper students ko dikhne lagta hai, Off se Live aur Library se wapsi bhi.
19. Supabase wale paper ki Live se pehle ki jaanch maujoodgi aur size dekhti hai; har picture ko padh kar fingerprint milana "poori jaanch" button par hai, kyunki woh Live hone ka samay lagbhag doguna kar deta hai. Emergent wale paper me padh kar milana hi ek raasta hai.
20. Pehle se Live mock ki apne aap (raat wali) jaanch nahi banti, kyunki owner ke mutabik abhi sirf JEE Main PYQ Live hai.
21. Phase 1 me bane hue Live paper ki gayab picture ko dobara save karne ka button nahi hai; woh Phase 2 me hai.
22. Badge ki hadein: 10 minute ke baad hara nahi; test file lagbhag 7 MB; badi file ka test 24 ghante me ek baar; galtiyon aur reading ki list 20-20 ki.
23. Emergent (fallback) ka jawab na dena badge ko peela karta hai, laal nahi, kyunki naya kaam Supabase se chal raha hota hai.
24. Storage test ki apni file live ke bucket me ek tay folder me jati hai aur turant hata di jati hai. Yeh feature ka hissa hai; builder ki jaanch live ke bucket me kuch nahi likhti.
25. Asli Supabase rukavat par "aaram" ke samay (15 second se 5 minute) wahi rehte hain.
26. Storage ki haalat CEO dashboard ke alerts me nahi jodi gayi, kyunki owner ne chetavni sirf upload row me maangi hai.
27. Phase 2 me students ki speed, dhaal aur cut ki jaanch; Phase 3 me machine ki speed aur compression. Kram is baat se tay hua ki kya exam ke beech student tak pahunchta hai.
28. WebP quality 90 owner ki aankh se jaanch ke bina kabhi chalu nahi hoga, kyunki usme pixel badalte hain.
29. Site ki 100 MB wali had nahi badalti.
30. Yeh file pichhle plan ki jagah leti hai; uska Pocket 0 aur Pocket 1 poora ho chuka hai.
