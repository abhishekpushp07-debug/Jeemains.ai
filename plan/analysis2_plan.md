# JEELIVE.AI Analysis 2.0: jo baaki hai, uska poora plan

Har mock ke baad student ek hi jagah dekhega ki marks kahan bane, kahan gaye, time kahan gaya aur agle mock mein kya badalna hai.
Har number student ke apne jawab aur time se banta hai (koi AI nahi), aur website aur app dono ek hi server se lete hain.

## Kiske liye

- **Student:** mock ke turant baad saaf hisaab, phone par bhi. Har number ke peeche ke sawaal aur unka solution ek tap par.
- **Owner:** Quizrr ke har screen ke barabar ka analysis, uske aage ki cheezein, aur ek PDF report jo student WhatsApp par bhej sake.
- **App agent:** ek taiyaar packet, jisse app wahi screens usi server se bana sake.

## Core features aur experience

### Abhi ki haalat

Jo material dekha gaya:

- Purana plan (17 Nov, 6 hisson wala).
- Quizrr ki 14-page analysis PDF.
- Quizrr ke 12 screenshots: Overview (2), Leaderboard, Performance, Attempt Analysis, Time Analysis, Difficulty, Question Journey, Qs by Qs (2), Solutions (2).
- "Results: 60 analyses" guide, aur site ka apna purana analysis (25 insights, charts, 60-metric ledger).
- Embibe, Aakash, Allen aur PW ke public feature pages (naye ideas ke liye).
- Quizrr ke Comparative mode aur Compare screen ka koi screenshot nahi mila. Woh hissa apne design se banega.

Code padhne par jo mila (chalakar ya test karke nahi dekha gaya):

- Pichhle note mein likha tha ki screens sirf dhaancha hain. Yeh sahi nahi nikla. 8 sections, Personal/Comparative switch, Compare screen, Solutions ki ek line, time record, class ka data, PDF report aur share image, sab ka code likha hua hai aur Results page se juda hai.
- Is poore kaam ki ek bhi test report nahi hai. App packet abhi bana hi nahi.
- Record ke hisaab se yeh live par nahi gaya. Is baar live par check nahi kiya gaya.

Isliye baaki kaam do tarah ka hai: (1) jo likha hai use chalakar, test karke pakka karna, (2) neeche har section mein likhi "Baaki" cheezein banana.

### Ek baat jo pehle jaan leni chahiye

Rank, Percentile, class ka % sahi, students se bana Par time, Difficulty level aur Compare, yeh sab tabhi bharte hain jab usi paper ko doosre students ne bhi diya ho. 15 Nov ki report mein live par 14 student profiles the. Jab tak students kam hain, in jagahon par saaf message dikhega ("Abhi 3 students ne diya hai, 10 par khulega"), koi andaaza nahi. Student ka apna hisaab (Score, Time, Attempt Quality, Journey) pehle attempt se poora dikhega.

### Quizrr ke saamne

| Cheez | Quizrr (diye gaye screens mein) | JEELIVE, is plan ke baad |
| --- | --- | --- |
| 8 sections aur neeche ka bar | Hai | Hai |
| Attempt ke tags | 4 (Perfect, Wasted, Overtime, Confused) | 8, jisme Careless galti aur Concept gap alag hain |
| Score Potential | Sirf "galti kam hoti to Score" | 3 step, har step ke sawaal, aur us Score par Rank |
| Par time kahan se aaya | Nahi dikha | Har jagah likha hoga |
| Agle mock ke liye 3 kaam | Nahi dikha | Hai |
| Har sawaal ki journey Solutions mein | Hai | Banega |
| Painful questions | Hai | Banega |
| "Note down your learnings" | Hai | Banega ("Is test se 3 seekh") |
| Leaderboard par naam aur Compare | Hai | Banega, naam student khud likhega |
| Jawab badalne ka hisaab | Nahi dikha | Banega |
| Pehli nazar vs wapas aakar | Nahi dikha | Banega |
| Speed–Accuracy map | Nahi dikha | Banega |
| Har number par "yeh kaise bana" | Chhota (i) | Poora hisaab aur ginti |
| Bhasha | English | Roman Hinglish |

### 1. Overview

Likha hua hai: Score ring, Rank, Percentile, Accuracy, Time, Attempted / Sahi / Galat / Chhode (tap par sawaal), har subject ka card, "Agle mock ke liye 3 kaam".

Baaki:

- Sabse upar ek line ka nateeja, data se bana. Jaise: "Accuracy 100% thi, lekin 16 sawaal chhoot gaye. Sabse zyada marks yahin gaye."
- "Marks ka hisaab": Positive Score, negative mein kate marks, aur galat ya chhode sawaalon mein reh gaye marks.
- "Aap kahan khade ho": sab students ke Score ka chart, student ka hissa alag rang mein. Rank par tap karne se Leaderboard khulega.
- "Is test se 3 seekh": student 3 tak chhoti baatein likhega. Yeh agle mock ke Overview par aur PDF mein dikhengi.
- Har number par (i): number ka matlab aur woh kaise gina gaya.
- Akela student ho ya khud topper ho, to saaf message.

### 2. Performance

Likha hua hai: subject tabs; Score, Accuracy, Attempt rate, Negative marks; MCQ vs Numerical; chapter table (Mazboot / Theek / Kamzor).

Baaki:

- Sab subjects ki ek table: Score, Sahi, Galat, Chhode, Dekha hi nahi.
- Chapter par tap karne se uske sawaal.
- "Kamzor chapter" ki list, gaye hue marks ke hisaab se.
- BITSAT ke sections aur bonus section ka Score yahin.
- Jis paper mein chapter ka tag nahi, wahan saaf likha hoga.

### 3. Score Potential

Likha hua hai: step chart (abhi, + Careless galti theek, + mushkil par risk nahi, + atka time wapas, Realistic target, Maximum), har step ke sawaal, "itne marks par Rank lagbhag".

Baaki:

- "Marks kis chapter se gaye": galat sawaal chapter ke hisaab se.
- "Bina galat jawab ke Score": har galat jawab chhoda hota to kitna banta.
- Guess ka niyam: is paper ki marking par kitna pakka hone par hi guess faydemand hai (+4 / −1 par 20%).
- Time record na ho to kaun se step 0 hain, yeh saaf likha hoga.

### 4. Attempt Quality

Likha hua hai: 5 bade cards (Perfect, Careless galti, Overtime, Confused, Concept gap), baaki tags, subject × tag table, bars, tap par sawaal.

Baaki:

- Speed–Accuracy map: har sawaal ek dot (kitna time laga vs Par, sahi ya galat). Dot par tap se solution.
- "Jaldi-sahi" note: jo sahi jawab Par ke 25% se kam time mein aaye. Tukka tha to concept ek baar dekh lene ki salah. Yeh alag tag nahi hai.
- "Painful sawaal": galat bhi aur Par se zyada time bhi, chapter ke hisaab se.
- Chart par har tag on/off.

### 5. Time kahan gaya

Likha hua hai: paper mein laga time, screen par time, sahi / galat / bina jawab par time ki patti, subject chart (Time / Questions / Accuracy), time journey blocks, pace curve, sabse dheeme 5 sawaal.

Baaki:

- Screen se bahar gaya time alag dikhega.
- "Pehli nazar vs wapas aakar": pehli baar mein diye jawab aur laut kar diye jawab, dono ki ginti, Accuracy aur time.
- "Aakhri 20% time": aakhir mein Accuracy giri ya nahi.
- Har subject ka time ka hissa vs marks ka hissa ("Physics par 45% time, 30% marks").
- Line chart par Sahi / Galat / Sab on/off.

### 6. Difficulty

Likha hua hai: subject tabs, Easy / Moderate / Tough / Not rated ki table (har khana tap hota hai), bars, "Leak: Easy sawaal".

Baaki:

- Har level ke saath likha hoga ki woh kahan se aaya (students ke result, paper ka tag, ya Not rated) aur kitne students par.
- "Tough jo aapne nikale": class mein 35% se kam sahi, student ka sahi.
- Not rated zyada ho to: "itne aur students ke baad level khulega".

### 7. Question Journey

Likha hua hai: har visit ka chip, time block ke hisaab se; kaun si baar dekha, kitna time, mark for review, jawab badla; tag ka rang on/off; ek line ka saar; subject order.

Baaki:

- Chip par result aur tag ka icon (sirf rang nahi), aur ek legend.
- Jawab badalne ka hisaab: galat se sahi, sahi se galat, galat se galat, aur isse kitne marks bane ya gaye.
- Sabse lambi sahi aur galat streak, asli solving order mein.
- Lambi journey mein time block fold ho sakenge.

### 8. Qs by Qs

Likha hua hai: desktop par table, phone par cards, 8 filters, row par tap se solution.

Baaki:

- Upar sawaalon ka grid: subject aur MCQ / Numerical ke hisaab se; har number par result ka icon, tag, aur class mein kitne % ne sahi kiya uska halka rang.
- Sort (time, marks, sawaal number) aur subject / level filter.
- "Dekha hi nahi" aur "Dekha, jawab nahi diya" alag.
- Comparative mode mein class ka average time aur topper ka time.

### 9. Solutions screen

Likha hua hai: har sawaal ke upar ek line (subject, level, aapka time, Par, kitne % sahi, topper ka time, sabse zyada chuna galat option, kitni baar dekha, jawab badla, tag); Careless / Overtime / Confused filter.

Baaki:

- Chaar cards: aapka time vs Par; class ka average time aur topper ka time; attempt karne walon mein kitne % sahi aur galat; kitne % ne attempt kiya aur kitne ne chhoda.
- Is sawaal ki journey: khola, chhoda, dobara khola, option diya, badla, har kadam ke saath time.
- Number ki patti par result aur tag ka rang aur icon. Naye labels Hinglish mein.

### 10. Comparative mode, Leaderboard, Compare screen

Likha hua hai: Personal / Comparative switch; Topper, Top 10%, Class average aur top 10 students ki list; aap vs woh ke cards; "gap sabse bada kahan"; subject chart aur table; Attempt Quality table; dono pace curve; Difficulty par Accuracy; live exam ke leaderboard se Compare screen.

Baaki:

- Leaderboard har us paper par jahan class ka data hai: top 50, student ke aas-paas ke 5 upar aur 5 neeche, naam ya Rank se search, har row par Compare.
- Chunne ki list mein "Aapse ek Rank upar".
- "Gap ka hisaab": gap ke kitne marks kam attempt se hain aur kitne galat jawab se, subject ke hisaab se.
- Har section mein compare ka apna hissa (Journey mein kul visits aur wapsi; Qs by Qs mein class ke columns).
- Har subject par laga time, dono ka saath-saath.
- Doosre student ke jawab kabhi nahi dikhenge. Sirf totals, averages aur time.

### 11. Display naam (naya)

- Student Profile mein ya Leaderboard par apna naam likhega. Phone number kabhi nahi dikhega.
- Naam na likhe to pehle jaisa "Learner AB12CD34".
- Naam Leaderboard, Compare, apni PDF ke cover aur apne scorecard par dikhega.
- Owner Super Admin › Students se kisi ka naam hata sakega.

### 12. Download aur Share

Likha hua hai: Hinglish A4 PDF report (har section ki tables aur bars), WhatsApp ke liye scorecard image, file ka naam `JEELIVE_<paper>_<date>`.

Baaki:

- PDF mein cover, contents, charts (Score ring, marks ka hisaab, pace curve, time blocks, Speed–Accuracy map), Question Journey, "3 seekh" aur tags ke matlab.
- PDF phone par khulti hai ya nahi, yeh check.
- Results page par do alag download, saaf naam ke saath: "Analysis report" aur "Solutions PDF" (purani, solutions wali).

### 13. Purana analysis

- Naye analysis ke neeche jo purana English fold hai, woh hatega.
- Uski kaam ki cheezein naye sections mein Hinglish mein jayengi: Score ka chart, subject par aap vs average vs top, sawaalon ka heat map, negative se gaye marks, bina galat ke Score, streak, aakhri hisse ki Accuracy, guess ka niyam, Easy chhoote aur Tough nikale.
- 60-metric ledger aur offline drafts wali screen ek chhoti "Advanced" link ke peeche rahegi, jaisi hai.
- Analysis tab par upar ke purane Score tiles nahi dikhenge, kyunki wahi cheez Overview mein hai.
- Progress, Confidence, Real-exam rank / Branch matches aur Solutions tabs jaise hain waise rahenge.

### 14. Har section par laagu

- Har comparison ke saath class ka size ("23 students mein").
- Khaali ya band haalat mein wajah aur kab khulega: live exam chal raha hai, result ban raha hai, class ka data ban raha hai, purana attempt, staff ka attempt, corrected Score.
- Purane attempts: Time, Attempt Quality aur Journey "Agle mock se shuru hoga" dikhayenge. Baaki sab chalega.
- Ek hi request mein poora analysis. Pichhla khula analysis bina internet ke bhi dikhega.

### 15. Time record aur app packet

Likha hua hai: website ka player har sawaal ka screen time, jawab badalna aur mark for review record karta hai. Refresh ya crash par record nahi jaata, aur jawab save ke saath hi server par jaata hai.

Baaki:

- Ise bheed mein chalakar pakka karna (answer save dheema na ho).
- App packet: server calls ki guide, analysis ka format, rulebook, har screen ka spec aur uski haalatein, app ke player ke liye time record ka spec, rang aur font, sample data, test checklist. Display naam, Leaderboard aur "3 seekh" ke calls bhi isi mein.

### Rulebook (pehle se tay, yahan ek jagah)

- **Par time:** 30 ya zyada students ne sahi kiya ho to unka beech ka time. Warna paper standard (paper ke 90% time ka hissa; Numerical ko MCQ se zyada).
- **Tags:** Perfect (sahi, Par ke 1.25 guna tak). Slow-correct (sahi, usse zyada). Careless galti (galat, Par ke aadhe se kam mein). Concept gap (galat, Par ke 0.5 se 1.5 guna). Mehnga overtime (galat, 1.5 guna se zyada). Confused (jawab nahi, par Par ke aadhe se zyada time). Smart skip. Dekha hi nahi. Har sawaal ko ek hi tag.
- **Difficulty:** 50 ya zyada students ne attempt kiya ho to: 65% ya zyada sahi = Easy, 35% se kam = Tough, beech mein Moderate. Warna paper ka apna tag. Warna Not rated.
- **Class aur Top 10% average:** kam se kam 10 students. **Topper:** kam se kam 2 students.
- **Realistic target:** abhi ka Score + Careless + mushkil par risk + time wale step ka aadha.
- **Time:** sirf screen par khula time. Tab chhupa ho to nahi ginta. Ek baar mein zyada se zyada 15 minute.
- **Naye:** Jaldi-sahi = Par ke 25% se kam. Painful = galat aur Par se zyada time. Aakhri hissa = paper ke aakhri 20% time, tabhi jab dono taraf 5 ya zyada jawab hon.

## User flow

1. Student mock submit karta hai. Result khulta hai, Analysis ka Overview saamne hota hai.
2. Upar ek line ka nateeja, phir Score, Rank aur "3 kaam".
3. Kisi number par tap: uske sawaalon ki list. Sawaal par tap: uska solution, upar time, class ka data aur us sawaal ki journey. Back: wahi chart, wahi jagah.
4. Neeche ke bar se ya swipe se agla section.
5. "Comparative" par switch: Topper, Top 10%, Class average ya Leaderboard ka koi student.
6. Rank par tap: Leaderboard. Kisi student par Compare: aap vs woh.
7. "Is test se 3 seekh" likhta hai.
8. "Analysis report" download karta hai ya scorecard WhatsApp par bhejta hai.
9. Agle mock ke Overview par pichhli 3 seekh dikhti hain.

## UI/UX feel

- Wahi dark theme (kaala aur blood red) aur wahi fonts.
- Ek card, ek baat: bada number, neeche ek seedhi line.
- Sahi, galat aur chhoda: rang ke saath icon bhi.
- Har chart ke saath wahi data table mein.
- Neeche chipka hua bar: Personal / Comparative aur 8 sections. Phone par swipe.
- 360 se 390 px ke phone par poora chalega. Chaudi table apne dabbe ke andar scroll hogi.
- Halka motion: section badalne par aur bars bharne par.
- Copy Roman Hinglish mein ("Time kahan gaya", "Careless galti", "Yahan se marks bach sakte the"). Score, Rank, Accuracy, Time, Percentile, Par English mein.

## Implementation phases

**Phase 1 (abhi banega):** upar likha poora Analysis.
- Jo likha hua hai use chalakar aur test karke pakka karna.
- Har section ki "Baaki" cheezein.
- Solutions screen ke cards aur sawaal ki journey.
- Har paper par Leaderboard, "koi bhi student" se Compare, display naam.
- Naya PDF, scorecard, purane analysis ka naye mein milna.
- App packet.
- Sirf preview mein. Live par tabhi jab "deploy" kaha jaye.

**Phase 2 (alag approval):**
- Sign-in rate limiter fix: student ka asli IP padhna aur sirf galat PIN ginna. Analysis dikhane ke turant baad.
- Mock se mock ka trend: pichhle 5 mocks mein Careless, Overtime aur galat par gaya time.
- Owner Master mein har sawaal ka Difficulty aur chapter tag set kar sake, taaki kam students par bhi Difficulty bhari rahe.
- Subject ke hisaab se Rank aur Percentile.
- Galti notebook: sab mocks ke galat aur chhode sawaal ek jagah, dobara practice ke liye.

**Phase 3 (alag approval):**
- 1 se 2 lakh students ek saath ka load test.
- Owner ke liye paper report: kaun sa sawaal sabse zyada galat hua, kaun sa galat option sabse zyada chuna gaya.
- Agle mock ka target Score aur uska follow-up.

## Assumptions

1. Naya Analysis, Solutions ke naye hisse aur PDF Roman Hinglish mein. Results page ke baaki purane labels English mein rahenge.
2. Section ke naam: Overview, Performance, Score Potential, Attempt Quality, Time kahan gaya, Difficulty, Question Journey, Qs by Qs.
3. Compare: Topper, Top 10%, Class average, aur Leaderboard ka koi bhi student.
4. Quizrr ke Comparative screens nahi mile, isliye woh hissa apne design se.
5. Revision PDF nahi banega, kisi phase mein nahi.
6. Display naam: 2 se 20 akshar; akshar, ank aur space. Phone number jaisa naam (6 ya zyada ank ek saath) nahi chalega. Gaaliyon ki ek list block hogi. Din mein 3 baar se zyada nahi badlega. Do students ek hi naam rakh sakte hain; naam ke saath Rank dikhta hai.
7. Koi student kisi aur ka naam likh sakta hai. Rok sirf owner ka "naam hatao" hai.
8. Leaderboard ya Compare se bahar rehne ka option Phase 1 mein nahi hai. Naam na likhne par student Learner ID ke peeche rehta hai.
9. Compare mein doosre student ka har sawaal par time aur uske totals dikhte hain, jawab nahi.
10. Rulebook ke number (30, 50, 10) nahi badle. Is wajah se abhi ke kam students par Difficulty aksar "Not rated" aur Compare aksar band dikhega.
11. Sawaal ki journey mein time "paper shuru hone ke kitne minute baad" likha hoga, ghadi ka time nahi.
12. "3 seekh" sirf usi student ko dikhengi. Har seekh 140 akshar tak.
13. PDF 8 se 12 page ki hogi (75 sawaal ke paper par). Naam cover par tabhi, jab student ne likha ho.
14. Scorecard par Score, Rank, Percentile, Accuracy aur naam (agar likha ho). Phone number kabhi nahi.
15. Purana English fold hatega; 60-metric ledger "Advanced" link ke peeche rahega.
16. Purane download button ka naam "Solutions PDF" hoga.
17. Class mein har student ka usi paper par pehla attempt ginta hai. Owner aur reviewer ke attempts nahi ginte. Live paper ka class data window band hone ke baad banta hai.
18. Purane attempts mein time record nahi hai, isliye unke teen time wale sections khaali rahenge.
19. App ke attempts mein time record tabhi aayega jab app agent packet ke hisaab se player badle. Tab tak app se diye mocks mein bhi wahi teen sections khaali.
20. Koi AI nahi, koi AI credit nahi.
21. Rate limiter fix Analysis ke baad alag se hoga. Yeh pehle ki "dono saath mein dikhao" wali baat ki jagah leta hai.
22. Phase 1 lagataar banega, har hissa test hoga, aur sab ek saath dikhaya jayega. Deploy sirf "deploy" kehne par.
23. Quizrr ke screenshots ek image reader se padhe gaye. Chhoti detail mein fark ho sakta hai.
