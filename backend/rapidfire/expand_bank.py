"""Rapid Fire bank expansion (rules: /app/memory/RAPID_FIRE_RULES.md).

Stages (each resumable, state in rapidfire/expansion/):
  syllabus  official subtopics per chapter (NTA JEE Main 2026 / BITSAT 2026)
  map       every existing card tagged to one subtopic
  report    coverage per subtopic -> targets (2x, up to 3x where thin) + /app/memory/RAPID_FIRE_COVERAGE.md
  author    new candidate cards, missing/thin subtopics first (Claude Sonnet 5.5)
  gate      blind second solve + 20-second gate G1-G7 (GPT-5.6 Terra, a different AI family)
  merge     accepted cards appended to rapidfire/cards/*.json (the live sync picks them up)
Run: python rapidfire/expand_bank.py <stage> [file-prefix ...]
"""
import asyncio, json, math, os, random, re, sys, uuid
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT.parent / ".env")
except Exception:  # noqa: BLE001
    pass
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

CARDS, WORK = ROOT / "cards", ROOT / "expansion"
CAND, GATED = WORK / "candidates", WORK / "gated"
for d in (WORK, CAND, GATED):
    d.mkdir(exist_ok=True)
SYL, TAGS, COVER = WORK / "syllabus.json", WORK / "tags.json", WORK / "coverage.json"
REPORT = Path("/app/memory/RAPID_FIRE_COVERAGE.md")
AUTHOR = ("anthropic", "claude-sonnet-5-5")
JUDGE = ("openai", "gpt-5.6-terra")
PLANNER = ("anthropic", "claude-opus-5-5")
BITSAT = {"English", "Logical Reasoning"}
NEW_CHAPTER = {"English": 70, "Logical Reasoning": 80, "Physics": 80, "Chemistry": 80, "Mathematics": 80}
REF = re.compile(r"\b(both|all of (these|the above)|none of (these|the above)|[abcd] and [abcd]|neither)\b", re.I)
BANNED = re.compile(r"\b(calculate|compute|find the value|evaluate numerically|how many joules)\b", re.I)
MARKDOWN = re.compile(r"\*[A-Za-z][^*]*\*|(?<![_\w])_[A-Za-z][\w']*_(?![_\w])")  # *word* / _word_ shows as raw stars on the card
STOP = set("the a an of in on to is are for and or with by at as be its it this that which what from".split())


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def fkey(subject, chapter):
    return f"{slug(subject)}__{slug(chapter)}.json"


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def save(p, v):
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(v, ensure_ascii=False, indent=1))
    tmp.replace(p)


def exam_of(subject):
    return "BITSAT 2026" if subject in BITSAT else "NTA JEE Main 2026"


def chapters():
    plan = json.loads((ROOT / "chapters.json").read_text())
    return [(s, c) for s, chs in plan.items() for c in chs]


def selected(prefixes):
    return [(s, c) for s, c in chapters() if not prefixes or fkey(s, c).startswith(prefixes)]


def words(t):
    return {w for w in re.findall(r"[a-z0-9α-ω]+", t.lower()) if w not in STOP}


def fp(t):
    return re.sub(r"\W+", "", t.lower())


def near_dup(card, others):
    """Same right answer and >= 70 % of the same words in the question = the same card asked again."""
    a, ans = words(card["prompt"]), fp(card["options"][card["answer"]])
    for o in others:
        b = words(o["prompt"])
        if fp(o["prompt"]) == fp(card["prompt"]):
            return True
        if a and b and len(a & b) / len(a | b) >= 0.7 and fp(o["options"][o["answer"]]) == ans:
            return True
    return False


async def ask(sem, model, system, text, want="[", tries=3, timeout=300):
    for k in range(tries):
        async with sem:
            try:
                chat = LlmChat(api_key=os.environ["EMERGENT_LLM_KEY"], session_id=str(uuid.uuid4()), system_message=system).with_model(*model)
                out = await asyncio.wait_for(chat.send_message(UserMessage(text=text)), timeout)
                i = out.find(want)
                if i >= 0:
                    return json.JSONDecoder().raw_decode(out[i:])[0]
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                print("ERR", model[1], msg[:160], flush=True)
                if "budget" in msg.lower() or "insufficient" in msg.lower():
                    raise SystemExit("LLM key budget exhausted")
                await asyncio.sleep(5 * (k + 1))
    return None


# ---------------- syllabus ----------------
SYL_SYSTEM = """You are the head of a top coaching institute's {exam} faculty. List the official syllabus subtopics of ONE chapter.
Return ONLY a JSON array of 8-16 objects: {{"name": "<short subtopic name, max 48 chars>", "weight": 1|2|3, "rf": 0|1}}
- Cover the WHOLE official {exam} syllabus of this chapter, nothing beyond it (respect the latest syllabus cuts).
- weight 3 = asked almost every year, 2 = often, 1 = occasionally.
- rf = 1 if the subtopic can be tested by 20-second, no-pen recall cards (formula, law, definition, fact, trend,
  exception, unit, graph shape, standard result, grammar rule, word meaning, one-rule pattern); rf = 0 if it only
  makes sense as long calculation, a long passage, or needs a figure."""


async def stage_syllabus(prefixes):
    syl, sem = load(SYL, {}), asyncio.Semaphore(8)

    async def one(s, c):
        key = fkey(s, c)
        if key in syl:
            return
        rows = await ask(sem, PLANNER, SYL_SYSTEM.format(exam=exam_of(s)), f"Subject: {s}\nChapter: {c}")
        rows = [r for r in rows or [] if isinstance(r, dict) and r.get("name")]
        if 6 <= len(rows) <= 20:
            syl[key] = {"subject": s, "chapter": c, "exam": exam_of(s),
                        "subtopics": [{"name": str(r["name"])[:60], "weight": int(r.get("weight") or 2), "rf": int(r.get("rf", 1))} for r in rows]}
            save(SYL, syl)
            print("SYL", key, len(rows), flush=True)
        else:
            print("SYL-FAIL", key, flush=True)
    await asyncio.gather(*[one(s, c) for s, c in selected(prefixes)])


# ---------------- map ----------------
MAP_SYSTEM = """You tag quiz cards with the syllabus subtopic they test. For EACH card return its subtopic index (or -1 if none fits).
Return ONLY a JSON array of integers, one per card, in order."""


async def stage_map(prefixes):
    syl, tags, sem = load(SYL, {}), load(TAGS, {}), asyncio.Semaphore(12)

    async def one(s, c):
        key = fkey(s, c)
        path = CARDS / key
        if key not in syl or not path.exists():
            return
        subs = syl[key]["subtopics"]
        todo = [x for x in json.loads(path.read_text()) if x["id"] not in tags]
        for k in range(0, len(todo), 25):
            batch = todo[k:k + 25]
            listing = "\n".join(f"{i}. {x['prompt']} -> {x['options'][x['answer']]}" for i, x in enumerate(batch))
            menu = "\n".join(f"{i}: {t['name']}" for i, t in enumerate(subs))
            for model in (JUDGE, JUDGE, AUTHOR):  # a short or broken list is asked again, last time by the other family
                rows = await ask(sem, model, MAP_SYSTEM, f"{s} / {c}\nSubtopics:\n{menu}\n\nCards ({len(batch)}):\n{listing}\n\nReturn exactly {len(batch)} integers.")
                if rows and len(rows) == len(batch):
                    break
            if rows and len(rows) == len(batch):
                for x, r in zip(batch, rows):
                    tags[x["id"]] = int(r) if isinstance(r, int) and -1 <= r < len(subs) else -1
                save(TAGS, tags)
        print("MAP", key, flush=True)
    await asyncio.gather(*[one(s, c) for s, c in selected(prefixes)])


# ---------------- report ----------------
def stage_report(_prefixes):
    syl, tags = load(SYL, {}), load(TAGS, {})
    cover, lines = {}, []
    for s, c in chapters():
        key = fkey(s, c)
        if key not in syl:
            continue
        subs = syl[key]["subtopics"]
        cards = json.loads((CARDS / key).read_text()) if (CARDS / key).exists() else []
        have = Counter(tags.get(x["id"], -1) for x in cards)
        n = len(cards)
        rows = [{"name": t["name"], "weight": t["weight"], "rf": t["rf"], "have": have.get(i, 0)} for i, t in enumerate(subs)]
        live = [r for r in rows if r["rf"]]
        missing = [r for r in live if r["have"] == 0]
        thin = [r for r in live if 0 < r["have"] < (4 if r["weight"] >= 2 else 2)]
        new = (n + min(n, 8 * len(missing) + 4 * len(thin))) if n else NEW_CHAPTER[s]
        final = n + new
        wsum = sum(r["weight"] for r in live) or 1
        need = [max(0.0, final * r["weight"] / wsum - r["have"]) for r in live]
        scale = new / (sum(need) or 1)
        quota = [round(x * scale) for x in need]
        drift = new - sum(quota)
        order = sorted(range(len(live)), key=lambda i: -need[i])
        for j in range(abs(drift)):
            quota[order[j % len(order)]] += 1 if drift > 0 else (-1 if quota[order[j % len(order)]] > 0 else 0)
        for r, q in zip(live, quota):
            r["quota"] = q
        cover[key] = {"subject": s, "chapter": c, "exam": syl[key]["exam"], "existing": n, "new": new, "final": final,
                      "missing": [r["name"] for r in missing], "thin": [r["name"] for r in thin],
                      "untagged": have.get(-1, 0), "subtopics": rows}
    save(COVER, cover)
    # Markdown overview for the owner.
    tot = Counter()
    for v in cover.values():
        tot[v["subject"] + ":existing"] += v["existing"]
        tot[v["subject"] + ":new"] += v["new"]
    lines.append("# Rapid Fire coverage map (before expansion)\n")
    lines.append("Measured against the official NTA JEE Main 2026 / BITSAT 2026 syllabus, split into subtopics. "
                 "`have` = live cards on that subtopic before this expansion; `+new` = cards to write (2x, up to 3x where thin).\n")
    lines.append("| Subject | Cards before | New target | After |\n|---|---|---|---|")
    for s in dict.fromkeys(v["subject"] for v in cover.values()):
        e, w = tot[s + ":existing"], tot[s + ":new"]
        lines.append(f"| {s} | {e} | +{w} | {e + w} |")
    lines.append("")
    for key, v in cover.items():
        lines.append(f"## {v['subject']} — {v['chapter']}  ({v['existing']} → {v['final']})")
        if v["missing"]:
            lines.append("- **Not covered before:** " + "; ".join(v["missing"]))
        if v["thin"]:
            lines.append("- **Thin:** " + "; ".join(v["thin"]))
        off = [r["name"] for r in v["subtopics"] if not r["rf"]]
        if off:
            lines.append("- **Outside 20-second format (calculation/figure/passage only):** " + "; ".join(off))
        lines.append("- Subtopics: " + "; ".join(f"{r['name']} {r['have']}" + (f" +{r.get('quota', 0)}" if r["rf"] else "") for r in v["subtopics"]))
        lines.append("")
    REPORT.write_text("\n".join(lines))
    print("REPORT", len(cover), "chapters", dict(tot), flush=True)


# ---------------- author ----------------
AUTHOR_SYSTEM = """You are a senior {exam} faculty member writing 20-second Rapid Fire recall cards.
STRICT RULES (a strict independent gate rejects any card that breaks one):
- ONLY the official {exam} syllabus of the named chapter and subtopic. Nothing beyond it.
- Each card tests ONE idea from short notes: a formula, law, definition, fact, concept statement, trend, exception,
  unit/dimension, graph shape or standard result{extra}.
- NO pen: answerable in the head within 15 seconds (reading included). At most one trivial mental step. No numerical
  substitution, no multi-step algebra/calculus, no solving equations, no long case work, no long passages.
- prompt: one short line, max {plen} characters. formula: optional short symbolic line or short note shown after the
  answer (plain Unicode like "E = hν", "Kₐ·K_b = K_w"), else "".
- 4 options, each max 40 characters, mutually exclusive, exactly ONE correct, plausible distractors from common mistakes.
  Never "all of these", "none of these", "both A and B", "neither".
- explain: one line, max 120 characters, the reason / the short note.
- Do NOT repeat any idea in the "already in the bank" list, not even with different wording or a swapped question.
- Exam level: the way the real {exam} asks it. Never trivial or obvious to everyone (no plain "+4" sequences, no
  "which is increasing"); a prepared student needs a moment of recall or one insight, yet finishes within 15 seconds.
- Stay inside THIS chapter of THIS subject (e.g. a Logical Reasoning series is a pattern, not an AP formula from Maths).
- Only facts you are sure of. If unsure, write a different card.
Return ONLY a JSON array: [{{"prompt":"..","formula":"","options":["..","..","..",".."],"answer":0,"explain":"..","kind":"formula|concept|fact|trend|exception|unit|graph|result|grammar|vocab|pattern"}}]"""
EXTRA = {"English": "; for English: a grammar rule in a short sentence, correct usage, error spotting in a short sentence, word meaning, "
                    "synonym/antonym, idiom, phrasal verb, one-word substitution, spelling, linker",
         "Logical Reasoning": "; for Logical Reasoning: one short pattern solvable in the head - analogy, odd one out, a short series, "
                              "a short code, a 1-2 step relation or direction, a 2-statement syllogism"}


def bank_ideas(key, subtopic_idx, cover, tags):
    cards = json.loads((CARDS / key).read_text()) if (CARDS / key).exists() else []
    mine = [x for x in cards if tags.get(x["id"], -1) == subtopic_idx]
    return mine


async def stage_author(prefixes):
    """Writes until every subtopic has enough cards: accepted by the gate + still waiting for it (counted at 75 %) >= quota.
    Run author -> gate -> author -> gate: each round only tops up what the gate threw out."""
    cover, tags, sem = load(COVER, {}), load(TAGS, {}), asyncio.Semaphore(int(os.environ.get("RF_AUTHOR_PAR", "28")))

    async def one(key):
        v = cover[key]
        s, c = v["subject"], v["chapter"]
        path = CAND / key
        cands = load(path, [])
        verdict = load(GATED / key, {"verdict": {}})["verdict"]
        live = [r for r in v["subtopics"] if r["rf"]]
        idx = {r["name"]: i for i, r in enumerate(v["subtopics"])}
        bank_all = json.loads((CARDS / key).read_text()) if (CARDS / key).exists() else []
        for r in live:
            quota = r.get("quota", 0)
            tries = 0
            while tries < 6 and quota:
                got = [x for x in cands if x["topic"] == r["name"]]
                ok = sum(1 for x in got if verdict.get(x["id"]) == [])
                waiting = sum(1 for x in got if x["id"] not in verdict)
                short = quota - ok - 0.75 * waiting
                if short <= 0:
                    break
                tries += 1
                need = min(20, math.ceil(short * (1.4 if not verdict else 1.6)))
                seen = bank_ideas(key, idx[r["name"]], cover, tags) + got
                listing = "\n".join(f"- {x['prompt']} -> {x['options'][x['answer']]}" for x in seen[-160:]) or "- none"
                # The whole chapter too: the dedupe stage drops a card that repeats another subtopic's card.
                rest = [x for x in bank_all if tags.get(x["id"], -1) != idx[r["name"]]] + \
                       [x for x in cands if x["topic"] != r["name"] and verdict.get(x["id"]) == []]
                around = "\n".join(f"- {x['prompt'][:100]}" for x in rest[-250:]) or "- none"
                system = AUTHOR_SYSTEM.format(exam=v["exam"], extra=EXTRA.get(s, ""), plen=150 if s in BITSAT else 120)
                msg = (f"Subject: {s}\nChapter: {c}\nSubtopic: {r['name']}\nWrite {need} NEW cards on this subtopic only, the most "
                       f"exam-important ideas first.\nAlready in the bank on this subtopic (do not repeat these ideas):\n{listing}\n\n"
                       f"Also already in this chapter (other subtopics; do not ask these facts again either):\n{around}")
                batch = await ask(sem, AUTHOR, system, msg)
                if not batch:
                    continue
                pool = seen[:]
                for x in batch:
                    try:
                        opts = [str(o).strip() for o in x["options"]]
                        card = {"prompt": str(x["prompt"]).strip(), "formula": str(x.get("formula") or "").strip()[:90], "options": opts,
                                "answer": int(x["answer"]), "explain": str(x.get("explain") or "").strip()[:180], "kind": str(x.get("kind") or "")[:12]}
                    except Exception:  # noqa: BLE001
                        continue
                    if not shape_ok(card, s) or near_dup(card, pool):
                        continue
                    card.update({"id": str(uuid.uuid4()), "subject": s, "chapter": c, "topic": r["name"]})
                    pool.append(card)
                    cands.append(card)
                save(path, cands)
        print("AUTHOR", key, len(cands), flush=True)
    keys = [k for k in cover if not prefixes or k.startswith(prefixes)]
    await asyncio.gather(*[one(k) for k in keys])


def shape_ok(c, subject):
    plen = 150 if subject in BITSAT else 120
    o = c["options"]
    return (5 < len(c["prompt"]) <= plen + 10 and len(o) == 4 and len({fp(x) for x in o}) == 4 and all(0 < len(x) <= 48 for x in o)
            and c["answer"] in (0, 1, 2, 3) and not any(REF.search(x) for x in o) and not BANNED.search(c["prompt"])
            and not MARKDOWN.search(c["prompt"]))


# ---------------- gate ----------------
GATE_SYSTEM = """You are the strict, independent examiner for {exam} 20-second Rapid Fire cards. You never see the author's key.
For EACH card: solve it yourself first, then judge. Return ONLY a JSON array, one object per card, in order:
{{"i": <index>, "solve": <the ONE correct option index 0-3, or -1 if none or more than one option is correct>,
  "pen": 0|1, "secs": <seconds a well-prepared student needs to read AND answer>, "syllabus": 0|1, "clear": 0|1, "dup": 0|1, "imp": 1-5}}
- pen = 1 if it needs written work (numerical substitution with non-trivial numbers, multi-step algebra/calculus,
  solving equations, long case analysis, long reading). One trivial mental step is fine (pen = 0).
- syllabus = 1 only if it is inside the official {exam} syllabus and belongs to this subject and chapter (the subtopic
  label may be loose; a card that really belongs to another subject, e.g. a Maths formula in Logical Reasoning, is 0).
- clear = 1 only if the wording is unambiguous, the fact is standard and undisputed, and the distractors are clearly wrong.
- dup = 1 if it asks the same fact as a card in the "already in the bank" list (even with different wording).
- imp = how valuable this card is for {exam} revision: 5 = must-know, asked often; 3 = useful; 1 = trivial or obvious
  to everyone (no learning value)."""


async def stage_gate(prefixes):
    cover, tags, sem = load(COVER, {}), load(TAGS, {}), asyncio.Semaphore(20)

    async def one(key):
        v = cover[key]
        cands = load(CAND / key, [])
        state = load(GATED / key, {"verdict": {}})
        verdict = state["verdict"]
        idx = {r["name"]: i for i, r in enumerate(v["subtopics"])}
        by_topic = {}
        for x in cands:
            if x["id"] not in verdict:
                by_topic.setdefault(x["topic"], []).append(x)
        for topic, todo in by_topic.items():
            bank = bank_ideas(key, idx.get(topic, -2), cover, tags)
            listing = "\n".join(f"- {x['prompt']} -> {x['options'][x['answer']]}" for x in bank[-120:]) or "- none"
            for k in range(0, len(todo), 15):
                batch = todo[k:k + 15]
                cards = "\n".join(f"{i}. {x['prompt']}\n   options: {json.dumps(x['options'], ensure_ascii=False)}" for i, x in enumerate(batch))
                rows = await ask(sem, JUDGE, GATE_SYSTEM.format(exam=v["exam"]),
                                 f"{v['subject']} / {v['chapter']} / {topic}\nAlready in the bank:\n{listing}\n\nCards to judge:\n{cards}")
                if not rows or len(rows) != len(batch):
                    continue
                for x, r in zip(batch, rows):
                    try:
                        reasons = []
                        if int(r.get("solve", -1)) != x["answer"]:
                            reasons.append("key")
                        if int(r.get("pen", 1)):
                            reasons.append("pen")
                        if float(r.get("secs", 99)) > 15:
                            reasons.append("slow")
                        if not int(r.get("syllabus", 0)):
                            reasons.append("syllabus")
                        if not int(r.get("clear", 0)):
                            reasons.append("unclear")
                        if int(r.get("dup", 0)):
                            reasons.append("dup")
                        if int(r.get("imp", 0)) <= 2:
                            reasons.append("low-value")
                    except Exception:  # noqa: BLE001
                        reasons = ["bad-verdict"]
                    verdict[x["id"]] = reasons
                save(GATED / key, state)
        ok = sum(1 for x in cands if verdict.get(x["id"]) == [])
        print("GATE", key, f"{ok}/{len(cands)}", flush=True)
    keys = [k for k in cover if (not prefixes or k.startswith(prefixes)) and (CAND / k).exists()]
    await asyncio.gather(*[one(k) for k in keys])


# ---------------- dedupe ----------------
DEDUPE_SYSTEM = """You check a {exam} Rapid Fire quiz bank for repeated questions. Cards marked R are already in the bank; cards
marked N are new. For EACH N card decide whether it repeats an R card or an EARLIER N card (smaller number).
Repeat = a student who knows the answer of one automatically knows the other: the same law, formula, definition, fact,
word meaning or rule asked again - reworded, reversed (name -> formula vs formula -> name) or with a trivially swapped frame.
NOT a repeat: a different property, case, exception, trend or consequence of the same topic; a pattern card with different
numbers/letters and a different answer.
Return ONLY a JSON array for the repeated N cards: [{{"n": <N number>, "same_as": "R12" or "N3"}}]. Return [] if none."""


def accepted(key):
    cands, verdict = load(CAND / key, []), load(GATED / key, {"verdict": {}})["verdict"]
    return [x for x in cands if verdict.get(x["id"]) == []]


async def stage_dedupe(prefixes):
    """G7 across the whole chapter (the gate only compared inside one subtopic) and, by same answer, across the subject's
    other chapters (e.g. banked road in Laws of Motion and in Circular Motion). Flagged cards get the verdict ["dup2"]."""
    cover, sem = load(COVER, {}), asyncio.Semaphore(16)
    keys = sorted(cover)
    banks = {k: (json.loads((CARDS / k).read_text()) if (CARDS / k).exists() else []) for k in keys}
    news = {k: accepted(k) for k in keys}

    async def one(key):
        v = cover[key]
        state = load(GATED / key, {"verdict": {}})
        done = set(state.get("dedupe", []))
        bank_ids = {x["id"] for x in banks[key]}
        todo = [x for x in news[key] if x["id"] not in done and x["id"] not in bank_ids]
        if not todo:
            return
        answers = {fp(x["options"][x["answer"]]) for x in todo}
        cross = [x for k in keys if k != key and cover[k]["subject"] == v["subject"]
                 for x in banks[k] + (news[k] if k < key else []) if fp(x["options"][x["answer"]]) in answers]
        ref = banks[key] + [x for x in news[key] if x["id"] in done and state["verdict"].get(x["id"]) == []] + cross
        flagged = 0
        for k in range(0, len(todo), 60):
            batch = todo[k:k + 60]
            listing = "\n".join(f"R{i}. {x['prompt']} -> {x['options'][x['answer']]}" for i, x in enumerate(ref))
            cards = "\n".join(f"N{i}. {x['prompt']} -> {x['options'][x['answer']]}" for i, x in enumerate(batch))
            rows = await ask(sem, JUDGE, DEDUPE_SYSTEM.format(exam=v["exam"]),
                             f"{v['subject']} / {v['chapter']}\nAlready in the bank:\n{listing or '- none'}\n\nNew cards:\n{cards}")
            if rows is None:
                continue
            dup = {int(str(r["n"]).lstrip("N")) for r in rows if isinstance(r, dict) and str(r.get("n", "")).lstrip("N").isdigit()}
            for i, x in enumerate(batch):
                if i in dup:
                    state["verdict"][x["id"]] = ["dup2"]
                    flagged += 1
                else:
                    ref.append(x)
                done.add(x["id"])
            state["dedupe"] = sorted(done)
            save(GATED / key, state)
        print("DEDUPE", key, f"{flagged}/{len(todo)}", flush=True)
    await asyncio.gather(*[one(k) for k in keys if not prefixes or k.startswith(prefixes)])


# ---------------- merge ----------------
class SubjectIndex:
    """Exact prompt or same answer + >= 70 % same words, checked against every chapter of the subject (fast by answer)."""

    def __init__(self):
        self.prompts, self.by_answer = set(), {}

    def add(self, x):
        self.prompts.add(fp(x["prompt"]))
        self.by_answer.setdefault(fp(x["options"][x["answer"]]), []).append(words(x["prompt"]))

    def has(self, x):
        if fp(x["prompt"]) in self.prompts:
            return True
        a = words(x["prompt"])
        return any(a and b and len(a & b) / len(a | b) >= 0.7 for b in self.by_answer.get(fp(x["options"][x["answer"]]), []))


def stage_merge(prefixes):
    cover, tags = load(COVER, {}), load(TAGS, {})
    totals = Counter()
    index = {}
    for key, v in cover.items():
        for x in (json.loads((CARDS / key).read_text()) if (CARDS / key).exists() else []):
            index.setdefault(v["subject"], SubjectIndex()).add(x)
    for key, v in cover.items():
        if prefixes and not key.startswith(prefixes):
            continue
        cands, state = load(CAND / key, []), load(GATED / key, {"verdict": {}})
        path = CARDS / key
        bank = json.loads(path.read_text()) if path.exists() else []
        names = [r["name"] for r in v["subtopics"]]
        changed = False
        for x in bank:  # existing cards get their syllabus subtopic as topic (better "worth revising" lines)
            t = tags.get(x["id"], -1)
            if 0 <= t < len(names) and x.get("topic") in (None, "", x["chapter"]):
                x["topic"] = names[t]
                changed = True
        have = {x["id"] for x in bank}
        quota = {r["name"]: r.get("quota", 0) for r in v["subtopics"] if r["rf"]}
        added = Counter()
        for x in cands:
            if x["id"] in have or state["verdict"].get(x["id"]) != [] or added[x["topic"]] >= quota.get(x["topic"], 0) + 2:
                continue
            if any(ch in t for t in [x["prompt"], x["formula"], x["explain"], *x["options"]] for ch in ("\\", "$")):
                continue  # raw TeX would show as code on the card
            sub = index.setdefault(v["subject"], SubjectIndex())
            if sub.has(x):
                continue
            sub.add(x)
            correct = x["options"][x["answer"]]
            opts = x["options"][:]
            random.Random(x["id"]).shuffle(opts)  # the key position carries no pattern
            bank.append({"id": x["id"], "subject": x["subject"], "chapter": x["chapter"], "topic": x["topic"], "prompt": x["prompt"],
                         "formula": x["formula"], "options": opts, "answer": opts.index(correct), "explain": x["explain"],
                         "review_status": "quick_recall_reviewed_v2", "syllabus": "BITSAT" if x["subject"] in BITSAT else "JEE Main",
                         "verified": 1, "gate": "rf-gate-v2"})
            added[x["topic"]] += 1
            changed = True
        if changed:
            save(path, bank)
        totals[v["subject"]] += len(bank)
        print("MERGE", key, v["existing"], "->", len(bank), flush=True)
    print("TOTAL", dict(totals), flush=True)


def stage_final(_prefixes):
    """Adds the 'after' numbers (live bank after the gate + merge) to the coverage report."""
    cover = load(COVER, {})
    lines, tot = ["", "# After expansion (gated cards now live)", "", "| Subject | Before | After | Growth |", "|---|---|---|---|"], Counter()
    rows = []
    for key, v in cover.items():
        bank = json.loads((CARDS / key).read_text()) if (CARDS / key).exists() else []
        gated = sum(1 for x in bank if x.get("gate") == "rf-gate-v2")
        tot[v["subject"] + ":b"] += v["existing"]
        tot[v["subject"] + ":a"] += len(bank)
        rows.append(f"| {v['subject']} | {v['chapter']} | {v['existing']} | {len(bank)} | +{gated} |")
    for s in dict.fromkeys(v["subject"] for v in cover.values()):
        b, a = tot[s + ":b"], tot[s + ":a"]
        lines.append(f"| {s} | {b} | {a} | {('%.1fx' % (a / b)) if b else 'new'} |")
    lines += ["", "| Subject | Chapter | Before | After | New (gated) |", "|---|---|---|---|---|", *rows]
    text = REPORT.read_text().split("\n# After expansion")[0]
    REPORT.write_text(text.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("FINAL", {k: v for k, v in tot.items()}, flush=True)


STAGES = {"syllabus": stage_syllabus, "map": stage_map, "report": stage_report, "author": stage_author, "gate": stage_gate,
          "dedupe": stage_dedupe, "merge": stage_merge, "final": stage_final}

if __name__ == "__main__":
    stage, prefixes = sys.argv[1], tuple(a.lower() for a in sys.argv[2:])
    run = STAGES[stage](prefixes)
    if asyncio.iscoroutine(run):
        asyncio.run(run)
