# JEELIVE.AI — Naya World-Class Look (Home, Test Screen, All India Series aur baaki screens)

App ka dark look aur JEELIVE laal rang wahi rehte hain. Design CRED jaisa saaf aur premium banta hai, aur Wit Circle jaisa exam-focused.
All India Test Series soft pastel rangon mein dikhti hai. Har din ka rang uske status se tay hota hai, aur din-ba-din score graph bhi milta hai.

Mockups (sirf rang-roop dikhane ke liye; number example hain, app mein asli data dikhega):
- Home: `home-v2-b.svg` (chuna gaya Option B — Journey First)
- Test dene wali screen: `player.svg`
- Question palette: `player-palette.svg`
- All India Series hub: `series-hub.svg`
- Teeno Home options ki tulna: `home-options.md`

## Kiske liye
- JEE Main, BITSAT aur COMEDK ki taiyari karne wale students, jo roz app kholte hain aur ek nazar mein dekhna chahte hain:
  - aaj kya karna hai
  - unki progress kahan tak pahunchi hai
- App owner, jo chahte hain ki app beautiful, elegant aur professional dikhe.

## Core features aur experience

### Sab screens par ek design language
- Section ke upar chhote, faile hue CAPITAL headings, halke grey rang mein. Daayein "view all ›" link, jahan poori list ho.
- Patli border wale, gol kinaron ke cards. Zyada khaali jagah, kam bheed.
- Gol pill buttons. Har screen par ek hi mukhya button, jo sabse saaf dikhe.
- Bottom bar: icon ke neeche faile CAPITAL labels; chuna hua tab chamakdaar, baaki dhundle.
  - Wahi 5 tabs, wahi kram.
  - Beech ka ubhra hua Rapid Fire button apne diamond look mein, halki laal roshni ke saath.
- Dark rang, JEELIVE laal, exam ke rang (JEE laal, BITSAT orange, COMEDK graphite) aur Figtree font wahi rehte hain.
- All India ke pastel status rang, poori app mein ek jaise:

| Status | Rang |
|---|---|
| Aaj / Live | peach-rose |
| Ho gaya | mint-aqua |
| Aane wala | lavender-periwinkle |
| Chhoot gaya | sand-blush |

### Home — Option B "Journey First"
1. **Upar:** logo aur account button. Session khatam hone ki maujooda notice zaroorat padne par wahi rehti hai.
2. **Bada All India card (sabse upar):** aaj ke status ke pastel rang mein. Isme ye sab hai:
   - Apple Fitness jaisi progress ring: kitne din ho gaye, jaise 16/62 aur 26%.
   - Aaj ke test ka naam aur jaankari: questions, samay, marking.
   - Current streak aur kitne din chhoote.
   - "100% AI" badge.
   - Ek bada button, jo halat ke hisaab se badalta hai: "Start today's test" / "Resume" / "View result" / "Opens 1 Dec".
   - Card par halki chamak (shine). Use rokne ka chhota control rehta hai.
3. **Continue row:** sirf jab koi test adhoora ho. Test ka naam, kitne answers save hue, bacha samay, aur "Resume" button.
4. **EXAMS:** 2×2 grid, aapki 3D art aur PYQ / 100% AI badges ke saath.
   - Art tile ke upar-daayein kone se thoda bahar "uchhalti" dikhti hai, peeche exam rang ki halki roshni ke saath (premium 3D feel).
   - Naam aur subtitle neeche-baayein.
   - Live JEE Series ka tile aaj ke status ke pastel rang mein. Baaki teen tiles dark, apne exam rang ki chamak ke saath.
5. **MY TESTS:** teen chhote stat cards (In progress, Saved, Completed), har ek ki ginti ke saath. Tap karne par My Tests usi tab par khulta hai.
6. **Rapid Fire:** patla entry card. Sirf frame naya, Rapid Fire khud nahi badalta.
- Koi search bar ya shortcut pills nahi.

### Test dene wali screen (world-class, NTA jaisa jaana-pehchaana)
**Upar ki patti**
- Bahar nikalne ka button aur test ka naam.
- "Saved / Saving / Offline" status, jaisa abhi hai.
- Bada timer pill: aakhri 10 minute mein amber, aakhri 2 minute mein laal.
- Laal "Submit" button.
- Neeche ek patli progress line: kitne sawaal attempt hue.

**Subject aur sawaal**
- Subject tabs (Physics / Chemistry / Maths) ek gol segmented pill mein, har subject ki ginti ke saath (jaise 12/25).
- Sawaal ka header: "Q 11 of 75", sawaal ka type (jaise Single correct), marking (+4 · −1), bookmark star aur zoom button.
- Sawaal ek saaf card mein, bade padhne-layak text aur zoom hone wali images ke saath.

**Options aur jawab**
- Options bade tap-cards hain, A/B/C/D gol ghere mein.
- Chuna hua option laal border, laal ghere aur ✓ ke saath.
- Numerical sawaal mein bada answer box.
- "How sure?" (Guess / Unsure / Sure) optional rehta hai, jaisa abhi hai.

**Neeche ki patti (angoothe ki pahunch mein)**
- Teen buttons: "Mark for review" (purple outline), "Clear", aur bada safed "Save & Next".
- Usse neeche ek patli line: "38 answered · 5 marked · 32 left" aur "Palette" button.

**Question palette (neeche se upar aane wali sheet)**
- Subject tabs.
- Ginti ke saath legend.
- Gol rangeen number-bubbles, NTA jaise jaane-pehchaane rangon mein:
  - Answered = hara
  - Not answered = laal
  - Marked for review = purple
  - Answered & marked = purple, hare dot ke saath
  - Not visited = grey
- Abhi wale sawaal par safed ghera.
- Kisi bubble par tap karne se wahi sawaal khulta hai.
- Neeche "Back to question" aur "Submit test".

**Submit se pehle**
- Confirm sheet har subject ki ginti dikhati hai: answered, marked, not answered.

**Jo nahi badalta**
- Saving, timer, resume, conflict handling aur submit ka saara logic.
- BITSAT bonus lock.
- Bahar nikalne par guard.

### All India Test Series hub (gehri soch ke saath, ek hi scroll page)
1. **Header:** "All India Series", "62 DAYS · FULL SYLLABUS" eyebrow, aur "i" button jo "How it works" kholta hai. "Score 200+ with AI" aur "Created by AI Astra" yahin rehte hain.
2. **Journey card:**
   - Badi progress ring (16/62 days).
   - Current streak, best streak aur skipped din.
   - Cups ki milestone line (7, 14, 30, 62 din). Jeete hue cups sunehre, baaki tale ke saath.
3. **TODAY card:** pastel rang mein.
   - Din aur tareekh, test ka naam, questions/samay/marking.
   - Chhota countdown "Last start in 3h 12m".
   - Bada button jo halat ke hisaab se badalta hai: "Check device & start" / "Resume live attempt" / "Open live result".
4. **ALL DAYS patti:** 1 se 62 tak din ke chhote pastel chips, side-swipe. Khulte hi aaj ke din par aati hai. Kisi din par tap karne se neeche us din ka bada card aata hai:
   - Ho chuka din: score (jaise 212/300) aur "View result".
   - Pichhla din: "Practise this paper" (archive).
   - Aane wala din: kab khulega.
   - Result abhi nahi aaya: "Results at 11:59 PM".
5. **SCORE TREND graph:** din-ba-din score ki line.
   - Best score sunehre nishaan se.
   - Average aur best upar likhe hote hain.
   - Chhoote din graph mein khaali jagah (dashed) ke roop mein.
   - Kisi point par tap karne se us din ka result khulta hai.
   - Sirf wahi din dikhte hain jinka result aa chuka hai. Pehle result se pehle ek pyara khaali-state message.
6. **MY RESULTS:** pastel mint cards ki list: din, test ka naam, score, aur ">" teer.
7. **62-DAY MAP:** GitHub jaisa rangeen chaukor-grid. Saare 62 din status ke rang mein, neeche rang-guide ke saath. Aage aane wale din halke rang mein.
- Pull-to-refresh, honest khaali/error states aur 12:01 AM – 11:59 PM IST ke niyam wahi rehte hain.

### Exam hubs aur paper lists
- Exam hub (JEE Main, BITSAT, COMEDK): upar exam art aur naam, neeche spaced headings ke saath sections (PYQ, Chapters, Mocks).
- Subject chips gol pill style mein.
- Paper ki har row ek saaf card hai:
  - naam
  - saal/shift ya questions/samay
  - chhoti rangeen status line
  - daayein pill button: Start / Continue / Result + Re-attempt
- Paper detail (start se pehle ki screen) bhi isi style mein.
- Search, filters, pages, pull-to-refresh aur honest empty states wahi rehte hain.

### My Tests
- Teen tabs (In progress, Saved, Completed) ek gol segmented pill mein.
- Har test card patli border ke saath, upar status ki rangeen patti aur saaf pill actions.
- Exam/status chips, search aur compare wahi rehte hain.

### Mission aur Account
- **Mission:** spaced headings, gol line icons ke saath chhote points (AI se bana content, 80-parameter PYQ analysis, poori tarah free), aur ek bold "Share" button.
- **Account:**
  - Upar profile card (phone ke aakhri 4 ank).
  - Neeche groups mein list rows: "SECURITY" (Change PIN), "PRIVACY", "ACCOUNT" (Delete account, Sign out).
  - Change PIN, Privacy aur Delete account ke andar ke pages bhi isi style mein.

### Jo bilkul nahi badlega
- Rapid Fire ki saari screens.
- Result aur Solutions screens (Phase 2 tak abhi jaisi).
- Login aur ye saare flows: data, website ke saath sync, caching, speed, logout se bachane wala system.
- Koi bhaari image nahi. Pastel, rings, graph aur map sab code se bante hain, isliye app ka size nahi badhta.

## User flow
1. App khulta hai, Home dikhta hai. Sabse upar pastel All India card hai: ring dikhati hai kitne din ho gaye, aur ek tap mein aaj ka test shuru hota hai.
2. Agar koi test adhoora hai, to Continue row se ek tap mein wapas test par.
3. EXAMS se JEE Main → JEE hub → PYQ list → Start. Test screen khulti hai.
4. Test mein:
   - subject tabs se subject badlo
   - option tap karo
   - "Save & Next" dabao
   - "Palette" se kisi bhi sawaal par jao
   - "Submit" → har subject ki ginti dekho → confirm
   - Result abhi jaisa khulta hai.
5. All India card ya "view all" → series hub: journey ring, aaj ka card, din-patti, score graph, results aur 62-din ka map.
6. My Tests ke stat card (jaise "Saved") → My Tests usi tab par.
7. Bottom bar se kabhi bhi Home, JEE Main, Rapid Fire, My Tests ya Mission. Account upar ke button se.

## UI/UX feel
- Beautiful, elegant, professional: shaant dark background, patli lines, zyada khaali jagah. Rang sirf jahan matlab ho: exam ki pehchaan, status ki pehchaan, aur All India ke pastel.
- CRED aur Wit Circle sirf inspiration hain, copy nahi. Look JEELIVE ka apna aur unse bhi sundar banta hai.
- Test screen par sab kuch padhne aur jaldi tap karne ke liye bana hai: bada text, bade options, mukhya buttons angoothe ki pahunch mein.
- Har tap target kam se kam 44px; 320px chhoti screen par bhi kuch nahi katta.
- Halke fade/slide animations, ring bharne aur graph banne ka chhota animation. Phone par "reduce motion" on ho to sab animation band.

## Implementation phases

**Phase 1 — MVP (abhi banega)**
- Nayi design language aur naya bottom bar.
- Home — Option B "Journey First".
- Test dene wali screen, question palette aur submit confirm.
- All India Series hub: journey ring, today card, din-patti aur din card, score trend graph, results, 62-din ka map. Home ka All India card aur Live tile bhi.
- Exam hubs, paper lists aur paper detail.
- My Tests.
- Mission, Account aur Account ke andar ke pages.

**Phase 2 — Baaki screens**
- Result aur Solutions isi style mein (analysis cards, subject-wise score rings).
- Login/entry aur Forgot PIN isi style mein.

**Phase 3 — Polish**
- Loading ke waqt naye style ke skeleton cards.
- Tap par halki vibration aur press animations.
- Tablet / badi screen aur test screen ke liye landscape layout.

## Aapke chune hue faisle
- Dark look hi rahega.
- Nayi design in screens par: Home, Exam hubs aur paper lists, My Tests aur All India Series, Mission aur Account. Test dene wali screen bhi ab Phase 1 mein ("jo world best ho").
- Home par 2×2 exam grid, naye style mein.
- All India cards soft pastel gradients mein, rang status ke hisaab se.
- All India mein din-ba-din score graph.
- Home par koi search bar ya shortcut pills nahi.
- Home ka layout: Option B — Journey First.

## Assumptions (bina pooche liye gaye faisle)
- **Question palette ke rang NTA jaise:**
  - hara = answered, laal = not answered, purple = marked, purple + hara dot = answered & marked, grey = not visited.
  - Abhi app mein marked laal aur answered & marked sunehra hai. Ye badal jaayega, kyunki students ko asli exam se yahi rang yaad hote hain.
- **"Save & Next" naam NTA jaisa.** Saving pehle ki tarah apne aap hoti rehti hai; button bas agle sawaal par le jaata hai.
- **Timer ka rang:** aakhri 10 minute mein amber, aakhri 2 minute mein laal. Ye chhota naya kaam hai.
- **Submit confirm sheet** mein har subject ki ginti dikhegi.
- **All India hub ke tabs hate:** "Live & schedule / Archive / My results" ki jagah ab ek hi scroll page hai. Archive ke din din-patti aur 62-din ke map se khulte hain.
- **"Skipped" din:** wo pichhla live din jismein aapka live attempt nahi hua.
- **Score graph** sirf live attempts ke released results dikhata hai. Archive practice ke score graph mein nahi milte.
- **Home ka All India card:**
  - "100% AI" badge rakhta hai.
  - "Score 200+ with AI" aur "Created by AI Astra" series hub ke header aur "How it works" mein chale jaate hain, taaki Home saaf rahe.
- **Series shuru hone se pehle** Home card lavender rang mein "Opens 1 Dec" dikhata hai. Series khatam hone ke baad archive dikhata hai.
- **Home ka Live JEE Series tile** bhi pastel status-rang leta hai. Baaki teen tiles dark rehte hain.
- **Beech ka Rapid Fire button** diamond hi rehta hai, kyunki Rapid Fire nahi badalna.
- **Labels normal case mein,** sirf section headings aur status lines CAPITAL mein.
- **Maujooda badges (PYQ, 100% AI) rehte hain.** Shine rokne ka control chhote icon ke roop mein rehta hai.
- **Layout website se alag dikhega,** par rang, font aur saara content website jaisa hi rehta hai.
