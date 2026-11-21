# PDF Engine 2.0: rollback ke baad jaanch, phir khoya kaam dobara, options ek ke neeche ek

Rollback ke baad sabse pehle poori machine ki jaanch hoti hai aur uski likhit report milti hai. Uske baad rollback me gaya kaam dobara banta hai: chhape hue boxes pehle, a/A alag, poore page wala fix tool.
Is baar options A, B, C, D har screen par ek ke neeche ek, poori chaudai me dikhte hain. PDF padhne me kahin AI nahi lagta.

## Kiske liye

- **Owner (super admin):** jaanna chahta hai ki rollback se kuch toota ya nahi, aur chahta hai ki boxed PDF bina haath lagaye sahi kate.
- **Reviewer:** engine ne jo sawaal roke, unhe ek hi page par theek karta hai.
- **Students:** har option apne button par padhte hain, ek ke neeche ek, phone aur desktop dono par.

## Kya banega aur kaise chalega

### 1. Rollback ke baad ki haalat: abhi tak kya pata hai

Planning me kuch chalaya nahi ja sakta. Neeche ki baatein sirf files padh kar aur preview site ko bina login ke khol kar dekhi gayi hain. Koi test abhi nahi chala.

| Baat | Abhi ki jaankari | Kaise pata chala |
| --- | --- | --- |
| Site chal rahi hai? | Haan. Server ne "ok" aur "ready" jawab diya. Opening page aur owner login page khule. | Bina login ke khol kar |
| Code kis haalat me hai? | Us haalat me jo owner ke chune hue message (21 Nov, din me) ke samay thi. Us message tak boxes ka kaam shuru nahi hua tha, isliye yeh wahi code hai jo pause ke samay tha (notes me 20 Nov 22:35 UTC, yaani India ke samay me 21 Nov subah 4:05). Notes ke mutabik yahi code jeelive.ai par live hai. Checkpoint ka samay khud nahi dekha gaya; yeh notes ke kram se nikala gaya hai. | Cutter, fix tool aur student option ki files padh kar |
| Rollback me kya gaya? | Us message ke baad bana poora kaam, sirf 2x2 nahi: (1) chhape boxes pehle, (2) a/A alag, (3) poore page wala fix tool, (4) boxed kitaab ke chhoote sawaal padhne ka sudhaar. | In files me yeh cheezein ab nahi hain |
| Kya bacha hai? | Owner ki boxed chemistry PDF, purane scan ke record aur test ke log. Yeh app folder ke bahar hain. | Folder ki list aur log padh kar |
| Padhi hui files | Saat files poori padhi gayi (cutter, cut ka hisaab, fix tool aur uska style, student options, ruke sawaal ka card, saare sawaal ki list). Adhoori ya aapas me bemel nahi lagi. | Padh kar |
| Peeche chhooti cheez | Khoye kaam ki 3 test scripts ab bhi folder me hain. Woh un features ko test karti hain jo ab code me nahi hain, isliye aaj chalane par fail hongi. App par iska asar nahi. | Files dekh kar |
| Shayad chhoota hua | Beech me ruke test ka ek kaam-chalau (disposable) test database. | Ek chhooti file se andaza; check nahi hua |
| Jo check nahi hua | Login ke peeche ka sab kuch: Super Admin ke screens, PDF upload, fix screen, student ka test, result. | Planning me mumkin nahi |

**Rollback ne theek kaam kiya ya nahi.** Rollback ne wahi kiya jiske liye woh bana hai: code aur chat ko chune hue message par wapas le gaya. Woh ek akela badlaav nahi chun sakta; us message ke baad ka sab kuch jata hai. Platform support ke mutabik rollback sirf app folder ka code wapas karta hai; database, app folder ke bahar ki files aur live site ko nahi chhoota; aur baad ka kaam wapas aage nahi laya ja sakta. Support ka jawab beech me kat gaya tha, isliye yeh pakka nahi hai. Jo dekha gaya woh isse milta hai: PDF aur record apni jagah hain.

**Aage ke liye.** Design ka ek faisla badalna ho toh rollback ki zaroorat nahi. Bata dene par sirf wahi hissa badla jata hai aur baaki kaam bacha rehta hai.

### 2. Pehla kadam: poori jaanch (kuch bhi banane se pehle)

| Kya jaancha jayega | Kaise saabit hoga |
| --- | --- |
| Engine wahi hai jo rollback se pehle tha | Teen chapter kitaabein (physics, chemistry, maths: 4,650 sawaal) aur boxed chemistry kitaab dobara scan hoti hain. Har sawaal ka cut 20–21 Nov ke record se milaya jata hai. Farq 0 hona chahiye. |
| Website ka code poora hai | Poori website naye sire se build hoti hai, 0 error ke saath. Build ko jeelive.ai par chal rahi files se milane ki koshish hoti hai (bina login, sirf padhna). Nateeja jo bhi ho, report me likha jata hai. |
| Super Admin ka poora raasta | Test copy me: owner login, Master, PDF upload, Draft, fix screen, proof view, Live. |
| Student ka poora raasta | Test copy me: test shuru, jawab, submit, result, Solutions. Phone (390) aur desktop (1920). |
| Purane test | Master, Library, chapter reader, typed option aur get-ready ke test dobara chalte hain aur apne pichhle record se milaye jate hain. |
| Safai | 3 bemel test scripts naye kaam ke hisaab se dobara likhi jati hain. Chhoota hua disposable test database naam dekh kar hataya jata hai. |

- Report me har line par ek hi nateeja hota hai: theek / rollback se toota / pehle se toota / check nahi ho paya.
- Rollback se tooti cheez sabse pehle theek hoti hai.
- 20 Nov ke record me kuch purane test pehle se fail the (Master 124 me se 3, structure 133 me se 1, chapters ka 1, publishing wala test beech me ruka). Har ek ke liye bataya jata hai: asli galti hai ya test purana pad gaya hai. Asli galti isi phase me tabhi theek hoti hai jab woh upload → fix → Live → student test ke raaste ko rokti ho. Baaki report me rehti hain.
- Jaanch saaf nikle toh aage ka kaam bina ruke shuru hota hai. Kuch toota mile toh pehle woh theek hota hai.

### 3. Khoya hua kaam dobara (wahi faisle jo pehle ho chuke hain)

**3a. Chhape hue boxes pehle**

- Jab sawaal ke hisse me ek bada chhapa rectangle aur uske baad chaar chhote chhape rectangle hon, toh wahi paanch rectangle paanch tukde hain: Sawaal, A, B, C, D.
- Kaun sa box kis option ka hai, yeh box ke andar chhape label (A) (B) (C) (D) se tay hota hai, box ki jagah se nahi.
- Option ki picture me chhapa label nahi aata, kyunki button par letter pehle se hai. Sawaal ke box ke upar ki heading ("Question 16", chapter ki line) sawaal ki picture me nahi aati.
- Boxes ek ke neeche ek chhape hon, do ek line me, ya chaaron ek line me; kone seedhe hon ya gol: sab chalte hain.
- Check phir bhi hote hain: har option box me label ke alawa kuch chhapa ho; A se D chaaron label mile; sawaal ke hisse me boxes ke bahar kuch na chhapa ho.
- Koi check fail ho toh engine andaza nahi lagata. Sawaal wajah ke saath ruk jata hai, aur fix tool me paanchon chhape boxes pehle se taiyaar milte hain.
- Chhape boxes na hon toh engine pehle ki tarah label dhoondh kar kaatta hai.

**3b. Chhote a,b,c,d aur bade A,B,C,D alag**

- Option ke label ka set kabhi mila-jula nahi hota: chaaron bade, ya chaaron chhote, ya chaaron number.
- Option ke apne text ke andar likhe letter, jaise "(a), (b) and (c) only", option ke label nahi maane jate.
- Sawaal me (a) se (e) statements aur neeche (A) se (D) options hon toh bade wale options hain. Ulta ho (statements bade, options chhote) toh chhote wale options hain.
- Saaf na ho toh sawaal ruk jata hai. Fix tool ke shuruaati boxes bhi isi niyam se bante hain.

**3c. Boxed kitaab ke saare sawaal milna**

- 21 Nov ke record ke mutabik aaj ka engine owner ki boxed chemistry kitaab (2,527 page, 1,250 sawaal) me 1,198 sawaal dhoondh pata hai aur unme se 34 rok deta hai. Chapter 9 me 47 ki jagah 1 hi sawaal milta hai.
- Khoye hue kaam ke record me isi kitaab par 1,250 sawaal mile the (1,000 options wale, 250 numerical), 0 ruke, aur har sawaal ki answer key mili thi. Dobara banne wala engine isi nateeje par parkha jata hai.

**3d. Fix tool poore page par**

- Poora page dikhta hai, sirf sawaal ki patti nahi.
- Rectangle dene ke do tareeke hain. Ek: pehle rectangle kheencho, phir batao kiska hai (Sawaal / A / B / C / D). Do: pehle Sawaal / A / B / C / D chuno, phir kheencho.
- Ek box bante hi agla apne aap chun liya jata hai: A ke baad B, phir C, phir D.
- Chhape boxes page par outline me dikhte hain. Kisi chhape box par tap karne se poora wahi box chun liya jata hai. Ek button paanchon chhape boxes ek saath le leta hai.
- Bane hue box ko hilana aur chhota-bada karna pehle jaisa rehta hai.
- Bagal me (phone par neeche) wahi dikhta hai jo student ko milega. Har badlaav apne aap check hota hai. Check paas hue bina save nahi hota.
- Do box kisi chhapi cheez ko share karein toh wajah ke saath mana ho jata hai. Sirf khaali kagaz par ek doosre par chadhna chalta hai.
- Boxes ke bahar kuch chhapa reh jaye toh bataya jata hai. Owner tick karke keh sakta hai ki woh is sawaal ka hissa nahi hai.
- Kuch type nahi karna padta. Option khud type karne ka purana raasta bana rehta hai.

### 4. Options ek ke neeche ek, har jagah (naya faisla)

| Screen | Options kaise dikhte hain |
| --- | --- |
| Test screen | A, B, C, D ek ke neeche ek; har card sawaal wale hisse jitna chauda |
| Result aur Solutions screen | Wahi; sahi option aur student ka chuna option usi card par nishaan ke saath |
| Proof view (Super Admin) | Wahi |
| Fix tool ka preview | Wahi |

- Phone aur desktop dono par. 2x2 ya ek line me do option kahin nahi.
- Kitaab me options jaise bhi chhape hon (ek line me chaar, do-do, ya boxes me), screen par hamesha A, B, C, D upar se neeche.
- Sawaal aur chaaron options me likhai ka size ek hi rehta hai.
- Yeh pehle ke plan ka woh niyam hata deta hai jisme desktop par chhote options do-do dikhte the.

### 5. Kasauti: capable, powerful, tez (naap kar)

- **Boxed chemistry kitaab:** 1,250 me se 1,250 sawaal mile, 0 ruke, har sawaal ki key. Na ho paye toh har ruke sawaal ki wajah report me aati hai.
- **Bina boxes wali teen kitaabein (4,650 sawaal):** jo sawaal aaj saaf katta hai woh saaf hi kate aur uska cut na hile. Aaj ke 5 ruke sawaal ruke rehte hain; woh "chipke hue" wale hain aur Phase 2 me hain.
- **AITS maths kitaab (1,250 sawaal):** aaj 0 ruke; 0 hi rahe.
- **Speed:** record me aaj ka engine boxed chemistry kitaab ko scan script se 332 second me padhta hai; khoya hua kaam 420 second leta tha. Target: naya engine aaj se dheema na ho. Upload se Draft tak ka asli samay app ke andar naapa jata hai aur report hota hai.
- **Andaza nahi:** galat cut se behtar ruka hua sawaal.
- **Screens:** phone (390) aur desktop (1920) par koi screen side me nahi khisakti aur koi picture kati nahi hoti.
- **Poora kab maana jayega:** jab builder se alag ek poora test run paas ho. Jo check na ho paye woh "check nahi hua" likha jata hai, "ho gaya" nahi.

### 6. Jo nahi badalta

- Rok ka niyam: ek bhi ruka sawaal ho toh mock Draft rehta hai, Live nahi hota.
- Summary line ("75 sawaal · 73 saaf kate · 2 aapko dekhne hain"), proof view, "Try as student", option type karna, "Poori picture hi dikhao".
- JEE Main PYQ purane look me rehte hain.
- Mobile app me koi badlaav nahi.
- PDF padhne me AI nahi.
- Sab kuch preview me banta hai. jeelive.ai par tabhi jata hai jab owner "deploy" kahe.

## User flow

**Owner**
1. Jaanch ki report chat me milti hai.
2. Super Admin › Master › exam › mock type › Upload PDF, pehle jaisa.
3. Boxed PDF ke mock Draft ban kar aate hain, summary line ke saath.
4. Ruka sawaal Fix me khulta hai: poora page, chhape boxes outline me. "Paanchon chhape boxes lo" dabao, ya rectangle kheench kar Sawaal / A / B / C / D do. Preview dekho, save karo.
5. Proof view me poora paper ek baar dekho. "Try as student" se asli screen dekho.
6. Mock Live karo ya series ka din do.

**Student**
1. Sawaal upar, uske neeche A, B, C, D ek ke neeche ek.
2. Option par tap.
3. Submit ke baad wahi sawaal aur options, sahi option aur apna chuna option nishaan ke saath.

## UI/UX feel

- Har option ek chauda card hai: baayin taraf letter, uske bagal option ki picture. Card poori chaudai ka.
- Chuna hua option laal outline aur tick ke saath. Result par sahi aur galat, rang aur icon dono se dikhte hain.
- Kitaab ki pictures safed "kagaz" card par rehti hain, light aur dark dono theme me.
- Fix tool: poora page; Sawaal, A, B, C, D ke box alag rang me; "Yeh hissa kiska hai?" ke button.
- Phone par kheencha hua rectangle aur "kiska hai" ke button ek saath screen par rehte hain; scroll nahi karna padta.
- Fix tool ki likhai Roman Hinglish me. JEELIVE ka maujooda look; koi naya style nahi.

## Phases

**Phase 1 (abhi banta hai)**
- Poori jaanch aur report (section 2), rollback se tooti cheez ka sudhaar, safai.
- Chhape boxes pehle, a/A alag, boxed kitaab ke saare sawaal, poore page wala fix tool (section 3).
- Options ek ke neeche ek, har screen par (section 4).
- Section 5 ki kasauti par poora test, phone aur desktop dono.
- Sirf preview me.

**Phase 2 (alag manzoori)**
- "Chipke hue" options: jahan do options ke beech khaali line nahi hai (aaj ke 5 ruke sawaal). Owner ne ise baad ke liye kaha hai.
- App team ki guide aur PDF format guide.
- Mushkil layout apne aap: options ke bagal diagram, agle page tak jata option, ek picture me chaar graph, do-column page.
- Scan (photo) PDF, site ke apne server par text dhoondh kar, bina AI.
- Saade shabdon wale options asli text me.
- Purane Draft ke liye "dobara padho" button.
- Solution ki pictures bhi isi tarah saaf kati hui.
- JEE Main PYQ naye look me.

**Phase 3 (alag manzoori)**
- Question bank: chune hue chapters se naya mock, bina nayi PDF.
- Owner ki paper report: kis sawaal me kaun sa galat option sabse zyada chuna gaya.
- Badi kitaab ki tez jaanch: keyboard se poori proof sheet approve.
- Ruke hue student features: Galti Notebook, Subject Rank aur Percentile, Seekh Reminder.

## Assumptions (jo faisle bina pooche liye gaye)

1. Owner ne teen raaston me se koi nahi chuna. Jawab ko "pehle batao aur test karo, phir sab theek karke best banao" padha gaya. Isliye Phase 1 me jaanch aur dobara banana dono hain.
2. Jaanch ki report ke baad dobara banane ka kaam owner ke jawab ka intezaar nahi karta, agar kuch toota na mile.
3. Baad wale checkpoint par wapas jaana mumkin nahi maana gaya. Yeh platform support ke adhoore jawab par tika hai.
4. Khoye code ki koi copy un folders me nahi mili jo dekhe gaye. Dhoondh poori nahi thi. Kaam pehle ke faislon aur purane test record se dobara banta hai. Copy mil bhi jaye toh sab kuch dobara parkha jata hai.
5. "Ek ke neeche ek" tab bhi lagta hai jab option bahut chhota ho (jaise ek number). Desktop par aise card me khaali jagah dikhegi.
6. Boxed page par sawaal ke box ke upar ki heading picture me nahi aati; test screen sawaal ka number khud dikhati hai. Bina boxes wale page par chhapa number pehle ki tarah picture me rehta hai.
7. Label ke bina option box, ya boxes ke bahar chhapi cheez: sawaal rukta hai, andaza nahi lagta.
8. Pehle se tooti cheezein (rollback se nahi) sirf report hoti hain, jab tak woh upload se student test tak ka raasta na rokein.
9. Test sirf disposable test copy me chalte hain. Asli preview database aur live site ko test nahi chhoote. Hataya sirf woh database jata hai jo test ne khud banaya tha, naam aur andar ka data dekh kar.
10. Section 1, 3c aur 5 ke number 20–21 Nov ke log se liye gaye hain. Planning me unhe dobara chalaya nahi gaya. "Aaj ka engine" wale number us log se hain jo naam aur andar ke nateeje se purane engine ka lagta hai; jaanch me yeh dobara chalta hai.
11. Speed ke number scan script ke hain, upload ke raaste ke nahi.
12. "Perfect", "most powerful", "lightning fast" ko section 5 ki naapi ja sakne wali kasauti maana gaya hai. Yeh vaada nahi hai ki har layout apne aap katega; baaki layout Phase 2 me hain.
13. Fix tool reviewer bhi chala sakta hai. "Boxes ke bahar wala hissa chhod do" wala tick sirf owner ka hai, jaise aaj hai.
14. jeelive.ai par pehle se pade Draft par naye engine ka kya asar hoga, yeh build me dekha jata hai aur deploy se pehle bataya jata hai.
15. Aaj ke code me options ka layout (phone aur desktop par) planning me nahi dekha gaya. Jaisa bhi ho, section 4 ke hisaab se kiya aur parkha jata hai.
16. Purane plan ki "purane look wale mock ki list" bani hai ya nahi, yeh nahi dekha gaya. Jaanch ki report me aata hai; is phase me nahi banti.
17. Pehle manzoor hua PDF Engine 2.0 plan `pdf_engine2_plan.md` me saath rakha gaya hai. Uske niyam lagoo rehte hain, sirf desktop par do-do option wala niyam hata hai.
18. Owner ke message me "solutions" ko options A, B, C, D padha gaya; owner ne "har jagah" chuna.
