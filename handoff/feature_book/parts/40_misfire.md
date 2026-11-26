# Part 4 — Misfire: the website's own, shown in the app

## 4.1 What it is, and who owns it

**Misfire** is every question a student got wrong or left in a finished paper, kept so they can solve it again. jeelive.ai has it, and the app has had it since 24 Nov 2026.

**It is the website's Misfire.** The app does not keep, count or mark Misfire questions of its own. It reads the website's answers and sends the student's tries back to the website. So the website and the app always show the same open questions, the same "Samajh gaya" (understood) questions and the same counts. **Nothing has to be handed over in either direction for it to work: it is already connected.** This part is here so the website agent can check that the two stay the same (Part 4.4).

| Decision | Date | Where it shows |
| --- | --- | --- |
| Misfire must be the same on the website and in the app: one calculation, the website's | 26 Nov 2026 (the owner) | the whole of this part |
| The app also shows it paper-wise for AITS, JEE Chapter-wise, JEE PYQ, BITSAT Mocks, BITSAT Chapter-wise and COMEDK Mocks | 24 Nov 2026 | Part 4.2 |
| All India Rapid's "Misfires" tab is Rapid Fire's own and is not given to the website | 26 Nov 2026 | Part 4.5 |

## 4.2 What a student sees in the app

[[shots: x01_home_misfire | 14. Home: the Misfire card under the exam tiles ; x02_misfire_all | 15. Misfire, tab "Sab": the website's own list ; x03_misfire_papers | 16. A paper-wise tab: the finished papers of one test family]]

- **Home card "MISFIRE"** (blood red, the word in glossy yellow, a row of lights round its edge): "607 sawaal dobara solve karne hain", plus one chip per subject with its open count. It is hidden until the student has a graded paper. It is read from `GET /api/my/misfire/summary`.
- **`/misfire`**, small line "Galat + chhode sawaal · dobara solve karo", with the count "607 OPEN" at the top right. Its tabs are **Sab** (all), then **AITS · JEE Chapter-wise · JEE PYQ · BITSAT Mocks · BITSAT Chapter-wise · COMEDK Mocks**. A family whose exam the website hides is not offered.
- **Sab** is the website's Misfire as it is:
    - **Galtiyan** = `status=open`, and **Samajh gaya** = `status=fixed`, 20 a page with "Aur dikhao" (show more);
    - subject pills, and a chapter sheet ("Saare chapter");
    - **Chapter report** = `GET /api/my/chapters`;
    - the questions sit under their paper's name.
- **A family tab** lists that family's finished, scored papers, newest first, each with its wrong and left counts. A tap opens **the paper's page** `/misfire/<attempt id>`. That page lists the paper's wrong and left questions, with subject, "Galat" and "Chhode" filters, plus "Dobara solve karo" (solve again) and "Poora analysis" (the normal result).
- **Solve again** shows the question as it was printed and the answer given in the paper, then takes a fresh try:
    - option tiles or option cards, or the app's own number keys for a numerical;
    - after a wrong try, the right answer;
    - after any try, the solution;
    - after a right try, "Samajh gaya"; and "Wapas list mein" (back to the list);
    - "Pichhla / Agla" (previous / next) at the bottom.
- **AITS:** the AITS Analysis list has one button, "AITS ki galtiyan dobara solve karo", which opens the AITS tab.
- While the website says some papers are still being prepared (`waiting` > 0), the app shows "Aapke kuch papers abhi jud rahe hain…" and asks again every 3 seconds, 8 times at most.

**Every request, and what the app expects back** (through the app's server, which passes them unchanged to `https://jeelive.ai/api/…`):

| Request | What the app reads |
| --- | --- |
| `GET /my/misfire/summary` | `open`, `fixed`, `waiting`, `subjects[] {name, open, fixed}` |
| `GET /my/misfire?status=open\|fixed&subject=&chapter=&page=` | `items[]`, `total`, `page`, `pages`, `waiting`, `chapters[] {name, count}`; each item: `id`, `attempt_id`, `question_id`, `title`, `exam`, `subject`, `chapter`, `number`, `outcome` (`incorrect` \| `skipped`), `lost`, `your_answer`, `type`, `question`, `solution_count`, `status`, `tries`, `last_correct`, `at` |
| `GET /my/chapters` | `papers`, `waiting`, `chapters[]` and `subjects[]` {subject, chapter, papers, total, correct, wrong, skipped, lost, sahi, accuracy, trend}, `untagged` |
| `POST /my/misfire/<id>/try {value}` | `{correct, item}`; the item carries `answer` and `solution_text` only after a try |
| `POST /my/misfire/<id>/done` | refused (409) until a right try; then the question moves to "Samajh gaya" |
| `POST /my/misfire/<id>/reopen` | back to the open list, tries back to 0 |
| `GET /exam-navigation/<slug>/history?kind=<kind>&page=` | the family tabs: JEE Main `chapter` and `pyq`; BITSAT `mock` and `chapter`; COMEDK `mock` |
| `GET /series/all-india-jee/history?page=` | the AITS tab (20 a page) |
| `GET /attempts/<id>/results?score_version=original` | a paper's page: its wrong and left questions |

## 4.3 The only three things the app works out by itself

| What | How the app does it | What the website should confirm |
| --- | --- | --- |
| **Which papers a family tab lists** | The website's paper history of that family. Attempts whose `mode` is `retry`, `preview` or begins with `series_` are left out of the family tabs: a retry repeats its own paper's questions, and an All India day has its own tab. Only papers that have a score (`summary`) are listed; the wrong and left counts are the summary's `incorrect` and `skipped` | that these kinds and modes mean what the app takes them to mean |
| **A paper's wrong and left questions** | From that paper's own result: every question whose `outcome` is `incorrect` or `skipped`. The question's Misfire id is built as **`<attempt id>:<question id>`**, and the tries on that page are sent to that id. "Samajh gaya" on that page comes from the website's `status=fixed` list (the newest 100). A result that is not out yet reads "Is paper ka result abhi nahi khula." | that every wrong or left question of every scored paper has a Misfire item, and that its id is written exactly so |
| **"Kitne marks gaye"** (marks lost) on a paper's page | The question's own `scoring.correct` (or the paper's `rules.correct`) minus the marks the question got. Under +4 / −1: wrong = 5, left = 4 | that the website's own `lost` in `/my/misfire` means the same |

Everything else on these screens (what is open, what is understood, every count, the chapter report, whether a try is right) is the website's answer, shown as it comes.

## 4.4 Checks for the website agent

1. The answers of Part 4.2 keep their fields. **A field may be added; none may be renamed or dropped without telling the app side** (rule 3 of the "who builds what" table the two sides keep).
2. Every wrong or left question of **every** scored paper has a Misfire item with the id `<attempt id>:<question id>`. That includes All India days, chapter tests, PYQ papers, BITSAT and COMEDK papers, a **Student Choice paper** (`test_kind` `choice`, when door C exists) and a **Matched paper** (Part 2.4b).
3. `lost` means "the marks a right answer would have given, minus the marks given" (Part 4.3).
4. `try` accepts the answer as the paper took it: the option's key for an MCQ (the same key `your_answer` holds), and the number as typed for a numerical. A numerical try may have a decimal point unless the question's `type` is `integer`.
5. **A question for the website:** what `kind` will Student Choice papers and Matched papers have in `GET /exam-navigation/jee-main/history?kind=…` (for example `choice` and `matched`)? Tell the app side. The app can then give each its own Misfire tab. Until then their questions are in "Sab" like every other paper's, and chapter tests taken from Student Choice are already in "JEE Chapter-wise".
6. A paper that has just been submitted, whose Misfire is still being prepared, is counted in `waiting`, and the app waits for it. Please keep doing that, rather than answering an empty list.

## 4.5 All India Rapid's "Misfires" tab: a different thing, Rapid Fire's own

The result screen of **All India Rapid** has a **"Misfires"** tab. All India Rapid is the app's daily Rapid Fire round, 45 cards, the same for all of India. The tab lists the cards of that round the student did not answer right: wrong, timed out or skipped, each with "You chose", the right answer and the explanation, and subject pills to filter them.

- It is **Rapid Fire's**, on the app's server (`GET /api/rf/daily/misses`). It is **never mixed** with the papers' Misfire above and needs nothing from the website. The website has no Rapid Fire of its own (Part 5).
- Cards the student never reached (they left the round early) stay sealed: all of India plays the same cards that day, so their answers must not come out through a student who quits at card 1. The tab's number counts every card not answered right; the list shows only the cards the student saw, and a note under it says how many were never reached.
- It is in the app since 25 Nov 2026. It is also in the browser Rapid Fire, rebuilt on 26 Nov 2026 (Part 5).

## 4.6 Not checked

- BITSAT and COMEDK papers in Misfire (the test learner has none), and questions the website sends in cut pieces inside Misfire.
- A real All India day (the series begins on {{SERIES_FIRST}}).
- Anything on a real phone.
