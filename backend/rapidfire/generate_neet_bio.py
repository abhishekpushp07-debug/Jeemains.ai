"""Offline authoring of NEET (UG) Biology Rapid Fire cards (NCERT-based). Writes 105 per chapter;
audit_cards.py then trims each chapter to the best 90. Idempotent.
Run: python rapidfire/generate_neet_bio.py
"""
import asyncio, json, os, random, re, uuid
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / ".env")
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402
from generate_cards import valid, slug, OUT  # noqa: E402

CHAPTERS = json.loads((ROOT / "neet_chapters.json").read_text())
TARGET, BATCH = 105, 25

SYSTEM = """You are a senior NEET (UG) Biology faculty member authoring 20-second Rapid Fire recall cards.
STRICT RULES:
- Syllabus: ONLY the current NMC NEET (UG) syllabus, strictly NCERT Class 11/12 Biology content of the named chapter.
- Each card tests ONE NCERT fact, term, definition, example, function, location, sequence, exception or direct conceptual distinction.
- Answerable mentally in 20 seconds: no calculations, no long passages, no trick wording, no "Both/All/None of these".
- prompt: max 110 characters, one short line. formula: "" (or a very short term/equation like "C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O").
- 4 options, each max 40 characters, mutually exclusive, exactly one correct, plausible distractors.
- explain: one line, max 120 characters, NCERT-accurate.
- Pick the MOST IMPORTANT, most frequently asked NEET points first. Use only verifiable NCERT facts; if unsure, skip.
Return ONLY a JSON array: [{"prompt":"...","formula":"","options":["..","..","..",".."],"answer":0,"explain":"..","topic":".."}]"""


async def author(sem, chapter):
    path = OUT / f"biology__{slug(chapter)}.json"
    cards = json.loads(path.read_text()) if path.exists() else []
    if cards and (ROOT / "rejected" / path.name).exists() or len(cards) >= TARGET:
        return print("SKIP", chapter, flush=True)
    tries = 0
    while len(cards) < TARGET and tries < 10:
        tries += 1
        need = min(BATCH, TARGET - len(cards))
        seen = "\n".join(f"- {c['prompt']}" for c in cards[-110:])
        msg = f"Chapter: {chapter} (NEET UG Biology)\nWrite {need} NEW cards.\nAlready written (do not repeat these ideas):\n{seen or '- none'}"
        async with sem:
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=str(uuid.uuid4()),
                               system_message=SYSTEM).with_model("anthropic", "claude-sonnet-4-6")
                text = await chat.send_message(UserMessage(text=msg))
            except Exception as e:  # noqa: BLE001
                print("ERR", chapter, str(e)[:100], flush=True)
                await asyncio.sleep(5)
                continue
        m = re.search(r"\[.*\]", text, re.S)
        try:
            batch = json.loads(m.group(0)) if m else []
        except Exception:
            continue
        known = {c["prompt"].strip().lower() for c in cards}
        for c in batch:
            if not valid(c) or c["prompt"].strip().lower() in known:
                continue
            correct = c["options"][c["answer"]]
            opts = [o.strip() for o in c["options"]]
            random.shuffle(opts)
            cards.append({"id": str(uuid.uuid4()), "subject": "Biology", "chapter": chapter,
                          "topic": str(c.get("topic") or chapter)[:60], "prompt": c["prompt"].strip(),
                          "formula": str(c.get("formula") or "").strip()[:80], "options": opts,
                          "answer": opts.index(correct.strip()), "explain": c.get("explain", "").strip(),
                          "review_status": "pilot_review_pending", "syllabus": "NEET"})
            known.add(c["prompt"].strip().lower())
        path.write_text(json.dumps(cards[:TARGET], ensure_ascii=False, indent=1))
    print(f"DONE {chapter}: {len(cards)}", flush=True)


async def main():
    sem = asyncio.Semaphore(8)
    await asyncio.gather(*[author(sem, ch) for ch in CHAPTERS["Biology"]])


if __name__ == "__main__":
    asyncio.run(main())
