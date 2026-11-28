"""T1 (iteration 165): LIVE Misfire Mock door C error sentences on TEST account B only (no paper is made by the 422s).
MF_PHONE=9000004282 MF_PIN=4282 MF_STATE=/tmp/mf_live_b.json python3 t1_misfire_live_b_api.py 422
`dup <set_key> <counts json>` re-asks with an old request_key (idempotency / 409 check)."""
import json, sys, uuid
import misfire_live_e2e_api as m

assert m.PHONE == "9000004282", "account B only"


def ask(counts, chapters=None, key=None):
    body = {"exam": "jee-main", "request_key": key or str(uuid.uuid4()), "mode": "misfire", "counts": counts}
    if chapters is not None:
        body["chapters"] = chapters
    st, j = m.jl("POST", "choice/papers", body)
    return st, j


def errors():
    cases = [
        ("all zero", {"Physics": 0, "Chemistry": 0, "Mathematics": 0}, None, 422, "Har subject mein 25 tak sawaal chuno, kul kam se kam 1."),
        ("26 physics", {"Physics": 26, "Chemistry": 0, "Mathematics": 0}, None, 422, "Har subject mein 25 tak sawaal chuno, kul kam se kam 1."),
        ("negative", {"Physics": -1, "Chemistry": 2, "Mathematics": 0}, None, 422, "Har subject mein 25 tak sawaal chuno, kul kam se kam 1."),
        ("unknown chapter", {"Physics": 3, "Chemistry": 0, "Mathematics": 0}, {"Physics": ["99 No Such Chapter"]}, 422, "Chune hue chapters mein abhi koi khula sawaal nahi hai. Doosre chapter chuno."),
    ]
    ok = 0
    for name, counts, ch, want_st, want in cases:
        st, j = ask(counts, ch)
        msg = ((j.get("error") or {}).get("message")) if isinstance(j, dict) else None
        good = st == want_st and msg == want
        ok += good
        print(("PASS " if good else "FAIL ") + f"{name}: {st} {json.dumps(j, ensure_ascii=False)[:300]}")
    print(f"{ok}/{len(cases)}")
    print("mocks after (must be unchanged):", json.dumps(m.jl("GET", "my/misfire/mocks?page=1")[1].get("data", {}).get("total")))


if __name__ == "__main__":
    if sys.argv[1] == "422":
        errors()
    elif sys.argv[1] == "make":  # make <counts json> [key]
        st, j = ask(json.loads(sys.argv[2]), None, sys.argv[3] if len(sys.argv) > 3 else None)
        print(st, json.dumps(j, ensure_ascii=False)[:600])
