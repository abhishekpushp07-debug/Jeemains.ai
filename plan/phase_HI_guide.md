# Final guide: Phase H "Matched" aur Phase I "Student Choice"

**Haalat (26 Nov 2026, doosra version):** sirf guide. Koi code nahi likha gaya, kuch deploy nahi hua.
Yeh version aapke 26 Nov ke saare faisle leta hai. App ki showcase files aane par sirf student wali screen aur API ke hisse (3.10, 4.8) dobara likhe jayenge; Super Admin wale pocket unka intezaar nahi karte.

Har baat ke saath likha hai ki woh kis tarah ki hai:
- **Tay**: aapne keh diya hai.
- **Maine rakha**: faisla maine liya, taaki aapko har chhoti baat na batani pade. Aap badal sakte hain.
- **Pata nahi**: abhi dekha ya naapa nahi gaya.

Naam ka dhyan: "Phase H" aur "Phase I" aapke product ke phase hain. Storage wale plan (plan/plan.md) ke "H" aur "I" hisson se inka koi rishta nahi.

---

## 0. Is version me kya badla

| Aapne kaha | Guide me ab |
| --- | --- |
| Har AITS sawaal ke kam se kam 10 tag; asli paper ke 10 tag se milaao; 7 ya 8 mile to match | Match ka niyam ab yahi hai (3.2, 3.3). Seema ek number hai: shuru me 7, aap 8 kar sakte hain. |
| 20 Jan ki shift ka match 27 Jan ke AITS paper se nikle, tab bhi Matched me rahega | Tay. Saare 50 din gine jate hain aur ek jaise dikhte hain. Koi alag line nahi. |
| Subject Rank aur Seekh Reminder nahi banana | Dono hata diye. Phase J band (Hissa 9). |
| App me Misfire dikh raha hai; dekho juda hai ya nahi | Jawab Hissa 9 me. Chhota jawab: website ka Misfire live hai; app usi se juda hai ya nahi, yahan se pakka nahi ho saka. |
| AITS ke paper tabhi daalunga jab Super Admin me AI ka section ban jaye; AI abhi se sab padhe, tag aur level tay kare | AI ki padhai ab sabse pehla pocket hai (H0 se H2), baaki sab uske baad. Level bhi AI ke record me hai. |
| Student Choice ki list me sirf sawaal; options nahi (list lambi aur bhaari ho jayegi) | List me sirf sawaal ka kata hua tukda aata hai, jo naye look me pehle se alag bana hota hai. Ek sawaal, ek picture (4.4). |
| Ek cheez banate hue doosri na toote; chhote pocket; jo bana hai uska dhyan | Hissa 1 (niyam), Hissa 5 (purana kaam kaise bacha rahega), Hissa 6 (pocket). |

---

## 1. Sunehre niyam

1. **Ek cheez banate hue doosri nahi tootti.** Naya kaam nayi files aur naye collection me rehta hai. Purani files sirf ginti ki jagah par chhui jati hain; woh jagah Hissa 5 me likhi hain.
2. **Har nayi cheez ka apna switch hota hai, shuru me Off.** Off rehne par app bilkul aaj jaisi chalti hai.
3. **Chhote pocket.** Ek pocket, ek kaam. Har pocket ke baad jaanch, phir aapko nateeja, phir agla.
4. **Har pocket ki jaanch me purani jaanch dobara chalti hai:** wahi 26 purani suite aur browser walk, phir testing agent ki alag jaanch.
5. **Jab tak test ka saboot na ho, "ho gaya" nahi kaha jata.**
6. **Live par kuch tabhi jata hai jab aap "deploy" likhen.**
7. **AI kisi paper, answer key ya student ke score ko nahi badalta.** Woh sirf padhta hai aur apna record alag rakhta hai.
8. **Student ke request ke andar koi AI call nahi hoti.**
9. **Ek kharab file, ek ruka upload, ya AI ka ek ruka sawaal kisi doosre kaam ko nahi rokta.**
10. **Student ko dikhne se pehle har picture storage me saabit hoti hai.**
11. **Verified JEE Main PYQ nahi chhua jata.**
12. **`LiveSeries.js` nahi chhui jati.**
13. **Email, SMS ya bahar ki koi chetavni nahi.**
14. **Live ke database se kuch hard delete nahi hota.**
15. **Test ke alag database ek-ek karke chalte hain, saath me nahi.**

---

## 2. Aaj kya hai (code aur preview ka database padh kar)

Live ka database maine nahi dekha. Jahan "preview" likha hai, woh sirf preview ka sach hai.

**AITS**
- 50 din, 9 Dec 2026 se 27 Jan 2027. Har paper 75 sawaal, 180 minute, +4 / −1.
- Preview me ek bhi AITS paper nahi hai, isliye asli AITS sawaal maine nahi dekha.
- Code ke mutabik PDF se aaya AITS paper tab banta hai jab use din milta hai; tabhi uski pictures banti aur saabit hoti hain.

**Chapter-wise bank (JEE Main, preview)**
- 78 chapter test × 50 = 3,900 sawaal (Physics 29 chapter, Chemistry 23, Maths 26). 3,398 MCQ, 502 numerical.
- Preview ke yeh 78 test purane look me hain: sawaal aur options ek hi picture me. Naye look (sawaal ka tukda alag, har option alag) wala ek bhi test preview me nahi.
- Naya look banane wali PDF machine code me hai: usme har sawaal ka "sirf sawaal" wala tukda alag kat-ta hai. Live ka bank kis look me hai, **pata nahi**.

**AI**
- App me AI ka ek purana raasta hai (model gpt-6-astra, universal key se): ek saath 2 call, roz 300 call ki default seema. Automatic solving 22 Oct se band hai. Phase H ise nahi chhuta.
- App ke paas AI ki sirf universal key hai. Us se OpenAI aur Claude dono chalte hain.
- Sawaalon ko matlab se milane wali koi machine aaj nahi hai.

**Student ki taraf**
- Test shuru hote hi uske sawaal jam jate hain; baad me test badle to bhi us attempt ke sawaal nahi badalte.
- Rank sirf do tarah ke attempt par banta hai: normal practice aur AITS ka live attempt.
- Website ka Misfire live par chal raha hai (Hissa 9).

**JEE Main 2027** (NTA ke 24 Oct 2026 ke notice me padha)
- Session 1: 20, 21, 22, 23, 24 aur 28 Jan 2027. Paper 1 ki do shift: 9 se 12 aur 3 se 6. Paper 75 sawaal ka.
- In chhe dino me kaun se din Paper 1 ke hain, aur NTA paper aur key kab dega: us notice me nahi hai.
- Session 2 April me. Dates maine NTA ke kagaz me nahi padhi (web search: 2 se 7 April).

---

## 3. Phase H: Matched

### 3.1 Poora raasta
1. Aap AITS ka paper waise hi upload karte hain jaise aaj.
2. Paper bante hi AI use padhta hai. Har sawaal ka poora record banta hai: poora sawaal, poora solution, 10 tag aur level.
3. Exam ke din aap us shift ka yaad wala paper upload karte hain (AITS ke neeche bani jagah me).
4. AI us paper ko bhi waise hi padhta hai aur har sawaal ka detail solution likhta hai.
5. Milaan: asli paper ke har sawaal ke 10 tag AITS ke saare 3,750 sawaalon ke 10 tag se milaye jate hain.
6. Aap manzoori ki screen par pass karte hain (ek, kai, ya sab), phir "Publish".
7. 28 Jan se students ko Matched dikhta hai, website aur app dono par.
8. NTA ka paper aane par wahi kaam official paper par dobara; page "NTA wala" ban jata hai.
9. April me doosre attempt ke liye kadam 3 se 8 dobara.

### 3.2 Ek sawaal ke 10 tag
Har sawaal ko theek 10 khaano me tag milte hain. Khaane sab sawaalon ke liye wahi hain, taaki "10 me 7" ka matlab hamesha ek rahe. (**Maine rakha**: yeh 10 khaane aapke shabdon se bane hain: chapter, topic, subtopic ka mixture, aatma, formula, solution ka raasta.)

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

Yeh udaharan samjhane ke liye banaya hai; asli AITS ka sawaal nahi hai.

### 3.3 Match ka niyam
- Asli paper ke sawaal ke 10 tag AITS ke sawaal ke 10 tag se khaana-dar-khaana milaye jate hain.
- **7 ya zyada khaane mile to match.** Yeh seema screen par ek number hai: shuru me 7, aap 8 kar sakte hain. (**Tay**: 7 ya 8.)
- Students ko ginti dikhti hai (jaise "8 / 10") aur mile hue tag ke naam: chapter, topic, subtopic, formula wagairah.
- Saare 50 din gine jate hain, shift ki tareekh chahe jo ho. Har match ke saath AITS ka din aur sawaal number dikhta hai (jaise "Day 50 · Q14").
- Ek shift ka number = us shift ke 75 me se kitne sawaalon ka kam se kam ek manzoor match hai.

Teen udaharan, upar wale AITS sawaal ke saamne:
| Asli paper ka sawaal | Mile hue khaane | Nateeja |
| --- | --- | --- |
| Wahi banavat, mass aur kon alag, tension poocha hai | 9 (sirf "kya maanga hai" alag) | Match |
| Usi chapter ka sawaal, par mode par ghoomti gaadi ka | 1 (sirf chapter) | Match nahi |
| Projectile: AITS me range ka formula, asli me sabse upar ke bindu par path ka radius | 3 (chapter, topic, banavat) | Match nahi |

### 3.4 AI ki yaad: ek sawaal ka poora record
Sirf tag nahi: poora sawaal aur poora solution rakha jata hai. Yaad database me rehti hai, kisi agent ke session me nahi.

| Hissa | Kya rakha jata hai |
| --- | --- |
| Pehchaan | AITS ka din, tareekh aur sawaal number; ya asli paper ka attempt, tareekh, shift aur source. Subject; MCQ ya numerical. |
| Poora sawaal | Picture se padha hua saaf likha sawaal, saare options, aur figure ka shabdon me bayan. Asli picture bhi judi rehti hai. |
| Jawab | Key ka jawab, AI ka apna jawab, aur dono mile ya nahi. |
| Poora solution | Book ka solution (agar paper me hai) likhe hue roop me, aur AI ka kadam-dar-kadam solution. |
| 10 tag | 3.2 ke das khaane. |
| Level | Easy, Moderate ya Tough, ek line ki wajah ke saath. Yeh AI ka andaza hai. |
| Jaanch | Doosre model ki raay mili ya nahi. Haalat: taiyar / aap dekhiye / padha nahi gaya. |
| Hisaab | Kaun sa model, kitne token, kab. |

- Record sawaal ke content ki fingerprint se juda hai. Sawaal badle to sirf wahi dobara padha jata hai; ek hi sawaal par do baar kharcha nahi hota.
- Paper me solution chhapa hai ya sirf key, yeh machine upload se khud jaan leti hai. Solution na ho to AI apna likhta hai.

### 3.5 Tag ki list
"Wahi tag" tabhi gina ja sakta hai jab dono sawaal ek hi list se tag hon. Isliye AI apne man se naye-naye naam nahi likhta.
- Chapter aur topic ki list pehle se banti hai: NTA ka syllabus aur hamare 78 chapter ke naam.
- Baaki khaano (subtopic, formula, raasta, nirnayak kadam, kya maanga, banavat) ki list AI ki padhai ke saath badhti hai. Naya tag tabhi banta hai jab list ka koi tag fit na ho.
- Asli paper ko tag karte samay AI ko wahi list di jati hai jo AITS se bani hai, taaki ek hi baat ke do naam na ban jayein.
- Screen "Tag ki list": aap tag dekh sakte hain, naam badal sakte hain, aur do tag ko ek kar sakte hain. Aapki manzoori ke bina bhi kaam chalta rehta hai. (**Maine rakha.**)

### 3.6 AITS ki padhai (Super Admin ka naya section)
- **Jagah:** Super Admin, JEE Main, All India Test Series, dino ki list ke neeche: "AI ki padhai".
- **Kab chalti hai:** paper ko din milte hi woh ban jata hai, aur bante hi padhai peeche line me lag jati hai, chahe woh din 40 din door ho. Isliye aap saare paper pehle se daal dein to sab abhi padh liye jate hain.
- **Jo Draft bina din ke hai, woh nahi padha jata**, kyunki uski pictures tab tak bani nahi hoti. Yani AI se padhwane ke liye har paper ko uska din dena hoga.
- **Upload aur Live par asar nahi:** padhai paper ke banne ke baad, alag se chalti hai. PDF machine, picture ka saboot aur student ka test iska intezaar nahi karte.
- **Screen par:** 50 din ki list. Har din: 75 me kitne taiyar, kitne "aap dekhiye", kitne ruke. Upar: switch (On / Off), aaj ke call, kul call, roz ki seema, "Roko", "Chalao", aur har din par "Dobara padhao".
- **"Aap dekhiye" kab:** AI ka jawab key se nahi mila; do model ke tag bahut alag hain; ya picture padhi nahi gayi. Aap teen me se ek karte hain: sahi maan lo, tag khud chuno, ya dobara padhao.
- **Ek sawaal ki galti us sawaal tak:** baaki 74 chalte rehte hain.
- **Section live hone se pehle paper daalna pade to:** daal dijiye. Section aate hi pichhle saare paper ek saath padhe jate hain; kuch khota nahi. Day 1 ko is section ka bandhak mat banaiye.

### 3.7 Asli paper ka upload
- **Jagah:** usi AITS screen par, "AI ki padhai" ke neeche: "JEE Main 2027 ke asli paper".
- **Dhancha:** Attempt 1 (January) aur Attempt 2 (April). Uske andar tareekh. Har tareekh me Shift 1 aur Shift 2. Har shift me do khaane: "Yaad wala" aur "NTA wala". (**Tay.**)
- Tareekh ki rows NTA ki dates se pehle se bhari hongi; aap jod aur hata sakte hain.
- **File:** PDF (wahi PDF machine) ya likh kar. NTA wale ke saath answer key. Yaad wale me key zaroori nahi.
- Yeh paper students ko test ki tarah nahi dikhta.
- **Haalat ki line** har khaane par: Upload hua. Padha ja raha hai (75 me 40). Milaan ho raha hai. Aapki manzoori baaki (N sujhav). Publish ho gaya.
- **Pata nahi:** coaching ki yaad wali PDF hamari PDF machine me saaf kategi ya nahi. Jo sawaal na kate, use aap Fix me theek karenge.

### 3.8 Milaan kaise hota hai
Har asli sawaal ke liye:
1. **Ginti (bina AI):** server uske 10 tag usi subject ke saare AITS sawaalon ke tag se milata hai aur sabse zyada milne wale ummeedvar nikalta hai.
2. **Doosra jaal (AI):** us chapter ke AITS sawaalon ki ek-ek line ki list AI ko di jati hai; woh aise sawaal bhi pakadta hai jinka tag kisi aur shabd me likha gaya.
3. **Gehri jaanch (AI):** har ummeedvar ke saath dono ka poora sawaal aur poora solution AI ko diya jata hai. Woh das ke das khaane ek-ek karke jaanchta hai (matlab se, sirf shabd se nahi) aur har khaane ki wajah likhta hai. Aakhri ginti yahin se aati hai.
4. **Doosri raay:** jo jodi seema par ya upar hai, use doosra model alag se jaanchta hai. Dono maanein to "pakka"; ek hi maane to "shaq wala".

### 3.9 Aapki manzoori ki screen
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

### 3.10 Students ko kya dikhega
Yeh hissa app ki showcase files ke baad pakka hoga.

- **Card:** 28 Jan 2027 ko raat 12 baje (IST) se Home ka AITS card Matched ban jata hai. Samay server tay karta hai, taaki website aur app saath badlein. Koi paper publish na hua ho to card "Matched jald aa raha hai" kehta hai. AITS ka practice archive series ke page par bana rehta hai.
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

Card ki haalat ka apna chhota raasta hai, taaki series ka purana raasta jaisa hai waisa rahe.

### 3.11 Yaad wale se NTA wale tak
- NTA ka paper upload hote hi us shift ka poora kaam official sawaal aur key par dobara chalta hai.
- Jo match pehle manzoor tha aur dobara nikla, woh "pehle se manzoor" nishaan ke saath aata hai; ek button se pass.
- Publish karte hi us shift ka page "NTA wala" ban jata hai. Yaad wala nateeja record me rehta hai, students ko nahi dikhta.
- NTA baad me key badle ya sawaal hataye, to sirf un sawaalon ki jaanch dobara hoti hai.

### 3.12 AI ke call
**Kaise:**
- Is kaam ka apna raasta, apni line aur apna budget hai. Purana AI raasta aur uski 300 ki seema jaise hain waise rehte hain.
- Har sawaal ek alag kaam hai. Server band ho kar chale to wahin se aage badhta hai.
- Roz ki seema aur kul seema aap screen par rakhte hain. Seema par kaam rukta hai, tootta nahi.
- Call fail ho to 3 baar koshish, phir "ruka" wajah ke saath, aur "Dobara chalao".
- AI ka jawab ek tay dhanche me aata hai; dhancha galat ho to server use nahi maanta.
- Ek saath chalne wale call ki ginti seemit rehti hai, taaki exam ke samay server par bojh na pade.

**Ek sawaal ki padhai:** 2 se 3 call. Pehla model padhta, hal karta aur tag deta hai; doosra model alag se apni raay deta hai; dono me fark ho to teesri call.

**Kitne call (design se nikala andaza, naapa nahi):**
| Kaam | Call |
| --- | --- |
| Poori AITS (3,750 sawaal) | 7,500 se 11,250 |
| Ek asli paper ki padhai | 150 se 225 |
| Ek asli paper ka milaan | 250 se 350 |
| Ek shift, dono roop (yaad wala + NTA wala) | 800 se 1,150 |
| January ka session (10 se 12 shift maan kar) | 8,000 se 14,000 |

Rupaye mujhe nahi pata: universal key ka rate mere paas nahi hai. Pehla pocket (H0) asli ginti, token aur samay naapega.

**Model:** pehla model wahi jo aaj lagta hai (gpt-6-astra). Doosri raay ke liye Claude. Dono universal key se. Claude ko picture bhejna is raaste se chala kar nahi dekha; H0 dekhega.

**Aapki apni ChatGPT ya Claude key:** abhi nahi chahiye. Tabhi chahiye hogi jab H0 me universal key ki raftaar ya seema kam pade.

**Balance:** saare 50 paper ek saath daalne par hazaaron call lagte hain. Us se pehle universal key ka balance bhar lijiye (Profile, Manage plan, Universal Key, Add Balance) aur auto top-up chalu rakhiye. Balance khatam hua to padhai ruk jati hai; kuch tootta nahi.

**"Perfect" ke baare me seedhi baat:** koi AI 100% sahi hone ka waada nahi kar sakta. Galat match students tak na pahunche, iske liye do model aur aapki manzoori hai. Chhoota hua match bach na jaye, iske liye do jaal aur "Khud jodo" hai.

### 3.13 Jo is phase me nahi hai
- Asli paper ko test ki tarah dene layak banana.
- AITS ke students ko AI ke likhe solution dikhana.
- Purana automatic AI solving dobara chalu karna.

---

## 4. Phase I: Student Choice

### 4.1 Aapne jo tay kiya
1. Abhi sirf JEE Main ka chapter-wise bank.
2. Student kisi bhi subject ke, kitne bhi chapter chunta hai.
3. Ginti do tarah se: har chapter ki alag, ya ek total.
4. Agle page par chapter-wise sawaalon ki list. List me sirf sawaal; options aur solution nahi.
5. Student khud tick kare, ya "Select Random" dabaye.
6. Samay: Maths ke 25 sawaal par 80 minute, Physics ke 25 par 60, Chemistry ke 25 par 40.
7. Rank nahi. Analysis normal mock jaisa.
8. Ek mock me zyada se zyada 75 sawaal. Aur koi seema nahi.

### 4.2 Student ka raasta
1. JEE Main ke page par naya card "Student Choice".
2. **Chapter chuno:** teeno subject ke chapter, har ek ke saamne kitne sawaal maujood hain.
3. **Ginti:** har chune chapter ke saamne ginti, ya upar ek total. Total chune chapter me barabar bat-ta hai; bacha hua pehle chapter ko jata hai.
4. **Sawaal chuno:** chapter-wise list, har sawaal ke saath tick. "Select Random" likhi ginti ke hisaab se chun leta hai; student uske baad bhi tick badal sakta hai. Upar ginti (jaise "32 / 75") aur banne wale mock ka samay.
5. **Mock banao:** naam, kul sawaal, subject-wise ginti aur samay. Phir wahi exam screen jo har mock me hai.
6. Submit ke baad result aur analysis. Mock "My Tests" me rehta hai.

Chhote niyam (**maine rakhe**): kisi chapter me maangi ginti se kam sawaal hon to jitne hain utne milte hain aur screen bata deti hai. 75 ke baad tick nahi lagta. Do baar button dabne se do mock nahi bante. Mock ka naam apne aap banta hai (jaise "Mera Mock 3 · 12 Dec").

### 4.3 Samay ka niyam
Har sawaal ka samay uske subject se: Maths 3.2 minute, Physics 2.4, Chemistry 1.6. Kul samay sab ka jod, upar ke poore minute tak. Ek hi ghadi poore mock ki. Marking chapter test jaisi: +4 / −1 / 0.

| Mock | Samay |
| --- | --- |
| Physics 25 + Chemistry 25 + Maths 25 | 60 + 40 + 80 = 180 minute |
| Physics 10 + Chemistry 5 + Maths 5 | 24 + 8 + 16 = 48 minute |
| Sirf Maths 10 | 32 minute |
| Chemistry 1 | 1.6, yani 2 minute |

### 4.4 Sawaal ki list: sirf sawaal ka tukda
- Naye look me har sawaal ka "sirf sawaal" wala tukda pehle se alag kata hota hai. List wahi tukda dikhati hai: ek sawaal, ek picture. Options ki koi picture list me nahi aati.
- List 10-10 sawaal ke tukdon me aati hai, jaise student neeche jata hai; pictures halki (WebP) aur usi tez raaste se jisse exam ki pictures aati hain.
- Server list me answer, options ya solution kabhi nahi bhejta.
- **Purane look wale test** (preview ke 78 aise hain; live ka **pata nahi**), aur naye look ka woh sawaal jise aapne Fix me "poora ek picture" rakha hai: numerical sawaal ki picture me options hote hi nahi, to wahi picture dikhti hai. MCQ me likhe hue shabdon se sirf sawaal wala hissa dikhta hai. Preview ke saare 3,398 MCQ me yeh hissa alag ho sakta hai, yeh maine ginkar dekha. (**Maine rakha.**)

### 4.5 Mock kaise banta hai
- Kram: Physics, Chemistry, Maths; subject ke andar chapter usi kram me jisme chune gaye.
- "Mock banao" par sirf chune hue sawaalon ki pehchaan rakhi jati hai. Poore sawaal tabhi jamte hain jab student test shuru karta hai, jaise har mock me.
- Student ke mock alag jagah rakhe jate hain, test ki list me nahi. Isliye woh Master ki list, Library, storage ki ginti aur rank ki machine me aate hi nahi.
- Har sawaal yaad rakhta hai ki woh kis chapter test se aaya, taaki "sawaal galat hai" ki report asli sawaal tak pahunche.
- Har sawaal par uske chapter ka naam rehta hai, taaki analysis chapter-wise bane.

### 4.6 Result aur analysis
- Wahi result aur wahi 8 hisson wala analysis jo normal mock me hai.
- Rank, percentile, leaderboard aur compare nahi. Rank ki jagah screen kehti hai "Is test par Rank nahi banta".
- Galat aur chhode sawaal Misfire me jate hain; My Tests aur PDF report normal mock jaise.

### 4.7 Super Admin me jagah
Super Admin, JEE Main, naya hissa "Student Choice":
- **On / Off.**
- **Pool ki list:** subject, chapter, kis test se, kitne sawaal, aur har chapter par "Shamil" ka switch. Pool me wahi chapter test aata hai jo students ke liye Live hai. Ek chapter ke do test hon to dono ke sawaal us ek chapter ke neeche judte hain.
- **Setting:** har subject ka samay per sawaal (3.2 / 2.4 / 1.6), zyada se zyada 75.
- **Ginti:** aaj aur kul kitne mock bane, kitne students ne banaye, sabse zyada chune gaye chapter.

### 4.8 API ka kachcha dhancha (app ki files ke baad pakka)
| Kaam | Raasta | Kya deta ya leta hai |
| --- | --- | --- |
| Chapter aur niyam | `GET /api/choice/jee-main` | chalu hai ya nahi, max 75, samay per sawaal, marking, subject-wise chapter aur maujood sawaal |
| Ek chapter ke sawaal | `GET /api/choice/jee-main/chapters/{chapter_id}/questions?page=` | sawaal ki id, number, MCQ ya numerical, sawaal ke tukde ka link. Options, answer, solution nahi. |
| Random | `POST /api/choice/jee-main/random` | chapter aur ginti (ya ek total) leta hai; chune hue sawaal ki id deta hai |
| Mock banao | `POST /api/choice/jee-main/mocks` | sawaal ki id leta hai; mock ki id, naam, ginti aur samay deta hai |
| Mock shuru karo | `POST /api/choice/jee-main/mocks/{id}/start` | attempt deta hai; uske baad exam, result aur analysis ke wahi raaste jo aaj hain |
| Mere bane mock | `GET /api/choice/jee-main/mocks` | student ke bane mock |

---

## 5. Purana kaam kaise bacha rahega

| Purani cheez | H aur I iske saath kya karte hain |
| --- | --- |
| PDF upload aur kaatne ki machine | Kuch nahi. AI bane hue paper ko sirf padhta hai. |
| Live / Schedule / picture ka saboot | Kuch nahi. Asli paper ki nayi pictures par wahi niyam lagta hai. |
| Student ka test: shuru, answer save, submit, score | H: kuch nahi. I: shuru karne ka naya raasta alag file me; purana raasta nahi badalta. |
| Rank aur leaderboard | H: kuch nahi. I: student ke mock rank ki machine me jate hi nahi. |
| Analysis | Ek-ek jagah (H8: AI ke tag aur level; I: rank ki jagah wali line). Baaki wahi. |
| Misfire, My Tests, PDF report | I ke mock normal mock ki tarah aate hain. I0 me padh kar pakka hoga. |
| Purana AI raasta (band) | Band hi rehta hai. |
| Series ka page (`LiveSeries.js`) | Nahi chhua jata. |
| Home ka AITS card | H6 me ek jagah: Matched chalu ho to naya card. |
| App ke purane raaste | Jaise hain waise. Sirf naye raaste judte hain. |

**Purani files jinhe chhuna padega (yahi, aur kuch nahi):**
- `server.py`: naye raaste jodna.
- `route_contracts.py`: har naye raaste ki entry. Ek bhi entry chhoote to server start nahi hota; isliye har pocket ki jaanch me server ka start shamil hai.
- `db.py`: naye collection ke index.
- `jobs.py`: 15 minute wale round me ek line, jo ruki hui padhai ko dobara uthati hai. Yeh line apne bachav ke andar hai, jaise picture ke saboot wali line; iski galti round ko nahi rokti.
- `MasterType.js`: AITS ki screen par naye panel.
- `HomeParts.js`: Matched ka card (H6).
- `ExamHub.js`: Student Choice ka card (I4).
- Analysis ki ek file: H8 aur I ke liye ek-ek jagah.

I ke liye code ki 14 files me 25 lines hain jo attempt ke test ki id se kaam karti hain. Pocket I0 unhe ek-ek padh kar likhega ki har ek student ke mock ke saath kya karegi. Us se pehle I ka koi code nahi.

---

## 6. Pocket: banane ka kram

Har pocket ke baad: nayi jaanch + wahi 26 purani suite + browser walk + testing agent. Phir aapko nateeja.

**Phase H**
| Pocket | Kya banta hai | Jaanch |
| --- | --- | --- |
| H0 | Trial, sirf preview me, app ka code nahi badalta. Chapter bank ke 20 sawaal dono model se padhwana; 10 banaye hue judwa aur ulte jode. Zyada se zyada 150 AI call. | Naap: call, token, second, AI ka jawab key se kitni baar mila, dono model ke tag kitne mile. |
| H1 | Tag ki list (10 khaane) aur uski screen | Alag test database; browser |
| H2 | AI ki padhai: apna raasta, budget, record, switch, "AI ki padhai" screen | Nakli AI ke saath alag test database; phir asli AI par ek chhota paper; purani suite |
| | **Deploy ka pehla mauka.** Iske baad aap AITS ke paper daalte hain. | |
| H3 | Asli paper ka upload (attempt, tareekh, shift, yaad wala / NTA wala) aur uski padhai | Ek purana paper upload karke |
| H4 | Milaan: ginti, doosra jaal, gehri jaanch, doosri raay | Banaye hue judwa aur ulte sawaal; ek poora paper |
| H5 | Manzoori ki screen | Browser, desktop aur 390 px |
| | **Deploy ka doosra mauka** (20 Jan se pehle). | |
| H6 | Student ka page, card ka badalna, API, pictures, app ka packet (app ki files ke baad) | Browser, API ke test, app ke namoone |
| | **Deploy ka teesra mauka** (28 Jan se pehle). | |
| H7 | NTA wale se badalna, April, key ka badalna | Alag test database |
| H8 | AI ke tag aur level AITS ke Analysis me ("AI ka andaza" likh kar) | Analysis ki purani suite + nayi |

**Phase I**
| Pocket | Kya banta hai | Jaanch |
| --- | --- | --- |
| I0 | Sirf padhna: un 25 lines ki list, mock rakhne ka dhancha, aakaar ka naap. Koi code nahi. | Likhi hui list |
| I1 | Pool aur Super Admin ka hissa | Alag test database; browser |
| I2 | Chapter, sawaal ki list (sirf sawaal ka tukda), Random | API ke test: answer aur options kabhi nahi aate |
| I3 | Mock banana, shuru karna, result bina rank, analysis, Misfire, My Tests | Ek poora mock dekar; rank kahin nahi dikhta |
| I4 | Website ki screens app ke showcase jaisi; app ka packet | Browser, desktop aur 390 px |
| I5 | Kinare: chapter test Off ya delete, do baar dabana, 75 ki seema | Alag test database |

**Kram:** H0, H1, H2 sabse pehle. Uske baad mera sujhav: H3 se H5, phir I, phir H6 aur H7 (app ki files ke baad), phir H8. Aap badal sakte hain.

**Deploy ke baare me ek baat:** deploy poore code ka hota hai. Pehle deploy me preview ka baaki kaam bhi live jayega, yani storage ka Packet E (bana aur jaancha hua; asli Supabase par abhi nahi chalaya).

---

## 7. Dates

| Tareekh | Kya |
| --- | --- |
| 26 Nov 2026 | Aaj. Yeh guide. |
| 9 Dec 2026 | AITS Day 1 |
| 20 se 24 Jan 2027 | JEE Main Session 1 (AITS ke Day 43 se 47 ke saath) |
| 27 Jan 2027 | AITS Day 50 |
| 28 Jan 2027, raat 12 baje IST | Card Matched banta hai; usi din Session 1 ka aakhri din |
| Session ke baad (tareekh NTA tay karta hai) | NTA ka paper aur key |
| April 2027 | Session 2 |

- 9 Dec tak sirf 13 din hain. H0 se H2 aur unka deploy isi beech chahiye, agar aap paper AI section ke baad hi daalna chahte hain. Main tareekh ka waada nahi kar sakta; har pocket jaanch ke baad hi aage badhta hai.
- Agar section 9 Dec se pehle live na ho, to paper phir bhi samay par daal dijiye (3.6 ki aakhri line).

---

## 8. Khatre

1. **AI figure galat padhe.** Tag galat nikalte hain. Bachav: doosra model, "aap dekhiye", aapki manzoori, "Khud jodo".
2. **Ek hi baat ke do tag.** Ginti kam aati hai. Bachav: tay list, asli paper ko wahi list dena, gehri jaanch matlab se, do tag ko ek karne ka button.
3. **Yaad wala paper adhoora ya galat.** Bachav: page par "Yaad wala" likha rehta hai; NTA wale se sab dobara.
4. **Balance ya seema beech me khatam.** Padhai rukti hai. Bachav: screen par saaf line, auto top-up.
5. **Samay.** 9 Dec, 20 Jan aur 28 Jan pakki tareekh hain.
6. **28 Jan ki bheed.** Bachav: jama hua nateeja, koi AI nahi, pictures tez raaste se.
7. **Student Choice: database ka aakaar.** Preview ke naap se 75 sawaal ka jama hua mock lagbhag 165 KB (dabane se pehle). Bachav: sawaal tabhi jamte hain jab test shuru hota hai. Asli aakaar I0 me napega.
8. **Student Choice: chapter test delete hona.** Us test ki pictures ke record chale jate hain. Aise mock ka sirf score bachna chahiye, jaise aaj delete hue test ke saath hota hai. I5 me banega aur jaancha jayega.
9. **Storage ka Packet F baaki hai.** Supabase band ho to naya paper tab tak nahi banta jab tak woh laute. Paper pehle se daalne par yeh khatra chhota hai.

---

## 9. Memory ke baaki kaam

**Phase J (teen ruke hue student feature): band.**
- **Subject Rank:** aapke kehne par nahi banega.
- **Seekh Reminder:** aapke kehne par nahi banega.
- **Galti Notebook:** "Misfire" naam se bana hua hai.

**Misfire: website aur app juda hai ya nahi**
- Website ka Misfire live par chal raha hai. Maine live par uska raasta (`/api/my/misfire`) dekha: woh maujood hai aur sign-in maangta hai.
- App ka Misfire usi raaste se data leta hai ya apna alag rakhta hai, yeh main yahan se nahi dekh sakta: app ka code mere paas nahi hai, aur app ka server apne raaston ki list nahi dikhata.
- Pehle maine sirf itna kaha tha ki app team ko diye gaye packet me Misfire ka zikr nahi hai. Iska matlab yeh nahi tha ki app me Misfire nahi hai.
- Ek minute ki jaanch: website par ek chhota test dekar ek sawaal galat kijiye, phir usi account se app ka Misfire kholiye. Wahi sawaal dikhe to dono jude hain. Ya app team se ek line pooch lijiye: "Misfire kis raaste se aata hai?"

**Phase K (tag, level, trend)**
- AI ke tag aur level ab Phase H ka hissa hain (H2 aur H8).
- Baaki: naye chapter-wise PDF ke test me chapter ka naam har sawaal par likhna (bina AI); purane AI solution ka pakka "Moderate" level hatana; Master me level aur chapter haath se rakhna; mock se mock ka trend.

**Phase L (storage)**
- Packet E ka bacha: "Pictures ki poori jaanch" button; is hisse ko ek baar asli Supabase par chalana.
- Packet F: Supabase band ho to poora paper Emergent me save hokar Live ho.
- Packet G: baad me aapke button se us paper ko Supabase me lana.
- Purani Emergent pictures ki copy: aapke kehne par sirf backlog.

**Phase M (PDF Engine 2.0 ke Phase 2 aur 3)**
- Phase 2: chipke hue options; options ke bagal me diagram; agle page par jata option; do column wale page; scan ki hui PDF; purane Draft ke liye "dobara padho"; solution ki pictures ki safai; PYQ naye look me.
- Phase 3: question bank; owner ki paper report; badi book ki jaldi jaanch.

**Phase N (bada load aur aapki taraf ruke kaam)**
- 1 se 2 lakh students ka load test.
- CDN: pictures ke liye CDN ka pata abhi save nahi hai. Matched ke din ki bheed me yeh kaam aata hai.
- Server ke aakaar ki arzi platform support ko bhejna.
- Rapid Fire ka Play Store link.
- Preview me do purane test database pade hain; hatane ke liye aapki haan chahiye.
- Ek purana test (`master_jee_series_iso181`) galat dates maangta hai; test ko theek karna hai, app ko nahi.

---

## 10. App se milaan

Website aur app ek jaisi rahein, iske liye mujhe yeh chahiye (H6 aur I4 se pehle; H0 se H5 aur I0 se I3 inke bina chal sakte hain):
1. Dono showcase ki har screen ka screenshot.
2. Un screens ki files, khaaskar unme bhara nakli data.
3. App ne koi API ka raasta ya khaane ka naam pehle se maan liya ho to woh.
4. Har screen ki khaali, loading aur galti wali haalat, aur screen par likhe shabd.

Uske baad: har screen ki har cheez ke saamne likha jayega ki server ka kaun sa khaana use bharta hai; jahan showcase is guide se alag hai, uski list aapko milegi; ek hi API tay hogi; app team ke liye packet aur namoone ke jawab banenge.

---

## 11. Aapse kya chahiye

1. Is guide ko haan, ya jo badalna hai.
2. H0 ke trial ke liye zyada se zyada 150 AI call ki ijazat (universal key ke balance se).
3. App ki dono showcase ke screenshot aur files.
4. Agar ho: pichhle saal ka ek yaad wala paper (PDF), H3 ki jaanch ke liye.

Jo faisle maine khud liye hain, woh guide me "Maine rakha" ke saath likhe hain: 10 khaano ke naam, tag ki list bina manzoori ke chalna, yaad wale paper me likha hua sawaal dikhana, purane look ke MCQ me likha hua sawaal, ek hi ghadi, mock ka apne aap bana naam.
