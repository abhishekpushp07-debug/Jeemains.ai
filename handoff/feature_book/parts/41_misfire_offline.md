## 4.7 Offline Misfire: a practice mock on the phone, also without internet

**New on 28 Nov 2026 (the owner's decision of that day).** Misfire's tab that was called "Mock" is now **"Offline Misfire"**. It makes a JEE Main-like mock out of the student's own Misfire questions, **on the phone**. With a line it takes them from the website's fresh Misfire list, as before; with no line, from the finished papers the phone already keeps. **It is never a paper on the website.** It never changes the website's Misfire by itself: the one thing it sends is a right answer, through the website's own Misfire doors, once the line is back.

| Decision | Date | Where it shows |
| --- | --- | --- |
| The "Mock" tab is called "Offline Misfire"; its setup, player and result stay as they were | 28 Nov 2026 (the owner) | the tab, My Tests, the mock's own screens |
| With no line, the questions come from the finished papers kept on the phone, leaving out those last seen as "Samajh gaya" | 28 Nov 2026 | below |
| A right answer becomes "Samajh gaya" on the website when the line is back | 28 Nov 2026 | below |
| Offline Misfire mocks are not on the website; they are in the app's My Tests | 28 Nov 2026 | below |
| The rules of the app's offline part stay: a sign-in with a line in the last 7 days, only the pictures already on the phone (512 MB at most) | 28 Nov 2026 | below |

[[shots: x04_offline_home | 17. No internet: the offline home offers Offline Misfire ; x05_offline_setup | 18. Its setup, from the papers kept on the phone ; x06_offline_result | 19. Its result: the right answers wait for the line]]

**What a student sees**

- **Misfire → "Offline Misfire"** (`/misfire?tab=mock`): the dark-red card "OFFLINE MISFIRE · Galtiyon se JEE Main mock", the button "Naya mock banao", and every mock made on this phone, newest first.
- **With no line**, the offline home ("Phone par rakha hua · Rapid Fire, results aur Misfire") has the card **"Offline Misfire"** ("Apni galtiyon se JEE Main jaisa mock, bina internet. Jo sahi karoge, internet aate hi “Samajh gaya” ho jayenge."). It opens the same list at `/offline/misfire`.
- **The setup** is the one it always was: Physics, Chemistry and Mathematics, up to 25 each (5, 10, 25 or "Max"), and the chapters. Time by the owner's ratio: 25 Physics = 60 min, 25 Chemistry = 40, 25 Maths = 80. When the questions come from the phone, it says so:
    - no line: "Sirf phone par rakhe N papers se · M sawaal mile. Jo pehle “Samajh gaya” ho chuke, woh nahi liye.";
    - a line, but the website's Misfire list does not come: "Website se list abhi nahi aa paayi." before the same sentence, and a button "Website se dobara laao".
- **The ready screen** adds "Phone par rakhe papers se bana: internet ke bina bhi poora chalega.", and "Saare sawaal phone par taiyaar" once every picture is there.
- **The result** is the one it always was: the score, subject by subject, the chapters to look at again, and every question with its key and solution. While right answers wait for the line: "N sahi sawaal “Samajh gaya” mein ja rahe hain. Internet aate hi pahunch jayenge." Once they are through: "N sawaal “Samajh gaya” mein chale gaye".
- **My Tests** lists it as "Offline Misfire #n", and its own screens are titled "OFFLINE MISFIRE #n".

**How it works (all of it on the phone)**

| What | How |
| --- | --- |
| The questions, with a line | the website's open Misfire list, `GET /my/misfire?status=open&subject=…` (Part 4.2), as before |
| The questions, with no line | every `incorrect` or `skipped` question of the finished papers the phone keeps (the same papers "Mere results" opens offline), of Physics, Chemistry and Mathematics, with its key; not a bonus or dropped question; once only (the newest paper's copy when a question was in two); and **only when its pictures are already on the phone**. A result kept but never opened once is left out, as it is everywhere offline. The question's id is its Misfire id `<attempt id>:<question id>` |
| "Samajh gaya", with no line | the phone remembers the ids it last saw in the website's `status=fixed` list, and leaves them out. It learns them from Misfire's own screens and, after the phone keeps papers, at most once in 15 minutes and never during a paper: `GET /my/misfire/summary`, and the `status=fixed` pages (20 a page, 50 pages at most) only when the website's count differs from the phone's, or a day after the last full read. A question marked on the website since then can still come in once |
| Who may open it with no line | the same rule as for the rest of the app's offline part: the account signed in on this phone **with a line in the last 7 days**. Otherwise: "Pehle ek baar internet ke saath app kholo" |
| A right answer | kept on the phone. When the line and the session are back, the app sends it **through the website's own doors**: `POST /my/misfire/<id>/try` with the answer, then `POST /my/misfire/<id>/done` when the website says it is right. It tries again every 45 seconds while the student is signed in, until it is through. **Nothing is sent while nobody is signed in** |
| Pictures | only those already on the phone (the same 512 MB as before); nothing new is fetched without a line |
| Where the mock is kept | on the phone only, under that account. It is **never** a set, an attempt or a result on the website, and the website's Mock tab never lists it |

**For the website: nothing to build.** Please keep three things as they are (Part 4.4 and Part 7.2 already ask for them):

1. `POST /my/misfire/<id>/try` judges the answer itself and gives `correct`. The app never decides on the website's behalf that an answer is right. A try that comes **hours later**, from a phone that was offline, is judged the same way.
2. `POST /my/misfire/<id>/done` after a right try moves the item to "Samajh gaya". A second `done` on an item already there does no harm (the app may send it again after an answer that got lost).
3. A try on an item the student has meanwhile marked "Samajh gaya" on the website is answered like any other try (the app then sends `done`, which changes nothing).

**Checked on 28 Nov 2026** (`tests/offline_misfire_check.py`, 30 checks; the website's writes were answered by the browser, nothing was written): the tab's name; the website's list with a line; the phone's papers when the list does not come, with the sentence and the button; a question listed as "Samajh gaya" left out; the offline door, the list, the setup, the mock and its result with no line at all, every picture from the phone; nothing sent while signed out; each right answer sent once (try, then done) about 6 seconds after the line came back; My Tests' name; shut on a phone with no confirmed session. The app side's independent review found no fault.

**Not checked:** a real phone with no network (the preview's browser was cut off from the network instead); many days offline; one student's two phones offline at once.
