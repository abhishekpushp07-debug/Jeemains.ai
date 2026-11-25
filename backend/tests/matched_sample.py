"""Sample Matched shifts for the OWNER to look at on the preview (not part of the app, never run by a test).

    python3 /app/backend/tests/matched_sample.py show    # publishes three sample shifts of 22 and 24 Jan 2027, and switches
                                                         # Home's Matched card ON on this database (rf_meta matched:card)
    python3 /app/backend/tests/matched_sample.py hide    # takes them back (published: false) and gives the card back to
                                                         # the series' dates ("auto"). Nothing is deleted.

They are made-up questions in the exact shape memory/MATCHED_CONTRACT.md asks for, written into THIS machine's database
only (the one in backend/.env). Run `hide` as soon as the owner has looked: a student must never see a sample as a match."""
import sys
import time
from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient


def q(text, options=None, correct=None, answer="", solution="", **more):
    return {"text": text, "options": options or [], "correct": correct, "answer": answer, "solution": solution, **more}


def pair(n, subject, chapter, jee, *ours):
    return {"n": n, "subject": subject, "chapter": chapter, "jee": jee, "ours": list(ours)}


SHIFTS = {
    "2027-01-22-s1": [
        pair(4, "Physics", "Kinematics",
             q(r"A particle is projected with speed $u = 20\,\text{m/s}$ at $30^\circ$ above the horizontal. Taking $g = 10\,\text{m/s}^2$, its time of flight is",
               ["1 s", "2 s", "3 s", "4 s"], "B",
               solution=r"Time of flight $T = \dfrac{2u\sin\theta}{g} = \dfrac{2 \times 20 \times \frac{1}{2}}{10} = 2\,\text{s}$."),
             q(r"A ball is thrown with speed $u = 40\,\text{m/s}$ at $30^\circ$ above the horizontal ($g = 10\,\text{m/s}^2$). Its time of flight is",
               ["2 s", "4 s", "6 s", "8 s"], "B",
               solution=r"$T = \dfrac{2u\sin\theta}{g} = \dfrac{2 \times 40 \times \frac{1}{2}}{10} = 4\,\text{s}$.",
               source="AITS Day 12 · Q 7", tag="Same concept")),
        pair(17, "Physics", "Current Electricity",
             q(r"Resistors of $6\,\Omega$ and $3\,\Omega$ are joined in parallel, and this pair is joined in series with a $4\,\Omega$ resistor across a $12\,\text{V}$ battery. The current drawn from the battery is",
               ["1 A", "2 A", "3 A", "4 A"], "B",
               solution=r"Parallel pair: $\dfrac{6 \times 3}{6 + 3} = 2\,\Omega$. Total resistance $= 2 + 4 = 6\,\Omega$. So $I = \dfrac{12}{6} = 2\,\text{A}$."),
             q(r"Resistors of $6\,\Omega$ and $3\,\Omega$ are joined in parallel, and this pair is joined in series with a $4\,\Omega$ resistor across a $12\,\text{V}$ battery. The current drawn from the battery is",
               ["1 A", "2 A", "3 A", "4 A"], "B",
               solution=r"$R = \dfrac{6 \times 3}{6 + 3} + 4 = 6\,\Omega$, so $I = \dfrac{V}{R} = \dfrac{12}{6} = 2\,\text{A}$.",
               source="AITS Day 31 · Q 14", tag="Same question")),
        pair(29, "Chemistry", "Mole Concept",
             q(r"The number of moles of oxygen atoms in $88\,\text{g}$ of $\text{CO}_2$ is", ["1", "2", "4", "8"], "C",
               solution=r"Moles of $\text{CO}_2 = \dfrac{88}{44} = 2$. Each molecule has 2 oxygen atoms, so moles of O atoms $= 2 \times 2 = 4$."),
             q(r"The number of moles of hydrogen atoms in $36\,\text{g}$ of $\text{H}_2\text{O}$ is", ["2", "4", "6", "8"], "B",
               solution=r"Moles of $\text{H}_2\text{O} = \dfrac{36}{18} = 2$. Each molecule has 2 hydrogen atoms, so moles of H atoms $= 4$.",
               source="AITS Day 5 · Q 33", tag="Same concept")),
        pair(41, "Chemistry", "Atomic Structure",
             q(r"The maximum number of electrons that can have principal quantum number $n = 3$ is", ["8", "18", "32", "9"], "B",
               solution=r"A shell holds at most $2n^2$ electrons: $2 \times 3^2 = 18$."),
             q(r"The total number of orbitals in the shell with $n = 4$ is", ["4", "8", "16", "32"], "C",
               solution=r"A shell has $n^2$ orbitals: $4^2 = 16$.",
               source="Chapter test · Atomic Structure · Q 9", tag="Same concept")),
        pair(52, "Mathematics", "Quadratic Equations",
             q(r"If $\alpha$ and $\beta$ are the roots of $x^2 - 5x + 6 = 0$, then $\alpha^2 + \beta^2$ equals", ["11", "13", "25", "37"], "B",
               solution=r"$\alpha + \beta = 5$ and $\alpha\beta = 6$. So $\alpha^2 + \beta^2 = (\alpha + \beta)^2 - 2\alpha\beta = 25 - 12 = 13$."),
             q(r"If $\alpha$ and $\beta$ are the roots of $x^2 - 7x + 10 = 0$, then $\alpha^2 + \beta^2$ equals", ["19", "29", "39", "49"], "B",
               solution=r"$\alpha + \beta = 7$, $\alpha\beta = 10$. So $\alpha^2 + \beta^2 = 49 - 20 = 29$.",
               source="AITS Day 3 · Q 61", tag="Same concept"),
             q(r"If $\alpha$ and $\beta$ are the roots of $x^2 - 5x + 6 = 0$, then $\dfrac{1}{\alpha} + \dfrac{1}{\beta}$ equals",
               [r"$\dfrac{5}{6}$", r"$\dfrac{6}{5}$", r"$\dfrac{1}{6}$", r"$\dfrac{1}{5}$"], "A",
               solution=r"$\dfrac{1}{\alpha} + \dfrac{1}{\beta} = \dfrac{\alpha + \beta}{\alpha\beta} = \dfrac{5}{6}$.",
               source="JEE Main practice set 4 · Q 12", tag="Same equation")),
        pair(71, "Mathematics", "Definite Integration",
             q(r"The value of $\displaystyle\int_0^2 3x^2\,dx$ is ______.", answer="8",
               solution=r"$\displaystyle\int_0^2 3x^2\,dx = \left[x^3\right]_0^2 = 8$."),
             q(r"The value of $\displaystyle\int_0^3 2x\,dx$ is ______.", answer="9",
               solution=r"$\displaystyle\int_0^3 2x\,dx = \left[x^2\right]_0^3 = 9$.",
               source="AITS Day 18 · Q 72", tag="Same concept")),
    ],
    "2027-01-22-s2": [
        pair(9, "Physics", "Work, Energy and Power",
             q(r"A body of mass $2\,\text{kg}$ moving at $10\,\text{m/s}$ is brought to rest by a constant force over a distance of $5\,\text{m}$. The magnitude of the force is",
               ["10 N", "20 N", "40 N", "50 N"], "B",
               solution=r"Work done by the force equals the kinetic energy lost: $F \times 5 = \dfrac{1}{2} \times 2 \times 10^2 = 100\,\text{J}$, so $F = 20\,\text{N}$."),
             q(r"A car of mass $1000\,\text{kg}$ moving at $20\,\text{m/s}$ is stopped by a constant braking force in $50\,\text{m}$. The braking force is",
               ["2000 N", "4000 N", "8000 N", "10000 N"], "B",
               solution=r"$F \times 50 = \dfrac{1}{2} \times 1000 \times 20^2 = 200000\,\text{J}$, so $F = 4000\,\text{N}$.",
               source="AITS Day 8 · Q 11", tag="Same concept")),
        pair(36, "Chemistry", "Ionic Equilibrium",
             q(r"The pH of a $10^{-3}\,\text{M}$ HCl solution at $25^\circ\text{C}$ is", ["1", "3", "7", "11"], "B",
               solution=r"HCl is a strong acid, so $[\text{H}^+] = 10^{-3}\,\text{M}$ and $\text{pH} = -\log 10^{-3} = 3$."),
             q(r"The pH of a $10^{-2}\,\text{M}$ $\text{HNO}_3$ solution at $25^\circ\text{C}$ is", ["2", "4", "7", "12"], "A",
               solution=r"$\text{HNO}_3$ is a strong acid, so $[\text{H}^+] = 10^{-2}\,\text{M}$ and $\text{pH} = 2$.",
               source="AITS Day 22 · Q 41", tag="Same concept")),
        pair(63, "Mathematics", "Sequences and Series",
             q(r"The sum of the first 20 terms of the A.P. $3, 7, 11, \ldots$ is", ["800", "820", "840", "860"], "B",
               solution=r"$S_n = \dfrac{n}{2}\left[2a + (n - 1)d\right] = 10\,[6 + 76] = 820$."),
             q(r"The sum of the first 10 terms of the A.P. $5, 8, 11, \ldots$ is", ["175", "185", "195", "205"], "B",
               solution=r"$S_{10} = 5\,[10 + 27] = 185$.",
               source="AITS Day 27 · Q 66", tag="Same concept")),
    ],
    "2027-01-24-s1": [
        pair(12, "Physics", "Simple Harmonic Motion",
             q(r"A particle executes SHM with time period $T = 2\,\text{s}$ and amplitude $4\,\text{cm}$. Its maximum speed is",
               [r"$2\pi$ cm/s", r"$4\pi$ cm/s", r"$8\pi$ cm/s", r"$16\pi$ cm/s"], "B",
               solution=r"$v_{max} = A\omega = A \times \dfrac{2\pi}{T} = 4 \times \pi = 4\pi$ cm/s."),
             q(r"A particle executes SHM with time period $4\,\text{s}$ and amplitude $6\,\text{cm}$. Its maximum speed is",
               [r"$3\pi$ cm/s", r"$6\pi$ cm/s", r"$12\pi$ cm/s", r"$\dfrac{3\pi}{2}$ cm/s"], "A",
               solution=r"$v_{max} = A \times \dfrac{2\pi}{T} = 6 \times \dfrac{2\pi}{4} = 3\pi$ cm/s.",
               source="AITS Day 40 · Q 19", tag="Same concept")),
        pair(68, "Mathematics", "Probability",
             q(r"Two fair dice are thrown. The probability that the sum of the numbers is 7 is",
               [r"$\dfrac{1}{6}$", r"$\dfrac{1}{12}$", r"$\dfrac{5}{36}$", r"$\dfrac{7}{36}$"], "A",
               solution=r"6 of the 36 equally likely results add up to 7: $(1,6), (2,5), (3,4), (4,3), (5,2), (6,1)$. So the probability is $\dfrac{6}{36} = \dfrac{1}{6}$."),
             q(r"Two fair dice are thrown. The probability that the sum of the numbers is 8 is",
               [r"$\dfrac{1}{6}$", r"$\dfrac{5}{36}$", r"$\dfrac{1}{9}$", r"$\dfrac{7}{36}$"], "B",
               solution=r"5 of the 36 results add up to 8: $(2,6), (3,5), (4,4), (5,3), (6,2)$. So the probability is $\dfrac{5}{36}$.",
               source="AITS Day 44 · Q 70", tag="Same concept")),
    ],
}


# So that the owner can walk the whole way on the preview ("Attempt all matched" -> sign up -> the paper's page -> the
# player and the result showing the JEE Main question under ours), ONE sample shift names a real paper of the website as
# its stand-in: the chapter test "01 Sets and Relations", and its first questions as "ours". A real Matched shift names
# the real paper the super admin made of the matched questions (memory/WEBSITE_MATCHED_NOTE.md).
PAPER_SHIFT, PAPER = "2027-01-22-s1", "f6ad0ca5-b3c8-59dc-a814-e358c197dd7a"
PAPER_QUESTIONS = ["9d8575c5-61fc-57a8-8457-cdddc8b28ebf", "8f97bb76-22ca-5f2b-9bad-fafad26b8f83", "2d75bc69-5116-5703-a8b8-5ae54eb64948", "e23b9eab-2c8d-5b0a-a740-f938cbbadab3",
                   "d650a1ad-f6ed-53f6-8ea5-dcce95e55eb1", "21c73c60-9d2f-5219-8c3a-f01e80b3404f", "864bdf8c-a6ec-5a13-a29b-93f8dab313b1", "4f0c6381-bca6-538c-ae8e-019e2bbd5a44"]
for _ours, _qid in zip((o for item in SHIFTS[PAPER_SHIFT] for o in item["ours"]), PAPER_QUESTIONS):
    _ours["question_id"] = _qid


def main(what):
    env = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    db = MongoClient(env["MONGO_URL"])[env["DB_NAME"]]
    shifts = db.matched_shifts
    if what in ("show", "hide"):
        db.rf_meta.update_one({"_id": "matched:card"}, {"$set": {"value": "on" if what == "show" else "auto", "ts": time.time()}}, upsert=True)
    if what == "show":
        for sid, items in SHIFTS.items():
            shifts.replace_one({"_id": sid}, {"_id": sid, "published": True, "sample": True, "asked": 75, "updated_at": int(time.time()), "items": items,
                                              **({"paper_id": PAPER} if sid == PAPER_SHIFT else {})}, upsert=True)
    elif what == "hide":
        shifts.update_many({"_id": {"$in": list(SHIFTS)}, "sample": True}, {"$set": {"published": False, "updated_at": int(time.time())}})
    else:
        sys.exit(__doc__)
    print([(d["_id"], d.get("published"), len(d.get("items", []))) for d in shifts.find({"sample": True}, {"published": 1, "items": 1}).sort("_id", 1)],
          "| card:", db.rf_meta.find_one({"_id": "matched:card"})["value"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
