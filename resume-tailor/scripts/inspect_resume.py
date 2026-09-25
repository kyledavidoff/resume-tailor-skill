#!/usr/bin/env python3
"""Inventory a resume .docx: editable paragraphs, roles, and length budgets.

Usage:
    python inspect_resume.py source.docx --out inventory.json [--work /tmp/rt]

Every editable paragraph gets a safe character range. Stay inside the range
and the rendered line count normally holds. verify_layout.py is the real gate.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx_lib as D  # noqa: E402

def is_heading(text):
    core = re.sub(r"[^A-Za-z]", "", text)
    return bool(core) and core.isupper() and len(text) < 40


def is_bold_start(p):
    r = p.find(D.W + "r")
    if r is None:
        return False
    rPr = r.find(D.W + "rPr")
    return rPr is not None and rPr.find(D.W + "b") is not None


ADD_SAFETY = 0.85     # use 85 percent of the free space on the last line
SHRINK_SAFETY = 0.70  # never cut more than 70 percent of the last line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default="/tmp/resume_tailor")
    args = ap.parse_args()

    os.makedirs(args.work, exist_ok=True)
    unpacked = D.unpack(args.docx, os.path.join(args.work, "src"))
    tree, _ = D.load_document(unpacked)
    paras = D.paragraphs(tree)

    layout = D.measure(args.docx, os.path.join(args.work, "render_base"))
    mapping = D.map_paragraphs_to_lines(
        [(i, D.para_text(p)) for i, p in enumerate(paras)], layout)

    items, current_role, section = [], None, None
    for i, p in enumerate(paras):
        text = D.para_text(p)
        if not text.strip():
            continue
        bullet = D.is_bullet(p)
        plain = D.editable_runs(p) is not None
        if is_heading(text):
            section = text.strip()
            current_role = None
        elif not bullet and not plain and is_bold_start(p):
            current_role = text
        editable = False
        if bullet and plain:
            editable = True
        elif plain and not is_heading(text) and section:
            head = section.upper()
            if head.startswith("SUMMARY") or head.startswith("PROFILE"):
                editable = len(text) > 40
            elif head.startswith("SKILL"):
                editable = len(text) > 20
        lines = [layout["lines"][j] for j in mapping.get(i, [])]
        rec = {
            "id": i,
            "section": section,
            "role": current_role,
            "bullet": bullet,
            "editable": editable,
            "text": text,
            "chars": len(text),
            "lines": len(lines),
        }
        if lines:
            max_x1 = max(l["x1"] for l in lines)
            last = lines[-1]
            free_pt = max(0.0, max_x1 - last["x1"])
            used_pt = sum(l["x1"] - l["x0"] for l in lines)
            cpp = len(text) / used_pt if used_pt else 0.0
            add = int(free_pt * cpp * ADD_SAFETY)
            shrink = int(len(last["text"]) * SHRINK_SAFETY)
            rec["safe_max"] = len(text) + add
            rec["safe_min"] = max(20, len(text) - shrink)
            rec["last_line_fill_pct"] = round(
                100 * (last["x1"] - last["x0"]) / (max_x1 - last["x0"]), 1)
        items.append(rec)

    out = {
        "source": os.path.abspath(args.docx),
        "pages": layout["pages"],
        "line_count": len(layout["lines"]),
        "paragraphs": items,
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)

    print("pages: %d   rendered lines: %d" % (out["pages"], out["line_count"]))
    print("%-4s %-6s %-6s %-9s %s" % ("id", "lines", "chars", "safe", "text"))
    for r in items:
        if not r["editable"]:
            continue
        print("%-4d %-6d %-6d %-9s %s" % (
            r["id"], r["lines"], r["chars"],
            "%d-%d" % (r.get("safe_min", 0), r.get("safe_max", 0)),
            r["text"][:70]))
    unmapped = [r["id"] for r in items if r["editable"] and r["lines"] == 0]
    if unmapped:
        print("WARNING: could not map paragraphs to rendered lines: %s"
              % unmapped)


if __name__ == "__main__":
    main()
