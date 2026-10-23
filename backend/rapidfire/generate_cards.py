"""Offline authoring tool for Rapid Fire formula/concept cards (JEE Main syllabus only).
Writes JSON files to rapidfire/cards/. Cards are marked review_status='pilot_review_pending'.
Run: python rapidfire/generate_cards.py  (idempotent: skips chapters already complete)
"""
import asyncio, json, os, re, random, uuid, sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / ".env")
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

OUT = ROOT / "cards"
OUT.mkdir(exist_ok=True)
CHAPTERS = json.loads((ROOT / "chapters.json").read_text())
INORGANIC = {"Periodic Properties", "p-Block", "d & f Block", "Coordination Compounds"}
BATCH = 25

SYSTEM = """You are a senior JEE Main faculty member authoring 20-second Rapid Fire recall cards.
STRICT RULES:
- Syllabus: ONLY the current NTA JEE Main syllabus for the named chapter. Nothing beyond it.
- Each card tests ONE formula, law, definition, relationship, unit/dimension, trend, exception, or direct conceptual distinction.
- NO pen needed: no numerical substitution, no arithmetic, no multi-step algebra, no derivations, no long passages, no trick wording.
- prompt: max 110 characters, one short line. formula: optional short symbolic expression (plain unicode, e.g. "E = hν", "Kₐ·K_b = K_w"), else "".
- 4 options, each max 40 characters, mutually exclusive, exactly one correct, plausible distractors.
- explain: one line, max 120 characters, stating the concept.
- Pick the MOST IMPORTANT, most frequently tested JEE Main concepts first.
- Use correct, verifiable facts only. If unsure, skip that idea.
Return ONLY a JSON array: [{"prompt":"...","formula":"","options":["..","..","..",".."],"answer":0,"explain":"..","topic":".."}]"""

BANNED = re.compile(r"\b(calculate|compute|find the value|evaluate|how many joules|numerically)\b", re.I)


def valid(c):
    try:
        opts = c["options"]
        return (isinstance(c["prompt"], str) and 5 < len(c["prompt"]) <= 140 and isinstance(opts, list) and len(opts) == 4
                and len({o.strip().lower() for o in opts}) == 4 and all(isinstance(o, str) and 0 < len(o) <= 60 for o in opts)
                and c["answer"] in (0, 1, 2, 3) and isinstance(c.get("explain", ""), str) and len(c.get("explain", "")) <= 180
                and not BANNED.search(c["prompt"]))
    except Exception:
        return False


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


async def author(sem, subject, chapter, target):
    path = OUT / f"{slug(subject)}__{slug(chapter)}.json"
    cards = json.loads(path.read_text()) if path.exists() else []
    tries = 0
    while len(cards) < target and tries < 8:
        tries += 1
        need = min(BATCH, target - len(cards))
        seen = "\n".join(f"- {c['prompt']}" for c in cards[-120:])
        msg = (f"Subject: {subject}\nChapter: {chapter} (JEE Main)\nWrite {need} NEW cards."
               f"\nAlready written (do not repeat these ideas):\n{seen or '- none'}")
        async with sem:
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=str(uuid.uuid4()),
                               system_message=SYSTEM).with_model("anthropic", "claude-sonnet-4-6")
                text = await chat.send_message(UserMessage(text=msg))
            except Exception as e:  # noqa: BLE001
                print("ERR", chapter, e, flush=True)
                await asyncio.sleep(5)
                continue
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            continue
        try:
            batch = json.loads(m.group(0))
        except Exception:
            continue
        known = {c["prompt"].strip().lower() for c in cards}
        for c in batch:
            if not valid(c) or c["prompt"].strip().lower() in known:
                continue
            # shuffle option order so the key position carries no bias
            correct = c["options"][c["answer"]]
            opts = c["options"][:]
            random.shuffle(opts)
            cards.append({"id": str(uuid.uuid4()), "subject": subject, "chapter": chapter,
                          "topic": str(c.get("topic") or chapter)[:60], "prompt": c["prompt"].strip(),
                          "formula": str(c.get("formula") or "").strip()[:80], "options": [o.strip() for o in opts],
                          "answer": opts.index(correct), "explain": c.get("explain", "").strip(),
                          "review_status": "pilot_review_pending", "syllabus": "JEE Main"})
            known.add(c["prompt"].strip().lower())
            if len(cards) >= target:
                break
        path.write_text(json.dumps(cards, ensure_ascii=False, indent=1))
    print(f"DONE {subject} / {chapter}: {len(cards)}/{target}", flush=True)


async def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    sem = asyncio.Semaphore(8)
    jobs = []
    for subject, chapters in CHAPTERS.items():
        if only and subject != only:
            continue
        for ch in chapters:
            jobs.append(author(sem, subject, ch, 100 if ch in INORGANIC else 50))
    await asyncio.gather(*jobs)


if __name__ == "__main__":
    asyncio.run(main())
