#!/usr/bin/env python3
"""Fail when BANNED.md documents a word the checker does not enforce.

A ban list that is written in one place and enforced from another drifts. It
drifted once: 28 documented words, including load-bearing and delve, were never
checked. Run this after editing either side.
"""
import importlib.util as il
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = il.spec_from_file_location("ste", os.path.join(HERE, "ste-lint.py"))
ste = il.module_from_spec(spec)
spec.loader.exec_module(ste)

enforced = {w.lower() for w in ste.BANNED + ste.HOUSE + ste.MARKETING + ste.PHRASAL}
enforced |= {n.split(" (")[0].lower() for n, _ in ste.SCOPED}
doc = open(os.path.join(HERE, "..", "BANNED.md"), encoding="utf-8").read()
section = doc[doc.index("### Vocabulary"):doc.index("### Formatting tells")]
# The list wraps across source lines, so a phrase can straddle a newline.
section = re.sub(r"\s*\n\s*", " ", section)
documented = {
    w.strip().split(" (")[0].strip(".,").lower()
    for w in section.split(",")
    if w.strip() and not w.startswith("#")
}
documented = {w for w in documented
              if len(w) > 3 and not w.startswith("###")
              and not w.startswith("(")}

missing = sorted(documented - enforced)
if missing:
    print(f"{len(missing)} documented words the checker does not enforce:")
    for w in missing:
        print("  ", w)
    sys.exit(1)
print(f"in sync: {len(documented)} documented words, all enforced")
