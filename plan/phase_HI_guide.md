# Phase H "Matched" aur Phase I "Student Choice": poori guide
(saath me memory me rakhe purane kaam: Phase J se N)

**Haalat (26 Nov 2026):** sirf guide. Koi code nahi likha gaya, kuch deploy nahi hua.
App ki dono showcase screen ke screenshot aur files aane ke baad yeh guide unke hisaab se dobara likhi jayegi (Hissa 6). Uske baad hi banana shuru hoga, aapki haan ke baad.

Is guide me har baat ke saath likha hai ki woh kis tarah ki hai:
- **Tay**: aapne keh diya hai.
- **Sujhav**: mera prastav; aap badal sakte hain.
- **Pata nahi**: abhi dekha ya naapa nahi gaya.

Naam ka dhyan: "Phase H" aur "Phase I" aapke product ke phase hain. Storage wale plan (plan/plan.md) ke andar bhi "H" aur "I" naam ke hisse hain; un se inka koi rishta nahi.

Aapke teen sawaalon ke seedhe jawab:
1. **AI ke call kaise honge:** Hissa 3.13. Aaj ki seema (roz 300 call, ek saath 2) is kaam ke liye bahut kam hai; iske liye alag line aur alag budget banega.
2. **Aapki ChatGPT ya Claude ki key chahiye?** Abhi nahi. App ki universal key se OpenAI aur Claude dono chalte hain. Aapki key do hi haalat me chahiye hogi; dono trial ke baad pata chalengi (Hissa 3.13).
3. **Memory me kya rakha tha:** teen student feature (Galti Notebook, Subject Rank, Seekh Reminder), is hidayat ke saath ki Super Admin ka kaam hone par aapko yaad dilaya jaye. Unki aaj ki haalat Hissa 5 me hai.

---

## Hissa 1. Ek nazar me

| Phase | Kya hai | Aaj ki haalat |
| --- | --- | --- |
| H | Matched: JEE Main 2027 ke asli paper ka AITS se sawaal-wise milaan | Sirf guide |
| I | Student Choice: chapter-wise bank se student ka apna mock | Sirf guide |
| J | Teen ruke hue student feature | 1 bana hua (Misfire naam se), 2 baaki |
| K | Chapter aur level ke tag, mock se mock ka trend | Baaki |
| L | Storage: Packet E ka bacha hissa, F, G | E lagbhag poora (sirf preview), F aur G shuru nahi |
| M | PDF Engine 2.0 ke Phase 2 aur 3 | Baaki |
| N | Bada load test, CDN, aur aapki taraf ruke kaam | Baaki |

J se N ke naam maine diye hain, kyunki aapne kaha ki memory wale kaam bhi phase ki tarah likhe jayein. Aap kram badal sakte hain.

---

## Hissa 2. Aaj kya hai (code aur preview ka database padh kar)

Live ka database maine nahi dekha. Jahan "preview" likha hai, woh sirf preview ka sach hai.

**AITS**
- 50 din, 9 Dec 2026 se 27 Jan 2027. Har paper 75 sawaal (har subject me 20 MCQ + 5 numerical), 180 minute, +4 / −1.
- Preview me ek bhi AITS paper nahi hai. Isliye asli AITS paper ka ek bhi sawaal maine nahi dekha.
- Code yeh nahi maangta ki series ke paper ke saath likha hua solution ho; sirf answer key se bhi paper ban jata hai.
- AITS ke sawaalon par chapter ka tag nahi hota (23 Nov ka note).

**Chapter-wise bank (JEE Main, preview)**
- 78 chapter test × 50 = 3,900 sawaal. Physics 29 chapter, Chemistry 23, Maths 26.
- Har sawaal: 1 picture (sawaal aur options ek hi picture me, yani purana look), saath me likhe hue shabd, answer, aur solution ki 1 picture. 3,398 MCQ, 502 numerical. Level kisi par nahi.
- Likhe hue shabdon me options bhi hain; saare 3,398 MCQ me pehle option ka nishaan mila, yani sawaal ka hissa options se alag kiya ja sakta hai. 507 sawaalon ke shabdon me figure, diagram, graph ya circuit ka zikr hai; unka figure shabdon me nahi hai.
- Naya look (sawaal aur har option alag kata hua): preview me 0 test.
- Preview me yeh 78 test Library me pade hain.
- Live par: 25 Nov ki report ke hisaab se "mathematics chapterwise" naam ki PDF ke 27 me 26 mock ready the. Live ka bank kis look me hai aur kitna hai, **pata nahi**.

**Purane saal ke paper**
- JEE Main ke 30 verified PYQ paper, 2,250 sawaal, key ke saath (2025 ke 11, 2026 ke 19).

**AI**
- AI ka ek gateway bana hua hai (model gpt-6-astra, universal key se). Usme ek saath 2 call chalte hain aur roz 300 call ki default seema hai; yeh seema badli ja sakti hai, par iski koi screen nahi hai.
- 7,100 purane AI solution ke record rakhe hain (5,939 taiyar, 1,161 ruke hue). Un me se 3,000 ka naap: ek call me beech ka (median) lagbhag 850 token andar aur 1,030 bahar.
- Us purane solution ka dhancha final answer me sirf A, B, C, D leta hai. Numerical sawaal ke liye naya dhancha chahiye.
- Automatic solving 22 Oct se code me band hai. Phase H ise chalu nahi karta.
- Matlab se milane wali koi machine nahi hai. Jo "duplicate" ki chetavni hai, woh sirf hu-ba-hu shabd milati hai, ek hi section aur subject ke andar.
- App ke paas AI ki sirf universal key hai; aapki apni OpenAI ya Claude key nahi lagi.

**Student ki taraf**
- Home ka AITS card server ke schedule se chalta hai. Series khatam hone par aaj woh "SERIES COMPLETE" aur "Open practice archive" dikhata hai.
- JEE Main ke page ke card (Mock Tests, Chapter-wise, PYQ...) server se aate hain.
- Test shuru hote hi uske sawaalon ka ek jama hua pack ban jata hai. Baad me test badle to bhi us attempt ke sawaal nahi badalte.
- Code ki 14 files me 25 lines attempt ke test ki id se kaam karti hain (rank, Misfire, analysis, report wagairah). Student Choice ke liye yeh sab jagah dekhni hongi.
- Analysis: rank class ke data se banta hai. Class na ho to screen kehti hai "Is test par Rank nahi banta".
- Pictures sirf chalte ya khatam attempt ke through milti hain. Matched ke page aur Student Choice ki list ke liye picture dene ka naya raasta chahiye.

**JEE Main 2027 ki dates**
- Session 1: 20, 21, 22, 23, 24 aur 28 Jan 2027. Yeh maine NTA ke 24 Oct 2026 ke public notice me khud padha.
- Paper 1 (B.E./B.Tech) ki do shift hoti hain: 9 se 12 aur 3 se 6. Paper 75 sawaal ka hai (har subject me 20 + 5), yani AITS jaisa.
- In chhe dino me kaun se din Paper 1 ke hain, us notice me nahi likha: **pata nahi**.
- Session 2 (April): us notice ke mutabik iski soochna baad me aayegi. Web search ne 2 se 7 April 2027 bataya; yeh maine NTA ke kagaz me nahi padha.
- NTA paper aur answer key kab dega, us notice me nahi likha.
- AITS 27 Jan tak chalti hai, yani 20 se 24 Jan ki shift AITS ke chalte hue hoti hain.

---

## Hissa 3. Phase H: Matched

### 3.1 Aapne jo tay kiya
1. AITS khatam hone ke agle din (28 Jan 2027) dashboard ka AITS card "Matched" ban jata hai.
2. Super Admin me AI har AITS sawaal ko options, answer aur solution ke saath padhta hai. Sirf chhota card nahi: poora sawaal aur poora solution yaad rehta hai. Yaad database me rehti hai, kisi agent ke session me nahi.
3. AITS ke neeche ek jagah, jahan JEE Main 2027 ke paper attempt-wise aur shift-wise upload hote hain. Har shift ke liye do jagah: pehle yaad wala paper, phir NTA wala.
4. AI asli paper ko padhta hai aur har sawaal ka detail solution likhta hai.
5. Har shift ke 75 sawaal AITS ke poore 50 din (3,750 sawaal) se milaye jate hain, shift ki tareekh chahe jo ho.
6. Match ka matlab: wahi chapter, uske andar wahi topic, wahi subtopic ka mixture. Dono ki aatma ek ho. Dono ka solution ek hi raaste se aage badhe. Hal me wahi formula lage.
7. Aapki manzoori ki jagah ho, lekin aasaan: "sab pass", aur kai chun kar ek saath pass.
8. Nateeja website par dikhe aur app ko mile.
9. AI ke call ka poora intezaam builder dekhe. Zaroorat ho to aap ChatGPT ya Claude ki key denge.

### 3.2 Is hisse ke shabd
- **Asli paper:** JEE Main 2027 ki kisi ek shift ka paper.
- **Yaad wala paper:** students ki yaad se bana paper (memory-based), jo exam ke din ya agle din milta hai.
- **NTA wala paper:** NTA ka apna paper aur answer key, jo session ke baad aata hai.
- **Padhai:** AI ka ek sawaal ko padhna, hal karna aur uski aatma nikalna.
- **Padhai ka record:** us padhai ka database me rakha poora nateeja (3.5).
- **Aatma (soul):** chapter, topic, subtopic ka mixture, formula aur hal ka raasta.
- **Milaan:** asli paper ke ek sawaal ke liye AITS me match dhoondhna.

### 3.3 Match ka niyam
Ek AITS sawaal asli paper ke sawaal ka match tabhi hai jab **chaaron** baatein milen:
1. Chapter wahi.
2. Topic wahi, aur subtopic ka mixture wahi (jaise "dhalaan par friction" + "pulley se jude block").
3. Hal me wahi formula ya niyam lage.
4. Solution usi raaste se, unhi kadmon se aage badhe.

Match ke do darje (**sujhav**; naam app ke saath pakke honge):
- **Seedha match:** wahi sawaal; sirf number, shabd ya maangi gayi cheez badli hai.
- **Soul match:** sawaal alag dikhta hai, par chaaron baatein milti hain.

Jo sirf chapter ya topic se milta hai par raasta alag hai, woh match nahi. Woh aapko "paas ka" naam se dikh sakta hai; students ko nahi dikhta aur ginti me nahi aata.

Udaharan:
- **Match:** AITS Day 12 Q14 me khurdure dhalaan par rakha block dhaage aur pulley se latke doosre block se juda hai; acceleration poocha hai. Asli paper me wahi banavat hai, mass aur kon alag hain, aur tension poocha hai. Chapter wahi (Laws of Motion), mixture wahi (dhalaan par friction + jude hue block), formula wahi (har block par F = ma, f = μN), raasta wahi (dono block ka free-body diagram, do equation, hal). Yeh match hai.
- **Match nahi:** dono Laws of Motion ke hain, par asli sawaal mode par ghoomti gaadi ka hai (v²/r wala). Chapter milta hai; mixture, formula aur raasta nahi.
- **Match nahi:** dono projectile ke hain. AITS me range ka formula lagta hai; asli sawaal sabse upar ke bindu par path ka radius poochta hai. Topic milta hai; formula aur raasta nahi.

Ginti: ek shift ka number = us shift ke 75 me se kitne sawaalon ka kam se kam ek manzoor match hai. Ek sawaal ke kai match hon to bhi woh ek hi baar ginta hai; page par sabse achhe 1 se 3 dikhte hain.

### 3.4 Poora raasta ek nazar me
1. Syllabus ki list banti hai (chapter, topic, subtopic, formula) aur aap use ek baar manzoor karte hain.
2. AITS ka har paper upload hote hi AI use padhta hai; har sawaal ka padhai ka record ban jata hai.
3. Exam ke din aap us shift ka yaad wala paper upload karte hain.
4. AI us paper ke har sawaal ko padhta hai aur solution likhta hai.
5. Milaan chalta hai: har sawaal ke liye 3,750 me se match ke sujhav nikalte hain.
6. Aap manzoori ki screen par sujhav pass ya radd karte hain, phir "Publish".
7. 28 Jan se students ko Matched dikhta hai (website aur app).
8. NTA ka paper aane par aap use upload karte hain; wahi kaam official sawaal aur key par dobara hota hai aur page "NTA wala" ban jata hai.
9. April me doosre attempt ke liye kadam 3 se 8 dobara.

### 3.5 AI ki yaad: ek sawaal ka poora record
| Hissa | Kya rakha jata hai |
| --- | --- |
| Pehchaan | AITS ka din, tareekh aur sawaal number; ya asli paper ka attempt, tareekh, shift aur source. Subject; MCQ ya numerical. |
| Poora sawaal | Picture se padha hua saaf likha sawaal, saare options, aur figure ho to uska shabdon me bayan. Asli picture bhi judi rehti hai. |
| Jawab | Key ka jawab, AI ka apna jawab, aur dono mile ya nahi. |
| Poora solution | Book ka apna solution (agar chhapa hai) likhe hue roop me, aur AI ka apna kadam-dar-kadam solution. |
| Aatma | Chapter; topic; subtopic ka mixture; formula (tay naam aur likha hua formula); hal ka raasta 3 se 6 chhote kadmon me; kya diya hai; kya maanga hai; sawaal ka phanda. |
| Jaanch | Doosre model ki raay mili ya nahi. Haalat: taiyar / aap dekhiye / padha nahi gaya. |
| Hisaab | Kaun sa model, prompt ka kaun sa version, kitne token, kab. |

- Record sawaal ke content ki fingerprint se juda hai. Sawaal ya solution badle to sirf wahi sawaal dobara padha jata hai, aur ek hi sawaal par do baar kharcha nahi hota.
- Padhai sirf padhti hai. Paper, key ya student ke score me kuch nahi badalta.

### 3.6 Syllabus ki list
"Wahi subtopic" tabhi pakka kaha ja sakta hai jab dono sawaal ek hi list se tag hon. Isliye AI apne man se naam nahi likhta; woh ek tay list se chunta hai.
- List: subject, uske andar chapter, uske andar topic, uske andar subtopic. Saath me formula ki list (har formula ka ek tay naam).
- Kahan se banegi (**sujhav**): NTA ka JEE Main syllabus, hamare 78 chapter ke naam, aur AI ka pehla draft. Aap ya aapke teacher use ek baar dekh kar manzoor karte hain.
- List ka version hota hai. List badle to jin sawaalon par asar hai, sirf unka tag dobara banta hai.
- **Pata nahi:** NTA ka syllabus maine abhi nahi padha; list ka aakaar (kitne subtopic) trial me pata chalega.

Yeh list milaan ki reedh hai: list kachchi hui to match bhi kachche honge.

### 3.7 AITS ki padhai
- **Kab:** jaise hi kisi din ka paper ban jata hai (Draft, Scheduled ya Live), uski padhai peeche line me lag jati hai. Aap "Padhao" se khud bhi chala sakte hain. Feature baad me live hua to pichhle saare din ek saath padhe ja sakte hain; kuch khota nahi.
- **Paper par asar nahi:** paper ka Live hona, upload aur student ka test padhai ka intezaar nahi karte.
- **Ek sawaal ki galti us sawaal tak:** ek picture na padhi jaye to baaki 74 chalte rehte hain.
- **Screen "AI ki padhai"** (Super Admin, AITS ke neeche): 50 din ki list. Har din: 75 me kitne taiyar, kitne "aap dekhiye", kitne ruke. Upar: aaj ke call, kul call, token, roz ki seema, "Roko" aur "Chalao".
- **"Aap dekhiye" kab:** AI ka jawab key se nahi mila (AI galat hai ya key), do model ne alag chapter bataya, ya picture padhi nahi gayi. Aap teen me se ek karte hain: sahi maan lo, chapter aur subtopic khud chuno, ya dobara padhao.

### 3.8 Asli paper ka upload
- **Jagah:** Super Admin, JEE Main, All India Test Series ki screen par, dino ki list ke neeche: "JEE Main 2027 ke asli paper".
- **Dhancha:** Attempt 1 (January) aur Attempt 2 (April). Uske andar tareekh. Har tareekh me Shift 1 aur Shift 2. Har shift me do khaane: "Yaad wala" aur "NTA wala".
- Tareekh ki rows NTA ki dates se pehle se bhari hongi; aap jod aur hata sakte hain.
- **File:** PDF (wahi PDF machine jo aaj mock kaat-ti hai) ya likh kar. NTA wale ke saath answer key. Yaad wale me key zaroori nahi.
- Yeh paper students ko test ki tarah nahi dikhta; private rehta hai.
- **Haalat ki line** har khaane par: Upload hua. Padha ja raha hai (75 me 40). Solution ban rahe hain. Milaan ho raha hai. Aapki manzoori baaki (N sujhav). Publish ho gaya.
- **Pata nahi:** coaching ki yaad wali PDF hamari PDF machine me saaf kategi ya nahi. Aisi PDF me aksar options nahi hote ya sawaal adhoore hote hain. Trial me pichhle saal ki ek aisi PDF se dekhna hai. Jo sawaal na kate, use aap Fix me theek karenge ya AI padhega.

### 3.9 Milaan kaise hota hai
Har asli sawaal ke liye do daur:

**Daur 1: ummeedvar chunna (3,750 me se lagbhag 15).** Teen jaal, taaki ek ki galti doosra pakad le:
- Jaal 1 (bina AI): wahi chapter, aur kam se kam ek subtopic ya formula saanjha.
- Jaal 2 (AI): us chapter aur paas ke chapter ke saare AITS sawaalon ki ek-ek line ki list AI ko di jati hai; woh un me se chunta hai jinki aatma mil sakti hai. Yeh tag ki galti se bachata hai.
- Jaal 3: jo sawaal do chapter ka mixture hai, use har subtopic se alag-alag bhi dhoondha jata hai.

**Daur 2: gehri jaanch.** Yahan card nahi, poora record chalta hai:
- Asli sawaal ka poora likha sawaal aur poora solution, aur har ummeedvar ka poora likha sawaal aur poora solution, AI ko diye jate hain.
- AI har jodi par chaaron shartein alag-alag jaanchta hai aur har ek ka saboot likhta hai: kaun se subtopic, kaun sa formula, kaun sa kadam kis kadam se milta hai.
- Faisla: seedha match, soul match, paas ka, ya nahi.
- Jis jodi ko pehla model match kahe, use doosra model alag se dobara jaanchta hai. Dono maanein to sujhav "pakka" hai; ek hi maane to "shaq wala".

Tay ke mutabik har shift ke liye saare 50 din jaanche jate hain. Har match ke saath yeh bhi rakha jata hai ki AITS ka woh din us shift se pehle aaya tha ya baad me (3.16 ka khatra 7 dekhiye).

### 3.10 Aapki manzoori ki screen
Ek paper ke 75 sawaal ki list. Har row me:
- Baayin taraf asli sawaal ki picture; daayin taraf sujhaye gaye AITS sawaal ki picture (Day aur number ke saath).
- Ek line me wajah, aur chaar nishaan: chapter, subtopic, formula, raasta.
- Darja (seedha / soul) aur "pakka" ya "shaq wala".

Button:
- Har jodi par "Pass" aur "Hatao".
- Tick lagakar "Chune hue pass karo".
- Upar "Sab pakke pass karo" aur "Sab pass karo".
- Filter: subject, sirf pakke, sirf shaq wale, bina match wale sawaal.
- "Khud jodo": Day aur number likh kar ya chapter se dhoondh kar koi AITS sawaal khud jodna.
- "Publish" (students ko dikhe) aur "Wapas lo".

Bina aapke "Publish" ke students ko kuch nahi dikhta.

### 3.11 Students ko kya dikhega
Yeh hissa kachcha hai; app ke showcase ke baad pakka hoga.

**Card:** Home ka AITS card 28 Jan 2027 ko raat 12 baje (IST) se Matched ban jata hai. Yeh server tay karta hai, taaki website aur app ek saath badlein. Us samay koi paper publish na hua ho to card "Matched jald aa raha hai" kehta hai. Purane AITS paper ka practice archive series ke page par bana rehta hai.

**Matched ka page (sujhav):**
- Upar: attempt (January / April), phir tareekh aur shift.
- Har shift: 75 me kitne match, subject-wise ginti, aur paper "Yaad wala" hai ya "NTA wala".
- Sawaal-wise list: sawaal number, subject, chapter, aur match hai to "Day 12 · Q14" aur darja.
- Ek sawaal kholne par: asli sawaal aur AITS ka sawaal saath-saath, dono ke solution, aur ek line ki wajah.
- Page par likha rahega ki match kise kaha gaya hai, aur ki yeh NTA se juda nahi hai.
- Agar app ke showcase me ho: sign-in kiye student ko yeh bhi ki usne woh AITS sawaal sahi kiya tha, galat, ya chhoda.

**Server ke niyam:**
- Jis AITS din ka paper abhi khula nahi, uska sawaal kabhi nahi dikhta.
- Student ke kholne par koi AI nahi chalta; publish hote samay ek jama hua nateeja ban jata hai aur wahi diya jata hai.
- Publish se pehle us page ki har picture storage me saabit hoti hai (Packet E wala niyam).
- AI ke likhe solution par "AI ka likha" likha rahega.

**API ka kachcha dhancha (app ki files ke baad pakka):**
| Kaam | Raasta | Kya deta hai |
| --- | --- | --- |
| Card ki haalat | `GET /api/series/all-india-jee` me naya khaana `matched` | `state` (off / soon / ready), `opens_at`, kul paper, kul match |
| Saari shift | `GET /api/matched` | attempt, tareekh, shift, source, 75 me kitne match, subject-wise ginti |
| Ek shift ki list | `GET /api/matched/papers/{paper_id}` | har sawaal: number, subject, chapter, match (Day, number, darja, wajah) |
| Ek sawaal | `GET /api/matched/papers/{paper_id}/questions/{n}` | dono sawaal ki pictures ke link, dono ke solution, wajah |

### 3.12 Yaad wale se NTA wale tak
- NTA ka paper upload hote hi us shift ka poora kaam official sawaal aur key par dobara chalta hai.
- Jo sawaal yaad wale me bhi tha aur uska match pehle manzoor tha, woh "pehle se manzoor" nishaan ke saath aata hai; aap unhe ek button se pass kar sakte hain.
- Publish karte hi us shift ka page "NTA wala" ban jata hai. Yaad wala nateeja record me rehta hai, students ko nahi dikhta.
- NTA baad me key badle ya sawaal hataye, to sirf un sawaalon ki jaanch dobara hoti hai.

### 3.13 AI ke call: kaise, kitne, kis model se
**Kaise:**
- Is kaam ki apni line hogi, purane AI kaam se alag. Har sawaal ek alag kaam hai: server band ho kar chale to wahin se aage badhta hai.
- Apna budget: roz ki seema aur kul seema aap screen par rakhte hain. Seema par kaam ruk jata hai, tootta nahi. "Roko" button.
- Har call ka hisaab rakha jata hai: model, token, samay, nateeja.
- Call fail ho to 3 baar koshish, phir "ruka" wajah ke saath, aur "Dobara chalao".
- AI ka jawab ek tay dhanche me aata hai; dhancha galat ho to server use nahi maanta aur dobara poochta hai.
- Koi bhi call student ke request ke andar nahi hoti.

**Ek sawaal ki padhai me call:**
1. Padho aur hal karo (model A; key dikhaye bina).
2. Server AI ka jawab key se milata hai. Na mile to ek aur call, jisme book ka solution dikhaya jata hai. Phir bhi na mile to "aap dekhiye".
3. Aatma nikalo (model A, syllabus ki list ke saath).
4. Doosri raay (model B, alag se): apna jawab aur apna chapter-subtopic.

Yaad wale paper me key nahi hoti, isliye wahan dono model ka jawab milna zaroori hai; na mile to "aap dekhiye".

**Kitne call (design se nikala andaza, naapa nahi):**
| Kaam | Call |
| --- | --- |
| Ek sawaal ki padhai | 2 se 4 |
| Poori AITS (3,750 sawaal) | 7,500 se 15,000 |
| Ek asli paper ki padhai (75 sawaal) | 150 se 300 |
| Ek asli paper ka milaan (ummeedvar 5-5 ke guchchhe me jaanche jayein to) | 400 se 700 |
| Ek shift, dono roop (yaad wala + NTA wala) | 1,100 se 2,000 |
| January ka poora session (10 se 12 shift maan kar) | 11,000 se 24,000 |

April ka session lagbhag utna hi aur. Rupaye maine nahi nikale: universal key ka rate mujhe nahi pata. Trial asli ginti, token aur kharcha dega.

**Model (sujhav, trial tay karega):** model A wahi jo aaj lagta hai (gpt-6-astra). Model B Claude (claude-opus-5-5 ya claude-sonnet-5-5). Dono universal key se chalte hain. **Pata nahi:** Claude ko is raaste se picture bheji ja sakti hai ya nahi; na ja sake to picture ki doosri padhai Gemini se hogi.

**Aapki apni key kab chahiye:**
- Agar trial me universal key ki raftaar ya seema kam pade.
- Agar jaal kam pade aur "matlab se khoj" (embeddings) jodni pade; yeh raasta universal key ke saath mujhe nahi mila.

**Universal key ka balance:** bade kaam se pehle balance bhar lena hoga (Profile, Manage plan, Universal Key, Add Balance), aur auto top-up chalu rakhna behtar hai. Balance khatam hua to padhai ruk jayegi; kuch tootega nahi.

### 3.14 "Perfect" ke liye jaanch
Seedhi baat: koi AI 100% sahi hone ka waada nahi kar sakta. Yeh design do kaam karta hai. Galat match students tak na pahunche, iske liye do model aur aapki manzoori hai. Chhoota hua match bach na jaye, iske liye teen jaal aur "Khud jodo" hai.

Banane se pehle ek trial purane data par (**sujhav**; aapki haan chahiye, kyunki isme PYQ padha jayega, badlega nahi):
- "Asli paper" ki jagah JEE Main 2026 ka ek verified paper (75 sawaal, key ke saath).
- "AITS" ki jagah chapter-wise bank ke kuch chapter (sawaal, key aur solution ke saath).
- Naap: kitne call, kitne token, kitna samay, AI ka jawab key se kitni baar mila.
- Aap ya aapke teacher 50 jodi khud dekhte hain: match hai ya nahi. Usse pata chalta hai AI ki raay aapki raay se kitni milti hai.
- Do jaan-boojh kar banaye test: ek hi sawaal number badal kar (milna chahiye), aur wahi chapter par alag raaste wala sawaal (nahi milna chahiye).

Trial ka nateeja teen cheezein tay karega: kaun sa model, ek paper ka kharcha, aur yeh raasta kaafi achha hai ya badalna hai.

### 3.15 Dates aur kab tak kya chahiye
| Tareekh | Kya |
| --- | --- |
| 9 Dec 2026 | AITS Day 1 |
| 20 se 24 Jan 2027 | JEE Main Session 1 (AITS ke Day 43 se 47 ke saath) |
| 27 Jan 2027 | AITS Day 50 |
| 28 Jan 2027, raat 12 baje IST | Card Matched banta hai; usi din Session 1 ka aakhri din bhi |
| Session ke baad (tareekh NTA tay karta hai) | NTA ka paper aur key |
| April 2027 (web search: 2 se 7 April; NTA ke kagaz me maine nahi padha) | Session 2 |

- 20 Jan se pehle live chahiye: syllabus ki list, AITS ki padhai, asli paper ka upload, milaan, aur manzoori ki screen.
- 28 Jan se pehle live chahiye: student ka page, card ka badalna, app ka packet.
- AITS ki padhai jitni jaldi live ho utna achha; der hui to pichhle din ek saath padhe jayenge.

### 3.16 Khatre
1. **AI figure galat padhe.** Aatma galat nikalti hai. Bachav: doosra model, "aap dekhiye", aapki manzoori, "Khud jodo".
2. **Yaad wala paper adhoora ya galat.** Match kam ya galat nikalte hain. Bachav: page par "Yaad wala" likha rehta hai, aur NTA wale se sab dobara hota hai.
3. **Syllabus ki list kachchi.** Bachav: aapki manzoori aur version.
4. **Balance ya seema beech me khatam.** Kaam rukta hai. Bachav: screen par saaf line, auto top-up.
5. **Samay.** 20 Jan aur 28 Jan pakki tareekh hain; storage ka F aur G bhi baaki hain (Hissa 7, H-13).
6. **Bina khule AITS din ka sawaal dikh jana.** Bachav: server ka niyam (3.11).
7. **Daave ki sachchai.** 20 Jan ki shift ka match agar 27 Jan ke AITS paper se hai, to woh paper exam ke baad aaya tha. Use "pehle se bataya" kehna sach nahi hoga. Aapka faisla hai ki saare 50 din gine jayein; mera sujhav sirf itna ki aise match par ek chhoti line ho (Hissa 7, H-3).
8. **28 Jan ki bheed.** Bachav: jama hua nateeja, pictures CDN se, koi AI nahi.
9. **Yaad wale paper ki picture kisi coaching ki hoti hai.** **Sujhav:** students ko AI ka dobara likha hua sawaal dikhe, coaching ki picture nahi (H-5).
10. **NTA ki key ka badalna.** Bachav: 3.12.

### 3.17 Banane ka kram (mushkil hissa pehle; har kadam alag se jaancha jayega)
| Kadam | Kya banta hai | Kaise jaancha jayega |
| --- | --- | --- |
| H0 | Trial purane data par (3.14) | Call, token, samay ka naap; aapki 50 jodi |
| H1 | Syllabus ki list, teeno subject | Aapki manzoori; har chapter bank ke sawaal ko list me jagah milti hai |
| H2 | AI ki alag line, budget, padhai ka record, "AI ki padhai" screen | Alag test database me nakli AI ke saath; phir asli AI par chhota sample |
| H3 | Asli paper ka upload (attempt, tareekh, shift, source) aur uski padhai | Ek purana paper upload karke |
| H4 | Milaan: teen jaal, gehri jaanch, doosri raay | Banaye hue judwa aur ulte sawaal; ek poora purana paper |
| H5 | Manzoori ki screen | Browser me, desktop aur 390 px par |
| H6 | Student ka page, card ka badalna, API, pictures, app ka packet | Browser, API ke test, app team ke sample |
| H7 | NTA wale se badalna, April, key ka badalna | Alag test database me |

Har kadam ke baad testing agent ki alag jaanch. Kuch bhi live tabhi jab aap "deploy" likhen.

### 3.18 Jo is phase me nahi hai
- Asli paper ko test ki tarah dene layak banana (H-6).
- AITS ke students ko AI ke likhe solution dikhana.
- Purana automatic AI solving dobara chalu karna.

---

## Hissa 4. Phase I: Student Choice

### 4.1 Aapne jo tay kiya
1. Abhi sirf JEE Main ka chapter-wise bank. (Aapke message me "GMAT" likha aaya; maine JEE Main maana.)
2. Student kisi bhi subject ke, kitne bhi chapter chunta hai.
3. Ginti do tarah se: har chapter ki alag, ya ek total.
4. Agle page par chapter-wise sawaalon ki list. List me poora sawaal dikhta hai; options aur solution nahi.
5. Student khud tick kare, ya upar "Select Random" dabaye.
6. Samay: Maths ke 25 sawaal par 80 minute, Physics ke 25 par 60, Chemistry ke 25 par 40.
7. Rank nahi. Analysis bilkul normal mock jaisa.
8. Ek mock me zyada se zyada 75 sawaal. Aur koi seema nahi.
9. Iski jagah Super Admin me bhi bane.

### 4.2 Student ka raasta
1. JEE Main ke page par naya card "Student Choice".
2. **Chapter chuno:** teeno subject ke chapter, har ek ke saamne kitne sawaal maujood hain. Kai chapter, kisi bhi subject ke.
3. **Ginti:** har chune chapter ke saamne ginti, ya upar ek total. Total likha to woh chune chapter me barabar bat-ta hai; bacha hua pehle chapter ko jata hai.
4. **Sawaal chuno:** chapter-wise list, har sawaal ke saath tick. Upar "Select Random" likhi ginti ke hisaab se har chapter se sawaal chun leta hai. Student uske baad bhi tick badal sakta hai. Upar ginti dikhti hai, jaise "32 / 75", aur banne wale mock ka samay.
5. **Mock banao:** naam, kul sawaal, subject-wise ginti aur samay dikhta hai. Phir wahi exam screen jo har mock me hai.
6. Submit ke baad result aur analysis. Mock "My Tests" me rehta hai.

Chhote niyam (**sujhav**):
- Kisi chapter me maangi ginti se kam sawaal hon to jitne hain utne milte hain, aur screen bata deti hai.
- 75 ke baad tick nahi lagta.
- Do baar button dabne se do mock nahi bante.

### 4.3 Samay ka niyam
Har sawaal ka samay uske subject se: Maths 3.2 minute, Physics 2.4, Chemistry 1.6 (yani 80, 60 aur 40 minute ko 25 se baant kar). Kul samay sab ka jod, upar ke poore minute tak.

| Mock | Samay |
| --- | --- |
| Physics 25 + Chemistry 25 + Maths 25 | 60 + 40 + 80 = 180 minute |
| Physics 10 + Chemistry 5 + Maths 5 | 24 + 8 + 16 = 48 minute |
| Sirf Maths 10 | 32 minute |
| Physics 5 + Chemistry 5 | 12 + 8 = 20 minute |
| Chemistry 1 | 1.6, yani 2 minute |

Marking chapter test jaisi: +4 / −1 / 0.

### 4.4 Sawaal ki list: sirf sawaal, options nahi
- **Naye look wale sawaal** (sawaal aur har option alag kata hua): list me sirf sawaal wala tukda dikhta hai. Figure bhi saath aata hai.
- **Purane look wale sawaal** (sawaal aur options ek hi picture me): picture dikhayi to options bhi dikhenge. Do raaste hain: likhe hue shabdon se sirf sawaal ka hissa dikhana (figure nahi dikhega; preview ke 3,900 me 507 sawaal figure ya graph ka zikr karte hain), ya aise sawaal pool se bahar rakhna. Yeh aapka faisla hai (I-5).
- Server list me answer, options ya solution kabhi nahi bhejta.
- Ek chapter me 50 ya zyada pictures hoti hain, isliye list tukdon me aati hai, jaise-jaise student neeche jata hai.

### 4.5 Mock kaise banta hai
- Kram (**sujhav**): Physics, Chemistry, Maths. Subject ke andar chapter usi kram me jisme chune gaye; chapter ke andar list wala kram.
- Ek hi ghadi poore mock ki (**sujhav**, I-1).
- Mock shuru hote hi uske sawaal jam jate hain, jaise har mock me. Baad me chapter test badle to yeh mock nahi badalta.
- Har sawaal yaad rakhta hai ki woh kis chapter test se aaya, taaki student "sawaal galat hai" ki report kare to woh asli sawaal tak pahunche.
- Har sawaal par uske chapter ka naam likha jata hai, taaki analysis chapter-wise bane.

### 4.6 Result aur analysis
- Wahi result aur wahi 8 hisson wala analysis jo normal mock me hai.
- Rank, percentile, leaderboard aur doosre student se compare nahi. Rank ki jagah screen kehti hai "Is test par Rank nahi banta".
- Har sawaal ka "par time" paper ke standard se aata hai (class ka data nahi hota). Level "Not rated" rahega jab tak Phase K ke tag na aayein.
- Galat aur chhode sawaal Misfire me jate hain; "3 seekh" aur PDF report normal mock jaise (I-4).

### 4.7 Super Admin me jagah
Super Admin, JEE Main, naya hissa "Student Choice":
- **On / Off:** students ko card dikhe ya nahi.
- **Pool ki list:** subject, chapter, kis test se, kitne sawaal, Live hai ya nahi, aur har chapter par "Shamil" ka switch.
- **Niyam (sujhav):** pool me wahi chapter test aata hai jo students ke liye Live hai. Ek hi chapter ke do test hon to dono ke sawaal us ek chapter ke neeche jud jate hain.
- **Setting:** har subject ka samay per sawaal (3.2 / 2.4 / 1.6), zyada se zyada 75.
- **Ginti:** aaj aur kul kitne mock bane, kitne students ne banaye, sabse zyada chune gaye chapter.

### 4.8 API ka kachcha dhancha (app ki files ke baad pakka)
| Kaam | Raasta | Kya deta ya leta hai |
| --- | --- | --- |
| Chapter aur niyam | `GET /api/choice/jee-main` | chalu hai ya nahi, max 75, har subject ka samay per sawaal, marking, subject-wise chapter aur maujood sawaal |
| Ek chapter ke sawaal | `GET /api/choice/jee-main/chapters/{chapter_id}/questions?page=` | sawaal ki id, number, MCQ ya numerical, sawaal ki picture ka link ya likha sawaal. Options, answer, solution nahi. |
| Random | `POST /api/choice/jee-main/random` | chapter aur ginti (ya ek total) leta hai; chune hue sawaal ki id deta hai |
| Mock banao | `POST /api/choice/jee-main/mocks` | sawaal ki id leta hai; mock ki id, naam, ginti aur samay deta hai |
| Mere bane mock | `GET /api/choice/jee-main/mocks` | student ke bane mock |

Mock banne ke baad start, exam, result aur analysis ke wahi raaste jo aaj har test ke hain. Random server par hota hai, taaki website aur app ek jaisa chunein.

### 4.9 Khatre
1. **Database ka aakaar.** Har mock ke sawaal jam kar rakhe jate hain. Preview ke naap se ek chapter sawaal lagbhag 2.2 KB ka hai, yani 75 sawaal ka mock lagbhag 165 KB (dabane se pehle). Bahut students bahut mock banayein to yeh bada ho jata hai. Bachav: "Mock banao" par sirf chune hue sawaalon ki id rakhi jati hai; poore sawaal tabhi jamte hain jab student test shuru karta hai. Isse kuch delete nahi karna padta. Asli aakaar banate samay naapa jayega.
2. **Chapter test ka Off ya delete hona.** Jis chapter test se sawaal aaye the, use aap delete karein to uski pictures ke record chale jate hain. Aaj delete hue test ke attempt me sirf score bachta hai; student ke bane mock ke liye yahi banana hoga, warna uski pictures khaali dikhengi. Sirf Off karne ya Library me bhejne se bane hue mock nahi tootne chahiye; yeh jaanchna hai.
3. **Rank ka galti se dikhna.** Ek student ke mock ka "class" sirf woh khud hai. Aise mock ko rank ki machine se poori tarah bahar rakhna hai.
4. **Code ki woh 25 lines** jo attempt ke test ki id se kaam karti hain (Hissa 2). Har ek ko dekhna hai ki woh student ke apne mock ke saath sahi chalti hai.
5. **Key ka sudhar.** Aap chapter test me key theek karein to woh pehle se bane mock tak apne aap nahi pahunchega. Baad ka faisla.
6. **Purani app build.** JEE Main ke page ke card server se aate hain; purani build naye card ko kaise dikhayegi, app team se poochna hai.
7. **Super Admin ki list.** Students ke bane mock Master ki list, Library aur ginti me nahi aane chahiye.

### 4.10 Banane ka kram
| Kadam | Kya banta hai | Kaise jaancha jayega |
| --- | --- | --- |
| I0 | Un 25 lines ko padhna, mock rakhne ka dhancha tay karna, aakaar naapna | Likhi hui list aur naap |
| I1 | Pool aur Super Admin ka hissa | Alag test database, browser |
| I2 | Chapter, sawaal ki list (bina options), Random | API ke test: answer aur options kabhi nahi aate |
| I3 | Mock banana, shuru karna, result bina rank, analysis, Misfire, My Tests | Ek poora mock dekar; rank kahin nahi dikhta |
| I4 | Website ki screens app ke showcase jaisi; app ka packet | Browser desktop aur 390 px |
| I5 | Kinare: chapter Off ya delete, seema, do baar dabana | Alag test database |

---

## Hissa 5. Memory me rakhe kaam: Phase J se N

### Phase J: teen ruke hue student feature
Memory me likha tha: "Super Admin ka kaam ho jaye to owner ko in teeno ki yaad dilana." Yeh wahi yaad hai.

| Feature | Aaj ki haalat | Bacha kya |
| --- | --- | --- |
| Galti Notebook | Bana hua, "Misfire" naam se (21 Nov). Har galat aur chhoda sawaal ek jagah, dobara hal karo, "Samajh gaya", subject aur chapter ka filter, chapter report. Live par hai ya nahi, pakka nahi kar paya. | App team ke packet me yeh nahi hai. Aapke purane faisle me sirf galat sawaal the; Misfire chhode hue bhi leta hai (J-1). |
| Subject Rank | Nahi bana. Aaj rank sirf poore score ka banta hai. | Physics, Chemistry, Maths ka alag Rank aur Percentile; Overview, Performance aur PDF me; app ka packet. |
| Seekh Reminder | Aadha. "3 seekh" likhi ja sakti hain aur agle mock ke Analysis me pichhle mock ki seekh dikhti hain. Par agla mock shuru hone se theek pehle wali screen par nahi dikhti. | Wahi screen par seekh ka card; app ka packet. |

### Phase K: chapter aur level ke tag, trend
- Naye chapter-wise PDF se bane test me chapter ka naam test par hota hai, har sawaal par nahi. Isliye unke Analysis me subject dikhta hai, chapter nahi. Kaam: chapter ka naam sawaalon par likhna, naye aur bane hue dono. AI nahi lagta. (25 Nov ko code padh kar mila; student ki screen par dobara nahi dekha.) Preview ke 78 purane chapter test me chapter ka naam har sawaal par pehle se hai; yeh kami sirf PDF machine se bane naye chapter test ki hai.
- AI se likhe purane solution ke saath ek pakka "Moderate" level save hota hai, jo paper ka apna level ban kar dikhta hai. Kaam: use hatana.
- Aap Master me har sawaal ka level aur chapter haath se rakh sakein.
- AITS ke sawaalon par chapter ka tag: Phase H ki padhai yeh tag de sakti hai, taaki AITS ke Analysis me "bar-bar galat chapter" asli chapter dikhaye (H-12).
- Mock se mock ka trend: pichhle 5 mock me Careless, Overtime aur galat par gaya samay.

### Phase L: storage
- Packet E ka bacha: "Pictures ki poori jaanch" button; likhe hue Draft ko Live karte samay wajah row par rakhna (aapka faisla); is hisse ko ek baar asli Supabase par chalana.
- Packet F: Supabase band ho to 5 minute me ya aapke button par poora paper Emergent me save hokar Live ho. AITS ke dino ke liye yeh bachav hai.
- Packet G: baad me aapke button se us paper ko Supabase me lana.
- Purani Emergent pictures ki copy: aapke kehne par sirf backlog.

### Phase M: PDF Engine 2.0 ke Phase 2 aur 3
- Phase 2: chipke hue options; options ke bagal me diagram; agle page par jata option; do column wale page; scan ki hui PDF bina AI ke; saade shabd wale options asli text me; purane Draft ke liye "dobara padho"; solution ki pictures ki safai; JEE Main PYQ naye look me; app guide aur PDF format guide.
- Phase 3: question bank (har kata sawaal chapter ke saath jama, taaki bina nayi PDF ke mock ban sake; yeh Student Choice se juda hai); owner ki paper report option ki pictures ke saath; badi book ki jaldi jaanch.

### Phase N: bada load aur aapki taraf ruke kaam
- 1 se 2 lakh students ek saath ka load test.
- CDN: pictures ke liye CDN ka pata abhi save nahi hai (dono khaane khaali). Matched ke din ki bheed ke liye yeh kaam aata hai.
- Server ke aakaar ki arzi platform support ko bhejna.
- Rapid Fire ka Play Store link.
- Owner ke liye paper report (kaun sa sawaal sabse zyada galat hua); agle mock ka target score.
- Preview me do purane test database pade hain; hatane ke liye aapki haan chahiye.
- Ek purana test (`master_jee_series_iso181`) galat dates maangta hai aur isliye fail hota hai; test ko theek karna hai, app ko nahi.

---

## Hissa 6. App se milaan

Aapne kaha ki app ne dono ka showcase bana liya hai aur website aur app ek jaisi honi chahiye. Mujhe yeh chahiye:
1. Dono showcase ki har screen ka screenshot. Matched: card, shift ki list, sawaal-wise list, ek sawaal ka detail. Student Choice: chapter chunna, ginti, sawaal ki list, mock ban gaya.
2. Un screens ki files, khaaskar unme bhara nakli data. Usi se pata chalega ki app kaun si jaankari maangti hai.
3. App ne koi API ka raasta ya khaane ka naam pehle se maan liya ho to woh.
4. Har screen ki khaali, loading aur galti wali haalat.
5. Screen par likhe shabd, taaki website par wahi rahein.
6. Yeh feature app ki kaun si build se aayega, aur purani build naye card ke saath kya karegi.

Uske baad main yeh karunga:
- Har screen ki har cheez ke saamne likhunga ki server ka kaun sa khaana use bharta hai.
- Jahan app ka showcase is guide se alag hai, un sab ki list bana kar aapse poochhunga.
- Ek hi API tay hogi, website aur app dono ke liye; 3.11 aur 4.8 ke kachche dhanche usi hisaab se badlenge.
- App team ke liye packet aur namoone ke jawab banenge, jaise pehle bane hain.

---

## Hissa 7. Aapke faisle jo baaki hain

**Phase H**
- H-1. AITS ki books me har sawaal ka likha hua solution hota hai, ya sirf answer key? Solution ho to AI wahi padhega; na ho to khud likhega.
- H-2. Students ko dono darje alag dikhen ("Seedha match", "Soul match"), ya ek hi "Matched"?
- H-3. Jo AITS din us shift ke baad aaya, uske match par ek chhoti line ho ("yeh paper exam ke baad aaya"), ya koi fark na dikhe? Sujhav: line ho.
- H-4. Sawaal-wise detail ke liye sign-in zaroori ho? Sujhav: ginti sabko dikhe, detail sign-in ke baad.
- H-5. Yaad wale paper me coaching ki picture dikhe, ya AI ka dobara likha sawaal? Sujhav: likha hua.
- H-6. Asli paper ko test ki tarah dene layak bhi banana hai, ya sirf Matched me dikhana? Sujhav: abhi sirf Matched.
- H-7. Doosri raay ka model: Claude (claude-opus-5-5 ya claude-sonnet-5-5) theek hai? Trial dono ko naapega.
- H-8. Trial ke liye JEE Main 2026 ka ek verified paper aur chapter bank ke kuch chapter padhne ki ijazat. Sirf padhna; PYQ me kuch nahi badlega.
- H-9. Trial ke liye pichhle saal ka ek yaad wala paper (PDF) de sakte hain?
- H-10. AI ka budget: roz ki aur kul seema. Trial ke baad number sujhaunga.
- H-11. Series ke page (LiveSeries.js) ko chhoone ki ijazat? Aaj woh file chhoona mana hai. Bina ijazat Matched ka apna page aur Home ka card banega; series ke page ke andar link nahi.
- H-12. AI ke nikale chapter tag AITS ke Analysis me bhi dikhen?
- H-13. Pehle kya bane: storage ka Packet F, ya Phase H? Dono ka samay 9 Dec se 20 Jan ke beech takrata hai.

**Phase I**
- I-1. Ek hi ghadi poore mock ki, ya subject-wise alag? Sujhav: ek.
- I-2. Kram Physics, Chemistry, Maths theek hai?
- I-3. Numerical sawaal par bhi −1, chapter test jaisa?
- I-4. Yeh mock Misfire, My Tests, PDF report aur "3 seekh" me normal mock ki tarah aaye? Sujhav: haan.
- I-5. Purane look wale sawaal: likha hua sawaal dikhe (figure nahi dikhega), ya pool se bahar?
- I-6. Pool ka niyam (jo chapter test Live hai wahi, aur har chapter par ek switch) theek hai?
- I-7. Student apne mock ko naam de sake aur dobara de sake?

**Phase J aur aage**
- J-1. Misfire me chhode hue sawaal bhi rahen?
- J-2. Subject Rank aur Seekh Reminder kab: H aur I ke baad?

---

## Hissa 8. Niyam jo nahi tootenge
- Live par kuch tabhi jata hai jab aap "deploy" likhen.
- `LiveSeries.js` nahi chhui jati, jab tak aap na kahen.
- Email, SMS ya bahar ki koi chetavni nahi.
- Ek kharab file, ek ruka upload, ya AI ka ek ruka kaam kisi doosre kaam ko nahi rokta.
- Verified JEE Main PYQ nahi badalta. Trial use sirf padhta hai, aur woh bhi aapki haan ke baad.
- Student ko dikhne se pehle har picture storage me saabit hoti hai.
- Live ke database se kuch hard delete nahi hota.
- Test ke alag database ek-ek karke chalte hain, saath me nahi.
- Jab tak kisi cheez ka test se saboot na ho, use "ho gaya" nahi kaha jata.
