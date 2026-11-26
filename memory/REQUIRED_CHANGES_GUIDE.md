# JEELIVE.AI App: ज़रूरी बदलाव और बचा हुआ काम, पूरी गाइड (26 Nov 2026)

> **Status (26 Nov 2026, शाम):** बदलाव 1 (रंग) ✅, बदलाव 5 (time का फर्क) ✅, बदलाव 8 (Book v3 + website handover) ✅,
> browser वाला Rapid Fire copy दोबारा build ✅ (Rapid Fire का code नहीं बदला)। ये सब सिर्फ preview पर हैं।
> बाकी: बदलाव 3 (Rapid Fire code, पहले बात), 4 (Misfire tabs, website के बाद), 6 (खुले फैसले), 7 (Publish + builds;
> मालिक नए agent के साथ करेंगे)। अगले agent के लिए पूरा हाल: `memory/HANDOFF_NEXT_AGENT.md`।

> मालिक के कहने पर लिखी गई: "website को देने वाला अभी मत बनाओ। पहले required changes का detailed guide बनाओ, और
> क्या-क्या काम बाकी है। फिर permission लो, फिर code करो।"
> **इस गाइड के लिए app का कोई code नहीं बदला गया।** हर बदलाव मालिक की permission के बाद होगा।

---

## भाग 0: आपके सवालों के सीधे जवाब

### 0.1 "Browser वाला Rapid Fire page" क्या है?
- यह **app वाली तरफ़ (मैंने) बनाया था, 15 Nov 2026 को**, आपकी approve की हुई plan से: "website के students भी browser में
  Rapid Fire खेल सकें"। इसे **website agent ने नहीं बनाया**, और उसे बनाने को कहा भी नहीं गया था।
- यह app का ही web रूप है, जिसमें **सिर्फ Rapid Fire** है। यह **app के अपने server** पर चलता है:
  `https://jeelive-mobile.emergent.host/api/arena` (27 Nov को production पर खुल रहा है)।
- Website agent को उस वक्त (15 Nov, `memory/WEBSITE_NOTE.md`) बस इतना कहा गया था: website पर एक "Rapid Fire" button
  लगाओ जो इस address को खोले। उसने button लगाया या नहीं, यह मैंने पक्का नहीं देखा।
- यह कहाँ काम आता है: (1) किसी को match का link भेजो और उसके पास app नहीं है, तो "Play in your browser";
  (2) website का Rapid Fire button (अगर लगा है)।
- **दिक्कत:** यह web रूप 21 Nov को आखिरी बार बना था। App के screens बदलने पर इसे फिर से बनाना पड़ता है (एक script)
  और फिर Publish। इसलिए 25 Nov का All India Rapid का "Misfires" tab app में है, browser वाले में नहीं।
- **Website agent को इसका code देने की ज़रूरत नहीं।** Rapid Fire app का हिस्सा है (23 Nov की "कौन क्या बनाता है"
  table: Rapid Fire = app)। Update = script चलाना + Publish; आपके कहने पर, आखिरी phase में (भाग 1, बदलाव 2)।

### 0.2 Misfire: मेरा और website का एक ही है या अलग-अलग?
दो अलग चीज़ें हैं, और दोनों में टकराव नहीं होगा:

**(क) Papers का Misfire** (Home का लाल MISFIRE card, `/misfire`, "Sab" tab, Galtiyan / Samajh gaya / Chapter report,
"Dobara solve karo") = **website का ही Misfire। App खुद कुछ calculate नहीं करता।**
- App वही website के answers पढ़ता है जो jeelive.ai का अपना Misfire page पढ़ता है: `GET /my/misfire/summary`,
  `GET /my/misfire`, `GET /my/chapters`, और दोबारा try / "Samajh gaya" / reopen भी website पर ही जाते हैं।
- दोबारा try का जवाब सही है या गलत, यह **website** बताती है। "Samajh gaya" website पर save होता है, इसलिए
  website और app में एक जैसा दिखेगा।
- **आपको website का Misfire मुझे देने की ज़रूरत नहीं:** यह 24 Nov से app से जुड़ा हुआ है।
- App का अपना हिस्सा सिर्फ तीन चीज़ें हैं, जो website agent से एक बार check करवाने लायक हैं:
  1. **Paper-wise tabs** (AITS, JEE Chapter-wise, JEE PYQ, BITSAT Mocks, BITSAT Chapter-wise, COMEDK Mocks): list
     website की paper history से आती है। Retry, preview और series वाले attempts को app छोड़ देता है, क्योंकि AITS का
     अपना tab है।
  2. **एक paper के गलत और छोड़े हुए सवाल:** उस paper के website वाले result से (website का अपना `incorrect` /
     `skipped`)।
  3. **"Kitne marks gaye"** (paper-wise list में) = सही जवाब के marks − मिले marks (जैसे छोड़ा = 4, गलत = 5)। यह
     सिर्फ दिखाने के लिए है; website के "Sab" वाले numbers website के अपने हैं।

**(ख) All India Rapid का "Misfires" tab** = Rapid Fire के cards की गलतियाँ। यह पूरी तरह app के server पर है
(`GET /api/rf/daily/misses`)। Website पर Rapid Fire है ही नहीं, इसलिए कोई टकराव नहीं। Rapid Fire अभी website agent
को नहीं दिया जाएगा (आपका फैसला)।

**Student Choice और Matched के साथ Misfire:** इनके papers website के ordinary papers हैं, इसलिए इनकी गलतियाँ
website के Misfire में अपने आप आती हैं ("Sab" tab)। Student Choice के chapter tests "JEE Chapter-wise" tab में भी आते
हैं। बने हुए Student Choice papers (बाद में) और Matched paper का **अलग paper-wise tab अभी नहीं** है (भाग 1, बदलाव 4)।

### 0.3 Website को देने वाली चीज़: "हो गया?"
- **Student Choice + Matched की पूरी book (version 2, 47 pages) 26 Nov को बन चुकी है** और उसके download links
  आपको दिए गए थे (3 Dec 2026 तक चलेंगे)। उसमें दोनों features पूरे हैं: screens, website के doors, super admin का
  काम, हर number और हर sentence।
- **उसमें अभी ये नहीं है:** Misfire की check-list (ऊपर के तीन points), नया रंग (भाग 1, बदलाव 1), और आपके आगे के
  फैसले।
- आपके कहने पर **नया handover अभी नहीं बनाया।** Order: पहले बदलाव, फिर book version 3 + website का handover
  (भाग 4)।

### 0.4 Student Choice और Matched: सब बन गया या कुछ बाकी है?
**App की तरफ़ से दोनों बन चुके हैं** (preview पर)। जो बचा है, उसमें ज़्यादातर website का काम है:

| | App में बना हुआ (preview) | बाकी |
|---|---|---|
| **Student Choice** | Home tile, landing, chapters चुनना (81 असली chapters), chapter search, चुने हुए chapters के tests (Start / Resume / Result), "Jald aa raha hai" box, time rule का card (3 hr max वाला sentence), सवाल चुनने वाले screens और random mock sheet (बने हुए, website के doors का इंतज़ार), Dream College meter में कभी नहीं गिना जाता | **App:** नया रंग (बदलाव 1), एक छोटी गलती (बदलाव 5), खुले फैसले (बदलाव 6)। **Website:** doors A, B, C; chapter tests का time ratio से, 180 min max |
| **Matched** | Home card (पहली shift publish होते ही), उसके नीचे AITS bar, Matched page (month → day → shift), shift page (JEE सवाल + हमारा सवाल, Question / Solution tabs), cup और fireworks, "Attempt all matched" (sign-up sheet → असली paper), solutions में "JEE का कौन सा सवाल", website से shifts अपने आप copy करना, card का on/off switch | **Website:** दो public doors, हर shift का एक paper, super admin का page, और **मिलान करने वाली machine** (JEE paper vs हमारे सवाल) — यह कहीं नहीं बनी। **App:** preview के sample shifts हटाना (आपका फैसला), Misfire tab (बदलाव 4) |

**कौन सा काम students तक पहुँचा है:** 26 Nov 05:33 UTC वाले publish में 26 Nov 05:29 तक का सारा काम गया था
(Student Choice असली chapters, search, Matched paper, Rank, Misfire card वगैरह)। **26 Nov 08:17 का काम (Matched पहली shift
पर, AITS bar, 3 hr sentence) अभी production में नहीं है:** अगले Publish और नए build के साथ जाएगा।

---

## भाग 1: ज़रूरी बदलाव (app side) — हर एक permission के बाद ही

### बदलाव 1: Student Choice को रंगीन बनाना (आपकी नई माँग) 🔴
**अभी:** चारों screens लगभग पूरे सफेद हैं। ऊपर title काले-सफेद में, subject tabs काले/सफेद, नीचे "Tests dekho" bar
grey। Result page पर ऊपर रंगीन हिस्से हैं (maroon "Aapka Score" card, gradient किनारे वाला "Report download",
रंगीन step tabs), Student Choice पर कुछ नहीं।

**Plan (सिर्फ ऊपर के हिस्से और tabs; हर card रंगीन नहीं, जैसा आपने कहा):**

| Screen | अभी | बदलाव के बाद |
|---|---|---|
| `/choice` (landing) | सफेद title + grey chips | ऊपर एक **रंगीन hero card**: "Apne chapters, apni marzi.", छोटी line, और उसी card में तीन chips (81 chapters · 3,750 sawaal · +4 / −1)। उस पर gloss, तिरछी रोशनी और चलता हुआ रंगीन किनारा (Shine, जो app में पहले से है; नया package नहीं)। नीचे के cards ("Chapters chuno", "Jald aa raha hai", time) सफेद ही रहेंगे, बस उनके icons subject/accent रंग में |
| `/choice/pick` (Step 1) | Physics / Chemistry / Maths: काला-सफेद pill | **My Tests और result जैसे glossy रंगीन tabs:** Physics लाल, Chemistry amber, Maths teal (हर subject का अपना रंग, जो app में पहले से है), चुना tab पूरा रंग + glow + सफेद count chip, बाकी हल्के रंग में। चुने chapter की row पर उसके subject का हल्का रंग + रंगीन tick। नीचे का bar: chapter चुनते ही रंगीन "Tests dekho" (अभी grey) |
| `/choice/tests` | सफेद list | ऊपर एक छोटी **रंगीन summary strip**: कितने chapters चुने, कितने हो गए / चल रहे / बाकी। हर row का Start / Resume / Result रंगीन badge (My Tests के रंग) |
| `/choice/questions` (बाद में खुलेगा) | सफेद | `/choice/pick` जैसे ही रंगीन subject tabs, ताकि दोनों steps एक जैसे दिखें |

- रंग सिर्फ app की theme file से (light/dark दोनों में सही)। नया font, picture या package नहीं।
- किसी data, test, attempt या result को हाथ नहीं लगेगा; सिर्फ screen का रूप बदलेगा। सारे testIDs वही रहेंगे।
- **Check:** web preview पर 390 और 320 चौड़ाई, QA learner से सिर्फ देखना (Start कभी नहीं), फिर testing agent।
- **आपसे पूछना है:** hero card का रंग: (a) result page जैसा maroon, या (b) तीनों subjects के रंगों (लाल, amber,
  teal) का mix। मेरी सलाह: (a), क्योंकि आपने result page का नाम लिया और app में यह रंग पहले से जाना-पहचाना है।

### बदलाव 2: Browser वाला Rapid Fire (आखिरी phase, जब आप कहें) 🟡
- Script `scripts/build_arena_web.sh` चलाना → `backend/arena_web/` नया बनेगा → Publish।
- साथ में: उस web रूप के अंदर एक पुराना fallback address है (testing agent ने iteration_129 में बताया था), जो हर fork
  पर पुराना हो जाता है। Rebuild के वक्त उसे config से पढ़वाना।
- इसके बाद All India Rapid का "Misfires" tab और 21 Nov के बाद के सारे Rapid Fire बदलाव browser में भी दिखेंगे।
- आपके कहने तक कुछ नहीं होगा।

### बदलाव 3: Rapid Fire के code में बदलाव (पहले आपसे बात) 🟡
- आपने कहा "तुम्हें वैसे ही उसमें code में बदलाव करना है, तो पहले मुझसे बात करो"। **मुझे अभी नहीं पता कि क्या
  बदलना है।** आप बताएँगे; तब तक Rapid Fire को कोई हाथ नहीं लगाएगा, और website agent को कुछ नहीं जाएगा।
- यह बदलाव 2 से पहले होना चाहिए, ताकि browser वाला एक ही बार rebuild हो।

### बदलाव 4: Misfire में "Student Choice" और "Matched" के tabs (website के बाद) 🟢
- आज ज़रूरी नहीं: इनकी गलतियाँ "Sab" में आ ही जाती हैं, और chapter tests "JEE Chapter-wise" में।
- जब website बने हुए Student Choice papers (door C) और Matched का paper बनाएगी, तब दो नए paper-wise tabs।
- **Website से चाहिए:** उसकी paper history में इन papers का अपना `kind` (जैसे `choice`, `matched`)। यह handover में
  सवाल के रूप में जाएगा।

### बदलाव 5: बने paper के time में 1-2 minute का फर्क (छोटी गलती) 🟢
- Student Choice का paper बनाते वक्त हर subject का time अलग-अलग ऊपर round होता है, इसलिए rows का जोड़ total से
  1-2 minute ज़्यादा दिख सकता है (उदाहरण: 10 सवाल → rows 10 + 5 + 10, total "24 min")।
- Fix: rows को total के हिसाब से बाँटना, ताकि जोड़ हमेशा बराबर हो। Students को यह अभी नहीं दिखता (door C खुलने पर
  दिखेगा), पर पहले ठीक करना सुरक्षित है।

### बदलाव 6: खुले फैसले (आपके जवाब के हिसाब से code) 🟡
| # | सवाल | जब तक जवाब नहीं |
|---|---|---|
| 1 | क्या **बने paper** का भी max time 3 hr हो? (ratio से 75 Maths सवाल = 240 min) | बने paper नहीं कटते |
| 2 | Chapter test का **कम से कम time**? (ratio से 11 tests 60 min से छोटे; सबसे छोटा 2 सवाल = 4 min) | कोई minimum नहीं |
| 3 | क्या **Matched paper** कभी Dream College meter में गिने? (68+ सवाल और 150+ marks हों तो आज गिना जाएगा; shift का paper इससे बहुत छोटा होता है) | गिना जा सकता है |
| 4 | बने papers के लिए app के सुझाव (random mock में पहले नए सवाल; रोज़ की limit; कभी न शुरू हुए papers हटाना; कोई leaderboard नहीं) | website बिना कहे न बनाए |
| 5 | Matched पर `source` / `tag` की wording | super admin जो ठीक लगे लिखे |
| 6 | Preview के made-up sample shifts: रखें या अभी हटाएँ? | सिर्फ preview पर दिखते रहेंगे |

### बदलाव 7: Publish + नए builds 🔴
- 26 Nov 08:17 के बाद का सारा काम (और ऊपर के बदलाव) सिर्फ preview पर है।
- App में `expo-updates` नहीं है, इसलिए **फोन में लगा app नया screen तभी दिखाएगा जब नया build बने और install हो।**
- Android: आखिरी build versionCode 153 (26 Nov 06:19 UTC)। इसके बाद का काम नए build में ही जाएगा।
- **iOS: आज तक एक भी build नहीं बना।**
- Deadline: AITS 9 Dec 2026 से शुरू; JEE Main की पहली shift (Jan 2027) से पहले Matched वाला build students के फोन में
  होना चाहिए।
- आपका जवाब अभी बाकी है: पिछली बार आपने installed app में देखा था या deployment panel के Expo Go QR से?

### बदलाव 8: Book version 3 + website का handover (जब आप कहें) 🟡
भाग 3 देखें।

---

## भाग 2: बचा हुआ सारा काम (एक जगह)

### 2.1 App side: आपकी permission या जवाब पर रुका हुआ
- बदलाव 1 से 8 (ऊपर)।
- **आपके जवाब बाकी:** (a) पिछले publish में installed app देखा या Expo Go; (b) QA learner (7004186276) पर 24-25 Nov के
  पाँच attempts आपने शुरू किए थे या नहीं।

### 2.2 Website side: website agent का काम (app इसे नहीं कर सकता)
**Student Choice**
- Door A `GET choice/bank`: `pick` / `random` का switch।
- Door B: एक chapter के सवाल **बिना options** (chapter id = उस chapter test का set id)।
- Door C `POST choice/papers`: चुने सवालों या random गिनती से एक paper; 75 सवाल max (90 कभी नहीं); +4 / −1;
  time Maths 3.2, Physics 2.4, Chemistry 1.6 minute प्रति सवाल।
- 81 chapter tests का time ratio से, **180 min max** (हर chapter का minute `memory/WEBSITE_CHOICE_NOTE.md` भाग 4 की
  table में)। आज हर chapter test 60 min का है।

**Matched** (JEE Main की पहली shift, Jan 2027 से पहले ज़रूरी)
- दो public doors: `GET matched` और `GET matched/<shift>`।
- हर shift का एक ordinary paper (हमारे matched सवाल, +4 / −1)।
- Super admin का page जो shifts लिखे, publish करे, वापस ले।
- **मिलान करने वाली machine** (JEE का paper vs हमारे सवाल): आज कहीं नहीं बनी, न app में न website में।

**बाकी website काम (पुराने notes से)**
- Misfire की तीन बातें check करना (भाग 0.2)।
- Pictures fast-load को jeelive.ai पर live करना; उसके बाद app side बनेगा (`memory/APP_PICTURES_NEEDS.md`)।
- Website पर Rapid Fire button (15 Nov note): लगा या नहीं, पक्का नहीं।
- CEO dashboard के लिए signups export (23 Nov brief): status पता नहीं।

### 2.3 Checks जो अभी तक कभी नहीं हुए
- असली फोन पर Student Choice और Matched (keyboard, maths वाले सवाल, safe area)।
- AITS का असली दिन (9 Dec से) और Home का AITS bar उस दिन।
- एक असली Matched shift: website से फोन तक, पूरा।
- Student Choice की question list में picture वाले सवाल (door B के बिना नहीं हो सकता)।
- 180 min से लंबा कोई attempt।
- Paper चलते वक्त (player में) "JEE का कौन सा सवाल" वाला हिस्सा।

### 2.4 पुराने बचे हुए काम (backlog)
- Offline Solutions (`memory/OFFLINE_SOLUTIONS_PLAN.md`): शुरू नहीं हुआ।
- Play Store / App Store readiness review: शुरू नहीं हुआ।
- Rapid Fire cards की teacher review list।
- दो छोटे labels (count pills पर `aria-checked`, `rf-history-empty`)।
- All India Rapid "Misfires" का number: हर गलत/छोड़ा card गिनता है (जैसे 36), पर जो cards तक student पहुँचा ही नहीं,
  वो list में नहीं (नीचे एक note बताता है कितने)। आपका फैसला बाकी।

---

## भाग 3: Website agent को क्या जाएगा (अभी बनाया नहीं: सिर्फ list, ताकि आप देख लें)
1. **Book version 3** (Student Choice + Matched), version 2 के ऊपर: नया रंग, बदलाव 5, आपके फैसले, Misfire की बातें।
2. साथ के notes: `WEBSITE_CHOICE_NOTE.md`, `WEBSITE_MATCHED_NOTE.md`, `MATCHED_CONTRACT.md` (पहले से book में हैं)।
3. **Misfire की check-list:** भाग 0.2 के तीन points + सवाल "Student Choice / Matched papers का `kind` क्या होगा"।
4. **Website के काम का order (मेरी सलाह):** (1) chapter tests का time (सिर्फ data का बदलाव, सबसे आसान);
   (2) Matched: doors + paper + super admin page + machine (JEE Main से पहले ज़रूरी); (3) Student Choice doors A, B, C।
5. **Rapid Fire: कुछ नहीं** (आपके कहने तक)।

---

## भाग 4: मेरा सुझाया order

| Phase | क्या | कब |
|---|---|---|
| 1 | बदलाव 1 (रंग) + बदलाव 5 (time का फर्क) + बदलाव 6 के जो जवाब आप दें। Check + testing agent | आपकी permission के बाद |
| 2 | Book version 3 + website का handover pack | Phase 1 के बाद, आपके कहने पर |
| 3 | Publish + नया Android build + पहला iOS build | Phase 1 के बाद, 9 Dec से पहले |
| आखिरी | बदलाव 3 (Rapid Fire code, पहले बात) → बदलाव 2 (browser वाला rebuild) → Publish | जब आप कहें |
| बाद में | बदलाव 4 (Misfire tabs) | website के papers बनने के बाद |
