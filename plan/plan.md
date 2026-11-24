# Supabase pipeline ki marammat: PDF na atke, ek galti sabko na roke, badge sach bole

Super Admin ki file-save machine (PDF aur pictures Supabase me) theek hoti hai: badi PDF ka 0% par atakna band, ek file ki galti se baaki kitaabon ka rukna band, aur storage badge wahi dikhata hai jo sach hai.
Har ruki cheez apni asli wajah aur agla kadam khud batati hai, aur koi mock tabhi Live hota hai jab uski har picture Supabase me maujood saabit ho.

Yeh plan likhte samay koi code nahi badla aur live par kuch nahi chheda gaya. Live ke logs is dauran nahi padhe ja sake, isliye neeche har baat ke saath likha hai ki woh saabit hai ya sirf sabse sambhav.

## Kiske liye

- **Owner (Super Admin):** PDF upload karta hai aur mock Live karta hai. Use sach chahiye: file gayi ya nahi, kyun ruki, ab kya karna hai.
- **Students:** Super Admin nahi dekhte, par wahi paper pate hain jo yahan se nikalta hai. Adhoori pictures wala paper un tak nahi pahunchna chahiye.
- **App team:** unke liye kuch nahi badalta. App jo server call karta hai unka jawab waisa hi rehta hai.

## Kya hoga aur kaise

### 1. Yeh sab kyun ho raha hai

Screenshot (jeelive.ai, 24 Nov, 10:43): badge hara "Storage: Supabase 1698 ms" aur saath me laal bindi; "mathematics chapterwise" par "Original Supabase mein: 0% · 0 KB / 49.1 MB" aur "Supabase ka intezaar · 342 min se".

| # | Kadi | Kya hota hai | Kitna pakka |
| --- | --- | --- | --- |
| 1 | Badi file ka raasta alag hai | 6 MB tak ki file (saari pictures) ek hi request me jati hai. Usse badi file (original PDF) 6 MB ke tukdon me, doosre raaste aur Supabase ke doosre pate se jati hai. Badge sirf ek nanhi file bhej kar jaanchta hai. | Saabit (code) |
| 2 | Is PDF ka pehla tukda hi manzoor nahi ho raha | "0 KB" ka matlab: Supabase ne upload shuru karne ki haan kahi, par ek bhi tukda manzoor nahi hua. | Saabit (screen + code) |
| 3 | Kyun manzoor nahi ho raha | Tukdon me bhejte samay "purani file ke upar likhne ki ijazat" sirf pehli request me jati hai, har tukde ke saath nahi. Us pate par file pehle se ho toh Supabase har tukda lautata hai (409, "already exists"). Wahi PDF hamesha wahi pata pati hai. Aisa do tarah ho sakta hai: (a) wahi PDF pehle upload hui thi aur uska record Library se delete hua (Library delete Supabase ki file nahi hatata; record ke mutabik 23 Nov ko Library se 7 uploads delete hue the, yeh PDF unme thi ya nahi woh Pocket 0 me dekha jata hai); (b) pichhli koshish me aakhri tukda pahunch gaya par uska jawab raaste me kho gaya. | Sabse sambhav, abhi saabit nahi |
| 4 | Har galti ko "Supabase chala gaya" maana jata hai | Kisi bhi ek file ki nakaami par machine us server par SAARI nayi files ke liye Supabase ko 15 second se 5 minute "aaram" de deti hai. Ek kharab PDF doosri kitaabon ki pictures ka save aur publish bhi rok deti hai. | Saabit (code) |
| 5 | Hara badge, laal bindi aur ghoomta chakkar | Hari bindi = nanhi file wali jaanch paas. Laal bindi = machine panel ke mutabik ek PDF ruki hai. Dono apni jagah sach hain, par saath me uljhate hain. Jaanch paas hote hi aaram hat jata hai aur saara ruka kaam ek saath jagta hai. Har server par PDF ka kaam ek samay me ek hi chalta hai, sabse purana pehle. Isliye wahi kharab PDF baar-baar us jagah ko gher leti hai: har koshish me poori PDF dobara jodi jati hai aur pehla tukda 6 baar tak bheja jata hai. Phir woh fail hoti hai, aaram lagta hai, aur jis kitaab ko usi pal picture ya PDF save karni thi woh bhi ruk jati hai. Super Admin khula ho toh yeh lagbhag har minute dohrata hai. Isi se "active dikhta hai, phir apne aap ruk jata hai, books aage nahi badhti". | Code se nikla; live par yeh kram dekha nahi gaya |
| 6 | Do server, do rai | Storage ki haalat har server apni yaad me rakhta hai. Pichhli report ke mutabik live par 2 server hain. Badge ek se poochta hai, kaam doosre par ho sakta hai. | Saabit (code) |
| 7 | Wajah chhupi rehti hai | Row hamesha "apne aap aage chalega" kehti hai (342 minute se) aur Supabase ka asli jawab nahi dikhati. Koi had nahi jiske baad woh "atki hai" kahe. | Saabit (screen + code) |

Kadi 3 ke doosre sambhav kaaran, jo pehle kadam me saath hi jaanche jate hain: adhe upload par Supabase ka lock (423), aur badi file wale pate par time-out.

**Jo nahi toota hai**
- Pictures (chhoti files) ka save hona. Woh tabhi rukti hain jab kadi 4 ka "aaram" laga ho.
- Picture chhoti karne ke dono raaste (save ke samay bina pixel badle chhoti PNG; student ko bhejte samay lossless WebP). Dikkat picture banne ke baad Supabase me jane ke raaste me hai, banne me nahi.
- Students ka padhna "aaram" se nahi rukta.
- Sign in, answer save, submit, score aur rank Supabase par nirbhar nahi hain.

### 2. Kitne kon se socha gaya

| # | Kon | Aaj ki haalat | Kahan theek hota hai |
| --- | --- | --- | --- |
| 1 | Badi file ka raasta | Pehla tukda atakta hai; ek hi raasta hai | Pocket 1 |
| 2 | Chhoti files (pictures) | Theek, par badi file ki galti se rukti hain | Pocket 2 |
| 3 | Intezaar aur atakne ka farq | Koi farq nahi; sab "intezaar" | Pocket 2 |
| 4 | Status ka sach | Sirf nanhi file ki jaanch | Pocket 3 |
| 5 | Do server | Apni-apni yaad | Pocket 3 |
| 6 | Wajah ka dikhna | Chhupi hui | Pocket 3 |
| 7 | Picture sahi save hui ya nahi | Save ke samay fingerprint likha jata hai; Live se pehle Supabase me maujoodgi nahi jaanchi jati; kami tabhi dikhti hai jab student paper khole | Pocket 4 |
| 8 | Atki PDF ki wapsi | Uske hisse server par surakshit hain | Deploy ke baad apne aap |
| 9 | Wahi PDF dobara upload | Wahi pata; Library delete ke baad file Supabase me padi rehti hai | Pocket 1; safai Phase 3 |
| 10 | Supabase account ki hadein | File size ki default had, spend cap, door ka region (nanhi file 1.7 second) | Owner ke kaam; Phase 3 |
| 11 | Exam ke din students ka padhna | Doosri copy nahi (owner ka faisla). Jo picture server ki yaad me nahi, woh Supabase se hi aati hai; Supabase chup ho toh ek request lagbhag 80 second tak latak sakti hai | Phase 2 |
| 12 | Purana kaam na toote | Section 5 ki rekha | Har pocket |

### 3. Phase 1: paanch chhote pocket

Har pocket alag se poora hota hai aur alag se deploy ho sakta hai. Pocket 1 jaan-boojh kar sabse chhota hai, taaki live ka atkaav sabse pehle hate.

**Pocket 0: Asli wajah ka saboot (kuch badle bina)**
- Live par sirf padhna: atki PDF ke saath save hua Supabase ka asli jawab, pichhle 24 ghante ki storage galtiyan wajah ke hisaab se gini hui, kitne server chal rahe hain, aur kaun si doosri kitaab ruki hai.
- Preview par wahi haalat test file se dobara banti hai: ek badi file ek hi pate par do baar, aur aakhri tukde ka jawab kho jana.
- Owner ko ek chhoti report milti hai, kisi sudhaar se pehle. Wajah kuch aur nikle toh Pocket 1 usi par lagta hai aur yeh report me likha jata hai. Bina deploy ka koi surakshit upaay ho toh woh bhi isi report me aata hai.

**Pocket 1: Badi file ka raasta pakka**
1. Upar likhne ki ijazat har tukde ke saath jati hai, sirf pehli request me nahi.
2. "Pehle se hai?" jaanch: bhejne se pehle aur har nakaam koshish ke baad machine dekhti hai ki us pate par wahi file poori maujood hai ya nahi. Ho toh use poora padh kar fingerprint se milaya jata hai; mil jaye toh dobara nahi bheji jati.
3. Atka hua adha upload: do koshish me ek bhi tukda aage na badhe toh purana adha upload chhod kar naya shuru hota hai. Aaj wahi adha upload 20 ghante tak dohraya ja sakta hai.
4. Doosra raasta: tukdon wala raasta lagataar do baar nakaam ho aur chhoti file ja rahi ho, toh wahi PDF ek hi request me bheji jati hai (Supabase is tarah 5 GB tak leta hai).
5. Supabase ka "lock" wala jawab (423) intezaar maana jata hai, nakaami nahi.
6. Har badi file ke save hone ke baad Supabase me uska size milaya jata hai; tabhi kitaab aage padhi jati hai.

**Pocket 2: Ek file ki galti us file tak**

| Galti ka prakar | Pehchaan | Machine kya karti hai |
| --- | --- | --- |
| Supabase door ya dheema | Jawab nahi, ya Supabase ki apni galti (5xx, 429) | Jaisa aaj: saara naya kaam rukta hai, Supabase lautte hi apne aap chalta hai |
| Supabase project par rok | Billing ya usage ki rok (402), project paused (540), key galat | Naya kaam rukta hai; saaf likha aata hai ki Supabase dashboard me kya dekhna hai |
| Sirf yeh file nahi ja rahi | Supabase jawab de raha hai par isi file ko lauta raha hai, ya wahi file 3 baar bina ek tukda badhe ruki | Sirf yahi file "atki hai" hoti hai. Supabase ko aaram nahi diya jata. Baaki kitaabein chalti rehti hain. |

- "Atki hai" wali file har minute nahi, har 15 minute par ek baar apne aap dobara koshish karti hai, aur "Dobara chalao" button se turant. Uske hisse server par rehte hain; kuch delete nahi hota.
- Badge ki jaanch paas hone par sirf wahi kaam jagta hai jo Supabase ke lautne ka intezaar kar raha tha, atki file nahi.
- Size ya file ke prakar ki rok pehle ki tarah turant saaf message ke saath rukti hai.

**Pocket 3: Sach bolne wala badge**
1. Storage ki haalat database me rakhi jati hai, har server ki apni yaad me nahi. Dono server ek hi baat dikhate hain.
2. Badge do raaston ka haal alag dikhata hai: "Pictures (chhoti file)" aur "PDF (badi file)". Hara tabhi jab dono theek hon.
3. Koi file 10 minute se ruki ho toh badge hara nahi rehta, chahe nanhi file wali jaanch paas ho.
4. "Badi file ka test" button: lagbhag 7 MB ki test file asli tukdon wale raaste se jati hai, wapas padhi jati hai, phir hata di jati hai. Samay ya wajah dikhti hai. Jab koi PDF ruki ho tab yeh test apne aap bhi ek baar chalta hai, taaki machine jaan sake ki raasta kharab hai ya sirf woh file.
5. Har ruki row par asli wajah saral shabdon me, Supabase ke code ke saath. Udaharan: "Wajah: Supabase ke mutabik yeh file us pate par pehle se hai (409)". Saath me agla kadam.
6. Machine panel me aakhri 20 storage galtiyon ki list: kab, kaun si file, kya wajah.

**Pocket 4: Picture ka saboot**
1. Mock ki pictures save hone ke baad aur Live hone se pehle machine Supabase se poochti hai ki us mock ki har picture wahan maujood hai. Nayi pictures ka size bhi milaya jata hai.
2. Jo picture na mile woh dobara save hoti hai. Phir bhi na mile toh mock Draft rehta hai aur wajah likhi aati hai: "3 pictures Supabase me nahi mili". Adhoora mock Live nahi hota.
3. Mock ki row par ek line: "Pictures: 312 / 312 Supabase me".
4. "Poori jaanch" button (owner): us mock ki har picture Supabase se padhi jati hai aur fingerprint se milayi jati hai. Kisi zaroori exam se pehle ke liye.

### 4. Owner ke kaam (Supabase dashboard; yeh builder nahi kar sakta)

1. **Storage › Settings › Upload file size limit:** 100 MB ya zyada. Site 100 MB tak ki PDF leti hai. Supabase ki default had aksar 50 MB hoti hai (Pro par badhayi ja sakti hai); utni rahi toh 50 MB se badi PDF Supabase lauta dega.
2. **Billing › Spend cap:** ON ho toh included usage paar hote hi Supabase project par rok laga deta hai (har request 402) jab tak billing cycle na badle. 9 Dec se pehle ek faisla: OFF (zyada usage ka bill aata hai, rok nahi lagti) ya ON (bill tay, rok ka jokhim).
3. Supabase ke email jis inbox me aate hain woh roz dekha jata ho.
4. Atki hui "mathematics chapterwise" ko abhi delete na karein. Uske hisse server par surakshit hain aur sudhaar ke baad wahin se aage badhte hain.

### 5. Kya nahi chhua jata

- PDF reader, cutter, chapter split, answer key, Fix tool.
- Students ka player, results, analysis, AITS hub, Rank, Mission, CEO dashboard, contacts.
- Students ko picture bhejne ka raasta (Phase 2 tak waisa hi).
- Picture chhoti karne ke dono raaste.
- Login, PIN, scoring, rank.
- Purani Emergent files: jahan hain wahin se padhi jati rehti hain. Koi nayi file Emergent me nahi jati.
- App ke liye server ke jawab. Storage health ke jawab me sirf naye khaane judte hain.

### 6. Poora kab maana jayega

- Live ki atki PDF deploy ke baad bina dobara upload ke 0% se aage badhti hai, ya row par uski sateek wajah likhi aati hai.
- Wahi badi PDF ek hi pate par do baar save ho jati hai.
- Ek file jaan-boojh kar fail karayi jaye, tab bhi doosri kitaab bina ruke publish hoti hai.
- Koi file 10 minute se ruki ho toh badge hara nahi dikhta, aur dono server ek hi haalat dikhate hain.
- Har ruki row par wajah aur agla kadam likha hai.
- Jis mock ki ek picture Supabase se gayab ho woh Live nahi hota.
- Upload › Draft › Fix › Live ka purana raasta pehle jaisa chalta hai.
- Jo cheez check na ho paye woh "check nahi hua" likhi jati hai, "ho gaya" nahi.

## User flow

**Owner, is kaam ke dauran**
1. Plan manzoor karta hai.
2. Pehle Pocket 0 ki chhoti report milti hai: asli wajah, saboot ke saath.
3. Pocket 1 se 4 ek-ek karke preview me bante hain. Har pocket ke baad ek line ka haal milta hai.
4. Owner jab chahe "deploy" kehta hai. Pocket 1 akela bhi deploy ho sakta hai.
5. Deploy ke baad atki PDF apne aap aage badhti hai. Dobara upload nahi karna.
6. Live par uska nateeja ek baar sirf padh kar bata diya jata hai.

**Roz ka upload (Phase 1 ke baad)**
1. Upload PDF › "Server par pahunchi X%".
2. "Original Supabase mein X%".
3. "Padhi ja rahi hai · X / Y page" › Draft.
4. Live dabane par: pictures save › "Pictures: N / N Supabase me" › Live.

**Jab kuch ruke**
- Supabase door ho: row "Supabase ka intezaar" kehti hai, wajah ke saath. Lautte hi apne aap chalta hai.
- Supabase project par rok ho: row aur badge batate hain ki dashboard me kya dekhna hai.
- Sirf ek file atki ho: row "Atki hai" kehti hai, wajah aur "Dobara chalao" ke saath. Baaki kitaabein chalti rehti hain.

## UI/UX feel

- Koi nayi screen nahi. Wahi badge, wahi panel, wahi upload row; bas sach aur wajah judte hain.
- Badge ke rang: hara = dono raaste theek; peela = dheema hai ya koi file atki hai; laal = Supabase jawab nahi de raha ya project par rok hai.
- Wajah ki line chhoti aur saral Roman Hinglish me; Supabase ka code bracket me.
- "Apne aap aage chalega" sirf tab likha aata hai jab woh sach ho. Atki file par nahi.
- Phone (390 px) par row ki line aur button ek ke neeche ek; tap ki jagah kam se kam 44 px.
- Maujooda JEELIVE look; koi naya style nahi.

## Phases

**Phase 1 (abhi banta hai): pipeline ki marammat**
- Pocket 0: asli wajah ka saboot.
- Pocket 1: badi file ka raasta pakka.
- Pocket 2: ek file ki galti us file tak.
- Pocket 3: sach bolne wala badge.
- Pocket 4: picture ka saboot.
- Sab preview me; live par sirf padhna; deploy owner ke kehne par.

**Phase 2 (alag manzoori): exam ke din students ki dhaal**
- Live paper ki pictures server ki disk par bhi rakhi jati hain, sirf yaad me nahi. Supabase ki chhoti rukavat un students tak nahi pahunchti jinka paper server par aa chuka hai.
- Tay samay wale exam aur AITS ke din se pehle har server par us paper ki saari pictures pehle se taiyaar; Super Admin me ek line: "Aaj ka paper: pictures 100% taiyaar".
- Supabase chup ho toh picture ki request kuch second me saaf jawab deti hai, latakti nahi; sign in, answer save aur submit tez rehte hain.
- AITS paper ko din dete hi uski "Poori jaanch" apne aap.
- Storage 10 minute se ruka ho toh CEO dashboard ke alerts me bhi dikhta hai.

**Phase 3 (alag manzoori): bada paimana aur safai**
- Pictures ke aage CDN, taaki 1 lakh students ka pehla load server aur Supabase par na pade (server ka hissa bana hua hai; CDN ka pata owner deta hai).
- Supabase me padi bekaar files ki safai: delete ho chuki kitaabon ki files, adhe upload, test files. Pehle list, phir owner ki haan.
- Owner chahe toh Live papers ki doosri swatantra copy, ya Supabase project server ke paas wale region me.
- Purani Emergent files ko poori tarah Supabase me lana.

## Assumptions (jo faisle bina pooche liye gaye)

1. Owner ka faisla maana gaya: sirf Supabase. Koi nayi file Emergent me nahi jati, na backup ke roop me.
2. Kadi 3 ki wajah sabse sambhav hai, saabit nahi. Pocket 0 use live ke saboot se pakka karta hai. Wajah alag nikle tab bhi Pocket 1 se 4 lagoo rehte hain, kyunki woh kadi 4 se 7 ko theek karte hain jo code me saabit hain.
3. Live par builder kuch nahi likhta aur login nahi karta. Live ki jaankari sirf padhne wali jaanch se aati hai.
4. Asli Supabase par test sirf preview ke bucket me hota hai, "TEST_" naam ki files se, jo baad me hata di jati hain. Live ke bucket me test ki koi file nahi jati.
5. Badi file ke liye doosra raasta (ek hi request) joda gaya, taaki tukdon wala raasta kharab ho tab bhi PDF pahunche.
6. Hadein chuni gayi: 2 nakaam koshish par naya upload ya doosra raasta; 3 baar bina pragati par "Atki hai"; atki file ki apne aap koshish har 15 minute; badge 10 minute ke baad hara nahi; test file lagbhag 7 MB.
7. Naya niyam: jis mock ki koi picture Supabase me na mile woh Live nahi hota, Draft rehta hai.
8. Live se pehle ki apne aap jaanch maujoodgi (aur nayi pictures ka size) dekhti hai. Har picture ko padh kar fingerprint milana "Poori jaanch" button par hai, kyunki woh publish ka samay lagbhag doguna kar deta hai.
9. Asli Supabase rukavat par "aaram" ke samay (15 second se 5 minute) wahi rehte hain.
10. Students ki dhaal (kon 11) Phase 2 me rakhi gayi, kyunki aaj ka atkaav upload me hai aur owner chhote pocket chahta hai.
11. Live par atki PDF ko haath se nahi chheda jata. Deploy ke baad woh apne hisson se aage badhti hai.
12. Supabase dashboard ke kaam (section 4) owner karta hai.
13. Site ki 100 MB wali had nahi badalti.
14. Screen ki bhasha saral Roman Hinglish; jame hue shabd (Master, Draft, Live, Library, Upload PDF) wahi rehte hain.
15. Deploy tabhi jab owner "deploy" kahe.
16. Yeh file pichhle plan (Super Admin re-audit) ki jagah leti hai; woh kaam poora ho chuka hai.
