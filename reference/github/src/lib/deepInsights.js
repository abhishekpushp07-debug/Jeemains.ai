const pct = (a, b) => (b ? Math.round((1000 * a) / b) / 10 : null);
const fmt = (n) => (n == null ? '—' : Math.round(n * 100) / 100);

function streak(rows, outcome) {
  let best = 0, run = 0, at = null, start = null;
  rows.forEach((q) => {
    if (q.outcome === outcome) { run += 1; if (run === 1) start = q.number; if (run > best) { best = run; at = start; } }
    else run = 0;
  });
  return { best, at };
}

function groups(s, rows) {
  if (s.sections) return s.sections.map((x) => ({ name: x.name, score: x.score, max: x.maximum, correct: x.correct, wrong: x.incorrect, skipped: x.skipped, count: x.count }));
  const map = {};
  rows.forEach((q) => {
    const g = (map[q.subject] = map[q.subject] || { name: q.subject, score: 0, max: 0, correct: 0, wrong: 0, skipped: 0, count: 0 });
    g.count += 1; g.score += Number(q.marks) || 0;
    g[q.outcome === 'correct' ? 'correct' : q.outcome === 'incorrect' ? 'wrong' : 'skipped'] += 1;
  });
  return Object.values(map);
}

// 25 data-backed insight cards from this attempt plus (optional) live peer statistics.
export function deepInsights(r, c) {
  const s = r.summary, rules = r.rules || {};
  const main = r.questions.filter((q) => !(q.bonus && !r.bonus_unlocked_at) && !['dropped', 'bonus'].includes(q.outcome));
  const attempted = main.filter((q) => q.outcome === 'correct' || q.outcome === 'incorrect');
  const right = main.filter((q) => q.outcome === 'correct'), wrong = main.filter((q) => q.outcome === 'incorrect');
  const skipped = main.filter((q) => q.outcome === 'skipped');
  const plus = Number(rules.correct) || 3, minus = Math.abs(Number(rules.wrong) || 0);
  const acc = attempted.length ? right.length / attempted.length : null;
  const sec = groups(s, main).map((g) => ({ ...g, acc: pct(g.correct, g.correct + g.wrong) }));
  const ranked = sec.filter((g) => g.correct + g.wrong >= 3).sort((a, b) => b.acc - a.acc);
  const used = r.submitted_at && r.started_at ? Math.max(0, Math.min(r.submitted_at, r.deadline || r.submitted_at) - r.started_at) : null;
  const allowed = r.deadline && r.started_at ? r.deadline - r.started_at : null;
  const timed = attempted.filter((q) => q.accepted_at).sort((a, b) => a.accepted_at - b.accepted_at);
  const mid = r.started_at && allowed ? r.started_at + allowed / 2 : null;
  const late = allowed ? attempted.filter((q) => q.accepted_at && q.accepted_at >= r.started_at + 0.8 * allowed) : [];
  const early = allowed ? attempted.filter((q) => q.accepted_at && q.accepted_at < r.started_at + 0.8 * allowed) : [];
  const marked = main.filter((q) => q.marked);
  const letters = {}; attempted.forEach((q) => { letters[q.response] = (letters[q.response] || 0) + 1; });
  const keyLetters = {}; main.forEach((q) => { const k = (q.accepted_answers || [q.answer])[0]; keyLetters[k] = (keyLetters[k] || 0) + 1; });
  const topLetter = Object.entries(letters).sort((a, b) => b[1] - a[1])[0];
  const peer = {}; (c?.questions || []).forEach((q) => { peer[q.id] = q; });
  const solveRate = (q) => { const p = peer[q.id]; return p && p.correct + p.incorrect >= 3 ? p.correct / (p.correct + p.incorrect) : null; };
  const easyMiss = main.filter((q) => q.outcome !== 'correct' && solveRate(q) >= 0.6);
  const hardWin = main.filter((q) => q.outcome === 'correct' && solveRate(q) != null && solveRate(q) <= 0.35);
  const cs = streak(main, 'correct'), ws = streak(main, 'incorrect');
  const peerOK = c && c.state === 'available' && c.sample_size > 0;
  const out = [];
  const add = (key, title, value, detail, tone = 'info', ok = true) => { if (ok && value != null) out.push({ key, title, value, detail, tone }); };

  add('score', 'Final score', `${s.score} / ${s.maximum}`, `${pct(s.score, s.maximum)}% of the maximum on this paper.`, s.score > 0 ? 'good' : 'warn');
  add('accuracy', 'Accuracy', acc == null ? null : `${pct(right.length, attempted.length)}%`, `${right.length} correct out of ${attempted.length} attempted.`, acc >= 0.7 ? 'good' : acc >= 0.5 ? 'info' : 'warn');
  add('attempt', 'Attempt rate', `${pct(attempted.length, main.length)}%`, `${attempted.length} of ${main.length} questions answered; ${skipped.length} left unanswered.`);
  add('penalty', 'Marks lost to negatives', `−${wrong.length * minus}`, `${wrong.length} wrong answers × ${minus}. Each wrong answer also cost the ${plus} you could have earned.`, wrong.length ? 'warn' : 'good');
  add('noguess', 'Score without wrong answers', `${Number(s.score) + wrong.length * minus}`, 'What you would score if every wrong answer had been left blank instead.', 'info', minus > 0);
  add('yield', 'Marks per attempted question', attempted.length ? fmt(Number(s.score) / attempted.length) : null, `Maximum possible is ${plus}. Higher means cleaner attempts.`);
  add('best', 'Strongest section', ranked[0] ? ranked[0].name : null, ranked[0] && `${ranked[0].acc}% accuracy · ${ranked[0].correct}/${ranked[0].correct + ranked[0].wrong} correct.`, 'good');
  add('weak', 'Section that needs work', ranked.length > 1 ? ranked[ranked.length - 1].name : null, ranked.length > 1 && `${ranked[ranked.length - 1].acc}% accuracy. Start your revision here.`, 'warn');
  const mostSkipped = [...sec].sort((a, b) => b.skipped / b.count - a.skipped / a.count)[0];
  add('skipsec', 'Most unanswered section', mostSkipped && mostSkipped.skipped ? mostSkipped.name : null, mostSkipped && `${mostSkipped.skipped} of ${mostSkipped.count} left blank.`, 'warn');
  add('spread', 'Section consistency', ranked.length > 1 ? `${fmt(ranked[0].acc - ranked[ranked.length - 1].acc)} pts gap` : null, 'Gap between your best and weakest section accuracy. Smaller is more balanced.', ranked.length > 1 && ranked[0].acc - ranked[ranked.length - 1].acc > 25 ? 'warn' : 'good');
  add('time', 'Time used', used != null && allowed ? `${Math.round(used / 60)} / ${Math.round(allowed / 60)} min` : null, used != null && allowed ? (used < allowed * 0.75 ? 'You submitted early. Spare time could have gone to unanswered questions.' : 'You used most of the available time.') : '');
  add('pace', 'Average time per answer', used != null && attempted.length ? `${Math.round(used / attempted.length)} s` : null, 'Elapsed time divided by answered questions (includes reading and idle time).');
  const firstHalf = mid ? timed.filter((q) => q.accepted_at < mid).length : null;
  add('halves', 'Answering rhythm', firstHalf != null && timed.length ? `${firstHalf} | ${timed.length - firstHalf}` : null, 'Answers saved in the first half vs the second half of the allowed time.');
  add('late', 'Accuracy under time pressure', late.length >= 5 && early.length >= 5 ? `${pct(late.filter((q) => q.outcome === 'correct').length, late.length)}% vs ${pct(early.filter((q) => q.outcome === 'correct').length, early.length)}%` : null, 'Last 20% of the time vs earlier. A big drop means rushed guessing at the end.', 'info');
  add('cstreak', 'Longest correct streak', cs.best ? `${cs.best} in a row` : null, cs.best ? `Starting at Q${cs.at}.` : '', 'good');
  add('wstreak', 'Longest wrong streak', ws.best > 1 ? `${ws.best} in a row` : null, ws.best > 1 ? `Starting at Q${ws.at}. Check if one concept caused all of them.` : '', 'warn');
  add('marked', 'Marked-for-review outcome', marked.length ? `${marked.filter((q) => q.outcome === 'correct').length} / ${marked.length} correct` : null, 'Questions you flagged while solving.');
  add('letters', 'Option pattern', topLetter ? `Chose ${topLetter[0]} ${topLetter[1]}×` : null, `The key has ${keyLetters[topLetter?.[0]] || 0} × ${topLetter?.[0]}. Never pick by pattern; answers are spread across options.`);
  add('breakeven', 'Smart guessing rule', minus ? `${Math.round((100 * minus) / (plus + minus))}% break-even` : null, `With +${plus}/−${minus}, guess only when you can eliminate options and are more than ${Math.round((100 * minus) / (plus + minus))}% sure.`, 'info', minus > 0);
  add('bonus', 'Bonus decision', r.rules?.bonus_rule ? (r.bonus_unlocked_at ? `Entered · ${s.bonus_block?.score} marks` : 'Not entered') : null, r.bonus_unlocked_at ? `${s.bonus_block?.correct} correct, ${s.bonus_block?.incorrect} wrong in the bonus.` : 'Bonus opens only after all main questions are answered.', r.bonus_unlocked_at ? 'good' : 'info');
  add('rank', 'App cohort rank', peerOK && c.rank ? `#${c.rank} of ${c.sample_size}` : null, c?.sample_size < (c?.stable_sample || 100) ? 'Live rank among students who took this paper so far (early sample).' : 'Live rank among students who took this paper.', 'good');
  add('percentile', 'Percentile', peerOK && c.percentile != null ? `${c.percentile}` : null, 'Share of students who scored at or below you on this paper.', 'good');
  add('avg', 'Versus average', peerOK && c.average != null ? `${Number(s.score) - c.average >= 0 ? '+' : ''}${fmt(Number(s.score) - c.average)}` : null, peerOK && `Average score is ${c.average}; median ${c.median}.`, peerOK && Number(s.score) >= c.average ? 'good' : 'warn');
  add('top', 'Gap to topper', peerOK && c.top != null ? `${fmt(c.top - Number(s.score))} marks` : null, peerOK && `Top score on this paper so far: ${c.top}.`);
  add('easy', 'Questions most students solved', peerOK ? `${easyMiss.length} missed` : null, easyMiss.length ? `You missed Q${easyMiss.slice(0, 8).map((q) => q.number).join(', Q')} — 60%+ of students got these. Fix them first.` : 'You did not miss any question that most students solved.', easyMiss.length ? 'warn' : 'good');
  add('hard', 'Tough questions you cracked', peerOK ? `${hardWin.length}` : null, hardWin.length ? `Q${hardWin.slice(0, 8).map((q) => q.number).join(', Q')} — solved by 35% or fewer students.` : 'No low-solve-rate questions solved yet.', 'good');
  const potential = acc != null ? Math.round(skipped.length * (acc * plus - (1 - acc) * minus)) : null;
  add('potential', 'Unanswered potential', potential != null ? `${potential >= 0 ? '+' : ''}${potential} marks` : null, `If you answered the ${skipped.length} blank questions at your current accuracy.`, potential > 0 ? 'info' : 'warn');
  add('next', 'Next best step', `${wrong.length + skipped.length} to revise`, ranked.length > 1 ? `Read the AI solutions for your ${ranked[ranked.length - 1].name} mistakes first, then take an untimed retry.` : 'Read the AI solutions for every wrong answer, then take an untimed retry.', 'info');
  // Always-available facts keep the list at 25 when peer or timing data is missing.
  const openingCount=Math.min(10,main.length);
  const fill = [
    ['correct', 'Correct answers', `${right.length}`, `Earned +${right.length * plus} marks.`, 'good'],
    ['wrongs', 'Wrong answers', `${wrong.length}`, wrong.length ? 'Revisit each one with the solution before your next test.' : 'No wrong answers. Excellent control.', wrong.length ? 'warn' : 'good'],
    ['blank', 'Unanswered', `${skipped.length}`, 'Blank answers cost nothing, but each one is a missed chance at marks.'],
    ['positive', 'Positive marks earned', `+${right.length * plus}`, `Before ${wrong.length * minus} negative marks were taken off.`, 'good'],
    ['size', 'Paper size', `${main.length} questions`, `${sec.length} section${sec.length === 1 ? '' : 's'} · +${plus} / −${minus} / 0 marking.`],
    ['firstten', 'Opening question group', `${main.slice(0, 10).filter((q) => q.outcome === 'correct').length} / ${openingCount}`, `Correct answers among the first ${openingCount} question numbers; this is not your actual solving order.`],
    ['lastten', 'Closing question group', `${main.slice(-10).filter((q) => q.outcome === 'correct').length} / ${openingCount}`, `Correct answers among the final ${openingCount} question numbers.`],
  ];
  fill.forEach(([k, t, v, d, tone]) => { if (out.length < 25) add(k, t, v, d, tone); });
  return out.slice(0, 25);
}
