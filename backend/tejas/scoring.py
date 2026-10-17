"""Exact, transparent score ledger. Unknown policies fail closed."""

from fractions import Fraction
import re


def canonical(value, kind):
    s = str(value).strip().replace("\u2212", "-")
    if not s:
        return ""
    if kind == "integer":
        if not re.fullmatch(r"[+-]?[0-9]{1,20}", s):
            raise ValueError(
                "Enter an exact integer, up to 20 digits. Decimal 3.0, expressions and pasted letters are invalid; no rounding is applied."
            )
        return str(int(s))
    return s


def number(f):
    return f.numerator if f.denominator == 1 else float(f)


def fraction(f):
    return f"{f.numerator}/{f.denominator}" if f.denominator != 1 else str(f.numerator)


def score(attempt):
    rules = attempt["rules"]
    rows = []
    net = Fraction(0)
    maximum = Fraction(0)
    for q in attempt["questions"]:
        scoring = q.get('scoring') or rules
        positive = Fraction(str(scoring['correct']))
        negative = Fraction(str(scoring['wrong']))
        response = attempt.get("answers", {}).get(q["id"], {})
        raw = response.get("value", "")
        normalized = canonical(raw, q["type"])
        disposition = q.get("disposition", "standard")
        accepted = (
            q.get("accepted_answers")
            if disposition == "multiple_accepted"
            else [q["answer"]]
        )
        if not accepted:
            raise ValueError("Approved accepted-answer policy is missing its keys.")
        is_correct = bool(normalized) and normalized in [
            canonical(v, q["type"]) for v in accepted
        ]
        state = (
            "skipped" if not normalized else "correct" if is_correct else "incorrect"
        )
        reason = (
            "unanswered"
            if not normalized
            else "matched_accepted_key" if is_correct else "incorrect_response"
        )
        if disposition == "dropped":
            marks = Fraction(0)
            state = "dropped"
            reason = "dropped_excluded_from_maximum"
        elif disposition == "bonus_all":
            marks = positive
            state = "bonus"
            reason = "reviewed_bonus_to_all"
            maximum += positive
        elif disposition in ["standard", "multiple_accepted"]:
            marks = (
                Fraction(str(scoring["skipped"]))
                if not normalized
                else positive if is_correct else negative
            )
            maximum += positive
        else:
            raise ValueError(
                "Unresolved or unsupported scoring disposition cannot produce a result."
            )
        net += marks
        rows.append(
            {
                **q,
                "response": raw,
                "normalized_response": normalized,
                "accepted_answers": accepted,
                "marked": response.get("marked", False),
                "outcome": state,
                "disposition": disposition,
                "marks": number(marks),
                "marks_exact": fraction(marks),
                "reason_code": reason,
                "accepted_at": response.get("accepted_at"),
                "content_version": attempt.get("version", 1),
                "key_version": attempt.get("key_version", attempt.get("version", 1)),
                "profile_id": attempt.get("profile", {}).get("id"),
                "solution_release": "released_after_submission",
            }
        )
    # A never-entered bonus section was unreachable, not skipped by choice.
    unreachable = {r["id"] for r in rows if r.get("bonus") and rules.get("bonus_rule") and not attempt.get("bonus_unlocked_at")}
    eligible = [r for r in rows if r["outcome"] not in ["dropped", "bonus"] and r["id"] not in unreachable]
    c = sum(r["outcome"] == "correct" for r in eligible)
    w = sum(r["outcome"] == "incorrect" for r in eligible)
    tried = c + w
    summary = {
        "score": number(net),
        "score_exact": fraction(net),
        "maximum": number(maximum),
        "maximum_exact": fraction(maximum),
        "percentage": round(float(net / maximum * 100), 2) if maximum else None,
        "correct": c,
        "incorrect": w,
        "skipped": sum(r["outcome"] == "skipped" and r["id"] not in unreachable for r in rows),
        "dropped": sum(r["outcome"] == "dropped" for r in rows),
        "bonus": sum(r["outcome"] == "bonus" for r in rows),
        "attempted": tried,
        "eligible_count": len(eligible),
        "attempt_rate": round(100 * tried / len(eligible), 1) if eligible else None,
        "accuracy": round(100 * c / tried, 1) if tried else None,
        "penalties": number(
            sum(
                (-Fraction(r["marks_exact"]) for r in rows if r["marks"] < 0),
                Fraction(0),
            )
        ),
        "total_seconds": max(
            0,
            round(
                attempt.get("submitted_at", attempt["started_at"])
                - attempt["started_at"]
            ),
        ),
    }
    for category in ["subject", "topic"]:
        groups = {}
        for r in rows:
            name = r.get(category) or "Unlabelled"
            g = groups.setdefault(
                name, {"count": 0, "correct": 0, "attempted": 0, "score": Fraction(0)}
            )
            g["count"] += 1
            g["correct"] += int(r["outcome"] == "correct")
            g["attempted"] += int(r["outcome"] in ["correct", "incorrect"])
            g["score"] += Fraction(r["marks_exact"])
        for g in groups.values():
            g["score_exact"] = fraction(g["score"])
            g["score"] = number(g["score"])
        summary[category + "s"] = groups
    if any(r.get("bonus") for r in rows):
        def block(items):
            total = sum((Fraction(r["marks_exact"]) for r in items), Fraction(0))
            return {"count": len(items), "score": number(total), "score_exact": fraction(total),
                    "maximum": number(sum((Fraction(str((r.get('scoring') or rules)['correct'])) for r in items), Fraction(0))),
                    "correct": sum(r["outcome"] == "correct" for r in items),
                    "incorrect": sum(r["outcome"] == "incorrect" for r in items),
                    "skipped": sum(r["outcome"] == "skipped" for r in items)}
        main = [r for r in rows if not r.get("bonus")]
        bonus = [r for r in rows if r.get("bonus")]
        order = list(dict.fromkeys(r.get("section") or "Unlabelled" for r in main))
        summary["sections"] = [{"name": n, **block([r for r in main if (r.get("section") or "Unlabelled") == n])} for n in order]
        summary["main_block"] = block(main)
        summary["bonus_block"] = {**block(bonus), "entered": bool(attempt.get("bonus_unlocked_at"))}
    return {"summary": summary, "questions": rows}
