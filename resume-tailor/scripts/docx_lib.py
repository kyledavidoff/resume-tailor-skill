"""Shared helpers for resume-tailor.

Everything here works on the ORIGINAL word/document.xml. Nothing is rebuilt.
Runs are deep copied so every run property survives the edit.
"""
import copy
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from difflib import SequenceMatcher

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Schema order of CT_RPr children. w:highlight must be inserted in this order
# or Word reports the file as corrupt.
RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike",
    "dstrike", "outline", "shadow", "emboss", "imprint", "noProof",
    "snapToGrid", "vanish", "webHidden", "color", "spacing", "w", "kern",
    "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd",
    "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout",
    "specVanish", "oMath",
]


# ---------------------------------------------------------------- zip helpers

def unpack(docx_path, dest):
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(docx_path) as z:
        z.extractall(dest)
    for root, _, files in os.walk(dest):
        for f in files:
            p = os.path.join(root, f)
            if os.path.islink(p):
                os.unlink(p)
    return dest


def repack(src_dir, docx_path):
    if os.path.exists(docx_path):
        os.remove(docx_path)
    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(src_dir):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, src_dir))
    return docx_path


def load_document(unpacked_dir):
    path = os.path.join(unpacked_dir, "word", "document.xml")
    tree = etree.parse(path)
    return tree, path


def save_document(tree, path):
    tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)


# ----------------------------------------------------------- paragraph access

def paragraphs(tree):
    """Body paragraphs in document order."""
    return list(tree.getroot().iter(W + "p"))


def para_text(p):
    return "".join(t.text or "" for t in p.iter(W + "t"))


def is_bullet(p):
    pPr = p.find(W + "pPr")
    return pPr is not None and pPr.find(W + "numPr") is not None


def run_text(r):
    return "".join(t.text or "" for t in r.findall(W + "t"))


def editable_runs(p):
    """Direct child runs that hold only text. Returns None if the paragraph
    holds a tab, break, drawing, or field, which we refuse to edit."""
    runs = p.findall(W + "r")
    if not runs:
        return None
    for r in runs:
        for child in r:
            tag = etree.QName(child).localname
            if tag not in ("rPr", "t"):
                return None
    return runs


# ------------------------------------------------------------- text rewriting

TOKEN = re.compile(r"\S+|\s+")


def tokenize(s):
    return TOKEN.findall(s)


def _char_to_run(runs):
    """Map each character index of the paragraph text to its run index."""
    mapping = []
    for i, r in enumerate(runs):
        mapping.extend([i] * len(run_text(r)))
    return mapping


def plan_runs(runs, new_text):
    """Return [(run_index, text, changed)] describing the rewritten paragraph.

    Unchanged tokens stay in their original run. New tokens inherit the run
    that owned the text they replace, so every run property is preserved.
    """
    old_text = "".join(run_text(r) for r in runs)
    old_tokens = tokenize(old_text)
    new_tokens = tokenize(new_text)
    c2r = _char_to_run(runs)

    starts, pos = [], 0
    for tok in old_tokens:
        starts.append(pos)
        pos += len(tok)

    def run_of(tok_index):
        if not old_tokens:
            return 0
        tok_index = max(0, min(tok_index, len(old_tokens) - 1))
        ch = starts[tok_index]
        return c2r[ch] if ch < len(c2r) else (len(runs) - 1)

    out = []
    pending_delete = False
    sm = SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                changed = pending_delete
                pending_delete = False
                out.append((run_of(i1 + k), new_tokens[j1 + k], changed))
        elif op == "delete":
            pending_delete = True
        else:  # replace or insert
            base = run_of(i1 if op == "replace" else i1 - 1)
            for k in range(j1, j2):
                out.append((base, new_tokens[k], True))
            pending_delete = False
    return out


def _set_highlight(rPr, value="yellow"):
    existing = rPr.find(W + "highlight")
    if existing is not None:
        existing.set(W + "val", value)
        return
    hl = etree.SubElement(rPr, W + "highlight")
    hl.set(W + "val", value)
    rPr.remove(hl)
    idx = RPR_ORDER.index("highlight")
    insert_at = len(rPr)
    for i, child in enumerate(rPr):
        name = etree.QName(child).localname
        order = RPR_ORDER.index(name) if name in RPR_ORDER else 99
        if order > idx:
            insert_at = i
            break
    rPr.insert(insert_at, hl)


def rewrite_paragraph(p, new_text, highlight=False):
    """Replace the text of a paragraph, keeping every run property.

    Returns the number of highlighted groups. Raises ValueError if the
    paragraph holds anything other than plain text runs.
    """
    runs = editable_runs(p)
    if runs is None:
        raise ValueError("paragraph holds non text runs, refusing to edit")

    plan = plan_runs(runs, new_text)

    groups = []
    for run_idx, text, changed in plan:
        if groups and groups[-1][0] == run_idx and groups[-1][2] == changed:
            groups[-1][1] += text
        else:
            groups.append([run_idx, text, changed])

    anchor = runs[0]
    new_runs = []
    for run_idx, text, changed in groups:
        src = runs[min(run_idx, len(runs) - 1)]
        r = copy.deepcopy(src)
        for child in list(r):
            if etree.QName(child).localname != "rPr":
                r.remove(child)
        t = etree.SubElement(r, W + "t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        if highlight and changed:
            rPr = r.find(W + "rPr")
            if rPr is None:
                rPr = etree.Element(W + "rPr")
                r.insert(0, rPr)
            _set_highlight(rPr)
        new_runs.append(r)

    parent = anchor.getparent()
    index = list(parent).index(anchor)
    for r in runs:
        parent.remove(r)
    for offset, r in enumerate(new_runs):
        parent.insert(index + offset, r)
    return sum(1 for g in groups if g[2])


# -------------------------------------------------------------- layout render

def render_pdf(docx_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="soffice_")
    subprocess.run(
        ["soffice", "-env:UserInstallation=file://" + profile, "--headless",
         "--convert-to", "pdf", os.path.abspath(docx_path),
         "--outdir", os.path.abspath(out_dir)],
        check=True, capture_output=True, timeout=300,
    )
    shutil.rmtree(profile, ignore_errors=True)
    name = os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
    return os.path.join(out_dir, name)


def _norm(s):
    s = s.replace("\u25aa", " ").replace("\u2022", " ")
    return re.sub(r"\s+", " ", s).strip()


def measure(docx_path, work_dir):
    """Render the file and return the layout fingerprint."""
    import pdfplumber

    pdf_path = render_pdf(docx_path, work_dir)
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        pages = len(pdf.pages)
        for pi, page in enumerate(pdf.pages):
            for ln in page.extract_text_lines(strip=True):
                lines.append({
                    "page": pi,
                    "top": round(ln["top"], 1),
                    "x0": round(ln["x0"], 1),
                    "x1": round(ln["x1"], 1),
                    "text": ln["text"],
                })
    return {"pages": pages, "lines": lines, "pdf": pdf_path}


def map_paragraphs_to_lines(para_texts, layout):
    """Greedy walk that assigns rendered lines to paragraphs in order."""
    lines = layout["lines"]
    result, cursor = {}, 0
    for pid, text in para_texts:
        target = _norm(text)
        if not target:
            result[pid] = []
            continue
        acc, used, probe = "", [], cursor
        while probe < len(lines):
            candidate = _norm(acc + " " + lines[probe]["text"])
            used.append(probe)
            acc = candidate
            probe += 1
            if candidate.replace(" ", "") == target.replace(" ", ""):
                break
            if len(candidate.replace(" ", "")) > len(target.replace(" ", "")):
                break
        if acc.replace(" ", "") == target.replace(" ", ""):
            result[pid] = used
            cursor = probe
        else:
            result[pid] = []
    return result
