#!/usr/bin/env python3
# Check only (not part of the app): every colour kept in frontend/src/websiteDesign.ts must equal the owner's website
# export, value for value. Exit code 1 and a list of differences when one does not.
#   python3 /app/tests/tools/website_tokens.py
import json
import re
import sys

EXPORT = "/app/frontend/assets/website-2026-10-26/design-tokens.json"
KEPT = "/app/frontend/src/websiteDesign.ts"

states = json.load(open(EXPORT))["viewports"]["390"]["other_component_states"]
source = open(KEPT).read()
entries = re.findall(r'"([a-z.]+)":\s*\{([^}]*)\}', source)
bad, seen = [], 0
for name, body in entries:
    for key, value in re.findall(r'(\w+):\s*"([^"]*)"', body):
        seen += 1
        real = (states.get(name) or {}).get("style", {}).get(key)
        if real != value:
            bad.append("%s.%s: app has %r, the export has %r" % (name, key, value, real))
if not seen:
    bad.append("no value found in " + KEPT)
print("website colours kept in the app: %d checked, %d different" % (seen, len(bad)))
for line in bad:
    print("  " + line)
sys.exit(1 if bad else 0)
