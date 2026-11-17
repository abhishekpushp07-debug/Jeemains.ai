# JEELIVE.AI Rank: ek halki screen par JEE Main ki rank, percentile aur college-branch

Student apne expected marks (ya percentile) daalta hai aur usi ek screen par use JEE Main ki rank, percentile aur wo top 50 college-branch dikhte hain jo counselling ke aakhri round tak mil sakte hain.
Poora feature sirf text aur rangeen segments se bana hai, 2026 ke official data (NTA, JoSAA, CSAB, JAC Delhi) par chalta hai, aur app ko bhaari nahi karta.

## Kiske liye
- **JEE Main 2027 ke aspirants:** "itne marks aaye to kya milega" jaanne ke liye.
- **Exam de chuke students:** answer key se nikle marks, ya result ka percentile daalkar.
- **Counselling ke waqt:** kaun sa college, kaun si branch, kis round mein band hui.
- **Owner:** app ka X-factor, jo student ko baar-baar app par wapas laata hai.

## Core features aur experience

### 1. Ek hi screen, bahut halka
Ye is feature ke pakke niyam hain.

- **Ek hi screen:** poora feature neeche ki bar ke **RANK** tab par rehta hai. App mein koi naya page nahi judta.
- **Sab kuch wahin khulta hai:** branch filter, home state ki list, college ki detail aur percentile chart, sab isi screen par khulte aur band hote hain.
- **Sirf text aur rang:** text, ank aur rangeen chip. Koi photo, college ka logo, tasveer, graph ya nayi artwork nahi.
- **App mein koi bhaari cheez nahi judti:** koi nayi image, font ya data file app ke andar nahi rakhi jaati. APK mein sirf is ek screen ka code judta hai.
- **Data server par:** colleges aur cutoff ka poora data server par rehta hai. Phone utna hi mangta hai jitna us waqt dikhana hai:
  - list ke 25 line ek baar mein
  - college ki detail sirf tap karne par
  - percentile chart ke 20 line sirf us percentile ko kholne par
- **Kam memory:** ek waqt mein 25 line hi screen par banti hain, isliye sasta phone bhi aaram se chalata hai.
- **Baaki app ko haath nahi lagta:** Home, tests, My Tests, Mission, Rapid Fire aur neeche ki bar jaise hain waise hi rehte hain. Sirf RANK tab ka "coming soon" page badalta hai.
- **Alag-thalag:** rank ka data na aaye ya network kamzor ho to sirf isi tab par message aur Retry dikhta hai. Baaki app chalti rehti hai.

### 2. Research se kya nikla
Feature inhi tathyon par bana hai. Jahan official data nahi hai, wahan saaf likha hai.

| Sawaal | Research ka jawab |
|---|---|
| Kya NTA marks → percentile ki table deta hai? | Nahi. NTA sirf itna batata hai: April 2026 mein 99 percentile ke liye sabse tough shift mein **165** aur sabse easy shift mein **196** marks lage (31 marks ka fark). 98 percentile par fark 27 aur 97 par 26 marks tha. |
| To marks → percentile kaise banega? | 2026 ki 19 shifts ke liye students ke public kiye hue marks-percentile se, jise NTA ke upar wale official numbers par fit kiya jaayega. |
| Percentile → rank kitna pakka hai? | Kaafi pakka. 2026 mein 15,38,468 students baithe. 1 percentile = lagbhag 15,385 rank. |
| Seedha formula kaafi hai? | Nahi. Formula General cutoff (93.4123549) par rank 1,01,349 deta hai, jabki NTA ki apni ginti wahan 96,873 hai. Isliye rank NTA ki ginti par fit hogi aur public scorecards se jaanchi jaayegi. |
| Category rank ki official table hai? | Nahi. NTA sirf category-wise ginti deta hai (General 5,38,239; OBC 6,11,953; EWS 1,80,086; SC 1,56,038; ST 52,152; PwD 4,800) aur JEE Advanced cutoff ki ginti. Category rank inhi se aur public scorecards se estimate hogi. |
| Marks se kitna sahi bataya ja sakta hai? | NTA ki shift tables ke hisaab se 80–85 percentile ke aas-paas **ek mark** hi lagbhag 0.5 percentile (7,000+ rank) hila deta hai. Isliye sirf marks se asli phailaav bada hota hai; percentile daalne par rank tight ho jaati hai. |
| College cutoff kahan se? | JoSAA 2026 ke 5 round, CSAB Special 2026 ke 2 round, JAC Delhi 2026 ke 4 round + upgradation + spot round. Teeno ke official portal par round-wise opening/closing rank hai. |
| Kaun si seat kis rank se bharti hai? | JoSAA: Open seat par CRL, EWS/OBC-NCL/SC/ST seat par category rank, PwD seat par PwD rank. CSAB Special aur JAC Delhi: har seat par CRL. |

### 3. Screen ka dhaancha
Upar se neeche, ek hi screen par:

1. **Exam ka switch:** JEE Main | BITSAT. BITSAT chunne par sirf ek line: "Coming next".
2. **Tareeke ka switch:** "My marks" | "Percentile chart".
3. **Input ka hissa:** chhota card.
4. **Result ka hissa:** bade ankon mein percentile aur rank.
5. **List ka hissa:** college type ke rangeen segment, 25 line, page 1 / page 2.
6. **Sabse neeche:** data ka note aur do chhote text link (All India series, My results), jo aaj ke page par button hain.

- "Show" dabate hi input card sikudkar ek line ban jaata hai ("180 marks · Normal · General · Edit"), taaki result turant saamne aaye. "Edit" se card wapas khulta hai.

### 4. Student kya daalta hai

| Field | Zaroori? | Na bhare to |
|---|---|---|
| Marks (300 mein se) | Marks ya percentile mein se koi ek | — |
| Percentile | Marks ya percentile mein se koi ek | — |
| Paper level: Tough / Normal / Easy | Optional | Normal |
| Category: General, EWS, OBC-NCL, SC, ST | Optional | General |
| Female | Optional (on/off) | Off |
| PwD | Optional (on/off) | Off |
| Home state | Optional | Koi nahi |
| Branch | Optional | All branches |

- Marks aur percentile ke khaane ek hi line mein, saath-saath. Paper level ke teen chip unke theek neeche.
- Category, Female, PwD, home state aur branch chhote chip hain. Tap karne par chunaav wahin khulta hai.
- **Sirf marks:** paper level ke hisaab se percentile aur rank nikalti hai.
- **Sirf percentile:** rank seedha percentile se nikalti hai. Paper level ki zaroorat nahi rehti.
- **Dono:** percentile se rank banti hai. Marks se ye bataya jaata hai ki paper Tough, Normal ya Easy jaisa tha. Dono aapas mein mel na khayein to halka sa "ek baar check kar lo" note aata hai.
- Pichhli baar bhari hui cheezein phone par yaad rehti hain.

### 5. Rank aur percentile ka result
- Bada result:
  - **Expected percentile** (range)
  - **Expected rank (CRL)** (range)
  - **Category rank** (range), agar category General nahi hai; PwD on ho to **PwD rank** bhi.
- Range ki chaudai owner ke niyam se:

| Expected rank | Rank ki range |
|---|---|
| 2,000 se behtar | 200 se zyada chaudi nahi |
| 2,000 se 10,000 | 500 se zyada chaudi nahi |
| 10,000 se aage | 1,000 se zyada chaudi nahi |

- Percentile ki range rank ki range se mel khaati hai aur kabhi 0.5 se chaudi nahi hoti.
- **Imaandaari ki line:** sirf marks daalne par ye range estimate ka beech ka hissa hai, guarantee nahi. Isliye theek neeche ek aur line aati hai: "Tough paper hota to rank lagbhag X, Easy paper hota to lagbhag Y."
- Percentile daalne par ye doosri line nahi aati, kyunki rank tight hoti hai.
- Namoona (numbers sirf samjhane ke liye):

```
180 marks · Normal paper · General
Expected percentile   98.97 – 99.03
Expected rank (CRL)   14,900 – 15,900
Paper ke hisaab se    Tough: ~9,000  ·  Easy: ~27,000
```

### 6. Top 50 college-branch
- Result ke neeche wo **50 college-branch** jo is rank par counselling ke aakhri round tak mil sakte hain. **25-25 ke do page**, usi screen par.
- Ek line = ek college ki ek branch. Jaise "MNNIT Allahabad · Electronics & Communication".
- **Kaun si seat ginti mein aati hai:** student jin-jin seats ka haqdaar hai, sab jaanchi jaati hain:
  - Open seats (sabke liye)
  - apni category ki seats
  - PwD on ho to PwD seats
  - Female on ho to female-only seats
  - home state diya ho to us state ke NIT ki home-state seats; baaki NIT mein other-state seats
- Jis raaste se seat sabse aasaani se milti hai, wo line par likha hota hai. Jaise "Home state · OBC-NCL".
- **"Aakhri round tak" ka matlab:** JoSAA Round 5, CSAB Round 1 aur CSAB Round 2 mein jo closing rank sabse door tak gayi. Delhi ke colleges ke liye JAC ka aakhri round, upgradation aur spot round.
- **Kram:** sabse zyada maang wali seat sabse upar. Maang ka paimana: 2026 mein wo seat general list par kitni jaldi bhar gayi.
- **Har line par (sirf text):**
  - college ka naam aur type ka rangeen tag (NIT / IIIT / GFTI / Delhi)
  - branch ka naam
  - 2026 ki aakhri closing rank aur kis round mein band hui
  - chance ka rangeen tag

| Tag | Rang | Matlab |
|---|---|---|
| Safe | Hara | Closing rank student ki rank se 15% ya zyada aage thi |
| Likely | Neela | Closing rank student ki rank se aage thi, par 15% se kam |
| Borderline | Narangi | Student ki range closing rank ko chhoo rahi hai, ya seat sirf CSAB / spot round mein khuli thi |

- **Segments:** All · NIT · IIIT · GFTI · Delhi. Har segment ka apna rang. Har segment mein 50 tak.
- **Branch filter:** "All branches" (default) aur 20 branch group. Ek ya kai chune ja sakte hain. Mechanical chunne par Mechanical ke top 50 college dikhte hain.
  - 20 group: Computer Science, AI & Data Science, Information Technology, Mathematics & Computing, Electronics & Communication, Electrical, Instrumentation, Mechanical, Civil, Chemical, Metallurgy & Materials, Production & Industrial, Aerospace, Biotechnology, Engineering Physics, Mining, Robotics & Mechatronics, Environmental, Food/Textile/Ceramic, Science & integrated courses.
- **Bas thoda sa door:** list ke neeche 5 seats jo 10% tak ke fark se chhoot rahi hain, saath mein "lagbhag +N marks aur".
- 50 se kam asli seats hon to utni hi dikhti hain. Ginti poori karne ke liye kuch joda nahi jaata.

### 7. College ki detail (usi screen par pop-up)
- Kisi bhi line par tap karne se us college ki detail **usi screen ke upar pop-up panel** mein khulti hai. Band karte hi student list mein wahin lautta hai jahan tha.
- **Upar:** college ka naam, type, shehar, aur student ki rank.
- **Text table:** us college ki 10 sabse zyada maang wali branches, har round ki closing rank ke saath.
  - NIT / IIIT / GFTI: Round 1, 2, 3, 4, 5, CSAB 1, CSAB 2
  - Delhi: Round 1, 2, 3, 4, Upgradation, Spot
- Jis khaane mein student ki rank andar aati hai, wo rang se highlight hota hai. Ek line saaf batati hai: "Aapki rank Round 3 se andar aati hai."
- **"Show all branches"** se usi panel mein us college ki saari branches khulti hain.
- **Seat ka raasta badalna:** Home state / Other state, Gender-neutral / Female-only, Open / category. Shuru mein student wala raasta chuna hota hai.
- Kisi branch par tap: us branch ki har round ki opening aur closing rank, wahin.
- Neeche "Official page kholo" ka link, jo JoSAA / CSAB / JAC ka official cutoff page phone ke browser mein kholta hai.

### 8. Percentile chart (usi screen par, bina kuch type kiye)
- Upar ke switch mein **"Percentile chart"** chunte hi input card ki jagah percentile ki list aa jaati hai. Kuch type nahi karna.
- 99.9 se 80 percentile tak **50 line**, har line par **20 college-branch** (kul 1,000 tak):

| Percentile | Step |
|---|---|
| 99.9 se 99.0 | har 0.1 par |
| 98.8 se 95.0 | har 0.2 par |
| 94.5 se 90.0 | har 0.5 par |
| 89 se 80 | har 1 par |

- Har line par: percentile, lagbhag rank, aur Normal paper mein lagbhag marks.
- Kisi line par tap: wahin neeche uski 20 sabse zyada maang wali seats khulti hain. Ek waqt mein ek hi line khuli rehti hai.
- Upar category ke chip (General pehle se chuna) aur wahi branch filter.
- Kisi seat par tap karne se wahi college ka pop-up khulta hai.
- 80 percentile se neeche chart nahi jaata. Marks type karne wala raasta har marks par chalta hai.

### 9. Data kahan se aata hai

| Kya | Official source |
|---|---|
| 2026 ke students ki ginti, category-wise ginti, cutoff | NTA press release, 20 April 2026: cdnbbsr.s3waas.gov.in/s3f8e59f4b2fe7c5705bf878bbd494ccdf/uploads/2026/04/20260420809492136.pdf |
| Shift-wise percentile ki ginti | NTA notice, 23 April 2026: cdnbbsr.s3waas.gov.in/s3f8e59f4b2fe7c5705bf878bbd494ccdf/uploads/2026/04/20260423459353913.pdf |
| NIT / IIIT / GFTI, Round 1–5 | josaa.admissions.nic.in/Applicant/SeatAllotmentResult/CurrentORCR.aspx |
| CSAB Special, Round 1–2 | admissions.nic.in/csabspl/Applicant/seatallotmentresult/currentorcr.aspx |
| DTU, NSUT, IIIT-Delhi, IGDTUW | jacdelhi.admissions.nic.in/or-cr/ |

- Ye data ek baar official portal se lekar app ke server par rakha jaayega. Student ke istemaal ke waqt sarkari site par koi call nahi jaati, isliye result turant aata hai.
- Screen par likha hoga: "2026 ke data par estimate. Asli cutoff har saal badalta hai."

## User flow
1. **Marks se:** RANK tab → marks daale (jaise 180) → Show → input sikudkar ek line → percentile aur rank ki range → neeche top 50 college-branch.
2. **Percentile se:** marks khaali chhode → percentile daala (jaise 97.4) → Show → rank ki tight range aur colleges.
3. **Apne hisaab se:** category OBC-NCL chuni, Female on kiya, home state Uttar Pradesh diya → list mein category, female-only aur home-state wali seats bhi aa gayin.
4. **Branch chunkar:** branch chip → Mechanical → Mechanical ke top 50 college.
5. **College ke andar:** "MNNIT Allahabad · ECE" par tap → pop-up mein 10 branches ki Round 1 se CSAB 2 tak closing rank → "Show all branches" → band kiya → list mein wahin wapas.
6. **Bina type kiye:** "Percentile chart" → 99.9 se 80 tak scroll → kisi percentile par tap → uski 20 seats wahin khuli.

Har flow shuru se aakhir tak isi ek screen par rehta hai.

## UI/UX feel
- **Look:** app ke Home jaisa halka aur saaf, wahi font. Rapid Fire wala laal arena look yahan nahi.
- **Sirf text:** naam, ank aur chip. Koi tasveer, logo ya graph nahi.
- **Rangeen segmentation:**
  - teen hisse alag halke rang ki patti se pehchane jaate hain: input, result, list
  - college type ke chaar rang: NIT, IIIT, GFTI, Delhi
  - chance ke teen rang: Safe hara, Likely neela, Borderline narangi
  - paper level ke teen chip alag rang mein: Tough, Normal, Easy
- **Bada result:** rank aur percentile bade ankon mein, Indian tareeke se likhe (1,07,693).
- **Aasaan:** do khaane aur ek button se kaam chal jaata hai. Baaki sab optional chip.
- **College pop-up ki table:** rounds aade mein scroll hote hain, branch ka naam jagah par tika rehta hai.
- **Tez aur halka:** result ek second ke andar. Halka sa fade; koi bhaari animation ya entry show nahi.
- **Imaandaar screens:** data na mile ya network kamzor ho to saaf message aur Retry. Koi nakli college ya nakli rank nahi.

## Implementation phases

### Phase 1: MVP (abhi yahi banega)
1. RANK tab par ek hi screen: JEE Main chalu, BITSAT "Coming next".
2. Input: marks / percentile / paper level, category, Female, PwD, home state, branch.
3. Percentile aur rank ka result, owner ke range wale niyam ke saath, aur paper ke hisaab se phailaav ki line.
4. Top 50 college-branch (25 × 2 page), rangeen segments, branch filter, chance tag, "bas thoda sa door" wali 5 seats.
5. College ka pop-up: 10 branches × saare round, saari branches, seat ka raasta badalna, official page ka link.
6. Percentile chart usi screen par: 50 line × 20 seats, bina type kiye.
7. 2026 ka poora data server par: NTA, JoSAA Round 1–5, CSAB Round 1–2, JAC Delhi.

### Phase 2: aur gehra
- BITSAT predictor, owner ke link se, isi screen ke switch par.
- 2025 aur 2026 ki tulna: college pop-up mein trend, aur Safe tag do saal ke data se.
- JEE Main 2027 ke har session ke result ke baad naya data, aur apni date-shift chunne ka option.
- "Mujhe apni rank pata hai": rank seedha daalna.
- Test ya PYQ ke result se ek tap mein predictor.
- Apni shortlist save karna aur WhatsApp par text share.
- JAC Delhi ke khaas quota (defence, Kashmiri migrant, single girl child).

### Phase 3: poora counselling saathi
- JEE Advanced ke marks se IIT predictor.
- JoSAA ke liye choice-filling ki list banane wala tool.
- College ki jaankari: fees, seats, placement (official sources se).
- Counselling ke dinon mein live round tracker.
- Yahi feature jeelive.ai website par.

## Assumptions
- **"Ek hi screen":** matlab RANK tab ke alawa koi naya page nahi. College ki detail usi screen par pop-up panel mein khulti hai (aapne pehle "pop-up" kaha tha). Percentile chart usi screen ka doosra tareeka hai.
- **"Bahut halka":** app ke andar koi nayi image, font ya data file nahi; sirf ek screen ka code. Cutoff ka data server par.
- **"All text":** photo, logo, graph aur nayi artwork nahi. Rang sirf chip, tag aur patti mein.
- **Rang:** Safe hara, Likely neela, Borderline narangi; NIT / IIIT / GFTI / Delhi ke chaar alag rang. Ye app ke halke look se mel khaate hue chune jaayenge.
- **"App kharab na ho":** RANK tab ke alawa app ki kisi screen, bar ya Rapid Fire mein koi badlaav nahi.
- **Rank button:** neeche ki bar ka maujooda RANK tab. Uske "coming soon" page ki jagah ye screen aayegi. Us page ke do button (All India series, My results) sabse neeche chhote text link ban kar rahenge.
- **Input ka sikudna:** Show ke baad input card ek line ban jaata hai, taaki ek hi screen par result aur list ko jagah mile.
- **Range ka niyam:** rank ki range 200 / 500 / 1,000 tak, percentile ki range 0.5 tak. Sirf marks se ye range estimate ka beech ka hissa hai; asli phailaav neeche ki line mein dikhta hai.
- **"Early rank":** 10,000 tak ki rank ko early maana gaya hai.
- **Paper level:** 2026 ki 19 shifts ko 99 percentile ke marks ke hisaab se teen hisson mein baanta jaayega: Tough, Normal, Easy.
- **Marks:** −75 se 300 tak, poore ank.
- **Marks aur percentile dono:** percentile ko maana jaayega.
- **Rank ka paimana:** 2026 (15,38,468 students). 2027 ke numbers aane tak yahi.
- **Category aur PwD rank:** estimate hain, kyunki NTA inki table nahi deta. PwD rank sabse mota estimate hai.
- **Marks → percentile:** students ke public data se, NTA ke official numbers par fit karke.
- **Colleges:** JoSAA ke 114 institute (32 NIT, IIEST Shibpur samet; 26 IIIT; 56 GFTI) aur Delhi ke DTU, NSUT, IIIT-Delhi, IGDTUW. IIT, IIIT Hyderabad, BITS, private university aur DSEU nahi.
- **Courses:** 4 saal ke B.Tech / B.E. aur Paper 1 ki rank se milne wale 5 saal ke dual / integrated course. B.Arch aur B.Planning nahi.
- **CSAB wali seat:** jo seat sirf CSAB mein khuli, wo Borderline maani jaayegi, kyunki wo bachi hui seats par tiki hoti hai.
- **Ek line:** ek college ki ek branch ek hi baar dikhegi, sabse aasaan raaste ke saath.
- **Kram:** maang ke hisaab se, kisi banayi hui college ranking se nahi.
- **Chance tag:** 15% aur 10% ki seema.
- **50 result:** har segment mein 25-25 ke do page.
- **Branch filter:** "top 20 branches" ka matlab 20 branch group + All branches liya gaya hai. Milte-julte naam wale course ek group mein.
- **Home state na dene par:** NIT mein sirf other-state seats, IIIT / GFTI mein all-India seats. Goa, J&K aur Ladakh ke khaas quota home state se apne aap judte hain.
- **Delhi:** home state Delhi chunne par JAC ki Delhi-region cutoff dikhegi, saath mein note ki iske liye 11th-12th Delhi ke school se zaroori hai. Baaki sabko Outside Delhi cutoff.
- **Female:** on karne par female-only seats aur IGDTUW judte hain.
- **Percentile chart:** General se shuru; home state ke bina; gender-neutral seats. Ek waqt mein ek hi percentile khula. Paas-paas ke step mein kai seats dobara aayengi. Jahan 20 se kam asli seats hain wahan utni hi.
- **80 se neeche:** chart nahi, par type karne wala raasta chalta hai.
- **"Bas thoda sa door":** ye maanga nahi gaya tha; joda gaya hai aur hataya ja sakta hai.
- **College pop-up:** 10 branches maang ke hisaab se; "browser page" ka matlab official cutoff page ka link liya gaya hai.
- **Data:** ek baar official portal se, app ke server par. Koi source apne aap padha na ja sake to wo hissa chhod kar screen par naam se bataya jaayega; andaaze se kuch nahi bhara jaayega.
- **Yaad rakhna:** pichhle input sirf phone par. Server par history nahi.
- **Test ke marks:** app ke tests ya All India series se marks nahi liye jaate; student khud daalta hai.
- **Bhasha:** buttons aur labels English mein, jaise baaki app.
- **Naya build:** feature dikhne ke liye naya Android build chahiye. Uske baad data bina build ke badla ja sakta hai.
- **Browser arena aur website:** Phase 1 mein ye feature sirf app mein.
