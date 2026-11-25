"""Made-up Student Choice chapters for the OWNER'S EYES ON THE PREVIEW ONLY, until jeelive.ai has its own doors.

    python3 backend/tests/choice_sample.py show    # writes the sample chapters and switches the sample on
    python3 backend/tests/choice_sample.py hide    # switches the sample off (the chapters stay, unseen; nothing is deleted)

The app then shows a real-looking bank marked SAMPLE: chapters can be picked, questions ticked, the time and marks add up.
"Paper banao" still needs jeelive.ai (it makes the real paper), so with the sample it answers that the paper could not be
made. Never run `show` against the production database."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

STEMS = {
    "Physics": ["A ball is thrown vertically up with speed $u$. The time it takes to come back to the thrower's hand is",
                "A block of mass $m$ rests on a rough incline of angle $\\theta$. The least coefficient of friction for it to stay at rest is",
                "Two resistors $R_1$ and $R_2$ are joined in parallel across a cell. The ratio of the heat produced in them is",
                "A particle moves in a circle of radius $r$ with constant speed $v$. Its acceleration is",
                "The dimensional formula of Planck's constant is", "A convex lens of focal length $f$ forms a real image twice the size of the object. The object distance is",
                "The escape speed from the surface of a planet of mass $M$ and radius $R$ is", "A wire of length $L$ is stretched by a load. The energy stored per unit volume is"],
    "Chemistry": ["The hybridisation of the central atom in $\\mathrm{SF_4}$ is", "The number of moles of $\\mathrm{KMnO_4}$ reduced by one mole of $\\mathrm{KI}$ in alkaline medium is",
                  "Which of these has the highest first ionisation enthalpy?", "The pH of a $10^{-3}$ M solution of $\\mathrm{HCl}$ is",
                  "The IUPAC name of $\\mathrm{CH_3CH(OH)CH_3}$ is", "For a first order reaction the half-life is 20 min. The rate constant is",
                  "The geometry of $[\\mathrm{Ni(CO)_4}]$ is", "The number of $\\sigma$ bonds in benzene is"],
    "Mathematics": ["If $A = \\{1, 2, 3, 4\\}$, the number of relations on $A$ that are reflexive is", "The value of $\\displaystyle\\int_0^{\\pi/2} \\sin^2 x\\,dx$ is",
                    "If the roots of $x^2 - 5x + k = 0$ differ by 1, then $k$ is", "The distance of the point $(1, 2, 3)$ from the plane $x + y + z = 3$ is",
                    "The number of ways of arranging the letters of the word MATHS is", "If $\\vec a\\cdot\\vec b = 0$ and $|\\vec a| = |\\vec b| = 1$, then $|\\vec a + \\vec b|$ is",
                    "The sum of the first $n$ odd natural numbers is", "The slope of the tangent to $y = x^3$ at $x = 2$ is"],
}
CHAPTERS = {
    "Physics": ["Units, Dimensions and Errors", "Kinematics", "Laws of Motion", "Work, Energy and Power", "Current Electricity", "Ray Optics"],
    "Chemistry": ["Mole Concept", "Atomic Structure", "Chemical Bonding", "Chemical Kinetics", "Coordination Compounds"],
    "Mathematics": ["Sets and Relations", "Quadratic Equations", "Definite Integration", "Vectors", "Straight Lines"],
}


def docs():
    out = []
    for subject, titles in CHAPTERS.items():
        for n, title in enumerate(titles, 1):
            cid = f"sample-{subject[:3].lower()}-{n:02d}"
            # 18 to 30 questions a chapter; every fifth one a number question, like a JEE Main paper.
            count = 18 + 3 * ((n * 2) % 5)
            out.append({"_id": cid, "subject": subject, "n": n, "title": title, "sample": True,
                        "questions": [{"id": f"{cid}-q{k:02d}", "n": k, "type": "integer" if k % 5 == 0 else "mcq",
                                       "text": f"(Sample) {STEMS[subject][(k + n) % len(STEMS[subject])]}"} for k in range(1, count + 1)]})
    return out


async def main(word: str):
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    if word == "show":
        for d in docs():
            await db.choice_sample.replace_one({"_id": d["_id"]}, d, upsert=True)
    await db.rf_meta.update_one({"_id": "choice:sample"}, {"$set": {"value": word == "show"}}, upsert=True)
    print(f"sample {'on' if word == 'show' else 'off'}: {await db.choice_sample.count_documents({})} chapters kept")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("show", "hide"):
        sys.exit("say: show | hide")
    asyncio.run(main(sys.argv[1]))
