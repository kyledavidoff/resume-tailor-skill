#!/usr/bin/env python3
"""Prove the tailored file has the same layout as the source.

Usage:
    python verify_layout.py source.docx tailored.docx [--work /tmp/rt]

Renders both files with LibreOffice and compares the rendered geometry:
page count, line count, and the top position of every line. If a bullet
gains or loses a line, every following line shifts and the check fails.

Exit code 0 = pass, 1 = fail.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx_lib as D  # noqa: E402

TOL = 0.6  # points


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("tailored")
    ap.add_argument("--work", default="/tmp/resume_tailor")
    args = ap.parse_args()

    base = D.measure(args.source, os.path.join(args.work, "verify_base"))
    new = D.measure(args.tailored, os.path.join(args.work, "verify_new"))

    ok = True
    if base["pages"] != new["pages"]:
        print("FAIL page count: %d -> %d" % (base["pages"], new["pages"]))
        ok = False
    if len(base["lines"]) != len(new["lines"]):
        print("FAIL line count: %d -> %d"
              % (len(base["lines"]), len(new["lines"])))
        ok = False

    for i, (a, b) in enumerate(zip(base["lines"], new["lines"])):
        if a["page"] != b["page"] or abs(a["top"] - b["top"]) > TOL:
            print("FAIL first shifted line at index %d" % i)
            print("  source:   p%d top %.1f  %s" % (a["page"], a["top"],
                                                    a["text"][:70]))
            print("  tailored: p%d top %.1f  %s" % (b["page"], b["top"],
                                                    b["text"][:70]))
            ok = False
            break

    # Report where each line now sits close to the right edge.
    if ok:
        max_x1 = max(l["x1"] for l in new["lines"])
        tight = [l for l in new["lines"] if max_x1 - l["x1"] < 4]
        print("PASS layout identical: %d pages, %d lines"
              % (new["pages"], len(new["lines"])))
        print("lines within 4pt of the right edge: %d" % len(tight))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
