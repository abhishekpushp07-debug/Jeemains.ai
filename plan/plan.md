# JEELIVE.AI — Organised Super Admin: "Pehle jagah chuno, phir upload karo"

Ek saaf Super Admin jahan har upload pehle yeh poochta hai ki woh kis exam aur kis section mein jayega, aur publish se pehle dikhata hai ki students ko woh website aur app par kahan dikhega.
Exams, sections aur tests ek hi jagah se banenge aur sambhale jayenge, aur unka order wahi hoga jo students dekhte hain. Koi bhi test "random" jagah par nahi jayega.

## Kiske liye
- **Owner (aap):** exam banana, section banana, books/papers upload karna, publish karna, students aur team sambhalna.
- **Reviewers (staff):** sirf review ka kaam: held items, question reports, solutions check karna. Upload, publish, exams aur students sirf owner ke paas.
- **Students:** website aur app par jahan jaate hain wahan sahi test sahi section mein milega.

## Core features aur experience (Phase 1)

### 1. Ek Super Admin, saaf hisson mein
Ab tak Super Admin, Content Studio aur Upload Book teen alag jagah hain, aur Content Studio mein ek ke neeche ek 10 panels hain. Ab sab ek workspace mein aayega, aur menu mein 7 hisse honge:
1. **Overview:** sirf woh jo aapka kaam maang raha hai: kaunsa upload chal raha hai, kitne mocks publish ke liye ready hain, kya held hai aur kyun, kitni nayi question reports aayi hain.
2. **Exams & Content:** exam → section → tests, bilkul usi order mein jo students dekhte hain. Yahin exam banana, section banana, naam badalna, order badalna, test ko doosre section mein bhejna, live/unlive karna.
3. **Upload:** ek hi "Add content" button. Pehle jagah chunte hain, phir file (neeche detail hai).
4. **Review:** held mocks aur unki wajah, question reports, manual solve, AI explanation review. Yeh sab tools pehle se hain, bas ek jagah aa jayenge.
5. **Schedule & Live:** All India JEE series ki schedule aur jin tests ka time window hai.
6. **Students:** mobile number list aur PIN reset (jaisa abhi hai).
7. **Team:** reviewer access dena ya hatana.
- Purane Content Studio aur Upload Book ke links kaam karte rahenge aur seedhe naye hisse mein khulenge.
- Har screen ke upar breadcrumb hamesha poora rasta dikhayega, jaise: BITSAT › Mock Tests › Mock 07.

### 2. Upload wizard: jagah pehle, file baad mein
- **Step 1: Kahan jayega?**
  - Exam chuno: JEE Main / BITSAT / COMEDK / aapke banaye exams / **+ Naya exam**.
  - Section chuno: PYQ Papers / Mock Tests / Chapter-wise Tests / aapke banaye sections / **+ Naya section**.
  - Exam aur section dono chune bina aage nahi badh sakte.
- **Step 2: Kis tarah ki file?** Sirf woh options dikhenge jo us section mein fit hote hain:
  - Ek combined book jismein kai mocks hain (100 MB tak, page ya mock ki koi limit nahi).
  - Ek paper ki questions + solutions PDFs.
  - Chapter book.
  - Excel.
- **Step 3: Details.** Sirf title aur rights ki confirmation. "Edition label" hata diya jayega. Wahi PDF dobara upload karne par purana upload hi khulega.
- **Step 4: Upload aur reading.** Progress, pause/resume aur auto-retry pehle jaise rahenge.
- **Step 5: "Students ko aise dikhega" preview.** Yahan dikhega:
  - Rasta: "Website aur App: Home › BITSAT › Mock Tests".
  - Us section ki poori list: pehle se live tests, aur aapke naye mocks unke baad.
  - Har mock ka status: Ready / Held (wajah ke saath) / Live.
- Mock ka exam ab upload par chuni jagah se aayega, isliye mock rules screen par exam alag se nahi poochha jayega. Printed rules (time, marks) pehle ki tarah har mock ke liye book se hi aayenge.

### 3. Publish: dono tareeke milenge
- Upload se kuch bhi apne aap live nahi hoga.
- **"Saare ready mocks publish karo":** ek click mein jo bhi mocks saare checks paas kar chuke hain, sab live. Chahein to "abhi" ya koi date/time chun sakte hain.
- **Har mock ka apna Live / Unlive switch.**
- Held mocks kisi bhi button se live nahi honge jab tak unki problem theek na ho.
- Students ko mocks seedhe section ki list mein dikhenge, book ka naam kahin nahi. Mock ka naam book par chhape naam se aayega (jaise "Mock Test 07"), aur aap use badal sakte hain.
- Alag "Book series" page hat jayega. Uske purane links us exam ke section mein khulenge.

### 4. Naya exam banana
- Exam ki details: naam, chhota naam, subjects, aur Home card ka rang (kuch taiyaar rangon mein se).
- Naya exam students ko tab tak nahi dikhega jab tak aap **"Home par dikhao"** na dabayein, chahe uske tests live hon. Wapas chhupana bhi ek click hai.
- Jab tak exam chhupa hai, students uske tests tak link se bhi nahi pahunch payenge. Aap "Student ki tarah dekho" se pehle check kar sakte hain.
- JEE Main, BITSAT, COMEDK aur All India card jaise hain waise hi rahenge. Naye exams unke baad aayenge.

### 5. Apne sections banana
- Kisi bhi exam mein naya section bana sakte hain, jaise "Revision Tests" ya "Crash Course".
- Section ki details: naam, ek line ka description, aur list ka tareeka: seedhi list (jaise Mock Tests) ya subject › chapter (jaise Chapter-wise).
- Exam page par sections aapke rakhe order mein dikhenge. Students ko section tabhi dikhega jab usmein kam se kam ek live test ho aur aapne use chhupaya na ho.
- JEE Main mein ab Mock Tests section bhi ho sakta hai. Abhi JEE Main ke mocks ka link PYQ par chala jaata hai. Yeh section tabhi dikhega jab usmein mocks live honge.
- Results section har exam mein apne aap rahega.

### 6. Pehle se maujood content apni jagah rahega
- 30 JEE Main PYQ papers, BITSAT mock book, chapter books, All India series, aur saare attempts, scores aur results wahin rahenge jahan students unhe abhi dekhte hain.
- Bas ab yeh sab "Exams & Content" mein unki sahi jagah par dikhenge. Students ke liye kuch bhi gayab nahi hoga ya jagah nahi badlega.
- Kisi test ko baad mein doosri jagah bhejne par bhi purane attempts aur scores bache rahenge.

### 7. App mein kahan dikhega
- App apne developer ka alag project hai aur wahi live API use karta hai jo website karti hai.
- Is phase mein naya structure (exams, sections, order, chhupana/dikhana) usi API mein aa jayega, aur app integration guide update hoga, taaki app bilkul wahi jagah dikhaye jo website dikhati hai.
- App ka apna code is project mein nahi badlega. App ke developer ko guide ke hisaab se update karna hoga.

## User flow (owner)
1. Owner login › Super Admin › **Overview** dikhega: "2 uploads reading, 28 mocks ready, 2 held".
2. **Add content** › BITSAT › Mock Tests › "Combined book" › PDF chuno › title › Upload.
3. Reading chalti rahegi, aap screen band kar sakte hain. Overview par progress dikhti rahegi.
4. "Students ko aise dikhega" preview: Home › BITSAT › Mock Tests › Mock 1–30 (2 held, wajah ke saath).
5. **Saare ready publish karo** dabao, ya kuch mocks ka switch alag se on karo.
6. Held mock ko Review mein theek karo, phir uska switch on karo.
7. Naya exam: Exams & Content › + Naya exam › NEET › sections banao › upload › publish › jab sab theek lage tab **Home par dikhao**.

**Student flow:** Home › exam card › section › test list › test shuru. Website aur app dono par yahi rasta.

## UI/UX feel
- Shaant, saaf workspace. Site ka maujooda dark theme aur brand rang hi rahenge.
- Desktop par baayein side fixed menu. Mobile par upar scroll hone wale tabs. Har screen par ek hi mukhya kaam.
- Wizard ke steps ek-ek karke, upar step bar ke saath. Mobile par har step poori screen par.
- Har jagah ek jaise status rang: Processing, Needs attention, Ready, Live, Hidden.
- Destination (Exam › Section) har upload aur har test par bade, saaf chip mein dikhega, taaki galat jagah ka shak hi na ho.
- Khaali jagahon par seedha agla kadam likha hoga, jaise "Is section mein abhi kuch nahi. Add content." Har action ke baad chhota toast confirmation.

## Implementation phases
**Phase 1 (MVP, abhi banega):** upar ke saare 7 features:
- 7 hisson wala Super Admin.
- Jagah-pehle upload wizard aur student preview.
- "Saare ready publish karo" aur har mock ka Live switch.
- Naya exam aur "Home par dikhao".
- Naye sections.
- Purane content ko catalogue mein lana, bina kuch badle.
- App ke liye API aur guide update.

**Phase 2 (baad mein, alag approval):**
- Tests par tags/filters.
- Kai tests ek saath doosri jagah bhejna.
- Kai books ki queue.
- Section ke hisaab se scheduling.
- Mushkil scans aur bilingual books ka support.
- Baar-baar aane wale publisher layouts yaad rakhna.
- All India series mein seedha upload.

**Phase 3 (baad mein, alag approval):**
- Exam ke hisaab se reviewers ko kaam baantna.
- Har exam aur section ki quality aur usage report.
- Bade paimane par bulk scheduling aur publishing.

## Assumptions (bina pooche liye gaye faisle)
- "Level" ka matlab upload form ka "Edition label" field samjha gaya hai. Woh hata diya jayega. Iske baad wahi PDF jaan-boojh kar doosri baar alag import nahi ho payega; wahi purana upload khulega.
- Pichle approved Phase 1 ka "checks pass hone par apne aap publish" wala checkbox hata diya jayega. Ab kuch bhi tabhi live hoga jab aap Publish dabayein ya switch on karein.
- Content Studio alag page ke roop mein nahi rahega. Uske saare tools Super Admin ke hisson mein chale jayenge, aur purane links naye hisse mein khulenge.
- Reviewers ko sirf Review hissa milega. Upload, publish, exams, sections, students aur team sirf owner ke paas.
- Purane uploaders (paper pair, chapter book) ki 50 MB limit aur unke format ke niyam waise hi rahenge. 100 MB aur koi page/mock limit nahi, sirf combined book ke liye.
- Chapter book ka maujooda format (har chapter 50 sawal) hi chalega. Wizard use sirf chapter-type sections mein dikhayega.
- Kisi section mein naye mocks pehle se live tests ke baad, book ke chhape order mein judenge. Order aap baad mein badal sakte hain.
- Naye exam ka Home card taiyaar rangon mein se ek lega. Maujooda chaar cards ke rang aur design nahi badlenge.
- All India JEE series catalogue mein dikhegi aur Schedule & Live se sambhali jayegi. Usmein seedha upload Phase 2 mein aayega.
- App ka code is project mein nahi badlega. Sirf API aur integration guide update honge.
- Saare purane tests, attempts, scores aur student accounts jaise hain waise rahenge. Koi data delete ya reset nahi hoga.
