"""LIVE Misfire Mock: one attempt of a mock through the app's server, TEST account only (tests/misfire_live_e2e_api.py).
python3 misfire_live_attempt.py <set_id> <right> <wrong>  — starts it, answers <right> questions right (keys read from the
TEST account's own earlier results, same question ids), <wrong> wrong, leaves the rest, submits, and prints the mocks list
row, the result's `misfire`, and Misfire's counts at each step."""
import json, sys, time, uuid
import misfire_live_e2e_api as m


def body(q):
    """A question's words without its "Question N" line: the same in a chapter test and in a mock made from it."""
    return (q.get("accessible_text") or "").split("\n", 1)[-1].strip()


def keys():
    """question id (and question words) -> its right answer, from the TEST account's finished papers."""
    out = {}
    for s in m.S.get("seeded", []) + m.S.get("mock_attempts", []):
        st, j = m.jl("GET", f"attempts/{s['attempt']}/results?score_version=original")
        for q in ((j.get("data") or {}).get("questions") or []):
            if q.get("answer") not in (None, ""):
                out[q["id"]] = str(q["answer"])
                if body(q):
                    out[body(q)] = str(q["answer"])
    return out


def row(set_id):
    st, j = m.jl("GET", "my/misfire/mocks?page=1")
    for it in (j.get("data") or {}).get("items") or []:
        if it.get("set_id") == set_id:
            return it
    return None


def counts():
    st, j = m.jl("GET", "my/misfire/summary")
    d = j.get("data") or {}
    return {"open": d.get("open"), "fixed": d.get("fixed")}


def wrong_of(q, right):
    if q.get("type") == "integer":
        return str(int(right) + 1) if right.lstrip("-").isdigit() else "0"
    return next(k for k in "ABCD" if k != right)


def run(set_id, n_right, n_wrong, start_path=None):
    K = keys()
    print("keys known:", len(K), "| misfire before:", counts())
    if start_path:
        st, a = m.jl("POST", start_path, {"start_key": str(uuid.uuid4()), "score_version": "original"})
    else:
        st, a = m.jl("POST", f"sets/{set_id}/start", {"start_key": str(uuid.uuid4()), "device_checked": True, "preview": False, "get_ready": True})
    print("start", st, json.dumps(a, ensure_ascii=False)[:200])
    aid = (a.get("data") or {}).get("id")
    if not aid:
        return
    print("row after start:", json.dumps(row(set_id), ensure_ascii=False)[:500])
    m.jl("POST", f"attempts/{aid}/begin", {})
    st, d = m.jl("GET", f"attempts/{aid}")
    qs = (d.get("data") or {}).get("questions") or []
    print("questions", len(qs), "known keys for", sum((q["id"] in K or body(q) in K) for q in qs))
    plan = []
    for i, q in enumerate(qs):
        right = K.get(q["id"]) or K.get(body(q))
        if right is None:
            continue
        if len([p for p in plan if p[1] == "right"]) < n_right:
            plan.append((q, "right", right))
        elif len([p for p in plan if p[1] == "wrong"]) < n_wrong:
            plan.append((q, "wrong", wrong_of(q, right)))
    for q, kind, v in plan:
        st, r = m.jl("PUT", f"attempts/{aid}/answers/{q['id']}", {"value": v, "marked": False, "revision": 1, "request_id": str(uuid.uuid4())})
        print(f"  {kind} q{q.get('number')} {q.get('subject')} = {v}: {st}")
    st, s = m.jl("POST", f"attempts/{aid}/submit", {})
    print("submit", st, json.dumps(s, ensure_ascii=False)[:200])
    for t in range(12):
        st, r = m.jl("GET", f"attempts/{aid}/results?score_version=original")
        d = r.get("data") or {}
        print(f"  result try {t}: {st} status={d.get('status')} test_kind={d.get('test_kind')} misfire={d.get('misfire')} summary={(d.get('summary') or {}).get('correct')}")
        if st == 200 and d.get("summary"):
            break
        time.sleep(3)
    print("row after submit:", json.dumps(row(set_id), ensure_ascii=False)[:600])
    print("misfire after:", counts())
    m.S.setdefault("mock_attempts", []).append({"set": set_id, "attempt": aid, "right": [q["id"] for q, k, _ in plan if k == "right"], "wrong": [q["id"] for q, k, _ in plan if k == "wrong"]})
    m.save(m.S)
    return aid


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else None)
