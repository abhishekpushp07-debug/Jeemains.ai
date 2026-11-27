# JEELIVE.AI — website look kit

**Owner ke liye (Hinglish):** Is folder mein app ka poora look hai: phone screenshots, saare colours, fonts, sizes
aur app ka asli code jahan woh look bana hai. Website agent ko bas is folder ka link do aur bolo:
"`LOOK_GUIDE.md` padho aur website ko is jaisa banao." Yeh sirf **look** ke liye hai. Data, login, paper, timer,
result ab bhi website ke hi rahenge. App ka koi bhi data route ya contract yahan se nahi badalta.

**For the website agent:** read `LOOK_GUIDE.md` first. It says, screen by screen, what the app shows and where the
exact values live. Copy the look only. Never copy data, never change any contract the app reads, and keep every
website route and response shape exactly as it is today.

| Folder / file | What is inside |
|---|---|
| `LOOK_GUIDE.md` | The rules, the colours, the fonts, and a screen-by-screen guide with the file that draws each part |
| `screens/` | 21 phone screenshots (390 x 844, shown at 2x), taken from the app preview on 28 Nov 2026 with the owner's QA learner, read only |
| `reference_code/` | Copies of the app files that hold the look: `theme.ts` (every colour), `GlossTabs.tsx` (the glossy tabs), Home parts, Misfire card, Share card, Dream meter, report card, and the "Get the app" card |

The fonts are already the website's own: Figtree 400/500/600/700/800 and Roboto Mono 400/700 (the app loads them
from the website's 26 Oct 2026 export).

Screenshots show the QA learner's real numbers on the day; the series card on Home is a stand-in day used only for the
picture. Do not copy any number from a picture into the website.
