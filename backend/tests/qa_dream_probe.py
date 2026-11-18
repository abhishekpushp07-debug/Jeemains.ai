"""QA helper: read/restore the QA account's dreams via the captured RF bearer (never prints the token).
usage: python qa_dream_probe.py get|save-orig|restore"""
import json
import os
import sys

import requests

BASE = os.environ["EXPO_BACKEND_URL"].rstrip("/") + "/api"
cap = json.load(open("/tmp/qa_cap.json"))
H = {"Authorization": cap["auth"], "Content-Type": "application/json"}
cmd = sys.argv[1]
r = requests.get(f"{BASE}/rf/dream", headers=H, timeout=15)
print("GET status", r.status_code)
if r.status_code != 200:
    sys.exit(1)
d = r.json()
if cmd == "save-orig" and not os.path.exists("/tmp/qa_dream_orig.json"):
    json.dump(d, open("/tmp/qa_dream_orig.json", "w"))
    print("saved original")
if cmd == "restore":
    orig = json.load(open("/tmp/qa_dream_orig.json"))
    p = requests.put(f"{BASE}/rf/dream/dreams", headers=H, json={"dreams": orig["dreams"]}, timeout=15)
    print("restore PUT", p.status_code)
    d = requests.get(f"{BASE}/rf/dream", headers=H, timeout=15).json()
print("dreams:", [(x["id"], x["exam"], x["college"][:20], x["note"]) for x in d["dreams"]])
print("mocks:", [(m["id"][:13], m["exam"], m["score"], m["raw"], m["rawMax"], m["title"][:35]) for m in d["mocks"]])
