# Final guide (chautha version): ek sawaal ek record, AI ka raasta, Phase H "Matched", Phase I "Student Choice", doosri app, aur saara baaki kaam

**Haalat (26 Nov 2026):** sirf guide. Koi code nahi likha gaya, kuch deploy nahi hua. Banana aapki haan ke baad hi shuru hoga.

Har baat ke saath likha hai ki woh kis tarah ki hai:
- **Tay**: aapne keh diya hai.
- **Maine rakha**: faisla maine liya, taaki aapko har chhoti baat na batani pade. Aap badal sakte hain.
- **Dekha**: maine aaj file ya database me ginkar dekha.
- **Pata nahi**: abhi dekha ya naapa nahi gaya.

Naam ka dhyan: "Phase H" aur "Phase I" aapke product ke phase hain. Storage wale plan (plan/plan.md) ke "H" aur "I" hisson se inka koi rishta nahi.

---

## 0. Is version me kya naya

| Aapne kaha | Guide me ab |
| --- | --- |
| Fallback me Emergent ka Sol 6.1 ya 6.2 ho. | Hissa 3.1: aakhri paaydaan ab Emergent ka Sol hai. Emergent ki list me aaj Sol 6 hai; 6.1 aur 6.2 abhi nahi dikhe. Wahan aate hi wahi chalega, code badle bina. |
| AITS ek baar padho; chapter-wise bina AI ke jud jaye. Kya search se ho sakta hai? | Haan. Do raaste, dono bina AI ke: PDF me chhapa hua pata ("Source" line), aur shabdon ki khoj. Hissa 5. |
| Sirf level transfer karna hai; kharcha dugna na ho. | Chapter-wise par AI ki call: 0. AITS ki padhai bhi chhoti hui, kyunki solution PDF me pehle se chhapa hai (4.5 aur 3.7). |
| AITS, chapter-wise aur Matched: wahi sawaal, ek hi database. | "Ek sawaal, ek record": Hissa 4 aur 5. |
| AITS ka upload isi wajah se ruka hai. | Rokne ki zaroorat nahi; kram se fark nahi padta (5.4). Ek faisla pehle chahiye: Hissa 8. |
| Universal banao; doosri app (Niche Life) ke Super Admin me yeh sab pehle se ho. | Hissa 9 aur sunehra niyam 17. |

**Pichhle version me meri galti.** Jod ka naap maine purane chapter bank (78 test, 3,900 sawaal, Library me) par kiya tha, aur kaha tha ki uski ginti AITS se nahi milti. Woh bank AITS wala nahi nikla: uski ginti alag hai, aur Chemistry ke shabd milakar dekhe to ek bhi sawaal nahi mila. AITS wale chapter-wise books alag hain. Unme se do mere saamne hain (Chemistry aur Maths), aur unki ginti AITS se poori milti hai (Hissa 2). Hissa 5 naye naap se dobara likha gaya hai.

Pichhle faisle jaise the waise hain: har sawaal ke 10 tag; 10 me 7 ya 8 mile to match; saare 50 din gine jate hain; Student Choice ki list me sirf sawaal; Subject Rank aur Seekh Reminder nahi banenge.

Is version me hisson ke number aur pocket ka kram badle hain (Hissa 11).

---

## 1. Sunehre niyam

1. **Ek cheez banate hue doosri nahi tootti.** Naya kaam nayi files aur naye collection me rehta hai. Purani files sirf ginti ki jagah par chhui jati hain; woh jagah Hissa 10 me likhi hain.
2. **Har nayi cheez ka apna switch hota hai, shuru me Off.** Off rehne par app bilkul aaj jaisi chalti hai.
3. **Chhote pocket.** Ek pocket, ek kaam. Har pocket ke baad jaanch, phir aapko nateeja, phir agla.
4. **Har pocket ki jaanch me purani jaanch dobara chalti hai:** wahi 26 purani suite aur browser walk, phir testing agent ki alag jaanch.
5. **Jab tak test ka saboot na ho, "ho gaya" nahi kaha jata.**
6. **Live par kuch tabhi jata hai jab aap "deploy" likhen.**
7. **AI kisi paper, answer key ya student ke score ko nahi badalta.** Woh sirf padhta hai aur apna record alag rakhta hai.
8. **AI ka record sawaal ka hota hai, paper ka nahi.** Ek sawaal par AI ka kharcha ek hi baar, chahe woh sawaal kitne bhi paper me ho.
9. **Student ke request ke andar koi AI call nahi hoti.**
10. **Ek kharab file, ek ruka upload, ya AI ka ek ruka sawaal kisi doosre kaam ko nahi rokta.**
11. **Student ko dikhne se pehle har picture storage me saabit hoti hai.**
12. **Verified JEE Main PYQ nahi chhua jata.**
13. **`LiveSeries.js` nahi chhui jati.**
14. **Email, SMS ya bahar ki koi chetavni nahi.**
15. **Live ke database se kuch hard delete nahi hota.**
16. **Test ke alag database ek-ek karke chalte hain, saath me nahi.**
17. **Naye kaam me kisi exam ka naam nahi likha jata.** JEE, subject ke naam, 75 sawaal, 180 minute, tareekh: sab us exam aur us series ki setting se aata hai. Har pocket ki jaanch me ek doosra, banaya hua exam bhi chalta hai (Hissa 9).
18. **Upload kisi naye kaam ka intezaar nahi karta.** Jod aur AI baad me aayein, to bhi woh pehle se daale hue paper par chalte hain.

---

## 2. Aaj kya hai

Yeh code, preview ka database, is machine par rakhi do PDF aur live ke khule (bina sign-in wale) raaste padh kar likha hai. Live ka database maine nahi dekha.

**AITS**
- 50 din, 9 Dec 2026 se 27 Jan 2027. Har paper 75 sawaal: har subject me 20 MCQ + 5 numerical. 180 minute, +4 / −1.
- Live ke khule schedule me 50 din dikhte hain aur kisi din par paper taiyar nahi dikhta. Yeh aapki baat se milta hai ki paper abhi daale nahi gaye.
- AITS ke 50 paper wali PDF maine nahi dekhi.
- PDF se aaya AITS paper tab banta hai jab use din milta hai; tabhi uski pictures banti aur saabit hoti hain.

**AITS ke sawaalon wale chapter-wise books (Dekha)**
| Book | Kahan dekha | Page | Chapter | Sawaal | MCQ | Numerical | Chhape hue pate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chemistry | preview ke database me Draft, aur file | 2,527 | 24 | 1,250 | 1,000 | 250 | 1,250, sab alag. Mock 1 se 50, har mock ke 25. Number 51 se 75. |
| Maths | sirf file | 2,530 | 27 | 1,250 | 1,000 | 250 | 1,250, sab alag. Mock 1 se 50, har mock ke 25. Number 1 se 25. |
| Physics | nahi dekha | | | | | | (andaza: number 26 se 50) |

- Har sawaal ke upar teen line chhapi hain: "Question 1", "Source: AITS Mock 04 / Q68", "CH 01 / Mole Concept and Stoichiometry".
- Chemistry me har mock ke number 51 se 70 MCQ hain aur 71 se 75 numerical. Yeh AITS ka hi dhancha hai.
- Solution ke page par bhi wahi "Source" line chhapi hai.
- Solution likhe hue shabdon me hai: Concept, Given / required, kadam, Check, Answer, Insight, Useful shortcut, Common mistakes, Exam route. PDF machine yeh shabd upload ke samay rakh leti hai (Chemistry ke page 73 par dekha).
- Book ke pehle page par likha hai: "Same questions, answer keys and detailed solutions".
- Chemistry ke 24 chapter preview me Draft hain, sab "ready", koi rukavat nahi. Naye look me 1,250 me 1,250 sawaalon ka "sirf sawaal" wala tukda alag kata hua hai.

**Purana chapter-wise bank (preview, Library me)**
| Subject | Chapter test | Sawaal | MCQ | Numerical |
| --- | --- | --- | --- | --- |
| Physics | 29 | 1,450 | 1,218 | 232 |
| Chemistry | 23 | 1,150 | 1,029 | 121 |
| Maths | 26 | 1,300 | 1,151 | 149 |
| Kul | 78 | 3,900 | 3,398 | 502 |
- Yeh AITS wala bank nahi lagta. Ginti alag hai, aur iske Chemistry ke 1,150 sawaalon me se ek bhi naye Chemistry book ke 1,250 se nahi milta (sabse milta-julta bhi sirf 0.36; 1 = hu-ba-hu). Physics aur Maths ke shabd maine nahi milaye.
- Purane look me hain (sawaal aur options ek hi picture me).

**AI**
- App ke paas AI ki sirf ek key hai: Emergent ki universal key. Aapki apni OpenAI ya Claude key nahi lagi.
- Universal key ki model list maine aaj dekhi (sirf list maangi; kisi model ko koi sawaal nahi bheja): 100 naam. Unme `gpt-6-sol`, `gpt-5.6-sol`, `gpt-6-astra` aur `claude-opus-5-5` hain. `gpt-6.1-sol` aur `gpt-6.2-sol` nahi hain.
- App me AI ka ek purana raasta hai (model gpt-6-astra): ek saath 2 call, roz 300 call ki default seema, automatic solving 22 Oct se band. Naya kaam ise nahi chhuta.
- App ki AI library universal key ko Emergent ke raaste bhejti hai aur kisi bhi doosri key ko seedhe us company ke paas. Picture sab ke liye ek hi tarah bheji jati hai. Yeh maine library ka code padh kar kaha hai; chala kar nahi dekha.
- Ek paper ke sawaal ko doosre paper ke sawaal se jodne wali koi machine aaj nahi hai. Sirf ek section ke andar "yeh sawaal do baar hai" ki laal chetavni hai.

**Analysis**
- Chapter ka naam har sawaal par likha ho tabhi analysis chapter-wise banta hai. PDF machine se bane naye chapter test me yeh naam test par hota hai, sawaalon par nahi.
- Level students ke result se aata hai, jab 50 student woh sawaal kar chuke hon (65% ya zyada sahi: Easy; 35% se kam: Tough). Tab tak zyada-tar "Not rated" dikhta hai.
- Tag jaisi koi cheez analysis me aaj nahi hai.
- Bana hua analysis 14 din rakha rehta hai.

**Student ki taraf**
- Test shuru hote hi uske sawaal jam jate hain; baad me test badle to bhi us attempt ke sawaal nahi badalte.
- Rank sirf do tarah ke attempt par banta hai: normal practice aur AITS ka live attempt.
- Website ka Misfire live par chal raha hai (Hissa 14).

**JEE Main 2027** (NTA ke 24 Oct 2026 ke notice me padha)
- Session 1: 20, 21, 22, 23, 24 aur 28 Jan 2027. Paper 1 ki do shift: 9 se 12 aur 3 se 6. Paper 75 sawaal ka.
- In chhe dino me kaun se din Paper 1 ke hain, aur NTA paper aur key kab dega: us notice me nahi hai.
- Session 2 April me. Dates maine NTA ke kagaz me nahi padhi (web search: 2 se 7 April).

---

## 3. AI ka raasta: "AI ki seedhi"

### 3.1 Seedhi
Kaam hamesha sabse upar ke chalte hue paaydaan se hota hai. (**Tay**: kram aapka hai.)

| Paaydaan | Key | Model (isi kram me aazmaye jate hain) | Aaj |
| --- | --- | --- | --- |
| 1 | Aapki OpenAI key | `gpt-6.2-sol` | Key lagi nahi |
| 2 | Aapki OpenAI key | `gpt-6.1-sol` | Key lagi nahi |
| 3 | Aapki Anthropic (Claude) key | `claude-opus-5-5` | Key lagi nahi |
| 4 | Emergent ki universal key | `gpt-6.2-sol`, phir `gpt-6.1-sol`, phir `gpt-6-sol` | Key lagi hai. List me aaj sirf `gpt-6-sol` hai. |

- **Paaydaan 4 (Tay):** Emergent ka Sol. Wahan har baar pehle 6.2 dekha jata hai, phir 6.1, phir Sol 6. Jis din Emergent ki list me 6.1 ya 6.2 aayega, kaam apne aap us par chala jayega.
- **Aapki key ke bina bhi poora kaam chal sakta hai:** padhai Emergent ke `gpt-6-sol` se, doosri raay Emergent ke `claude-opus-5-5` se. Aapki apni key baad me kabhi bhi lag sakti hai; lagte hi kaam upar ke paaydaan par aa jata hai.
- Model ke naam aur kram screen par badle ja sakte hain. Naya model aaye to code nahi badalta. (**Tay**: key ek setting.)
- 6.2 ko 6.1 se upar maine rakha, kyunki woh naya hai. (**Maine rakha.**)

### 3.2 Seedhi se neeche kab utarta hai
- **Key lagi hi nahi:** woh paaydaan chhod diya jata hai.
- **Pakki dikkat** (key radd hui, balance khatam, model us key par nahi milta): woh paaydaan "band" ho jata hai aur kaam agle par chala jata hai. Screen par wajah likhi rehti hai. Har 15 minute me ek chhoti jaanch hoti hai; theek hote hi kaam wapas upar aa jata hai. "Abhi jaancho" button bhi hai.
- **Thodi der ki dikkat** (raftaar ki seema, timeout): usi paaydaan par ruk-ruk kar 3 baar koshish. Phir sirf us ek sawaal ke liye agla paaydaan.
- **Saare paaydaan band:** padhai rukti hai aur screen par saaf line aati hai. Kuch tootta nahi.
- Har record yaad rakhta hai ki use kis model ne padha. Screen par ginti dikhti hai (jaise "Sol 6.2: 3,600 · Sol 6: 150") aur ek button: "Jo neeche ke paaydaan se padhe gaye, unhe dobara padhao".

### 3.3 Doosri raay
- Har sawaal par pehle model ke baad ek doosri raay li jati hai, hamesha doosri company ke model se: pehla Sol ho to doosra Claude Opus 5.5; pehla Claude ho to doosra OpenAI ka.
- Claude ke liye: aapki Anthropic key ho to us se, warna universal key se.
- Sirf ek hi model chal raha ho to doosri raay usi model se, alag nayi call me; record me yeh likha rehta hai.
(**Maine rakha.**)

### 3.4 Key kaise di jati hai
- Key chat me kabhi nahi likhi jati. Jab aap dena chahein, main ek surakshit card kholta hoon; aap key wahin daalte hain.
- Preview aur live ke liye alag key rakhi ja sakti hai.
- Super Admin ki screen key kabhi nahi dikhati; sirf "lagi hai" ya "nahi lagi".

### 3.5 Screen "AI ki setting" (Super Admin)
- **Seedhi:** har paaydaan par key lagi hai ya nahi, model ke naam (badle ja sakte hain), aakhri jaanch ka nateeja, "Abhi jaancho".
- **Budget:** roz ki seema aur kul seema. Seema par kaam rukta hai, tootta nahi. "Roko" aur "Chalao".
- **Hisaab:** aaj aur kul call, token, har model ka alag, aur rate ke hisaab se andaze ka kharcha.
- **Raftaar:** ek saath kitne call chalein.

### 3.6 Kaam ki line
- Is kaam ka apna raasta, apni line aur apna budget hai. Purana AI raasta aur uski 300 ki seema jaise hain waise rehte hain.
- Har sawaal ek alag kaam hai. Server band ho kar chale to wahin se aage badhta hai.
- AI ka jawab ek tay dhanche me aata hai; dhancha galat ho to server use nahi maanta aur dobara poochta hai.
- Ek saath chalne wale call ki ginti seemit rehti hai, taaki exam ke samay server par bojh na pade.

### 3.7 Rate aur kharcha
Rate maine dono company ke apne page par padhe:
| Model | 10 lakh token andar | 10 lakh token bahar |
| --- | --- | --- |
| `gpt-6.2-sol` | $2 | $10 |
| `claude-opus-5-5` | $4 | $20 |
- Universal key ka rate, aur `gpt-6-sol` ka rate: **pata nahi**.
- OpenAI ke page ke mutabik "batch" raaste se rate aadha hota hai (jawab der se aata hai). Yeh pehle version me nahi banega; baad ka vikalp hai.

Mota andaza (naap nahi). AITS ke sawaal ka solution PDF me chhapa hai, isliye AI ko solution likhna nahi padta; woh sirf tag aur level deta hai (4.5). Maan lijiye us call me 2,500 token andar aur 1,000 bahar jaate hain, aur doosri raay me 2,500 andar aur 800 bahar.
| Kaam | Is version ka andaza | Pichhle version me |
| --- | --- | --- |
| Ek AITS sawaal (tag + level + doosri raay) | lagbhag $0.04 | lagbhag $0.10 |
| Poori AITS (3,750 sawaal) | $150 ke aas-paas | $400 ke aas-paas |
| Chapter-wise ke wahi sawaal | $0 | $0 (jahan jod ban jaye) |
| January ke asli paper (10 se 12 shift, dono roop) | $400 se $700 | wahi |
Asli paper me solution AI ko likhna padta hai, isliye woh andaza nahi badla. Asli token trial batayega; asli kharcha is se aadha ya dugna bhi nikal sakta hai.

### 3.8 Jo abhi pata nahi
- `gpt-6-sol` aur `claude-opus-5-5` is app me picture padh kar tay dhanche me jawab dete hain ya nahi: naam list me hain, chala kar nahi dekha.
- Aapki key ke saath Sol 6.2: code ke hisaab se chalega, chala kar nahi dekha. `gpt-6.1-sol` ka naam web search se mila; uska apna page maine nahi khola.
- Raftaar ki seema (aapke account ki, aur universal key ki).
- Do model ke diye tag kitne ek jaise aate hain.
- Emergent ki list me theek 100 naam aaye. Sol 6.1 aur 6.2 ka wahan na hona maine list dekh kar kaha hai; un naamon par call karke nahi.
Trial (pocket H0) yeh sab naapega.

---

## 4. Ek sawaal, ek record

AITS ka paper, chapter-wise test aur Matched: teeno ek hi sawaal ko dikhate hain. Isliye sawaal ka ek hi record hota hai, aur teeno jagah us record ki taraf ishara karti hain. Yaad database me rehti hai, kisi agent ke session me nahi.

### 4.1 Ek sawaal ka poora record
| Hissa | Kya rakha jata hai | Kahan se aata hai |
| --- | --- | --- |
| Pate | Sawaal kahan-kahan hai: AITS ka Mock aur number; AITS ka din; chapter test aur number. Asli paper ke sawaal ke liye: attempt, tareekh, shift aur source. | PDF aur Super Admin se, bina AI |
| Poora sawaal | Likhe hue shabd, saare options, aur sawaal ki picture | PDF machine se, bina AI |
| Jawab | Key ka jawab | PDF se, bina AI |
| Poora solution | Chhapa hua solution, likhe hue shabdon me aur picture me | PDF machine se, bina AI. Asli paper me AI likhta hai. |
| Chapter aur subject | Chapter ka naam aur number | Chapter-wise book se, bina AI |
| 10 tag | 4.2 ke das khaane | AI, ek baar |
| Level | Easy, Moderate ya Tough, ek line ki wajah ke saath. Yeh AI ka andaza hai. | AI, usi call me |
| Jaanch | Doosri raay mili ya nahi. Haalat: taiyar / aap dekhiye / padha nahi gaya. | AI |
| Hisaab | Kis model ne padha, kitne token, kab | Server |

Record apne shabd aur solution ki apni copy rakhta hai. Paper Library me jaye ya upload delete ho, record aur uska card bache rehte hain.

### 4.2 Ek sawaal ke 10 tag
Khaane sab sawaalon ke liye wahi hain, taaki "10 me 7" ka matlab hamesha ek rahe. (**Maine rakha**: khaano ke naam aapke shabdon se bane hain.)

| # | Khaana | Udaharan (dhalaan par block, pulley se juda doosra block) |
| --- | --- | --- |
| 1 | Chapter | Laws of Motion |
| 2 | Topic | Friction |
| 3 | Mukhya subtopic | Dhalaan par kinetic friction |
| 4 | Doosra idea (mixture ka doosra hissa) | Dhaage aur pulley se jude do block |
| 5 | Mukhya formula ya niyam | Har block par F = ma |
| 6 | Saath ka formula | f = μN, N = mg cosθ |
| 7 | Hal ka raasta | Dono block ka free-body diagram, do equation, saath hal |
| 8 | Nirnayak kadam | Friction ki disha tay karna |
| 9 | Kya maanga hai | Acceleration |
| 10 | Sawaal ki banavat | Dhalaan + pulley + latka hua block |

Yeh udaharan samjhane ke liye banaya hai; asli AITS ka sawaal nahi hai. Khaana 1 (chapter) AI nahi bharta; woh chapter-wise book se aata hai. Khaano ke naam exam ki setting hain (Hissa 9).

### 4.3 Tag ki list
- Chapter aur topic ki list pehle se banti hai: NTA ka syllabus aur hamare chapter ke naam.
- Baaki khaano ki list AI ki padhai ke saath badhti hai. Naya tag tabhi banta hai jab list ka koi tag fit na ho.
- Asli paper ko tag karte samay AI ko wahi list di jati hai jo AITS se bani hai, taaki ek hi baat ke do naam na ban jayein.
- Screen "Tag ki list": aap tag dekh sakte hain, naam badal sakte hain, aur do tag ko ek kar sakte hain. Aapki manzoori ke bina bhi kaam chalta rehta hai. (**Maine rakha.**)
- Har exam ki apni list hoti hai.

### 4.4 Sawaal ka pata
- AITS ke sawaal ka pata: series, Mock ka chhapa number, sawaal ka chhapa number. Jaise "Mock 04 / Q68".
- Yeh pata chapter-wise PDF ke har sawaal par chhapa hai, aur PDF machine use upload ke samay hi padh kar rakh leti hai (preview ke Draft me 1,250 me 1,250).
- Pata Mock ke chhape number se banta hai, din se nahi. Mock 04 ko aap Day 7 de dein, to bhi jod wahi rehta hai; Matched me din dikhta hai.
- Jod kaise banta aur jaancha jata hai: Hissa 5.

### 4.5 AI kya padhta hai, aur kab
| Sawaal | AI ko kya diya jata hai | AI kya deta hai | Kab |
| --- | --- | --- | --- |
| AITS aur chapter-wise ka sawaal (ek hi record) | Sawaal ki picture aur shabd, options, key, chhapa hua solution | 10 me se 9 tag aur level | Us record ki kisi bhi jagah ki pictures bante hi. Ek hi baar. |
| JEE Main ka asli paper | Sawaal ki picture aur shabd; key, agar hai | Poora solution, jawab, tag, level | Upload hote hi |
| Verified PYQ | Nahi chhua jata | | |

- **AI solution dobara nahi likhta.** Aapka solution PDF me hai; AI use padh kar sirf tag aur level nikalta hai. Isi se call chhoti hoti hai. (**Maine rakha.**)
- **"AI se key bhi jaanchwao"** ek alag switch hai, Off. On karne par AI har sawaal khud hal karke key se milata hai; call badi ho jati hai. (**Maine rakha.**)
- **Jod Draft me hi ban jata hai.** AI ki padhai tab chalti hai jab us sawaal ki pictures kahin ban chuki hon: Live chapter test me, ya din mile hue AITS paper me.
- **Dobara upload:** wahi sawaal wapas aaye to pate se usi record par baith jata hai; AI dobara nahi chalta. Shabd ya jawab badle hon to woh sawaal "badla hua" list me aata hai; aap chunte hain: purana card rakho, ya sirf ise dobara padhao.
- **Upload aur Live par asar nahi:** jod aur padhai paper ke banne ke baad, alag se chalte hain.

### 4.6 Screen "AI ki padhai" (Super Admin, AITS ke neeche)
- 50 mock ki list. Har mock: 75 me kitne taiyar, kitne "aap dekhiye", kitne ruke, aur kis model se padhe gaye.
- Upar: switch (On / Off), aaj ke call, "Roko", "Chalao", har mock par "Dobara padhao".
- **"Aap dekhiye" kab:** do model ke tag bahut alag hain; picture padhi nahi gayi; ya (switch On ho to) AI ka jawab key se nahi mila. Aap teen me se ek karte hain: sahi maan lo, tag khud chuno, ya dobara padhao.
- Ek sawaal ki galti us sawaal tak rehti hai; baaki 74 chalte rehte hain.

---

## 5. Teeno ka jod: AITS, chapter-wise aur Matched

### 5.1 Seedha jawab
Haan. AITS ek baar padhi jati hai aur chapter-wise bina AI ke jud jata hai. Is ke liye AI ki zaroorat nahi, aur zyada-tar search ki bhi nahi: aapki chapter-wise PDF har sawaal par khud bata rahi hai ki woh AITS ka kaun sa sawaal hai.

### 5.2 Teen chabi, isi kram me
1. **Chhapa hua pata.** Chapter-wise ka sawaal kehta hai "Source: AITS Mock 04 / Q68". AITS ke paper me Mock 04 ka sawaal 68 wahi record hai. Na AI, na khoj.
2. **Shabdon ki khoj** (jab pata chhapa na ho, ya AITS paper par Mock ka number na mile). Server sawaal ke likhe shabdon ko baaki sawaalon ke shabdon se milata hai. Bina AI ke, ek second se kam me.
3. **Aap.** Jo apne aap na jude, woh ek list me aata hai: dono pictures saath, ek tap se "wahi hai" ya "alag hai". "Khud jodo" bhi hai.

Jo kisi se na jude, uska apna naya record banta hai. Use AI tabhi padhta hai jab aap "Inhe bhi padhao" dabayein; dabane se pehle call ki ginti dikhti hai.

### 5.3 Jod ke taale
Koi bhi jod, pate wala bhi, tabhi pakka hota hai jab teeno baatein milen:
- dono MCQ hain, ya dono numerical;
- jawab ek hai. MCQ me sahi option ke shabd dekhe jate hain, akshar (A/B/C/D) nahi, taaki options ka kram badla ho to bhi chale;
- sawaal ke shabd kaafi milte hain.

Ek bhi taala na khule to jod nahi banta; sawaal aapki list me aata hai, wajah ke saath (jaise "pata wahi, jawab alag: C aur D"). Is se galat chhapa pata, ya ek jagah sudhara aur doosri jagah na sudhara sawaal, pakad me aa jata hai.

Shabdon ki khoj ke do aur taale: sabse milta sawaal doosre number wale se saaf aage ho, aur ek record par ek hi sawaal baithe.

### 5.4 Upload ka kram: koi bhi
| Aap kya pehle daalte hain | Kya hota hai |
| --- | --- |
| Chapter-wise pehle | Har sawaal ka record uske chhape pate par ban jata hai ("Mock 04 / Q68"), AITS paper ke bina bhi. Baad me AITS paper aaye to uska sawaal 68 usi record par baith jata hai. |
| AITS pehle | Record AITS ke sawaal se banta hai. Chapter-wise aaye to "Source" line se jud jata hai. |
| Dono saath | Wahi nateeja. |

- Har haal me AI ek hi baar chalta hai, us copy par jiski pictures pehle ban jayein.
- AI ke liye alag se kuch upload nahi karna. AITS ka paper AITS me, chapter-wise book chapter-wise me, jaise aaj.
- Jod aur AI ka code baad me live ho, to bhi pehle se daale paper par chalta hai: jo shabd aur pata chahiye, woh upload ke samay hi save ho jate hain.
- AITS ke paper ki taraf se pata banne ke liye paper par Mock ka number chahiye ("Mock 04" jaisa heading machine aaj bhi padhti hai) aur sawaal ka chhapa number. Yeh na mile to chabi 2 kaam karti hai.

### 5.5 Naap
**Chhapa hua pata (Dekha, asli PDF par)**
- Chemistry: 1,250 sawaal, 1,250 pate, sab alag. Maths: 1,250 sawaal, 1,250 pate, sab alag.
- Dono me Mock 1 se 50, har mock ke theek 25 sawaal. Maths me har mock ke number 1 se 25, ek-ek baar.
- AITS ke paper wali PDF maine nahi dekhi, isliye jod ka doosra sira abhi jaancha nahi gaya.

**Shabdon ki khoj (mera banaya hua naap, do asli PDF ka nahi)**
Maine har sawaal ki ek doosri copy banayi, uske akshar jaan-boojh kar bigade, aur sirf khoj se use wapas jodne diya (taalon ke saath):
| Kitne akshar bigade | Purana bank (3,900): apne aap jude | Galat jude | Naya Chemistry (1,250): apne aap jude | Galat jude |
| --- | --- | --- | --- | --- |
| 3% | 3,895 (99.9%) | 0 | 1,236 (98.9%) | 0 |
| 6% | 3,879 (99.5%) | 0 | 1,233 (98.6%) | 0 |
| 10% | 3,706 (95.0%) | 0 | 1,176 (94.1%) | 0 |
| 15% | 2,189 (56.1%) | 0 | 677 (54.2%) | 0 |
- Jo sawaal aapki list me gaye, unme lagbhag har baar sahi sawaal sabse upar tha (purane bank me 10% par 144 me 143). Zyada bigaad par kuch sawaal mile hi nahi: purane bank me 10% par 50 aur 15% par 658.
- 156 aise sawaal bhi daale jinka judwa bank me tha hi nahi: ek bhi galat nahi juda.
- Naye Chemistry me 9 sawaal (4 group, "Match List-I with List-II" wale) aise hain jinka shuru ka hissa bilkul ek jaisa hai aur list ya options alag. Mere naap me khoj inhe apne aap nahi jodti, aapki list me bhejti hai. Chhapa pata inhe bina uljhan ke jodta hai. Isi liye pata pehli chabi hai.

### 5.6 Kaun si cheez kahan se aati hai
| Cheez | Kahan se | AI ki call |
| --- | --- | --- |
| Jod (AITS ka sawaal = chapter-wise ka sawaal) | Chhapa pata, phir shabdon ki khoj | 0 |
| Chapter aur subject | Chapter-wise book ("CH 01 / ..." line aur chapter ka naam) | 0 |
| Jawab | Chhapi key | 0 |
| Poora solution | Chhapa solution | 0 |
| Level aur tag | AI ka card, ek baar; dono jagah wahi dikhta hai | AITS ke hisaab me gini ja chuki |
| Chapter-wise test ka alag kharcha | | 0 |

Is se ek purana baaki kaam bhi nikal jata hai: AITS ke analysis me asli chapter ke naam, AI ke bina.

### 5.7 Analysis me kya judega
| Jagah | Aaj | Jod aur card ke baad |
| --- | --- | --- |
| AITS: chapter | Sawaal par chapter nahi | Asli chapter, jod bante hi, AI ke bina |
| Qs by Qs (har sawaal) | Subject; chapter kabhi-kabhi; level zyada-tar "Not rated" | Chapter, topic, level, aur saare 10 tag |
| Difficulty | 50 student ke baad hi banta hai | Pehle din se AI ka andaza, "AI ka andaza" likh kar. 50 student ke baad students ka result uski jagah le leta hai (yeh niyam aaj bhi hai). |
| Kamzor hisse | Chapter-wise; chapter test me sab ek hi chapter ka hota hai, to yeh list kaam ki nahi | Topic aur subtopic-wise: jaise "Friction › dhalaan par: 3 galat" |

- Yeh AITS, chapter-wise aur Student Choice, teeno ke analysis me aata hai, kyunki teeno ka sawaal ek hi record hai.
- Student Choice ki list me level aur topic ka chhota nishaan bhi isi card se aa sakta hai; yeh app ke showcase ke hisaab se tay hoga.
- Matched me match hue AITS sawaal ke saath uske chapter test ka pata bhi dikh sakta hai.

### 5.8 Bina kuch tode
- Paper me kuch nahi likha jata. Record alag collection me rehta hai; analysis bante samay card upar se joda jata hai.
- Score, rank, sahi-galat: kuch nahi badalta. Sirf naam aur label judte hain.
- Rakha hua analysis card aane par ek baar dobara banta hai. Purane attempt ko bhi tag milte hain.
- Do switch, dono shuru me Off: "Sawaalon ko jodo" aur "Analysis me AI ke tag dikhao".

### 5.9 App
- Analysis ke jawab me naye khaane sirf judte hain (har sawaal ke tag, level kahan se aaya, kamzor topic ki list). Purane khaane wahi rehte hain.
- App team ke liye chhota packet banega. Unse ek sawaal poochna hai: purani app build anjaana "level kahan se aaya" kaise dikhati hai.

### 5.10 Screen "Jod" (Super Admin, AITS ke neeche)
- Upar ginti: kul record; AITS se jude; chapter-wise se jude; dono se jude; aapki list me; bina jod ke.
- Har mock ki row: 75 me kitne sawaal chapter-wise se jude.
- **Aapki list:** dono pictures saath, wajah, "Wahi hai" / "Alag hai". Tick lagakar kai ek saath.
- **"Badla hua":** dobara upload me jinke shabd ya jawab badle.
- **"Inhe bhi padhao":** bina jod wale sawaal, call ki ginti ke saath.
- Jod todna bhi ek tap hai; todne se card nahi mit-ta.

### 5.11 Jo pata nahi
- **AITS ke paper ki PDF:** uspar Mock ka number aur sawaal ka number kaise chhapa hai, aur uske shabd chapter-wise wale se kitne milte hain. Ek paper milte hi yeh dekh liya jayega.
- **Physics ki chapter-wise PDF:** nahi dekhi.
- **Live:** jo maine dekha woh preview aur is machine ki file hai. Live par aapne kya daala hai, maine nahi dekha.
- **Scan ki hui PDF:** usme likhe hue shabd nahi hote; na pata padha jata hai, na khoj chalti hai. Aise sawaal aapki list aur "Inhe bhi padhao" se hi judte hain.

---

## 6. Phase H: Matched

### 6.1 Poora raasta
1. Aap AITS ka paper waise hi upload karte hain jaise aaj.
2. Sawaal apne record se judte hain; jo record abhi padha nahi gaya, use AI ek baar padhta hai (Hissa 4 aur 5).
3. Exam ke din aap us shift ka yaad wala paper upload karte hain.
4. AI us paper ko padhta hai aur har sawaal ka detail solution likhta hai.
5. Milaan: asli paper ke har sawaal ke 10 tag AITS ke saare 3,750 sawaalon ke 10 tag se milaye jate hain.
6. Aap manzoori ki screen par pass karte hain (ek, kai, ya sab), phir "Publish".
7. 28 Jan se students ko Matched dikhta hai, website aur app dono par.
8. NTA ka paper aane par wahi kaam official paper par dobara; page "NTA wala" ban jata hai.
9. April me doosre attempt ke liye kadam 3 se 8 dobara.

### 6.2 Match ka niyam
- Asli paper ke sawaal ke 10 tag AITS ke sawaal ke 10 tag se khaana-dar-khaana milaye jate hain.
- **7 ya zyada khaane mile to match.** Seema screen par ek number hai: shuru me 7, aap 8 kar sakte hain. (**Tay.**)
- Students ko ginti dikhti hai (jaise "8 / 10") aur mile hue tag ke naam.
- Saare 50 din gine jate hain, shift ki tareekh chahe jo ho. 20 Jan ki shift ka match 27 Jan ke paper se nikle, tab bhi woh Matched me rehta hai, baaki match jaisa. (**Tay.**)
- Ek shift ka number = us shift ke 75 me se kitne sawaalon ka kam se kam ek manzoor match hai.

Teen udaharan, 4.2 wale AITS sawaal ke saamne:
| Asli paper ka sawaal | Mile hue khaane | Nateeja |
| --- | --- | --- |
| Wahi banavat, mass aur kon alag, tension poocha hai | 9 (sirf "kya maanga hai" alag) | Match |
| Usi chapter ka sawaal, par mode par ghoomti gaadi ka | 1 (sirf chapter) | Match nahi |
| Projectile: AITS me range ka formula, asli me sabse upar ke bindu par path ka radius | 3 (chapter, topic, banavat) | Match nahi |

### 6.3 Asli paper ka upload
- **Jagah:** AITS ki screen par, "AI ki padhai" ke neeche: "Asli paper".
- **Dhancha:** Attempt 1 (January) aur Attempt 2 (April). Uske andar tareekh. Har tareekh me Shift 1 aur Shift 2. Har shift me do khaane: "Yaad wala" aur "NTA wala". (**Tay.**)
- Tareekh ki rows NTA ki dates se pehle se bhari hongi; aap jod aur hata sakte hain.
- **File:** PDF (wahi PDF machine) ya likh kar. NTA wale ke saath answer key. Yaad wale me key zaroori nahi.
- Yeh paper students ko test ki tarah nahi dikhta.
- **Haalat ki line** har khaane par: Upload hua. Padha ja raha hai (75 me 40). Milaan ho raha hai. Aapki manzoori baaki (N sujhav). Publish ho gaya.
- **Pata nahi:** coaching ki yaad wali PDF hamari PDF machine me saaf kategi ya nahi. Jo sawaal na kate, use aap Fix me theek karenge.

### 6.4 Milaan kaise hota hai
Har asli sawaal ke liye:
1. **Ginti (bina AI):** server uske 10 tag usi subject ke saare AITS sawaalon ke tag se milata hai aur sabse zyada milne wale ummeedvar nikalta hai.
2. **Doosra jaal (AI):** us chapter ke AITS sawaalon ki ek-ek line ki list AI ko di jati hai; woh aise sawaal bhi pakadta hai jinka tag kisi aur shabd me likha gaya.
3. **Gehri jaanch (AI):** har ummeedvar ke saath dono ka poora sawaal aur poora solution AI ko diya jata hai. Woh das ke das khaane ek-ek karke jaanchta hai (matlab se, sirf shabd se nahi) aur har khaane ki wajah likhta hai. Aakhri ginti yahin se aati hai.
4. **Doosri raay:** jo jodi seema par ya upar hai, use doosra model alag se jaanchta hai. Dono maanein to "pakka"; ek hi maane to "shaq wala".

### 6.5 Aapki manzoori ki screen
Ek paper ke 75 sawaal ki list. Har row me:
- Baayin taraf asli sawaal; daayin taraf AITS ka sawaal (Day aur number).
- Ginti (jaise 8 / 10), mile aur na mile khaane, aur "pakka" ya "shaq wala".

Button:
- Har jodi par "Pass" aur "Hatao".
- Tick lagakar "Chune hue pass karo".
- Upar "Sab pass karo" aur "Sab pakke pass karo".
- Seema ka number (7 ya 8).
- Filter: subject, sirf pakke, sirf shaq wale, bina match wale sawaal.
- "Khud jodo": koi AITS sawaal khud jodna.
- "Publish" aur "Wapas lo". Bina "Publish" ke students ko kuch nahi dikhta.

### 6.6 Students ko kya dikhega
Yeh hissa app ki showcase files ke baad pakka hoga.

- **Card:** series ke aakhri din ke agle din, raat 12 baje (IST) se Home ka AITS card Matched ban jata hai. JEE Main ki series me yeh 28 Jan 2027 hai. Samay server tay karta hai, taaki website aur app saath badlein. Koi paper publish na hua ho to card "Matched jald aa raha hai" kehta hai. AITS ka practice archive series ke page par bana rehta hai.
- **Matched ka page:** attempt, phir tareekh aur shift. Har shift: 75 me kitne match, subject-wise ginti, aur paper "Yaad wala" hai ya "NTA wala". Sawaal-wise list: har sawaal ke saamne "Day 12 · Q14 · 8 / 10" aur mile hue tag.
- **Ek sawaal kholne par:** asli sawaal aur AITS ka sawaal saath-saath, dono ke solution, aur das khaano ki list.
- **Yaad wale paper me** students ko AI ka dobara likha sawaal dikhta hai, coaching ke page ki picture nahi. NTA wale me official picture. (**Maine rakha.**)
- **Server ke niyam:** jis AITS din ka paper abhi khula nahi, uska sawaal nahi dikhta. Student ke kholne par koi AI nahi chalta; publish ke samay jama hua nateeja diya jata hai.

API ka kachcha dhancha (app ki files ke baad pakka):
| Kaam | Raasta | Kya deta hai |
| --- | --- | --- |
| Card ki haalat | `GET /api/matched/summary` | `state` (off / soon / ready), `opens_at`, kul paper, kul match |
| Saari shift | `GET /api/matched` | attempt, tareekh, shift, source, 75 me kitne match, subject-wise ginti |
| Ek shift ki list | `GET /api/matched/papers/{paper_id}` | har sawaal: number, subject, match (Day, number, ginti, mile hue tag) |
| Ek sawaal | `GET /api/matched/papers/{paper_id}/questions/{n}` | dono sawaal, dono ke solution, das khaane |

### 6.7 Yaad wale se NTA wale tak
- NTA ka paper upload hote hi us shift ka poora kaam official sawaal aur key par dobara chalta hai.
- Jo match pehle manzoor tha aur dobara nikla, woh "pehle se manzoor" nishaan ke saath aata hai; ek button se pass.
- Publish karte hi us shift ka page "NTA wala" ban jata hai. Yaad wala nateeja record me rehta hai, students ko nahi dikhta.
- NTA baad me key badle ya sawaal hataye, to sirf un sawaalon ki jaanch dobara hoti hai.

### 6.8 Call ki ginti (design se nikala andaza, naapa nahi)
| Kaam | Call |
| --- | --- |
| Ek AITS sawaal (tag + level, phir doosri raay) | 2 |
| Poori AITS (3,750 sawaal) | 7,500 |
| Chapter-wise ke wahi sawaal | 0 |
| Ek asli paper ki padhai | 150 se 225 |
| Ek asli paper ka milaan | 250 se 350 |
| Ek shift, dono roop (yaad wala + NTA wala) | 800 se 1,150 |
| January ka session (10 se 12 shift maan kar) | 8,000 se 14,000 |

**"Perfect" ke baare me seedhi baat:** koi AI 100% sahi hone ka waada nahi kar sakta. Galat match students tak na pahunche, iske liye do model aur aapki manzoori hai. Chhoota hua match bach na jaye, iske liye do jaal aur "Khud jodo" hai.

### 6.9 Jo is phase me nahi hai
- Asli paper ko test ki tarah dene layak banana.
- AITS ke students ko AI ke likhe solution dikhana.
- Purana automatic AI solving dobara chalu karna.

---

## 7. Phase I: Student Choice

### 7.1 Aapne jo tay kiya
1. Abhi sirf JEE Main ka chapter-wise bank.
2. Student kisi bhi subject ke, kitne bhi chapter chunta hai.
3. Ginti do tarah se: har chapter ki alag, ya ek total.
4. Agle page par chapter-wise sawaalon ki list. List me sirf sawaal; options aur solution nahi.
5. Student khud tick kare, ya "Select Random" dabaye.
6. Samay: Maths ke 25 sawaal par 80 minute, Physics ke 25 par 60, Chemistry ke 25 par 40.
7. Rank nahi. Analysis normal mock jaisa.
8. Ek mock me zyada se zyada 75 sawaal. Aur koi seema nahi.

### 7.2 Student ka raasta
1. Exam ke page par naya card "Student Choice".
2. **Chapter chuno:** teeno subject ke chapter, har ek ke saamne kitne sawaal maujood hain.
3. **Ginti:** har chune chapter ke saamne ginti, ya upar ek total. Total chune chapter me barabar bat-ta hai; bacha hua pehle chapter ko jata hai.
4. **Sawaal chuno:** chapter-wise list, har sawaal ke saath tick. "Select Random" likhi ginti ke hisaab se chun leta hai; student uske baad bhi tick badal sakta hai. Upar ginti (jaise "32 / 75") aur banne wale mock ka samay.
5. **Mock banao:** naam, kul sawaal, subject-wise ginti aur samay. Phir wahi exam screen jo har mock me hai.
6. Submit ke baad result aur analysis. Mock "My Tests" me rehta hai.

Chhote niyam (**maine rakhe**): kisi chapter me maangi ginti se kam sawaal hon to jitne hain utne milte hain aur screen bata deti hai. 75 ke baad tick nahi lagta. Do baar button dabne se do mock nahi bante. Mock ka naam apne aap banta hai (jaise "Mera Mock 3 · 12 Dec").

### 7.3 Samay ka niyam
Har sawaal ka samay uske subject se: Maths 3.2 minute, Physics 2.4, Chemistry 1.6. Kul samay sab ka jod, upar ke poore minute tak. Ek hi ghadi poore mock ki. Marking chapter test jaisi: +4 / −1 / 0.

| Mock | Samay |
| --- | --- |
| Physics 25 + Chemistry 25 + Maths 25 | 60 + 40 + 80 = 180 minute |
| Physics 10 + Chemistry 5 + Maths 5 | 24 + 8 + 16 = 48 minute |
| Sirf Maths 10 | 32 minute |
| Chemistry 1 | 1.6, yani 2 minute |

### 7.4 Sawaal ki list: sirf sawaal ka tukda
- Naye look me har sawaal ka "sirf sawaal" wala tukda pehle se alag kata hota hai. List wahi tukda dikhati hai: ek sawaal, ek picture. Options ki koi picture list me nahi aati.
- **Dekha:** naye Chemistry book ke 1,250 me 1,250 sawaalon ka yeh tukda bana hua hai (1,000 MCQ aur 250 numerical), aur kisi bhi tukde me "Source" line nahi aati.
- List 10-10 sawaal ke tukdon me aati hai, jaise student neeche jata hai; pictures halki (WebP) aur usi tez raaste se jisse exam ki pictures aati hain.
- Server list me answer, options ya solution kabhi nahi bhejta.
- **Purane look wale test**, aur naye look ka woh sawaal jise aapne Fix me "poora ek picture" rakha hai: numerical sawaal ki picture me options hote hi nahi, to wahi picture dikhti hai. MCQ me likhe hue shabdon se sirf sawaal wala hissa dikhta hai. (**Maine rakha.**) Aapke naye books naye look me hain, to yeh raasta kam hi lagega.

### 7.5 Mock kaise banta hai
- Kram: exam ke subject ke kram me; subject ke andar chapter usi kram me jisme chune gaye.
- "Mock banao" par sirf chune hue sawaalon ki pehchaan rakhi jati hai. Poore sawaal tabhi jamte hain jab student test shuru karta hai, jaise har mock me.
- Student ke mock alag jagah rakhe jate hain, test ki list me nahi. Isliye woh Master ki list, Library, storage ki ginti aur rank ki machine me aate hi nahi.
- Har sawaal yaad rakhta hai ki woh kis chapter test se aaya, taaki "sawaal galat hai" ki report asli sawaal tak pahunche.
- Har sawaal par uske chapter ka naam rehta hai, taaki analysis chapter-wise bane.

### 7.6 Result aur analysis
- Wahi result aur wahi 8 hisson wala analysis jo normal mock me hai. AI ke tag aur level yahan bhi aate hain (Hissa 5).
- Rank, percentile, leaderboard aur compare nahi. Rank ki jagah screen kehti hai "Is test par Rank nahi banta".
- Galat aur chhode sawaal Misfire me jate hain; My Tests aur PDF report normal mock jaise.

### 7.7 Super Admin me jagah
Super Admin, exam ke andar, naya hissa "Student Choice":
- **On / Off.**
- **Pool ki list:** subject, chapter, kis test se, kitne sawaal, aur har chapter par "Shamil" ka switch. Pool me wahi chapter test aata hai jo students ke liye Live hai. Ek chapter ke do test hon to dono ke sawaal us ek chapter ke neeche judte hain.
- **Setting:** har subject ka samay per sawaal (JEE Main: 3.2 / 2.4 / 1.6), zyada se zyada kitne sawaal (JEE Main: 75).
- **Ginti:** aaj aur kul kitne mock bane, kitne students ne banaye, sabse zyada chune gaye chapter.

### 7.8 API ka kachcha dhancha (app ki files ke baad pakka)
| Kaam | Raasta | Kya deta ya leta hai |
| --- | --- | --- |
| Chapter aur niyam | `GET /api/choice/{exam}` | chalu hai ya nahi, max sawaal, samay per sawaal, marking, subject-wise chapter aur maujood sawaal |
| Ek chapter ke sawaal | `GET /api/choice/{exam}/chapters/{chapter_id}/questions?page=` | sawaal ki id, number, MCQ ya numerical, sawaal ke tukde ka link. Options, answer, solution nahi. |
| Random | `POST /api/choice/{exam}/random` | chapter aur ginti (ya ek total) leta hai; chune hue sawaal ki id deta hai |
| Mock banao | `POST /api/choice/{exam}/mocks` | sawaal ki id leta hai; mock ki id, naam, ginti aur samay deta hai |
| Mock shuru karo | `POST /api/choice/{exam}/mocks/{id}/start` | attempt deta hai; uske baad exam, result aur analysis ke wahi raaste jo aaj hain |
| Mere bane mock | `GET /api/choice/{exam}/mocks` | student ke bane mock |

---

## 8. Ek faisla: chhapi hui "Source" line

Jod isi line se banta hai. Par yahi line aaj students tak bhi pahunchti hai. Yeh maine naye Chemistry book ke 1,250 sawaalon ke kaat ke naap se dekha; browser me Live test khol kar nahi (preview me aisa koi Live test nahi hai).

| Jagah | "Source: AITS Mock 04 / Q68" dikhta hai? |
| --- | --- |
| Website par sawaal aur options ke tukde (naya look) | Nahi. 1,250 me 0. |
| Solution ki picture (submit ke baad) | Haan. 1,250 me 1,250. |
| Sawaal ki "poori picture" (sawaal + options ek saath; har sawaal ki banti hai) | Haan. 1,250 me 1,250. |
| Test ke data me chhupe hue likhe shabd | Haan. Screen par nahi dikhte; data me jate hain. Ek sawaal par function chala kar dekha. |

- App ke packet me sawaal dikhane ka sirf "poori picture" wala raasta likha hai. App kya dikhati hai, yeh main nahi dekh sakta; app ka code mere paas nahi hai.
- **Matlab:** chapter-wise karne wala student jaan sakta hai ki kaun sa sawaal AITS ke kis mock me, kis number par hai. Din kram se bhare hon to Mock 04 = Day 4.

Aapke teen raaste:
1. **Chhupao (mera sujhav).** Students ki har picture aur data se "Source" line hat-ti hai; server ke record me pata bana rehta hai, to jod par koi asar nahi. Yeh ek chhota pocket hai (S1), aur in books ko Live karne se pehle hona chahiye, kyunki pictures Live karte samay kat-ti hain.
2. **AITS khatm hone tak** in chapter-wise books ko Draft rakhiye.
3. **Jaisa hai waisa.** Aapka faisla; machine kuch nahi rokti.

---

## 9. Doosri app ke liye: universal

Maine yeh samjha: is code ki copy se ek aur app banegi ("Niche Life" likha aaya; shayad NEET Live). Theme, exam, paper aur content naye honge; machine wahi. Uske Super Admin me yeh saare feature pehle se hone chahiye, aur AI uske paper dobara padhega.

**Naya kaam (Hissa 3 se 8) aise banega**
1. **Kisi exam ka naam code me nahi.** JEE, Physics / Chemistry / Maths, 75 sawaal, 180 minute, 9 Dec, 28 Jan: yeh sab us exam aur us series ki setting se padhe jate hain.
2. **Har screen exam ke andar hai.** Super Admin › exam › AITS › "Jod", "AI ki padhai", "Asli paper". Super Admin › exam › "Student Choice". Naya exam banate hi wahi screens us exam me mil jati hain.
3. **Har exam ki apni setting:**
   - 10 khaano ke naam (jahan formula na ho, jaise Biology, wahan naam badal sakta hai) aur tag ki list;
   - match ki seema (7 ya 8);
   - asli paper ke dhanche ke naam (attempt, tareekh, shift; ya jo us exam me ho);
   - Student Choice: har subject ka samay per sawaal, zyada se zyada sawaal;
   - Matched kab khulta hai: us series ke aakhri din ke agle din.
4. **Pata:** "Source: ... Mock 04 / Q68" jaisi line kisi bhi series ke liye padhi jati hai. Line na ho to shabdon ki khoj.
5. **AI ki seedhi** app ki setting hai. Nayi app me apni key lagti hai.
6. **Content saath nahi jata.** Record, tag, jod aur match database me hain. Nayi app khaali shuru hoti hai aur apne paper khud padhti hai.
7. **Naam aur rang:** nayi screens app ki theme ke rang leti hain; app ka naam kisi screen ke shabdon me nahi likha jata.
8. **Jaanch:** har pocket ki jaanch me ek banaya hua doosra exam chalta hai (alag subject, alag ginti), taaki saabit ho ki kuch JEE se bandha nahi.

**Jo aaj pehle se universal hai (code me dekha)**
- Super Admin me kisi bhi naam aur subject ka naya exam ban sakta hai.
- Har exam ki apni All India Test Series ban sakti hai, apni dates aur samay ke saath.
- Mock type ka apna default samay aur marks.

**Jo purane code me JEE ya is app se bandha hai**
- JEE ki bani-banayi series (uska apna page, Home ka card): server ki 8 files aur website ki 12 files me.
- "JEE Main" ka naam: server ki 30 files aur website ki 21 files me. App ka naam: 14 aur 33 files me.
- AITS paper ki purani jaanch (75 sawaal ka JEE dhancha), aur rank / college predictor.

Yeh purana kaam hai; is guide ke pocket ise nahi chhute. Jab aap doosri app ka handoff maangenge, in sab jagah ki file-dar-file list us handoff me jayegi. Yeh ginti maine shabd khoj kar nikali hai, har file padh kar nahi.

---

## 10. Purana kaam kaise bacha rahega

| Purani cheez | Naya kaam iske saath kya karta hai |
| --- | --- |
| PDF upload aur kaatne ki machine | Kuch nahi. Jod aur AI bane hue sawaal ko sirf padhte hain. (Hissa 8 me "Chhupao" chunne par: students ki picture aur shabdon se ek line hat-ti hai.) |
| Live / Schedule / picture ka saboot | Kuch nahi. Asli paper ki nayi pictures par wahi niyam lagta hai. |
| Student ka test: shuru, answer save, submit, score | Matched: kuch nahi. Student Choice: shuru karne ka naya raasta alag file me; purana raasta nahi badalta. |
| Rank aur leaderboard | Kuch nahi. Student ke mock rank ki machine me jate hi nahi. |
| Analysis | Card upar se judta hai, switch ke peeche. Score aur rank wahi rehte hain. |
| Misfire, My Tests, PDF report | Student ke mock normal mock ki tarah aate hain. Pocket I0 me padh kar pakka hoga. |
| Purana AI raasta (band) | Band hi rehta hai; uski file nahi chhui jati. |
| "Yeh sawaal do baar hai" ki laal chetavni | Jaisi hai waisi. Jod apni alag file me hai. |
| Series ka page (`LiveSeries.js`) | Nahi chhua jata. |
| Home ka AITS card | Ek jagah: Matched chalu ho to naya card. |
| App ke purane raaste | Jaise hain waise. Sirf naye raaste aur naye khaane judte hain. |

**Purani files jinhe chhuna padega (yahi, aur kuch nahi):**
- `server.py`: naye raaste jodna.
- `route_contracts.py`: har naye raaste ki entry. Ek bhi entry chhoote to server start nahi hota; isliye har pocket ki jaanch me server ka start shamil hai.
- `db.py`: naye collection ke index.
- `jobs.py`: 15 minute wale round me ek line, jo ruke hue jod aur ruki hui padhai ko dobara uthati hai. Yeh line apne bachav ke andar hai; iski galti round ko nahi rokti.
- `MasterType.js`: AITS ki screen par naye panel.
- Analysis: server par do jagah (card ko jodna; rakhe hue analysis ko dobara banana) aur website par teen jagah (Qs by Qs, Difficulty, kamzor hisse).
- `HomeParts.js`: Matched ka card.
- `ExamHub.js`: Student Choice ka card.
- Sirf agar aap Hissa 8 me "Chhupao" chunen: `book_publish.py` me do jagah (solution aur poori picture ka upari kinara; students ko jaane wale shabd).

Student Choice ke liye code ki 14 files me 25 lines hain jo attempt ke test ki id se kaam karti hain. Pocket I0 unhe ek-ek padh kar likhega ki har ek student ke mock ke saath kya karegi. Us se pehle Student Choice ka koi code nahi.

---

## 11. Pocket: banane ka kram

Har pocket ke baad: nayi jaanch + wahi 26 purani suite + browser walk + testing agent. Har nayi jaanch me ek banaya hua doosra exam bhi. Phir aapko nateeja.

**Jod (bina AI)**
| Pocket | Kya banta hai | Jaanch |
| --- | --- | --- |
| S1 | Sirf agar aap "Chhupao" chunen: students ki picture aur data se "Source" line hatana | Naye Chemistry book par: 1,250 solution aur poori picture me line nahi; jod ka pata record me maujood |
| C1 | Sawaal ka record, pata, taale, shabdon ki khoj, aur "Jod" screen. AITS ke sawaalon ko chapter ka naam. | Chemistry aur Maths ki asli PDF; ek asli AITS paper (aap denge); bigadi hui copy; dobara upload |

**AI ki neenv**
| Pocket | Kya banta hai | Jaanch |
| --- | --- | --- |
| H0 | Trial, sirf preview me; app ka code nahi badalta; zyada se zyada 150 AI call. Seedhi ke har chalte paaydaan par ek call. 20 asli sawaal (chhape solution ke saath) dono model se. 10 banaye hue judwa aur ulte jode. | Naap: kaun sa paaydaan chalta hai, token, second, kharcha, dono model ke tag kitne mile |
| H1 | AI ka raasta: seedhi, key, budget, hisaab, aur "AI ki setting" screen. Abhi koi padhai nahi. | Nakli AI ke saath har tarah ki galti par sahi paaydaan; phir har asli paaydaan par ek call |
| H2 | Tag ki list (10 khaane) aur uski screen | Alag test database; browser |
| H3 | AI ki padhai: har record ke tag aur level, "AI ki padhai" screen | Nakli AI ke saath alag test database; phir asli AI par ek chhota paper; purani suite |
| C2 | Analysis me chapter, topic, level aur 10 tag (AITS, chapter-wise), switch ke peeche; app ka packet | Analysis ki purani suite + nayi; score aur rank wahi rehte hain |

**Matched**
| Pocket | Kya banta hai | Jaanch |
| --- | --- | --- |
| H4 | Asli paper ka upload (attempt, tareekh, shift, yaad wala / NTA wala) aur uski padhai | Ek purana paper upload karke |
| H5 | Milaan: ginti, doosra jaal, gehri jaanch, doosri raay | Banaye hue judwa aur ulte sawaal; ek poora paper |
| H6 | Manzoori ki screen | Browser, desktop aur 390 px |
| H7 | Student ka page, card ka badalna, API, pictures, app ka packet (app ki files ke baad) | Browser, API ke test, app ke namoone |
| H8 | NTA wale se badalna, April, key ka badalna | Alag test database |

**Student Choice**
| Pocket | Kya banta hai | Jaanch |
| --- | --- | --- |
| I0 | Sirf padhna: un 25 lines ki list, mock rakhne ka dhancha, aakaar ka naap. Koi code nahi. | Likhi hui list |
| I1 | Pool aur Super Admin ka hissa | Alag test database; browser |
| I2 | Chapter, sawaal ki list (sirf sawaal ka tukda), Random | API ke test: answer aur options kabhi nahi aate |
| I3 | Mock banana, shuru karna, result bina rank, analysis, Misfire, My Tests | Ek poora mock dekar; rank kahin nahi dikhta |
| I4 | Website ki screens app ke showcase jaisi; app ka packet | Browser, desktop aur 390 px |
| I5 | Kinare: chapter test Off ya delete, do baar dabana, sawaalon ki seema | Alag test database |

**Kram (mera sujhav):** S1 (agar chuna), C1, H0, H1, H2, H3, C2, phir H4 se H6, phir Student Choice, phir H7 aur H8. Aap badal sakte hain.

**Deploy ke mauke:** C1 ke baad (jod aur AITS me chapter ke naam); H3 aur C2 ke baad (AI ka card); H6 ke baad, 20 Jan se pehle; H7 ke baad, 28 Jan se pehle. Har baar tabhi, jab aap "deploy" likhen.

**Deploy ke baare me ek baat:** deploy poore code ka hota hai. Pehle deploy me preview ka baaki kaam bhi live jayega, yani kam se kam storage ka Packet E (bana aur jaancha hua; asli Supabase par abhi nahi chalaya).

---

## 12. Dates

| Tareekh | Kya |
| --- | --- |
| 26 Nov 2026 | Aaj. Yeh guide. |
| 9 Dec 2026 | AITS Day 1 |
| 20 se 24 Jan 2027 | JEE Main Session 1 (AITS ke Day 43 se 47 ke saath) |
| 27 Jan 2027 | AITS Day 50 |
| 28 Jan 2027, raat 12 baje IST | Card Matched banta hai; usi din Session 1 ka aakhri din |
| Session ke baad (tareekh NTA tay karta hai) | NTA ka paper aur key |
| April 2027 | Session 2 |

- 9 Dec ke liye AI ya jod ka live hona zaroori nahi: AITS aaj ki machine par chalti hai, aur jod aur padhai baad me pehle se daale paper par chal jate hain.
- AI ka card Matched ke liye chahiye, yani 20 Jan se pehle.
- Main kisi tareekh ka waada nahi kar sakta; har pocket jaanch ke baad hi aage badhta hai.

---

## 13. Khatre

1. **AI figure galat padhe.** Tag galat nikalte hain. Bachav: chhapa hua solution saath diya jata hai, doosri company ka model, "aap dekhiye", aapki manzoori, "Khud jodo".
2. **Ek hi baat ke do tag.** Ginti kam aati hai. Bachav: tay list, asli paper ko wahi list dena, gehri jaanch matlab se, do tag ko ek karne ka button.
3. **Beech me model badalna.** Aadhi AITS ek model se aur aadhi doosre se padhi jaye to tag ka andaz thoda alag ho sakta hai. Bachav: har record par model ka naam, ginti, aur "dobara padhao" ka button.
4. **Pata chhapa na ho, ya galat chhapa ho.** Bachav: taale (type, jawab, shabd), shabdon ki khoj, aapki list.
5. **AITS ke paper ki PDF maine nahi dekhi.** Uspar Mock ya sawaal ka number alag tarah chhapa ho to pata us taraf se nahi banega; tab shabdon ki khoj jodegi. Ek paper dekhte hi yeh saaf ho jayega.
6. **Yaad wala paper adhoora ya galat.** Bachav: page par "Yaad wala" likha rehta hai; NTA wale se sab dobara.
7. **Balance ya seema beech me khatam.** Padhai rukti hai ya agle paaydaan par jati hai. Bachav: screen par saaf line.
8. **Samay.** 9 Dec, 20 Jan aur 28 Jan pakki tareekh hain.
9. **28 Jan ki bheed.** Bachav: jama hua nateeja, koi AI nahi, pictures tez raaste se.
10. **Student Choice: database ka aakaar.** Preview ke naap se 75 sawaal ka jama hua mock lagbhag 165 KB (dabane se pehle). Bachav: sawaal tabhi jamte hain jab test shuru hota hai. Asli aakaar I0 me napega.
11. **Student Choice: chapter test delete hona.** Us test ki pictures ke record chale jate hain. Aise mock ka sirf score bachna chahiye, jaise aaj delete hue test ke saath hota hai. I5 me banega aur jaancha jayega.
12. **Storage ka Packet F baaki hai.** Supabase band ho to naya paper tab tak nahi banta jab tak woh laute. Paper pehle se daalne par yeh khatra chhota hai.
13. **AITS ke sawaal chapter-wise me pehle se khule hain.** Jis student ne chapter-wise kiya hai, woh AITS ka sawaal pehle dekh chuka hoga, aur rank me aage rahega. "Source" line use yeh bhi bata deti hai ki sawaal kis mock ka hai (Hissa 8). Yeh aapka faisla hai. Jod banne ke baad yeh mumkin hoga ki jis sawaal ka AITS din abhi nahi aaya, woh chapter-wise me na dikhe; yeh plan me nahi hai jab tak aap na kahen.

---

## 14. Saara baaki kaam

Yeh list memory ke note se bani hai. Kuch line hafton purani hain aur har ek ko maine aaj dobara nahi jaancha. Jo aaj dekha, uske saath "aaj dekha" likha hai.

**A. Is guide ka kaam:** Hissa 3 se 9 (AI ka raasta, ek sawaal ek record, jod, Matched, Student Choice, "Source" line, universal).

**B. Storage**
- Packet E deploy nahi hua (aaj dekha: uska "Dobara chalao" wala raasta live par nahi hai).
- Packet E ka bacha: "Pictures ki poori jaanch" button; is hisse ko ek baar asli Supabase par chalana; likhe hue Draft ko Live karte samay wajah row par rakhna (aapka faisla).
- Purane darwazon (paper import, chapter book, book ka "resume mock", automatic import) par mana to hota hai, par row ki line aur "Dobara chalao" nahi hai.
- Packet F: Supabase band ho to poora paper Emergent me save hokar Live ho.
- Packet G: baad me aapke button se us paper ko Supabase me lana.
- Purani Emergent pictures ki copy: aapke kehne par sirf backlog.

**C. PDF machine**
- Phase 2: chipke hue options; options ke bagal me diagram; agle page par jata option; do column wale page; scan ki hui PDF bina AI ke; saade shabd wale options asli text me; purane Draft ke liye "dobara padho"; solution ki pictures ki safai; PYQ naye look me; app guide aur PDF format guide.
- Phase 3: question bank; badi book ki jaldi jaanch.
- Jin AITS books me numerical sawaalon ke upar "Numerical" ya "Section B" ka heading nahi hota, unka har numerical sawaal rukta hai aur ek-ek karke theek karna padta hai. Ek saath confirm karne ka button nahi bana. AITS ke upload me yeh aapko lag sakta hai.
- Jo paper Live hai ya jise din mil chuka hai, uske sawaal ko badalne ka raasta ("sudhra hua version") nahi bana.
- Phone par chaudi picture chhoti shuru hoti hai (zoom ka button hai).

**D. Analysis**
- Mock se mock ka trend (pichhle 5 mock).
- Master me level aur chapter haath se rakhna.
- Purane AI solution ke saath save hone wala pakka "Moderate" level hatana.
- Owner ke liye paper report (kaun sa sawaal sabse zyada galat hua); agle mock ka target score.
- AITS ke sawaalon par chapter ke naam: ab pocket C1 se, AI ke bina.

**E. Super Admin**
- Agle saal ki series aur purani ka archive.
- PDF mock ke andar likha hua sawaal jodna ya badalna; mock ki copy; mock ko doosre exam me le jana.
- Khoj aur filter; kheench kar kram badalna.
- Do bhasha wali PDF; har exam ka alag reviewer; har mock ki report; badlav ka itihaas.
- Akela test Library me bhejne par uski PDF Library me nahi jati.

**F. Bada load aur server**
- 1 se 2 lakh students ek saath ka load test.
- Server ke aakaar ki arzi (docs/SERVER_SIZE_REQUEST.md) platform support ko.
- CDN: pictures ke liye CDN ka pata abhi save nahi hai.
- Live par kabhi-kabhi 30 second ka atakna (Cloudflare 520): platform ki taraf ka masla, khula hai.
- Bahut bheed me intezaar ki line; class ke data ka tez banna; sign-in ki raftaar ki seema.

**G. App team**
- 18 Nov aur 19 Nov ke packet se build.
- Series ke card ke liye `GET /api/series`; pictures ka naya raasta.
- Naye packet: Matched, Student Choice, analysis ke tag.
- App sawaal ki "poori picture" dikhati hai ya tukde (Hissa 8).
- Misfire: neeche dekhiye.

**H. Aapki taraf ruke kaam**
- Rapid Fire ka Play Store link.
- Server ke aakaar ki arzi bhejna; CDN ka pata.
- Preview ke do purane test database hatane ki haan.
- AITS hub ka naya design (23 Nov): memory ke note me yeh "aapke dekhne ke liye" likha tha. Uske baad deploy ho chuke hain; woh live par hai ya nahi, maine nahi jaancha.
- CEO dashboard ke "enhancer" ka naam.
- Naya content: BITSAT ke mock, chapter-wise aur PYQ.
- Live par ek baar dekhna ki sign-in ke baad Mission aur Dream khulte hain.

**I. Safai**
- Ek purana test (`master_jee_series_iso181`) galat dates maangta hai; test ko theek karna hai, app ko nahi.
- Kuch purani suite ki ummeed purani ho chuki hai.
- Kuch chhoti dikhne wali cheezein (jaise upar aane wala note breadcrumb ko dhakta hai).

**J. Doosri app**
- Handoff ke samay: purane code me JEE aur app ke naam se bandhi jagah ki file-dar-file list (Hissa 9).

**Band**
- Subject Rank aur Seekh Reminder: aapke kehne par nahi banenge.
- Galti Notebook: "Misfire" naam se bana hua hai.

**Misfire: website aur app juda hai ya nahi**
- Website ka Misfire live par chal raha hai. Maine live par uska raasta (`/api/my/misfire`) dekha: woh maujood hai aur sign-in maangta hai.
- App ka Misfire usi raaste se data leta hai ya apna alag rakhta hai, yeh main yahan se nahi dekh sakta: app ka code mere paas nahi hai.
- Ek minute ki jaanch: website par ek chhota test dekar ek sawaal galat kijiye, phir usi account se app ka Misfire kholiye. Wahi sawaal dikhe to dono jude hain.

---

## 15. App se milaan

Website aur app ek jaisi rahein, iske liye mujhe yeh chahiye (H7 aur I4 se pehle; baaki pocket inke bina chal sakte hain):
1. Dono showcase ki har screen ka screenshot.
2. Un screens ki files, khaaskar unme bhara nakli data.
3. App ne koi API ka raasta ya khaane ka naam pehle se maan liya ho to woh.
4. Har screen ki khaali, loading aur galti wali haalat, aur screen par likhe shabd.

Uske baad: har screen ki har cheez ke saamne likha jayega ki server ka kaun sa khaana use bharta hai; jahan showcase is guide se alag hai, uski list aapko milegi; ek hi API tay hogi; app team ke liye packet aur namoone ke jawab banenge.

---

## 16. Aapse kya chahiye

1. Is guide ko haan, ya jo badalna hai.
2. "Source" line ka faisla (Hissa 8): chhupao, AITS tak Draft, ya jaisa hai waisa.
3. AITS ke ek paper ki PDF. Chapter-wise PDF ab nahi chahiye (Chemistry aur Maths mere paas hain); Physics ki ho to de dijiye.
4. Trial (H0) ke liye zyada se zyada 150 AI call ki ijazat. Yeh ab aapki key ke bina, Emergent ki key par ho sakta hai.
5. Doosri app ka sahi naam aur exam ("Niche Life" likha aaya).
6. App ki dono showcase ke screenshot aur files.
7. Agar ho: pichhle saal ka ek yaad wala paper (PDF).
8. Aapki OpenAI ya Claude key: zaroori nahi. Jab dena chahein, bata dijiye; main surakshit card kholunga. Chat me key mat likhiye.

Jo faisle maine khud liye hain, woh guide me "Maine rakha" ke saath likhe hain: 6.2 ko 6.1 se upar rakhna, doosri raay doosri company se, 10 khaano ke naam, tag ki list bina manzoori ke chalna, AITS ke sawaal par AI se solution dobara na likhwana, "AI se key bhi jaanchwao" ka Off rehna, jod ke taale, yaad wale paper me likha hua sawaal dikhana, purane look ke MCQ me likha hua sawaal, ek hi ghadi, mock ka apne aap bana naam, pocket ka kram.
