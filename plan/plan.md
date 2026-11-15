# JEELIVE.AI Super Admin: Ek Master

Ek hi screen jahan exam banta hai, exam ke andar mock type judta hai, aur mock type ke andar PDF upload karke ya likh kar mock banta hai.
Har mock ka status wahin badalta hai, aur All India Test Series har exam ke liye Home par apna alag card pati hai.

## Kiske liye

- **Owner (Super Admin):** exam, mock type, mock, status, series. Sab kuch ek jagah se.
- **Reviewer:** sirf woh mocks jinme kuch theek karna hai, aur students ke question reports.
- **Students:** website aur app par wahi dekhte hain jo Master mein Live hai.

## Core features and experience

### 1. Ek Master screen, teen level

Exam › Mock type › Mock. Upar hamesha raasta dikhta hai, jaise `Master › JEE Main › Mock Tests`.

Master ke upar ek patli line batati hai ki aaj kya dekhna hai, jaise "4 mock theek karne hain · 12 Live ke liye taiyaar · 3 student reports". Click karne par wahi mocks khulte hain.

Upar teen chhote links rehte hain: **Library, Students, Team**.

### 2. Naya exam

"+ New exam" par chaar cheezein: naam, chhota naam, subjects, card ka rang. Naya exam students se chhupa rehta hai jab tak "Show on Home" na dabaya jaye.

### 3. Mock type jodna

Exam ke andar "+ Add mock type" par paanch vikalp:

| Type | Students ko kaise dikhta hai |
|---|---|
| PYQ | Papers saal ke hisaab se |
| Mock | Poore papers ki seedhi list |
| Chapter-wise | Subject › Chapter |
| All India Test Series | Roz ek paper, rank ke saath, Home par alag card |
| Apna type | Naam owner deta hai (jaise Revision Tests), list seedhi ya Subject › Chapter |

Har type ka naam badal sakta hai, upar-neeche ho sakta hai, students se chhup sakta hai, aur uska apna default time aur marks hota hai. Students ko ek type tabhi dikhta hai jab usme kam se kam ek Live mock ho.

### 4. Mock banana: PDF upload

- Ek box mein main PDF. System khud dekhta hai ki usme ek mock hai ya kai. "File type" nahi poochha jaata.
- Ek hi PDF mein questions, answer key aur solutions teeno hon to teeno wahi se liye jaate hain.
- Alag-alag hon to do aur optional box hain: **Answer key PDF** aur **Solutions PDF**.
- Chapter-wise type mein har chapter alag test banta hai. Baaki types mein har chhapa hua mock ya paper alag test banta hai.
- Padhna peeche chalta rehta hai; screen band kar sakte hain. Progress usi mock type ki list ke upar dikhta hai.
- Har mock Draft ban kar list mein aata hai. Jis question ko system pakka nahi padh paya, us mock par "Draft · 3 to fix" dikhta hai aur "Fix" button khulta hai: question ki photo, jawab ka type, sahi jawab, save.
- Answer key ke bina mock Live nahi ho sakta. Solution ke bina ho sakta hai (sirf answer key ke saath).
- Koi AI credit apne aap kharch nahi hota.

### 5. Mock banana: Write

Pehle mock ka naam. Time aur marks type ke default se bhare aate hain.

- **Ek-ek question:** subject (chapter-wise mein chapter bhi), question ka text (maths ke saath) aur chaho to photo, jawab ka type (options ya numerical), options A–D (text ya photo), sahi jawab, solution (text ya photo, optional). "Save & next".
- **Poora paper paste:** poora text chipkao. System questions, options, answer key aur solutions alag karta hai aur list dikhata hai. Jo saaf nahi hai us par nishaan lagta hai aur woh ek-ek wale form mein theek hota hai.

Dono tareeke ek hi mock mein mil sakte hain. Likha hua mock kabhi bhi wapas khol kar badla ja sakta hai.

### 6. Har mock ka status

| Status | Matlab |
|---|---|
| Draft | Sirf owner ko dikhta hai |
| Live | Students ko dikhta hai |
| Scheduled | Chuni hui date aur time (IST) par apne aap Live |
| Off | Students se chhupa; scores surakshit |
| Library | List se hata, Library mein surakshit, wahan se wapas aa sakta hai |

- Har mock ki row par ek status button; ek click mein badalta hai.
- Kai mock chun kar, ya "Select all" se, ek saath status badalta hai.
- Schedule karte waqt ek switch "Live exam": sab students ek saath dete hain, 15 minute ka start window, turant score, rank. Switch ke bina mock us time se practice ke liye khul jaata hai.
- Jis mock mein kuch theek karna baaki hai woh Live ya Scheduled nahi ho sakta; wajah saath mein dikhti hai.
- Naye PDF se purane mock badalna (ek, kuch ya sab) rehta hai: purane tab tak Live rehte hain jab tak naya Live na ho, phir Library mein jaate hain.
- Students ke purane attempts aur scores hamesha rehte hain.

### 7. All India Test Series, har exam ke liye

- Jodte waqt: shuru ki date, kitne din, roz khulne ka time, aur start karne ka aakhri time (IST).
- Andar din ki list dikhti hai (Day 1 · 1 Dec, Day 2 · 2 Dec …). Paper PDF se ya likh kar bante hain, phir har paper ko din milta hai: ek-ek karke, ya "Fill days in order" se.
- Paper apne din se pehle students ko nahi dikhta. Din ke baad practice ke roop mein rehta hai.
- Jo din khul chuka hai woh nahi badalta. Aage ke din, dates aur time badal sakte hain.
- "Show on Home" chalu karte hi us exam ki series ka alag card Home par aata hai.
- Aaj ki JEE Main series (62 din, 1 Dec – 31 Jan) jaisi hai waisi rehti hai aur isi jagah se chalti hai.

### 8. Students ko kya dikhega

- Har exam ka ek card. Uske andar PYQ, Mock, Chapter-wise aur apne types.
- Har chalu series ka alag bada card, aaj wale All India banner jaisi polished design mein, us exam ke naam ke saath. Ek se zyada series hon to cards saath-saath; mobile par ek ke neeche ek.

### 9. Purane screens

- Overview, Exams & Content, Upload, Review aur Schedule & Live hat jaate hain. Unka kaam Master ke andar hota hai. Purane links Master par le jaate hain.
- Screen se hatne wale purane tools: 5-step upload wizard, file type chunna, purana manual editor, JEE transfer panel, Solutions (AI review) tab, Mock book checks tab, Data health panel.
- Koi content, attempt ya score delete nahi hota.

## User flow

1. Super Admin kholne par Master khulta hai: saare exams ke cards.
2. "+ New exam" se naam, chhota naam, subjects aur rang bhar kar exam banta hai (abhi chhupa).
3. Exam ke andar "+ Add mock type" se Mock chuna jaata hai.
4. Mock type ke andar "Upload PDF" se file jaati hai. Mocks Draft ban kar list mein aate hain.
5. Jis mock par "Fix" hai, uske cards bhar kar save hote hain.
6. "Select all" ke baad "Make Live" ya "Schedule".
7. "+ Add mock type" se All India Test Series: date, din, time. Papers upload, "Fill days in order", phir "Show on Home".
8. Exam par "Show on Home".
9. Student Home par exam ka card aur series ka alag card dekhta hai.

## UI/UX feel

- Ek screen, teen level. Kahin bhi teen click se zyada door nahi.
- Bade, saaf cards aur rows. Har row par ek hi mukhya button.
- Mock banane ke liye har jagah sirf do bade buttons: "Upload PDF" aur "Write".
- Status ek rangeen chip hai jo dabane par badalta hai.
- Engine ke shabd (held, matching, allowance, region, publication) screen par nahi aate.
- Aaj ki dark theme rehti hai. Home ke exam cards ke rang nahi badalte.
- Mobile par poora kaam hota hai: level ek-ek karke khulte hain.

## Implementation phases

**Phase 1 (abhi banega):** upar ke 9 hisse. Master screen, naya exam, mock type (4 + apna), PDF upload (ek PDF ya alag key/solutions), Write (ek-ek aur paste), paanch status aur bulk badlav, har exam ke liye All India Test Series apni dates ke saath aur Home par alag card, purane screens hatana.

**Phase 2 (alag approval):** ek exam mein agle saal ki nayi series aur purani series ka archive; PDF se bane mock mein question likh kar jodna ya badalna; mock ki copy aur doosre exam mein le jaana; search aur filters; drag karke order; kai numerical questions ek saath confirm karna.

**Phase 3 (alag approval):** scanned (photo) PDF aur do-bhasha papers padhna; har exam ke liye alag reviewer; har mock ki report (kitne attempts, average score); kisne kya badla ka itihaas.

## Assumptions

1. Aaj ka saara content jahan hai wahin rehta hai. Aaj ke "sections" hi ab "mock types" kehlate hain.
2. PYQ, Mock, Chapter-wise aur All India Test Series ek exam mein ek-ek baar judte hain. Apne types jitne chahiye utne.
3. PYQ type mein ab upload aur likhna khula hai. Har PYQ paper par saal zaroori hai; date aur shift optional.
4. Aaj ke 30 verified JEE Main PYQ papers par taala rehta hai: unhe badla nahi ja sakta aur Library mein nahi bheja ja sakta. Sirf Live ya Off.
5. Har PDF 100 MB tak. Sirf searchable PDF apne aap padhe jaate hain; scanned PDF ke liye Phase 1 mein Write.
6. Upload par ek tick rehta hai: "is content ko students ko dikhane ki permission hai". Write mein nahi.
7. Excel se questions laana Write ke andar ek chhote link ke roop mein rehta hai.
8. Master mein koi AI button nahi hai. Padhna aur theek karna bina AI ke hota hai.
9. Default time aur marks: JEE Main, BITSAT aur COMEDK mein exam ke pattern se bhare aate hain; naye exam mein owner ek baar bharta hai. PDF mein chhape niyam milen to wahi lagte hain, na milen to default.
10. Live mock mein badlav naya version banata hai. Purane attempts aur scores nahi badalte.
11. Mock ka naam PDF mein chhapa label hota hai; badal sakte hain.
12. Ek exam mein ek samay par ek hi series. Result aur rank ke niyam wahi hain jo aaj JEE Main series mein hain.
13. Ek series ke saare papers ka pattern ek jaisa hona chahiye (questions, time, marks) taaki rank barabar ho. JEE Main, BITSAT aur COMEDK mein exam ka apna pattern; naye exam mein pehla paper pattern tay karta hai.
14. Series ka card Home aur website ke opening page dono par aata hai, exam card ke andar row ke roop mein nahi. Card exam ke rang mein banta hai; JEE Main series ka rang jaisa hai waisa.
15. Website aur app ek hi jagah se content lete hain. JEE Main series app mein bina badlav chalti hai. Naye exams ki series ka card app mein tab dikhega jab app nayi series list padhne lage; app integration guide update hogi.
16. Reviewer ko sirf theek karne wali list aur student question reports dikhte hain.
17. Data health check raat ko apne aap chalta rehta hai. Dikkat ho to Master ke upar ek line dikhti hai.
18. Kathin PDF ke liye page-level repair tools rehte hain, lekin "Fix" screen se ek link door, alag screen nahi.
19. Jo purane tests kisi type mein nahi hain woh exam ke andar "Not in any type" ke neeche dikhte hain, jahan se unhe type mein rakha ja sakta hai.
20. Screen ke labels saral English mein rehte hain, jaise abhi.
21. Pichhle deploy ke saath gaya ek-baar ka cleanup (BITSAT mocks aur chapter-wise, JEE Main chapter-wise Library mein; PYQ untouched) is plan mein nahi badalta. Unki jagah naya content isi Master se aayega.
22. Phase 1 pehle preview mein banta hai. jeelive.ai par sirf go-ahead ke baad jaata hai.
