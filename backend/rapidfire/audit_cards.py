"""Rapid Fire pool audit: NO rewriting. Each card is only judged, then the pool is trimmed.
- reject cards that need pen/paper (substitution, arithmetic, multi-step algebra) or are not a direct
  formula / concept / statement answerable mentally in 20 s,
- keep the most exam-important cards: 90 per chapter (120 for inorganic chapters).
Judgements are cached in audit_cache.json (keyed by card id), so re-runs cost no credits.
Rejected/trimmed cards are moved to rapidfire/rejected/ (server retires them softly).
Run: python rapidfire/audit_cards.py [file-prefix ...]   e.g. physics chemistry mathematics
"""
import asyncio, json, os, sys, uuid
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / ".env")
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

CARDS, REJ, CACHE = ROOT / "cards", ROOT / "rejected", ROOT / "audit_cache.json"
REJ.mkdir(exist_ok=True)
INORGANIC = {"Periodic Properties", "p-Block", "d & f Block", "Coordination Compounds"}
BATCH = 30
cache: dict = json.loads(CACHE.read_text()) if CACHE.exists() else {}

SYSTEM = """You audit 20-second {exam} Rapid Fire MCQ cards. Do NOT rewrite anything; only judge.
For EACH card return [index, ok, imp]:
- ok = 1 only if a well-prepared student can answer it MENTALLY within 20 seconds without pen/paper: a direct formula, law, definition,
  unit/dimension, trend, exception, fact or one-line conceptual statement. Single-step obvious mental arithmetic (e.g. doubling) is fine.
- ok = 0 if it needs written work: numerical substitution with non-trivial numbers, multi-step algebra/calculus, solving equations,
  integration/differentiation of non-standard expressions, long case analysis, reading a long passage, or if it is vague/trivia/off-syllabus.
- imp = 1..5, how important/frequently tested this exact idea is in {exam} (5 = must-know, asked often).
Return ONLY a JSON array like [[0,1,5],[1,0,2],...] with one entry per card, in order."""


async def judge(sem, batch, exam):
    listing = "\n".join(f'{i}. {c["prompt"]}' + (f' [{c["formula"]}]' if c.get("formula") else "") + f'\n   options: {json.dumps(c["options"], ensure_ascii=False)}'
                        for i, c in enumerate(batch))
    for _ in range(3):
        async with sem:
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=str(uuid.uuid4()),
                               system_message=SYSTEM.format(exam=exam)).with_model("anthropic", "claude-sonnet-4-6")
                text = await chat.send_message(UserMessage(text=f"{batch[0]['subject']} / {batch[0]['chapter']}\n\n{listing}"))
                k = text.find("[[")
                if k < 0:
                    k = text.find("[")
                rows = json.JSONDecoder().raw_decode(text[k:].replace("[ [", "[["))[0] if k >= 0 else None
                if rows and len(rows) == len(batch) and all(isinstance(r, list) and len(r) == 3 for r in rows):
                    return rows
            except Exception as e:  # noqa: BLE001
                print("ERR", str(e)[:100], flush=True)
                await asyncio.sleep(4)
    return None


async def run_file(sem, path, stats):
    cards = json.loads(path.read_text())
    if not cards:
        return
    exam = cards[0].get("syllabus", "JEE Main")
    todo = [c for c in cards if c["id"] not in cache]
    for s in range(0, len(todo), BATCH):
        batch = todo[s:s + BATCH]
        rows = await judge(sem, batch, exam)
        if not rows:
            continue
        for c, (_, ok, imp) in zip(batch, rows):
            cache[c["id"]] = {"ok": int(ok == 1), "imp": int(imp) if str(imp).isdigit() else 3}
        CACHE.write_text(json.dumps(cache))
    if any(c["id"] not in cache for c in cards):
        print("INCOMPLETE", path.name, flush=True)
        return  # never trim on partial judgement
    cap = 120 if cards[0]["chapter"] in INORGANIC else 90
    good = [c for c in cards if cache[c["id"]]["ok"]]
    order = {c["id"]: i for i, c in enumerate(cards)}
    good.sort(key=lambda c: (-cache[c["id"]]["imp"], order[c["id"]]))
    keep = {c["id"] for c in good[:cap]}
    kept = [c for c in cards if c["id"] in keep]
    out = [{**c, "reject": "needs_pen" if not cache[c["id"]]["ok"] else "over_cap"} for c in cards if c["id"] not in keep]
    if out:
        rp = REJ / path.name
        prev = json.loads(rp.read_text()) if rp.exists() else []
        rp.write_text(json.dumps(prev + out, ensure_ascii=False, indent=1))
        path.write_text(json.dumps(kept, ensure_ascii=False, indent=1))
    stats["pen"] += sum(1 for c in out if c["reject"] == "needs_pen")
    stats["cap"] += sum(1 for c in out if c["reject"] == "over_cap")
    print(f"DONE {path.name}: {len(cards)} -> {len(kept)}", flush=True)


async def main():
    prefixes = tuple(a.lower() for a in sys.argv[1:])
    sem = asyncio.Semaphore(10)
    stats = {"pen": 0, "cap": 0}
    files = [p for p in sorted(CARDS.glob("*.json")) if not prefixes or p.name.startswith(prefixes)]
    await asyncio.gather(*[run_file(sem, p, stats) for p in files])
    print("TOTAL", stats, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
