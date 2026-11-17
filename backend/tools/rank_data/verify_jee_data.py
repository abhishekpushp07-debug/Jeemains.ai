"""Re-checks backend/rank_data/jee_main_2026.json.gz against a fresh download of the official JoSAA / CSAB pages.

Two independent checks:
  1. every official ORCR row (JoSAA R1-R5, CSAB R1-R2) is looked up in the served data, opening and closing must match;
  2. the data rebuilt from the fresh download must equal the served file seat for seat (JAC Delhi PDFs included).

Usage:  python build_rank_data.py fetch <raw_dir>   then   python verify_jee_data.py <raw_dir>
"""
import gzip, json, sys
from collections import Counter
from pathlib import Path

import build_rank_data as b

SERVED = b.OUT


def load(path):
    return json.load(gzip.open(path, "rt", encoding="utf-8"))


def row_check(raw, data):
    inst_ix = {i["name"].lower(): n for n, i in enumerate(data["institutes"])}
    prog_ix = {(p["inst"], p["name"], p["degree"]): n for n, p in enumerate(data["programs"])}
    seats = {tuple(s[:5]): s for s in data["seats"]}
    stats, bad = Counter(), []
    for fname, slot in [(f"josaa_r{r}.json", r - 1) for r in range(1, 6)] + [("csab_r1.json", 5), ("csab_r2.json", 6)]:
        for row in json.load(open(raw / fname)):
            if len(row) < 7 or row[0] == "Institute":
                continue
            name = b.norm(row[0])
            quota, seat = b.QUOTA.get(row[2]), b.SEAT.get(row[3])
            base, degree = b.split_program(row[1])
            if name.lower() not in inst_ix or not quota or not seat or base is None:
                stats["outside scope (IIT / unsupported quota)"] += 1
                continue
            prog = prog_ix.get((inst_ix[name.lower()], base, degree))
            s = seats.get((prog, quota, seat[0], seat[1], int(row[4].startswith("Female"))))
            o, c = b.rank_value(row[5]), b.rank_value(row[6])
            if s is None:
                stats["missing" if c else "no closing rank (skipped by design)"] += 1
                if c:
                    bad.append((fname, row))
                continue
            if (s[5][slot], s[6][slot]) == (o, c):
                stats["match"] += 1
            else:
                stats["mismatch"] += 1
                bad.append((fname, row, s[5][slot], s[6][slot]))
    return stats, bad


def rebuild_equal(raw, served):
    tmp = Path("/tmp/jee_main_2026.rebuilt.json.gz")
    b.OUT = tmp
    b.build(raw)
    fresh = load(tmp)
    same = {k: fresh[k] == served[k] for k in ("institutes", "programs", "marks")}
    a, z = {tuple(s[:5]): s for s in served["seats"]}, {tuple(s[:5]): s for s in fresh["seats"]}
    diff = [k for k in set(a) | set(z) if a.get(k) != z.get(k)]
    return same, len(a), len(z), diff


if __name__ == "__main__":
    raw = Path(sys.argv[1])
    served = load(SERVED)
    stats, bad = row_check(raw, served)
    print("Official rows vs served data:", dict(stats))
    for x in bad[:20]:
        print("  BAD", x)
    same, n_served, n_fresh, diff = rebuild_equal(raw, served)
    print("Rebuilt == served:", same, "seats served", n_served, "fresh", n_fresh, "differing seats", len(diff))
    for k in diff[:20]:
        print("  DIFF", k)
