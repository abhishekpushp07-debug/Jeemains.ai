# Iteration101 helper: read/write the QA account's dream list through the RF bearer (session from /tmp/iter101_sess.json, 0600).
import json, os, sys, time
import requests

BASE = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
SESS = "/tmp/iter101_sess.json"
TOK = "/tmp/iter101_tok.json"


def _sid():
    v = json.load(open(SESS))["sid"]
    for _ in range(3):
        try:
            v2 = json.loads(v)
            if isinstance(v2, str):
                v = v2
                continue
        except Exception:
            pass
        break
    return v


def token():
    if os.path.exists(TOK):
        t = json.load(open(TOK))
        if t["until"] > time.time() + 60:
            return t["token"]
    r = requests.post(BASE + "/api/rf/access", headers={"X-JL-Sid": _sid(), "Content-Type": "application/json"}, data="{}", timeout=20)
    r.raise_for_status()
    d = r.json()
    fd = os.open(TOK, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, json.dumps({"token": d["token"], "until": time.time() + 600}).encode())
    os.close(fd)
    return d["token"]


def h():
    return {"Authorization": "Bearer " + token(), "Content-Type": "application/json"}


def get():
    r = requests.get(BASE + "/api/rf/dream", headers=h(), timeout=20)
    r.raise_for_status()
    return r.json()


def put(dreams, base):
    r = requests.put(BASE + "/api/rf/dream/dreams", headers=h(), json={"dreams": dreams, "base": base}, timeout=20)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "get":
        d = get()
        print(json.dumps({"dreams": [(x["id"], x["exam"]) for x in d["dreams"]], "mocks": [(m["id"][:8], m["exam"], m["raw"], m["rawMax"], m["score"]) for m in d["mocks"]]}))
    elif cmd == "backup":
        d = get()
        fd = os.open("/tmp/iter101_orig.json", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, json.dumps(d).encode()); os.close(fd)
        print("backed up", len(d["dreams"]), "dreams", len(d["mocks"]), "mocks")
    elif cmd == "setfile":  # replace the account list with the dreams in a json file (base = current ids => exact replace)
        want = json.load(open(sys.argv[2]))
        cur = get()["dreams"]
        print(put(want, [x["id"] for x in cur])[0])
        print([(x["id"], x["exam"]) for x in get()["dreams"]])
