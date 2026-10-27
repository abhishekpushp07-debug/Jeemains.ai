# JEELIVE Rapid Fire — Premium Portrait Game Redesign

Rapid Fire ko mechanical quiz screen se ek original, inviting competitive game mein badla jayega—teal, royal blue aur purple ki identity ke saath.
Core experience quick concept recall hoga: readable dark cards, 20-second turns, visible coins aur clearly accessible Friends Fight history.

## Who it's for

JEE Main, BITSAT aur COMEDK students jo short, exciting solo rounds aur friend duels se concepts, formulae aur diagrams revise karna chahte hain. Experience everyday Android phones par comfortable hoga, sirf high-end devices ke liye nahi.

## Core features and experience

### 1. Original game lobby, not a dashboard
- Rapid Fire ki apni visual identity hogi; JEELIVE branding retained rahegi.
- Top player strip mein avatar, existing progression aur clearly labelled **Coins** balance rahega. Coins kisi hidden menu mein nahi honge.
- Center mein original energy-themed emblem aur prominent **Play Now** action hoga. **Challenge Friend** equally discoverable, separate action hoga.
- Friends Fight history lobby se one tap par khulegi. Existing leaderboard, shop aur avatar options readable, consistent game-style shortcuts banenge—not a wall of identical utility tiles.
- Reference se polished depth, tangible rewards aur inviting buttons ki feeling li jayegi; pool balls, cues, chests, logo ya layout copy nahi honge.

### 2. Premium dark playing cards
- Card faces near-black/graphite rahenge, subtle grey depth aur restrained teal/blue/purple edge lighting ke saath. Plain white question cards replace honge.
- Question, formula aur diagram hero content honge; decoration unke peeche rahegi. Options comfortably tappable aur clearly separated honge.
- Solo aur duel screens same visual family mein honge. Duel mein both players, live score, card progress aur timer instantly readable honge.
- Correct, incorrect aur timeout states colour ke saath text/symbol se bhi clear honge. Result screen actual score, earned coins aur existing performance information dikhayegi.
- Existing 30-card format aur **20 seconds per card** retained rahenge. Scoring aur rewards rules is redesign ke bahane silently change nahi honge.

### 3. Existing question bank ka full suitability pass
- Existing active Rapid Fire bank ko card-by-card reread kiya jayega; sirf number/keyword filter ya small sample review par selection depend nahi karega.
- Numerical calculation, pen-and-paper working, multi-step derivation, lengthy reading aur strong student ko approximately **20 seconds ya zyada** lene wale cards reject honge.
- Keep: direct concept understanding, formula recognition, relationships, units, trends, misconceptions aur fast diagram interpretation.
- Kisi card mein number ya constant hona apne aap rejection nahi hai. Direct recall acceptable hai; calculation-based numerical nahi.
- Target answer time generally 5–15 seconds hoga. Borderline or ambiguous cards active play mein nahi rakhe jayenge. Timing suitability ek informed estimate hogi, har student ke liye guarantee nahi.
- Suitable existing questions rewrite nahi honge. Existing concepts par necessary diagrams add honge; unke labels, relationships aur correct answer scientifically consistent hone chahiye. Diagrams decorative filler ya answer giveaways nahi honge.
- Subject/chapter coverage ko jitna suitable bank allow kare utna balanced rakha jayega. Pool bharne ke liye rejected questions ya same-match duplicates wapas nahi aayenge.
- Completion par kept/deleted counts aur rejection reasons ka concise summary milega.

### 4. Approved permanent cleanup
- Rejected Rapid Fire cards **bank se permanently delete** honge, archive nahi.
- Purani Rapid Fire testing-game history, including solo aur friend duels, **delete** hogi. Us history se nikle old match-performance records aur leaderboard standings fresh gameplay ke liye reset honge.
- Coins balance, existing owned/equipped cosmetics aur account access preserve rahenge. Coin earning/spending records balance correctness ke liye preserve rahenge; unhe match history samajhkar delete nahi kiya jayega.
- Cleanup sirf Rapid Fire tak limited rahega. Academic tests, PYQs, website results, login aur archived NEET material delete ya alter nahi honge.
- Plan approval ke baad hi cleanup implement hoga. Deleted testing matches aur rejected card records app se recoverable nahi rahenge.

### 5. Coins and Friends Fight history
- Lobby aur relevant shop/results screens mein actual current balance visible rahega; decorative/fake coin totals nahi honge.
- Completed rounds aur existing purchases ke baad balance correctly refresh hoga. Rewards screen sirf actually credited coins ko credited batayegi.
- Dedicated Friends Fight history mein opponent, result, both scores aur date/time clearly visible honge. Apne matches ki details sirf relevant participants ko milengi.
- Old testing history delete hone ke baad honest empty state hogi; first new completed duel se real history populate hogi.
- History se existing friend-challenge flow tak quick action milega; purane result ko tap karna bina confirmation naya match start nahi karega.

## User flow

1. Rapid Fire open → portrait lobby → avatar/progression, coins aur main play choices immediately visible.
2. Play Now → existing solo/match choices → 30-card quick-recall round.
3. Challenge Friend → existing invite/join flow → both players ready → live duel.
4. Har card → readable prompt/diagram → 20-second answer window → clear feedback → next card.
5. Round complete → result, actual earned coins aur relevant performance summary → play again, challenge friend ya lobby.
6. Friends Fight History → recent new duels → selected match details → friend challenge shortcut.
7. Coins/shop shortcut → current balance aur existing cosmetics → existing purchase/equip flow.

## UI/UX feel

- **Art direction:** polished, playful energy arena—not a sci-fi control panel. Teal brings energy, royal blue gives depth, purple adds personality; graphite surfaces keep content calm.
- **Original artwork:** cohesive dimensional illustrations for the main play, friend duel, coin and trophy actions. Generic line icons main attraction nahi honge; small utility controls simple reh sakte hain. Full 3D rendering required nahi hoga.
- **Typography:** warm, rounded, confident game headings; questions/options mein clean, highly readable typography. Fractions, superscripts, subscripts aur diagram labels visually correct rahenge. Font treatment formula reading ko compromise nahi karega.
- **Screen composition:** top player/coin strip, one strong central play area, clear friend action aur compact secondary navigation. No crowded rewards wall, unnecessary badges or landscape layout squeezed into portrait.
- **Motion:** responsive button presses, quick card transitions, controlled victory celebration aur subtle feedback. No continuous flashing, long unskippable animation or visual effect covering a question.
- **Clarity:** strong text contrast, generous tap targets, readable small-phone layouts, reduced-motion support aur useful loading/error/empty states.
- **Performance:** artwork compressed aur reused/cached hoga. Decorative art loading gameplay ko block nahi karegi. Essential scientific diagrams load na hone par unreadable questions silently serve nahi honge.
- **Size discipline:** lightweight art and effects; heavy videos or full 3D engine nahi. Android app ka existing under-20MB target retained hai, lekin final build measurement ke bina size guarantee nahi di jayegi.

## Implementation phases

### Phase 1 — MVP: complete requested Rapid Fire refresh — abhi ka scope
Original portrait lobby, coherent game artwork/typography, dark solo/duel cards, existing results/shop/leaderboard/avatar surfaces ka matching treatment, prominent actual coins, accessible Friends Fight history, full existing-bank suitability pass, concept-based diagrams, approved permanent cleanup aur 20-second gameplay. Requested features ko cosmetic-only preview tak limit nahi kiya jayega.

### Phase 2 — Content depth and refinement — abhi build nahi hoga
Fresh gameplay feedback ke basis par further pacing refinements, sparse chapters ke liye separately approved new concept/diagram content aur a broader original cosmetics collection. Whole-bank rewriting automatically start nahi hogi.

### Phase 3 — Expanded competition — abhi build nahi hoga
Separately approved recurring competitions, longer-term social progression aur richer friend rivalry features. New earning/spending rules ya monetisation bina separate approval introduce nahi honge.

## Assumptions

- Current scope Rapid Fire hai. Baaki JEELIVE app ka charcoal/red theme, PIN authentication, academic content synchronisation aur PYQ experience unchanged rahenge.
- Portrait-only gameplay compulsory hai; device rotate karna required nahi hoga.
- Supplied screenshot mood reference hai, reproduction brief nahi. Product name JEELIVE Rapid Fire retained rahega.
- Existing gameplay modes, 30-card format, scoring, reward rates aur friend invite/join behaviour retained rahenge unless a change is explicitly described above.
- User ne rejected cards aur old RF testing history permanently delete karne ko choose kiya hai. Approval mein unse derived match-performance/leaderboard reset included hai; wallet balances, owned items aur account access reset nahi hain.
- Existing concepts par original explanatory diagrams add karna allowed hai; bulk question rewriting allowed nahi hai. Active NEET content reintroduce nahi hoga.
- Existing question language retained rahegi. Game labels short aur familiar rahenge; content ka automatic Hindi translation is scope mein nahi hai.
- Artwork ke liye existing media hosting reuse hogi. Cached art available reh sakti hai, lekin live duels, latest coins aur new results ke liye internet required rahega; offline multiplayer promise nahi hai.
- New ads, paid currency, payment integration, clubs, loot boxes, push notifications ya new question-generation service Phase 1 ka part nahi hain.
- “World-class” quality ambition hai, measurable superiority claim nahi. Final experience ka focus original identity, delightful interaction, scientific correctness aur clear gameplay hoga.