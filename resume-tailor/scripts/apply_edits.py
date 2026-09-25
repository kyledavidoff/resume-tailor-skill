#!/usr/bin/env python3
"""Apply tailored wording to a resume .docx without touching formatting.

Usage:
    python apply_edits.py source.docx edits.json \
        --submission out/Name_Company_Resume.docx \
        --review     out/Name_Company_Resume_REVIEW.docx

edits.json:
{
  "edits":   [{"id": 7, "new_text": "..."}],
  "reorder": [{"ids": [9, 7, 8, 10, 11]}]      # optional, same role only
}

The submission file carries no markup. The review file highlights every
changed run in yellow. Both keep the original runs and run properties.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import docx_lib as D  # noqa: E402


def build(source, spec, out_path, work, highlight):
    unpacked = D.unpack(source, work)
    tree, xml_path = D.load_document(unpacked)
    paras = D.paragraphs(tree)

    changed = []
    for edit in spec.get("edits", []):
        pid = edit["id"]
        new_text = edit["new_text"]
        p = paras[pid]
        old = D.para_text(p)
        if old == new_text:
            continue
        n = D.rewrite_paragraph(p, new_text, highlight=highlight)
        changed.append((pid, n))

    for block in spec.get("reorder", []):
        ids = block["ids"]
        elems = [paras[i] for i in ids]
        parent = elems[0].getparent()
        positions = sorted(list(parent).index(e) for e in elems)
        for e in elems:
            parent.remove(e)
        for pos, e in zip(positions, elems):
            parent.insert(pos, e)

    D.save_document(tree, xml_path)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    D.repack(unpacked, out_path)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("edits")
    ap.add_argument("--submission", required=True)
    ap.add_argument("--review", required=True)
    ap.add_argument("--work", default="/tmp/resume_tailor")
    args = ap.parse_args()

    with open(args.edits) as f:
        spec = json.load(f)

    changed = build(args.docx, spec, args.submission,
                    os.path.join(args.work, "build_sub"), highlight=False)
    build(args.docx, spec, args.review,
          os.path.join(args.work, "build_rev"), highlight=True)

    print("edited paragraphs: %d" % len(changed))
    for pid, groups in changed:
        print("  id %-3d  highlighted groups: %d" % (pid, groups))
    print("submission: %s" % args.submission)
    print("review:     %s" % args.review)


if __name__ == "__main__":
    main()
