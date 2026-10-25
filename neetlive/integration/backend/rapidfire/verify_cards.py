"""Offline second-pass verifier for Rapid Fire cards: an independent expert check of every answer key.
- fixes wrong keys, rewrites options that refer to other options ("Both A and B", "All of these"),
- drops ambiguous / out-of-syllabus cards, removes duplicate prompts.
Idempotent: cards get "verified": 1 and are skipped on re-run.
Run: python rapidfire/verify_cards.py
"""
import asyncio, json, os, re, uuid
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / ".env")
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

CARDS = ROOT / "cards"
BATCH = 20
REF = re.compile(r"\b(both|all of (these|the above)|none of (these|the above)|[abcd] and [abcd]|neither)\b", re.I)

SYSTEM = """You are a meticulous JEE Main subject expert auditing multiple-choice recall cards. For EACH card, solve it yourself first, then compare with the given key.
Return ONLY a JSON array, one object per card, in order: {"i": <index>, "v": "ok" | "fix" | "drop", "answer": <correct option index 0-3>, "options": [4 strings] (only if you rewrite options)}
- "ok": key is correct, exactly one option is correct, wording is clear.
- "fix": the key is wrong (give the right index) and/or an option refers to other options by letter/position ("Both A and B", "All of these", "None of these") -> rewrite those options as explicit standalone text (max 40 chars) and give the matching index.
- "drop": two options are correct, none is correct, the fact is disputed, or it is outside the JEE Main syllabus.
Be strict about facts (e.g. exceptions, trends, signs, units). Keep option order unless rewriting."""


async def check(sem, batch):
    listing = "\n".join(f'{i}. {c["prompt"]} {("[" + c["formula"] + "]") if c.get("formula") else ""}\n   options: {json.dumps(c["options"], ensure_ascii=False)}\n   key: {c["answer"]}'
                        for i, c in enumerate(batch))
    for _ in range(3):
        async with sem:
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=str(uuid.uuid4()), system_message=SYSTEM.replace("JEE Main", batch[0].get("syllabus", "JEE Main"))).with_model("anthropic", "claude-sonnet-4-6")
                text = await chat.send_message(UserMessage(text=f"Subject: {batch[0]['subject']} / {batch[0]['chapter']}\n\n{listing}"))
                k = text.find("[")
                rows = json.JSONDecoder().raw_decode(text[k:])[0] if k >= 0 else None
                if rows and len(rows) == len(batch):
                    return rows
            except Exception as e:  # noqa: BLE001
                print("ERR", str(e)[:100], flush=True)
                await asyncio.sleep(4)
    return None


async def run_file(sem, path, stats):
    cards = json.loads(path.read_text())
    seen, uniq = set(), []
    for c in cards:  # drop duplicate prompts
        k = re.sub(r"\W+", "", c["prompt"].lower())
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    stats["dup"] += len(cards) - len(uniq)
    cards = uniq
    todo = [c for c in cards if not c.get("verified")]
    drop = set()
    for s in range(0, len(todo), BATCH):
        batch = todo[s:s + BATCH]
        rows = await check(sem, batch)
        if not rows:
            continue
        for c, r in zip(batch, rows):
            v = r.get("v")
            if v == "drop":
                drop.add(c["id"]); stats["drop"] += 1
                continue
            if v == "fix":
                opts = r.get("options")
                if isinstance(opts, list) and len(opts) == 4 and all(isinstance(o, str) and 0 < len(o) <= 60 for o in opts) and len({o.lower() for o in opts}) == 4:
                    c["options"] = [o.strip() for o in opts]
                if r.get("answer") in (0, 1, 2, 3):
                    stats["fix"] += c["answer"] != r["answer"]
                    c["answer"] = r["answer"]
            if any(REF.search(o) for o in c["options"]):
                drop.add(c["id"]); stats["drop"] += 1
                continue
            c["verified"] = 1
        out = [c for c in cards if c["id"] not in drop]
        path.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    if not todo:
        path.write_text(json.dumps(cards, ensure_ascii=False, indent=1))
    print(f"DONE {path.name} {stats}", flush=True)


async def main():
    sem = asyncio.Semaphore(10)
    stats = {"dup": 0, "fix": 0, "drop": 0}
    import sys
    prefixes = tuple(a.lower() for a in sys.argv[1:])
    await asyncio.gather(*[run_file(sem, p, stats) for p in sorted(CARDS.glob("*.json")) if not prefixes or p.name.startswith(prefixes)])
    print("TOTAL", stats, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
