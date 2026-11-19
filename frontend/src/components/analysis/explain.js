// "Yeh kaise bana": one plain line per number, written from the server's own rulebook (an.rules), so the text can never drift from the maths.
export function explain(an) {
  if (!an?.rules) return {};
  const { quality: q, difficulty: d, par: p, extra: x, potential: t, compare: c } = an.rules;
  const m = an.paper.marks, n = an.class?.n, swing = m.correct - m.wrong;
  const klass = n ? `Is paper ke ${n} students mein (har student ka pehla attempt; owner aur reviewer nahi ginte).` : 'Class ka data aane par dikhega.';
  const share = v => Math.round(v * 100);
  return {
    score: `Score = sahi jawabon ke marks − galat jawabon par kate marks. Is paper mein sahi par +${m.correct}, galat par ${m.wrong}, chhode par 0.`,
    rank: `${klass} Jitne students ka Score aapse zyada hai, usme 1 jodo. Barabar Score par Rank barabar.`,
    percentile: '100 × (jin students ka Score aapke barabar ya kam hai) ÷ kul students. Yeh sirf is paper ka hai, asli exam ka percentile nahi.',
    accuracy: 'Accuracy = Sahi ÷ (Sahi + Galat) × 100. Chhode hue sawaal isme nahi ginte.',
    time: 'Paper shuru hone se submit tak ka time. "Sawaalon par" = jitni der koi sawaal screen par khula raha. Tab chhupa ho to nahi ginta, aur ek baar mein zyada se zyada 15 minute.',
    attempted: 'Jin sawaalon ka jawab diya: Sahi + Galat. Dropped ya sabko-bonus wale sawaal isme nahi.',
    ledger: 'Kamaye = sahi jawabon ke marks. Negative mein kate = galat jawabon ki penalty. Reh gaye = galat ya chhode sawaalon ke poore marks jo mil sakte the. Kamaye + reh gaye = paper ke kul marks.',
    next3: 'Teeno kaam isi attempt ke sawaalon se nikle hain. Jis kaam mein sabse zyada marks daav par hain, woh sabse upar. Koi AI nahi.',
    standing: 'Sab students ke Score 10 barabar hisson mein baante gaye hain. Laal column woh hai jisme aapka Score aata hai.',
    attempt_rate: 'Attempt rate = (Sahi + Galat) ÷ (Sahi + Galat + Chhode) × 100.',
    negative: 'Galat jawabon par kate marks ka jod.',
    not_seen: 'Jo sawaal ek baar bhi screen par nahi khula.',
    chapters: 'Mazboot = Accuracy 75% ya zyada. Kamzor = 40% se kam. Beech mein Theek. 3 se kam sawaal wale chapter par koi label nahi. Marks gaye = galat par (marks + negative) aur chhode par marks.',
    vs_class: `Topper kam se kam 2 students par dikhta hai. Class average aur Top 10% kam se kam ${c.min_finishers} students par.`,
    realistic: 'Abhi ka Score + Careless galti ke poore marks + mushkil par risk ke poore marks + atke time wale step ka aadha.',
    maximum: 'Abhi ka Score + teeno step ke poore marks. Paper ke kul marks se zyada nahi.',
    careless: `Jo sawaal Par ke ${q.wasted_x} guna se kam time mein galat hue. Sahi hote to har ek par +${swing} (${m.correct} milte, ${m.wrong} nahi katte).`,
    guard: `Tough sawaal jo class mein ${t.guard_solved_below}% se kam students se bane aur aapse galat hue. Chhod dete to negative bachta. Class ka data ${c.min_finishers} students ke baad hi ginta hai.`,
    reinvest: 'Atka time = Mehnga overtime mein Par se upar ka time + Confused sawaalon ka poora time. Yeh time chhode hue sawaalon ko diya gaya (Easy pehle), aapki apni Accuracy par.',
    guess: `Break-even = penalty ÷ (sahi ke marks + penalty). +${m.correct} / ${m.wrong} par ${m.wrong < 0 ? Math.round((1000 * -m.wrong) / swing) / 10 : 0}%.`,
    par: `Par time = us sawaal ka ideal time. ${p.min_solvers} ya zyada students ne sahi kiya ho to unka beech ka (median) time. Warna paper standard: paper ke ${share(p.share_of_duration)}% time ka hissa, Numerical ko MCQ se zyada.`,
    perfect: `Sahi jawab, aur time Par ke ${q.perfect_x} guna tak.`,
    wasted: `Galat jawab, aur time Par ke ${q.wasted_x} guna se kam.`,
    overtime: `Sahi par Par ke ${q.perfect_x} guna se zyada time (Slow-correct), ya galat par ${q.gap_x} guna se zyada (Mehnga overtime).`,
    confused: `Jawab nahi diya, phir bhi Par ke ${q.confused_x} guna se zyada time laga.`,
    concept_gap: `Galat jawab, time Par ke ${q.wasted_x} se ${q.gap_x} guna ke beech.`,
    speed_map: 'Har dot ek sawaal. Baayein-daayein = aapka time ÷ Par time. Teen line: Sahi, Galat, Chhoda. Upar-neeche ka halka fark sirf dots ko alag dikhane ke liye hai.',
    lucky: `Sahi jawab jo Par ke ${share(x.lucky_x)}% se kam time mein aaya. Yeh alag tag nahi, sirf ek note hai.`,
    painful: 'Galat jawab, aur time Par se zyada. Sabse zyada time wala sabse pehle.',
    elapsed: 'Paper shuru hone se submit tak.',
    on_screen: 'Jitni der koi sawaal screen par khula raha, sab sawaalon ka jod.',
    off_screen: 'Paper mein laga time − sawaalon par screen time. Tab band, app background ya instructions padhne ka time.',
    time_share: 'Time ka hissa = us subject par laga screen time ÷ kul screen time. Marks ka hissa = us subject ke marks ÷ paper ke kul marks.',
    first_look: 'Pehli nazar = jawab usi visit mein diya jab sawaal pehli baar khula. Wapas aakar = baad ki kisi visit mein diya.',
    last: `Aapke kul time ka aakhri ${share(x.last_share)}%. Dono taraf ${x.last_min} ya zyada jawab hon tabhi yeh compare banta hai.`,
    pace: 'Paper ke time ko 20 barabar hisson mein baanta. Har point: tab tak kul kitne jawab diye ja chuke the (pehli baar jawab dene ka time).',
    difficulty: `${d.min_attempted} ya zyada students ne attempt kiya ho to: ${d.easy}% ya zyada sahi = Easy, ${d.tough}% se kam = Tough, beech mein Moderate. ${d.early_attempted} se ${d.min_attempted - 1} students par wahi hisaab "shuruaati" likh kar. Warna paper ka apna tag. Warna Not rated.`,
    leak: 'Easy sawaal jo galat hue (marks + negative) ya chhoot gaye (marks).',
    streak: 'Jis order mein aapne jawab diye, usme lagataar sahi (ya lagataar galat) jawabon ki sabse lambi line.',
    changes: `Pehla diya jawab vs aakhri jawab. Galat se sahi: +${swing}. Sahi se galat: −${swing}. Galat se galat: 0.`,
    journey: 'Visit = ek baar sawaal khola aur us par ruke. Beech mein tab chhupa ho to bhi woh ek hi visit hai.',
    gap: 'Volume = unke zyada attempts × unke marks per attempt. Quality = aapke attempts × (unke marks per attempt − aapke). Dono ka jod = kul gap.',
  };
}
