# Super Admin ka gehra re-audit: 11 charan me jaanch, ek hi daur me sudhaar, ant me ek report

Super Admin ke har hisse ki 11 charan me jaanch hoti hai: PDF machine, "fix required", upload, Master ke raaste, haq aur suraksha, bada data, design, phone, speed, aur jeelive.ai ki sirf-padhne wali jaanch.
Jo galti milti hai woh isi daur me theek hoti hai. Ant me ek report milti hai: kya mila, kya badla, pehle aur baad ka saboot, aur owner ke karne ke kaam.

Yeh plan likhte samay koi test nahi chala aur koi code nahi badla.

## Kiske liye

- **Owner (Super Admin):** PDF upload karta hai, mock theek karta hai, Live karta hai. Chahta hai ki machine faltu blockage na dikhaye, tez chale, aur phone par bhi poori chale.
- **Reviewer:** sirf ruke mock aur student reports theek karta hai. Usse zyada kuch nahi khulna chahiye.
- **Students:** Super Admin nahi dekhte, par wahi paper pate hain jo yahan se nikalta hai. Galat cut ya galat answer key unhi tak pahunchti hai.

## Kya hoga aur kaise

### 1. Tareeka

| Kadam | Kya hota hai |
| --- | --- |
| 1. "Pehle" ka record | Har Super Admin screen ki picture (desktop 1920 aur phone 390), speed ke number, saari kitaabon ka scan record, aur haq ki table. Sudhaar se pehle. |
| 2. Jaanch, bina kuch badle | 11 charan. Har charan ki jaanch alag hoti hai aur us dauran koi file nahi badalti. |
| 3. Ek mili-juli list | Har galti ke saath: kahan hai, dobara kaise dikhegi, saboot, aur kitni gambhir hai. |
| 4. Ek hi daur me sudhaar | Sabse gambhir pehle. Har file ek hi haath se badalti hai, taaki do sudhaar aapas me na takrayein. |
| 5. Alag se dobara test | Sudhaar karne wale se alag ek poora test run. Kadam 1 ke wahi naap dobara. |
| 6. Ek report | Section 7 me likha hai. |

Is daur me owner se koi sawaal nahi poocha jata. Jahan faisla lena pade, woh is plan ke niyam se liya jata hai aur report me likha jata hai.

**Galti kitni gambhir hai**

| Darja | Matlab |
| --- | --- |
| S1 Gambhir | Student ko galat paper ya galat answer; data ka nuksaan; bina haq ke access; koi secret bahar |
| S2 Bada | Owner ka kaam rukta hai (upload, fix, Live); faltu blockage; galat ginti |
| S3 Madhyam | Dheema, uljhane wala, phone par mushkil |
| S4 Chhota | Dikhawat, shabd |

### 2. Jaanch ke 11 charan

| # | Charan | Kya jaancha jata hai |
| --- | --- | --- |
| 1 | PDF machine | Reader, cutter, chapter split, answer key, solutions, aur naya version aane par kitaab ka apne aap dobara padha jana. Saari maujooda kitaabon ki local copy dobara scan hoti hai, sirf memory me. Nateeja pichhle record se milaya jata hai. |
| 2 | "Fix required" ki sachchai | Har tarah ka blockage, ginti ke saath: asli hai ya faltu. Ginti Master, Fix list aur mock ke andar ek jaisi hai ya nahi. Dobara padhte samay purani ginti ka dikhna. "Confirm printed examination rules…" wala prompt. Override. |
| 3 | Upload aur storage | Ek PDF, batch upload, alag answer key aur solution PDF, beech me ruk kar resume, wahi PDF dobara, duplicate ki chetavni, publish ka progress, Supabase band ho toh Emergent, 10 minute wali chetavni, net band, do upload ek saath, galat file, 50 MB ki photo. |
| 4 | Master ke raaste | Exam › Type › Mock. Draft, Live, Scheduled, Off, Library. Schedule aur Live exam. AITS ke din. Write editor. Chapter split. Fix aur Proof. Try as student. Library (delete, restore, replace). Students, Team, Reports. Har button aur har link. Do baar dabane par do kaam toh nahi hote. Beech me refresh ya Back. Net band me "saved" toh nahi dikhta. Khaali form. Sirf keyboard se poora kaam. Doosre time zone ke browser me IST ka din aur samay. |
| 5 | Haq aur taale | Ek table: owner, reviewer, student, bina login × Super Admin ka har kaam. Screen chhod kar seedha server ko call. Kisi aur ki ID se call. Request me role ya status badal kar bhejna. Reviewer hatate hi uska access band. Student ka PIN reset staff account ko na chhoo sake. Browser ki files aur git history me koi secret. Private file store aur khatm hone wale link. Login session ki settings. Logs me password ya token. Mock ke naam, option ke text, likhe hue sawaal, leaderboard naam ya photo (SVG) me chhupa script. |
| 6 | Bill aur bheed se bachav | Login, sign-up, PIN reset aur owner login par had. Ek hi call 100 baar. Upload ka size aur file ka prakar. AI ka call kaun chala sakta hai. Ek click me account band karna. Libraries ki jaani-pehchaani kamzoriyan. Debug band. Test account aur test data. |
| 7 | Bada data aur database | 10,000 students, 2,000 mocks, 50 kitaabein aur bhari Library ke saath har screen. 200 akshar aur emoji wala naam. Ek hi email alag capital me. Index. Baar-baar wahi query. Lambi list page-wise. Cache ke niyam. Bhaari kaam background me. Scheduled kaam aur uski nakaami ka dikhna. |
| 8 | Design ek jaisa, har state | Pehle Super Admin ka DESIGN.md. Phir rang, font size, spacing, corner us par. Ek jaise button, card, input. Loading, khaali aur error ki apni screen. Button ka hover, pressed, disabled. Form ki galti wahin dikhna. Submitting, success, failure. Modal, dropdown, tab ka transition. Light aur dark dono me padhne layak. Shabd. Placeholder text. Har screen ka apna title aur ek main button. |
| 9 | Phone aur CSS | 390 px par side scroll nahi. Mobile menu. Tap ki jagah 44 px. Text 200% bada karne par layout. good-css ki teen tarah ki galtiyan (section 6). Safari ka engine. |
| 10 | Speed | Pehle aur baad ka naap. Sabse bhaari packages. Bhaari hisse (editor, fix tool, charts) zaroorat par load. Skeleton. Ek ke baad ek hone wale server call ek saath. Kamzor Android aur slow 4G par main raaste. |
| 11 | jeelive.ai (sirf padhna) aur launch ki taiyari | Live par reader ka kaun sa version chal raha hai. AITS aur BITSAT ki kitaabein dobara padhi gayi ya nahi, aur unki ginti. Live storage ki 500 wali galti. Scheduled kaam. Live browser files me secret. Admin aur login page Google se bahar. Na-maujood page. Owner ke dashboard wale kaam. |

Charan 1 me scan hone wali kitaabein: physics, chemistry, maths ki chapter kitaabein (4,650 sawaal), boxed chemistry (1,250), AITS maths (1,250), AITS JEE Main ki do kitaabein (25-25 mock), BITSAT Logical Reasoning (18 chapter, 900 sawaal), BITSAT Chemistry (32 chapter, 1,600 sawaal), aur jo bhi PDF workspace me maujood ho. Database aur storage me kuch nahi likha jata. AI ka koi credit nahi lagta.

### 3. Jo pehle se pata hai (jaanch yahin se shuru hoti hai)

| Baat | Abhi ki jaankari |
| --- | --- |
| Dobara padhte samay purani ginti | Live par AITS ki kitaabein dobara padhi ja rahi thi, par Master purana "500 to fix" dikhata raha. Owner ko laga deploy ka asar nahi hua. |
| "Confirm printed examination rules, count, duration, marking and solution coverage" | BITSAT chapter-wise me har chapter par ek baar aata hai (18 + 32). Asli zaroorat hai ya faltu, yeh tay nahi hua. |
| AITS kitaab 2 | Local jaanch me 25 me se 24 mock saaf. Ek sawaal (Q46, graph wala) ka aakhiri nateeja record me nahi hai. |
| BITSAT ka sudhaar (reader version 7) | Preview me test hua: 900 aur 1,600 answer key, 0 galat. Live par pahuncha ya nahi, yeh nahi dekha gaya. |
| Live storage | Emergent storage par file likhte samay 500 aata tha. Platform ki dikkat hai; aaj ki haalat nahi pata. |
| Super Admin ki bhasha | Kuch screens English me hain (Students, Library), kuch Hinglish me (Fix tool, storage). |
| Super Admin ka light theme | Haath se kabhi nahi sudhara gaya. |

### 4. Sudhaar ke niyam

**Isi daur me theek hota hai:** Super Admin aur uske server hisse ki har S1 se S4 galti.

**PDF machine ka niyam**
- Galat cut se behtar ruka hua sawaal. Machine andaza nahi lagati.
- Faltu blockage machine ke star par hatta hai, kisi ek kitaab ya ek sawaal ke liye nahi.
- Asli blockage rehte hain: answer key nahi mili ya do alag mili, options aur key bemel, sawaal ka prakar saaf nahi.
- Jo sawaal aaj saaf katta hai uska cut wahi rehta hai. Jo cut badalta hai woh report me ek-ek karke likha jata hai. Bina wajah ka badlaav ho toh woh sudhaar nahi jata.
- PDF padhne me AI ya OCR nahi.

**Sirf report hota hai, badalta nahi**

| Kya | Kyun |
| --- | --- |
| Owner ke jaan-boojh kar liye faisle: PIN reset bina OTP, AITS ke solutions usi din khulna, submit ke turant baad score, 30 verified JEE Main PYQ locked | Faisle owner ke hain. Jokhim ek baar report me likha jata hai. |
| Bahar ke dashboard ke kaam: 2-step login, backup, uptime monitor, kharch ki had, domain auto-renew, key badalna | Sirf owner kar sakta hai. Report me kadam-dar-kadam likhe hote hain. |
| Platform ki dikkat (live storage 500) | Haalat aur support ko bhejne wala message report me. |
| jeelive.ai ka data | Audit live par kuch nahi likhta. |
| Jo paper students ke liye pehle se Live hai | Uska cut audit nahi badalta. |
| Library ka bada version upgrade, koi library hatana, database ya server ki jagah badalna | Report me sujhav ke roop me. |

### 5. Is daur me owner ko dikhne wale naye badlaav

1. **Dobara padhne ka sach:** jab kitaab dobara padhi ja rahi ho, Master purani "to fix" ginti ki jagah "dobara padhi ja rahi hai · 1,200 / 3,000 page" dikhata hai. Ginti padhai poori hone par aati hai.
2. **Rules wala prompt:** jab mock type me time aur marks pehle se tay hon, aur sawaalon ki ginti, answer key aur solutions machine ne khud saabit kar di hon, tab yeh prompt mock ko nahi rokta. Kuch sach me na pata ho tabhi rokta hai.
3. **Account band karna:** Students screen par har student ke saamne "Block". Pakka karne ke baad woh number har jagah se sign out ho jata hai, dobara sign in ya PIN reset nahi kar pata. "Unblock" se wapas. Purane attempt aur rank rehte hain. Sirf owner ke liye.
4. **Machine ki haalat:** upar ki patti ka storage badge ek chhota panel kholta hai: storage, aakhiri scheduled jaanch kab chali, kitne kaam fail hue, kaun si kitaab 15 minute se atki hai ("Dobara chalao" ke saath). Kuch dekhne layak ho toh laal bindi. Sirf owner ke liye.
5. **Owner login par had:** 10 galat password ke baad 15 minute ki rok, students wale niyam jaisi.
6. **File ke niyam:** PDF andar se bhi PDF ho, sirf naam se nahi. Photo sirf PNG, JPG, WebP (SVG nahi). Excel sirf .xlsx. Jahan size ki had pehle se hai woh rehti hai; jahan nahi hai wahan photo 5 MB aur Excel 10 MB.
7. **Ek bhasha:** Super Admin ke vaakya, madad aur galti ke message saral Roman Hinglish me. Jame hue shabd wahi rehte hain: Master, Draft, Live, Scheduled, Off, Library, Upload PDF.
8. **Har screen poori:** loading, khaali aur error ki apni screen; form ki galti usi box ke neeche; har button ka hover, pressed, disabled; har Super Admin screen ka apna browser title; admin aur login page Google ke liye band.

### 6. Chipkayi gayi suchiyon ka hisaab

Owner ki bheji suchiyon ke group in charan me aate hain: design (charan 8, 9), server ke peeche ki 25 cheezein (5, 6, 7, 11), todne wale 16 sawaal (4, 5, 6, 7, 9), speed (7, 10), good-css (9).

**good-css:** uski list aur zaroori reference files padh kar teen tarah ki galtiyan dhoondhi jati hain: (1) phone par tootne wali: tap ke baad atka hover, 44 px se chhoti tap ki jagah; (2) jo CSS se ho sakta tha par script ya kai breakpoint se bana; (3) baareekiyan: sticky patti ke neeche chhupta link, khulte hi laal border wale form, hilte number, hataya gaya focus ring. Prakar 1 aur 3 theek hote hain. Prakar 2 tabhi badalta hai jab usse koi dikhne wali galti theek ho; baaki report me. Component library ke apne component nahi gine jate. Jo tareeka kisi browser me nahi chalta, woh report me likha jata hai.

**Jo lagoo nahi**

| Suchi ki cheez | Kyun nahi | Uski jagah |
| --- | --- | --- |
| Payment: webhook, refund, trial, test se live key | App me payment nahi hai | Kuch nahi |
| Database ke RLS niyam | Browser database tak seedha nahi pahunchta; Supabase sirf private file store hai | File store private hai aur link khatm hote hain, yeh jaancha jata hai |
| next/image, next/font, ISR, server ka region | Site us dhaanche par nahi bani | Wahi maqsad: picture ka size, font, zaroorat par load |
| Email verify, free credits | App me nahi hain | Kuch nahi |
| Sign-up par CAPTCHA | Mobile app wahi server chalata hai aur owner ne saada PIN chuna hai | Number aur address ke hisaab se had |
| AI jawab stream karna | Super Admin me AI chat nahi | Kuch nahi |
| Sign-up aur checkout ka raasta | Yahan lagoo nahi | Owner ka poora raasta: login se Live tak |
| ~/.claude/agents ki files, model aur effort ki setting | Is workspace me woh vyavastha nahi hai | Wahi bantwara yahan ke read-only jaanch-karta se; suraksha wala group sabse gehra |
| Public pages ka SEO, bina JS ke page, sitemap, free tool page | Super Admin ka hissa nahi | Phase 2 |

### 7. Report me kya hoga

- Upar ek chhoti table: kitni galtiyan mili (S1 se S4), kitni theek hui, kitni owner ya platform ke paas.
- Poori list: har galti, kahan thi, kya kiya gaya, ab ki haalat. Haalat ek hi hoti hai: theek / galti nahi thi / owner ka kaam / platform ka kaam / check nahi hua (wajah ke saath).
- Pehle aur baad: har Super Admin screen ki picture, speed ke number (3 baar naap kar beech wala), kitaabon ka scan (kitne sawaal, kitne ruke, kaun sa cut badla), haq ki table.
- Jo faisle bina pooche liye gaye.
- Owner ke kaam, kadam-dar-kadam.
- Kya deploy ka intezaar kar raha hai, aur deploy ke baad live par kya hoga.
- Koi secret mile toh sirf uski jagah likhi jati hai, uska maan kabhi nahi.

### 8. Suraksha ki rekhayein

- jeelive.ai par sirf padhna: bina login ke khule page aur platform ki read-only jaanch. Live par koi login, koi data badlaav, koi todne wala test nahi.
- Todne wale test (100 call, 10,000 record, role badalna, script daalna) sirf ek kaam-chalau test copy me chalte hain, jo baad me hata di jati hai.
- Test asli storage, asli Supabase ya AI ko nahi chhoote.
- Git history dobara nahi likhi jati.
- Speed ke liye koi feature nahi hatta.
- Sab kuch preview me banta hai. jeelive.ai par tabhi jata hai jab owner "deploy" kahe.

### 9. Poora kab maana jayega

- Haq ki table me ek bhi galat khaana nahi.
- AITS ke 50 mock aur BITSAT ke 50 chapter par sawaal ke star ka faltu blockage 0. Jo blockage bache, har ek ki wajah report me.
- Jo sawaal pehle saaf katta tha uska cut wahi, ya badlaav wajah ke saath likha hua.
- 390 aur 1920 par koi Super Admin screen side me nahi khisakti.
- Har S1 aur S2 ya toh theek hai, ya wajah ke saath owner ya platform ke paas.
- Sudhaar karne wale se alag ek poora test run paas.
- Jo check na ho paye woh "check nahi hua" likha jata hai, "ho gaya" nahi.

## User flow

**Owner, is kaam ke dauran**
1. Plan manzoor karta hai.
2. Beech me koi sawaal nahi aata.
3. Ant me ek report milti hai.
4. Report padh kar "deploy" kehta hai, jab chahe.
5. Deploy ke baad live ki jo kitaabein abhi publish nahi hui, apne aap dobara padhi jati hain. Us dauran Master "dobara padhi ja rahi hai" dikhata hai, purani ginti nahi.
6. Padhai poori hone par live ki ginti ek baar read-only dekh kar bata di jati hai.

**Owner ka woh raasta jo poora chal kar dekha jata hai**
1. Owner login.
2. Master › exam › mock type.
3. Upload PDF (ek, phir batch), progress, Draft.
4. Fix list › Fix › Proof › Try as student.
5. Live, ya Schedule, ya AITS ka din.
6. Library: bhejna, wapas lana, delete, replace.
7. Students (PIN reset, naam hatana, Block), Team, Reports.
8. Yahi sab phone par.

**Reviewer:** login › ruke mock › fix › student reports. Baaki sab band milta hai.

## UI/UX feel

- JEELIVE ka maujooda look. Koi naya style nahi.
- Super Admin ka DESIGN.md is look ko likh kar pakka karta hai: thode rang, ek font size ki seedhi, ek spacing ki seedhi, corner ke tay size.
- Ek hi tarah ka har button, card aur input har screen par ek jaisa.
- Har screen par ek hi main button saaf dikhta hai.
- Phone par upar ki patti menu me simat jati hai; har tap ki jagah kam se kam 44 px.
- Loading me skeleton, khaali list par agla kadam batane wali line, error par "Dobara koshish".
- Transition chhote aur halke; jis phone me motion kam rakha gaya ho wahan nahi chalte.
- Light aur dark dono me text saaf padha jata hai.
- Likhai saral Roman Hinglish.

## Phases

**Phase 1 (abhi banta hai)**
- Section 2 ke 11 charan ki jaanch, Super Admin aur uske server hisse par.
- Section 4 ke niyam se saare sudhaar, ek hi daur me.
- Section 5 ke aath dikhne wale badlaav.
- Section 7 ki report, pehle aur baad ke saboot ke saath.
- Sirf preview me; live par sirf padhna.

**Phase 2 (alag manzoori)**
- Wahi suchiyan student aur public hisse par: design, phone, speed, picture ke format.
- Public pages ka SEO: har page ka apna title, description aur canonical; sitemap; robots; asli 404; bina JS ke padhe ja sakne wale page.
- Free tool page: teen vikalp search term ke saath dikhaye jate hain, owner ek chunta hai.
- Bahar ki monitoring aur uptime seva jodna (owner ka account aur key chahiye).
- AITS ke numerical sawaal ek saath confirm karna.
- PDF Engine ki ruki hui list: chipke options, do-column page, scan PDF bina AI, purane Draft ke liye "dobara padho".

**Phase 3 (alag manzoori)**
- "Read all mocks": pehle se upload hue sawaalon par AI tags, bina dobara upload, ek sawaal ek hi baar.
- AI doubt solver aur uski library.
- 1 se 2 lakh students ka load test.
- Super Admin me kisne kya badla, uska itihaas; har exam ka alag reviewer.

## Assumptions (jo faisle bina pooche liye gaye)

1. Owner ne "audit + saare fix ek saath, ant me ek report" chuna aur kaha ki koi sawaal na poocha jaye. Bheji gayi suchiyon me likha hai "pehle list dikhao, confirm ke baad badlo". Owner ka aakhiri nirdesh maana gaya: list poori banti hai aur report me aati hai, par sudhaar uske liye rukta nahi.
2. "Kam se kam 8 phase" ko jaanch ke 11 charan maana gaya. Yeh sab Phase 1 ke andar hain aur inke beech kaam nahi rukta.
3. Phase 1 ka daayra Super Admin aur uska server hissa hai, kyunki maang "super admin section ka re-audit" thi. Public SEO, free tool page aur student screens ka design Phase 2 me rakhe gaye.
4. Free tool page ke liye owner ka chunaav chahiye, isliye woh Phase 2 me hai. Site par /rank ke chhah free tool pehle se hain.
5. Rules wala prompt (section 5.2) ab har baar nahi rokta. Yeh ek niyam ka badlaav hai.
6. Account Block (5.3), machine ki haalat ka panel (5.4) aur owner login ki had (5.5) nayi cheezein hain, suchi ki in line se li gayi: "ek click me account band", "scheduled kaam fail ho toh pata chale", "login par had".
7. Block hua number mobile app me bhi band hota hai, kyunki app wahi server chalata hai. App ka code nahi badalta; app apna aam error dikhata hai.
8. Bahar ki error-monitoring seva Phase 1 me nahi judti, kyunki uske liye owner ka account aur key chahiye. Uski jagah 5.4 ka panel hai.
9. Super Admin ki bhasha Roman Hinglish chuni gayi (5.7), kyunki fix tool aur storage ke message pehle se usi me hain.
10. CAPTCHA nahi lagta. PIN reset bina OTP waisa hi rehta hai. Dono owner ke pehle ke faislon par tike hain; jokhim report me likha jata hai.
11. AI ka call sirf owner chala sake, yeh server par pakka kiya jata hai. Owner par koi nayi daily had nahi lagti.
12. Jahan had pehle se hai (10 galat PIN par 15 minute, 15 minute me 5 PIN reset, PDF 100 MB) woh nahi badalti. Nayi had ke number 5.5 aur 5.6 me hain.
13. Library ki chhoti version badhat, jo kisi jaani kamzori ko band kare aur test paas kare, kar di jati hai. Bada version upgrade sirf report me.
14. Haq ka model wahi rehta hai: owner, reviewer, student. Koi naya role ya permission system nahi banta; sirf chhooti hui jaanch judti hai.
15. Test ke liye owner, reviewer aur do student account test copy me khud banaye jate hain. Owner se koi account nahi maanga jata.
16. Live par builder login nahi karta. Live ki jaankari khule page aur platform ki read-only jaanch se aati hai.
17. Koi secret browser files ya git history me mile toh code me uski jagah server wala raasta lagta hai, aur key badalne ke kadam owner ko diye jate hain. Git history nahi chhedi jati.
18. Maana gaya hai ki kitaabon ki local copy workspace me ab bhi hain. Jo na mile woh "check nahi hua" likhi jati hai, PDF ke naam ke saath.
19. PDF machine me badlaav hone par reader ka version badhta hai. Deploy ke baad live ki bina-publish kitaabein apne aap dobara padhi jati hain. Owner ke haath ke sudhaar aur publish ho chuke paper rehte hain.
20. Speed ka naap Master home aur 2 se 3 sabse dheeme Super Admin screen par, phone mode me, 3 baar. Login ke peeche ka page us tool se na napa ja sake toh load ka samay doosre tareeke se napa jata hai aur yeh report me likha jata hai.
21. Safari ki jaanch uske engine par automated browser me hoti hai, asli iPhone par nahi.
22. Pehle-baad ki pictures sirf Super Admin screens ki hoti hain, default theme me. Dark ki picture wahan jahan dark me kuch badla ho.
23. Purane test jinki ummeed ab purani pad gayi hai, naye niyam ke hisaab se badle jate hain. Unhe galti nahi gina jata.
24. Report Roman Hinglish me ek document hoti hai, chat me uska chhota saar.
25. Section 3 ke number pichhle record se liye gaye hain. Planning me unhe dobara nahi chalaya gaya.
26. Yeh file pichhle plan (rollback ke baad wala PDF Engine plan) ki jagah leti hai. Woh kaam poora ho chuka hai; uski ruki hui list Phase 2 me likhi hai.
