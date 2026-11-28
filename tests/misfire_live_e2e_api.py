"""Misfire Mock on LIVE jeelive.ai through the app's own server (/api/jl proxy, /api/choice), with the TEST account
only (owner, 29 Nov 2026: "Live pr hi kr lo test"). Never the owner's QA learner. Steps are chosen by argv:
  signup  — make (or sign in) the TEST account, name it "TEST Misfire QA"
  look    — door A, Misfire summary/open list, mocks list (reads only)
  seed <set_id> — start that paper on the TEST account, answer a few wrong, leave the rest, submit (fills Misfire)
State (sid, uid) is kept in /tmp/mf_live.json (0600)."""
import json, os, sys, time, uuid
import httpx

B = os.environ.get("BACKEND", "http://localhost:8001") + "/api"
PHONE, PIN, NAME = os.environ.get("MF_PHONE", "9000004281"), os.environ.get("MF_PIN", "4281"), "TEST Misfire QA"
STATE = os.environ.get("MF_STATE", "/tmp/mf_live.json")


def state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    s = {"sid": "mf-live-" + uuid.uuid4().hex}
    save(s)
    return s


def save(s):
    with open(STATE, "w") as f:
        json.dump(s, f)
    os.chmod(STATE, 0o600)


S = state()
H = {"X-JL-Sid": S["sid"], "Content-Type": "application/json"}
c = httpx.Client(timeout=40)


def jl(method, path, body=None, again=True):
    r = c.request(method, f"{B}/jl/{path.lstrip('/')}", headers=H, json=body)
    if r.status_code == 401 and again and not path.startswith("auth/"):  # the short access cookie ran out: sign in again once
        c.request("POST", f"{B}/jl/auth/phone", headers=H, json={"phone": PHONE, "pin": PIN})
        return jl(method, path, body, False)
    try:
        j = r.json()
    except ValueError:
        j = {"raw": r.text[:300]}
    return r.status_code, j


def show(tag, st, j, n=600):
    print(f"--- {tag}: {st}", json.dumps(j, ensure_ascii=False)[:n])


def signup():
    st, j = jl("POST", "auth/phone", {"phone": PHONE, "pin": PIN})
    show("sign in", st, j, 300)
    if st >= 400:
        st, j = jl("POST", "auth/phone/signup", {"phone": PHONE, "pin": PIN, "confirm_pin": PIN})
        show("sign up", st, j, 300)
    st, me = jl("GET", "auth/me")
    show("me", st, me, 400)
    uid = (me.get("data") or {}).get("id")
    if uid:
        S["uid"] = uid
        save(S)
    if (me.get("data") or {}).get("display_name") != NAME:
        show("name", *jl("PUT", "profile/display-name", {"name": NAME}), 300)


def look():
    r = c.get(f"{B}/choice/bank", params={"exam": "jee-main"}, headers=H)
    print("--- app door A (/api/choice/bank):", r.status_code, r.text[:500])
    for p in ["my/misfire/summary", "my/misfire?status=open&page=1", "my/misfire/mocks?page=1", "my/tests?tab=completed&page=1"]:
        show(p, *jl("GET", p), 1500)


def seed(set_id):
    show("set", *jl("GET", f"my/sets/{set_id}"), 500)
    show("preflight", *jl("POST", f"sets/{set_id}/preflight", {"preview": False, "test_response": "25"}), 300)
    st, a = jl("POST", f"sets/{set_id}/start", {"start_key": str(uuid.uuid4()), "device_checked": True, "preview": False, "get_ready": True})
    show("start", st, a, 300)
    aid = (a.get("data") or {}).get("id")
    if not aid:
        return
    S.setdefault("seeded", []).append({"set": set_id, "attempt": aid})
    save(S)
    show("begin", *jl("POST", f"attempts/{aid}/begin", {}), 200)
    fill(aid)


def fill(aid):
    st, d = jl("GET", f"attempts/{aid}")
    qs = (d.get("data") or {}).get("questions") or []
    print("questions", len(qs), [q.get("type") for q in qs])
    for i, q in enumerate(qs[:6]):  # six answered with a guess (some will be wrong), the rest left = Misfire items
        v = "ABCD"[i % 4] if q.get("type") != "integer" else "7"
        show(f"answer {i+1}", *jl("PUT", f"attempts/{aid}/answers/{q['id']}", {"value": v, "marked": False, "revision": 1, "request_id": str(uuid.uuid4())}), 160)
    show("submit", *jl("POST", f"attempts/{aid}/submit", {}), 300)
    time.sleep(3)
    show("result", *jl("GET", f"attempts/{aid}/results?score_version=original"), 300)


if __name__ == "__main__":
    step = sys.argv[1]
    {"signup": signup, "look": look}.get(step, lambda: None)()
    if step == "seed":
        seed(sys.argv[2])
    if step == "fill":
        fill(sys.argv[2])
    if step == "call":  # call METHOD path [json body]
        show(" ".join(sys.argv[2:4]), *jl(sys.argv[2], sys.argv[3], json.loads(sys.argv[4]) if len(sys.argv) > 4 else None), int(os.environ.get("N", "1500")))
