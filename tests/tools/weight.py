#!/usr/bin/env python3
# The app's weight, measured (a check for whoever changes the app; not part of the app).
#
#   python3 /app/tests/tools/weight.py build            # makes the Android release JS bundle in /tmp, then reports
#   python3 /app/tests/tools/weight.py report <dir>     # reports on a bundle that was already made
#       --save       keep these numbers as the ones to compare with from now on (weight_baseline.json, next to this file)
#       --files 60   also list the app's own 60 heaviest files
#
# What it prints: the size of the JS the phone loads, how much of it is the app's own code and how much is libraries,
# the heaviest parts, and every picture / font / sound that goes into the app. It then compares with the kept numbers and
# ends with exit code 1 when the JS grew by more than 2 % or the files by more than 3 %, so a new feature that makes the
# app heavier is noticed on the day it is written.
# Bytecode is off (`--no-bytecode`): this machine cannot run the Hermes compiler; the comparison is JS to JS.
import collections
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "weight_baseline.json")
FRONTEND = "/app/frontend"
JS_GROWTH, FILE_GROWTH = 0.02, 0.03


def kb(n):
    return "%9.1f KB" % (n / 1024)


def measure(out):
    js_dir = os.path.join(out, "_expo/static/js/android")
    name = next(f for f in os.listdir(js_dir) if f.endswith(".js"))
    text = open(os.path.join(js_dir, name), encoding="utf-8").read()
    sections = json.load(open(os.path.join(js_dir, name + ".map"), encoding="utf-8"))["sections"]
    starts = [0]
    i = text.find("\n")
    while i >= 0:
        starts.append(i + 1)
        i = text.find("\n", i + 1)
    at = lambda o: starts[o["line"]] + o["column"]  # noqa: E731
    files = collections.Counter()
    for k, s in enumerate(sections):  # Metro writes one section per module: a module ends where the next one starts
        end = at(sections[k + 1]["offset"]) if k + 1 < len(sections) else len(text)
        source = (s["map"].get("sources") or ["(runtime)"])[0]
        files[re.sub(r"^.*/app/frontend/", "", source).lstrip("/")] += max(0, end - at(s["offset"]))
    groups, own = collections.Counter(), {}
    for f, n in files.items():
        m = re.findall(r"node_modules/((?:@[^/]+/)?[^/]+)", f)
        if m:
            groups["library: " + m[-1]] += n
        elif f.startswith(("app/", "src/")):
            own[f] = n
            part = "app (screens)" if f.startswith("app/") else "/".join(f.split("/")[:3 if f.startswith("src/components/") else 2])
            groups["own: " + part] += n
        else:
            groups["other: " + f.split("/")[0]] += n
    meta = json.load(open(os.path.join(out, "metadata.json")))["fileMetadata"]["android"]["assets"]
    assets = collections.Counter()
    count = collections.Counter()
    for a in meta:
        assets[a["ext"]] += os.path.getsize(os.path.join(out, a["path"]))
        count[a["ext"]] += 1
    return {"js": len(text.encode("utf-8")), "own": sum(own.values()), "modules": len(sections), "groups": dict(groups), "own_files": own,
            "assets": dict(assets), "asset_count": dict(count), "asset_total": sum(assets.values())}


def report(m, files=0):
    print("JS the phone loads   %s   (%d modules)" % (kb(m["js"]), m["modules"]))
    print("  the app's own code %s   %4.1f %%" % (kb(m["own"]), 100 * m["own"] / m["js"]))
    print("  libraries, runtime %s   %4.1f %%" % (kb(m["js"] - m["own"]), 100 * (m["js"] - m["own"]) / m["js"]))
    print("\nHeaviest parts of the JS")
    for k, n in sorted(m["groups"].items(), key=lambda x: -x[1])[:28]:
        print("  %s %5.2f %%  %s" % (kb(n), 100 * n / m["js"], k))
    print("\nFiles packed into the app   %s in %d files" % (kb(m["asset_total"]), sum(m["asset_count"].values())))
    for ext, n in sorted(m["assets"].items(), key=lambda x: -x[1]):
        print("  %s  %3d  .%s" % (kb(n), m["asset_count"][ext], ext))
    if files:
        print("\nThe app's own heaviest files")
        for f, n in sorted(m["own_files"].items(), key=lambda x: -x[1])[:files]:
            print("  %s  %s" % (kb(n), f))


def compare(m):
    if not os.path.exists(BASELINE):
        print("\nNo kept numbers yet (run with --save to keep these).")
        return 0
    b = json.load(open(BASELINE))
    dj, da = m["js"] - b["js"], m["asset_total"] - b["asset_total"]
    print("\nAgainst the kept numbers of %s" % b.get("saved", "?"))
    print("  JS     %+9.1f KB  (%+.2f %%)" % (dj / 1024, 100 * dj / b["js"]))
    print("  files  %+9.1f KB  (%+.2f %%)" % (da / 1024, 100 * da / max(1, b["asset_total"])))
    moved = [(k, m["groups"].get(k, 0) - b["groups"].get(k, 0)) for k in set(m["groups"]) | set(b["groups"])]
    for k, d in sorted(moved, key=lambda x: -abs(x[1]))[:8]:
        if abs(d) >= 1024:
            print("    %+8.1f KB  %s" % (d / 1024, k))
    heavy = dj > b["js"] * JS_GROWTH or da > b["asset_total"] * FILE_GROWTH
    print("  -> " + ("HEAVIER THAN ALLOWED (JS +2 % / files +3 %). Find what grew before going on." if heavy else "within the allowed growth."))
    return 1 if heavy else 0


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("build", "report"):
        print(__doc__ or "usage: weight.py build | report <dir> [--save] [--files N]")
        return 2
    if args[0] == "build":
        out = "/tmp/jl-weight-%d" % int(time.time())
        log = out + ".log"
        print("Making the Android JS bundle in %s (about a minute)..." % out)
        with open(log, "w") as fh:
            done = subprocess.run(["npx", "expo", "export", "--platform", "android", "--no-bytecode", "--source-maps", "--output-dir", out], cwd=FRONTEND, stdout=fh, stderr=subprocess.STDOUT)
        if done.returncode != 0:
            print("The bundle could not be made: the app does not build. See %s" % log)
            return 1
    else:
        out = args[1]
    m = measure(out)
    report(m, int(args[args.index("--files") + 1]) if "--files" in args else 0)
    code = compare(m)
    if "--save" in args:
        keep = {k: m[k] for k in ("js", "own", "modules", "groups", "assets", "asset_count", "asset_total")}
        keep["saved"] = time.strftime("%d %b %Y %H:%M UTC", time.gmtime())
        json.dump(keep, open(BASELINE, "w"), indent=1, sort_keys=True)
        print("\nKept as the numbers to compare with: " + BASELINE)
        return 0
    return code


if __name__ == "__main__":
    sys.exit(main())
