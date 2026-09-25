---
name: resume-tailor
description: Rewrite the wording of an existing resume .docx to mirror one specific job posting, keeping the original formatting byte for byte identical and inventing nothing. Produces a submission file and a yellow highlighted review file, plus a short change summary. Use this skill whenever the user asks to tailor, customize, adapt, target, or optimize a resume or CV for a job posting, job description, or application, mentions ATS or applicant tracking, asks to add keywords from a posting to a resume, or hands over a resume plus a job link. Use it even if they only say "make my resume fit this role".
compatibility: Requires LibreOffice (soffice), pdfplumber, and lxml. Needs an editable .docx source. Cannot work from a PDF.
---

# Resume Tailor

Rewrite the words inside a resume. Change nothing else.

## Two hard rules

1. **Formatting never changes.** Fonts, sizes, margins, spacing, section
   order, bullet count, line count, and page count stay identical. The
   scripts edit `word/document.xml` inside the original file. Never rebuild
   the document with python-docx. Never pour text into a template.
2. **Nothing is invented.** Reframe, reorder, and reword real experience.
   Never create an employer, title, date, metric, tool, certification, or
   outcome that the source resume does not contain. If the posting asks for
   something the resume does not show, leave it out and say so in chat.

## Inputs

Ask for both before you start:

- The resume as a `.docx` file.
- One job posting, as a link or pasted text.

If the user supplies a PDF, stop and ask for the editable `.docx`. Do not
reconstruct the layout. If they cannot find the `.docx`, say plainly that
the skill cannot run and that a converted PDF will lose the formatting.

## Workflow

Set `SK=<path to this skill>/scripts` and work in a scratch directory.

### 1. Inventory the resume

```bash
python $SK/inspect_resume.py source.docx --out inventory.json
```

This renders the file and prints, for every editable paragraph, its id, its
rendered line count, its current character count, and a **safe character
range**. Stay inside that range. Below the range a line disappears. Above it
the text wraps and pushes the page.

Read the printed table before you write anything. Some bullets have almost
no free space. Those bullets can only take equal length word swaps.

### 2. Read the posting and extract its vocabulary

Load `references/rewriting.md` and follow it. Build a list of the exact
nouns, verb phrases, tools, and metrics the employer used. Mirror those
words. Do not substitute synonyms.

### 3. Plan the edits

Decide, per role, which bullet leads. Reordering bullets inside a role is
allowed and expected. Adding or deleting bullets is not.

Write `edits.json`:

```json
{
  "company": "EQT",
  "edits": [{"id": 7, "new_text": "..."}],
  "reorder": [{"ids": [15, 18, 17, 16]}]
}
```

`reorder.ids` lists the new order of a set of bullets that already sit
together. The paragraphs swap positions. Nothing else moves.

Check every `new_text` against its safe range before you build. If a good
rewrite does not fit, keep the original wording for that bullet and report
it. A weaker bullet that fits beats a stronger bullet that breaks the page.

### 4. Build both files

```bash
python $SK/apply_edits.py source.docx edits.json \
  --submission out/<LastName>_Resume_<Company>.docx \
  --review     out/<LastName>_Resume_<Company>_REVIEW.docx
```

The submission file carries no markup. The review file highlights every
changed word in yellow and leaves unchanged text clean.

### 5. Verify before you present

```bash
python $SK/verify_layout.py source.docx out/<LastName>_Resume_<Company>.docx
python $SK/verify_layout.py source.docx out/<LastName>_Resume_<Company>_REVIEW.docx
```

This renders both files and compares page count, line count, and the top
position of every line. `PASS layout identical` is the gate. If it fails,
the message names the first line that moved. Shorten or restore the bullet
that caused it and build again.

Then validate the XML and look at the result:

```bash
python /mnt/skills/public/docx/scripts/office/validate.py \
  out/<LastName>_Resume_<Company>.docx --original source.docx
soffice --headless --convert-to pdf out/<LastName>_Resume_<Company>_REVIEW.docx --outdir render
pdftoppm -jpeg -r 110 render/<LastName>_Resume_<Company>_REVIEW.pdf rev
```

Read the image. Confirm the highlights land on the changed words and the
page looks like the original.

### 6. Present and summarise

Copy both files to `/mnt/user-data/outputs` and present them together, the
submission file first.

Then print a change summary in chat. Keep it under fifteen lines:

- Posting requirement to bullet map, one line each, short.
- Posting requirements with no match in the resume. Name them plainly.
- Any bullet where the fit is a stretch, or where no room existed to edit.

Do not pad the summary. If nothing was a stretch, say so in one line.

## Rewriting rules

- **Mirror the posting's exact words.** Literal overlap is what both keyword
  filters and LLM screeners reward.
- **Keep every number exactly as written.** Dollar amounts, fund sizes,
  counts, percentages, and dates never change.
- **Match seniority language,** but never downgrade a true claim. If the
  resume says the person led something, keep "led" even for a junior
  posting. Match seniority only where the original verb is neutral.
- **Keep density natural.** A human reads this after the filter. Three or
  four mirrored terms per bullet is the ceiling.
- **Follow the source resume's own conventions,** not any house style. Copy
  its voice, its punctuation, and its hyphenation. If the resume writes
  "late-stage", the rewrite writes "late-stage".
- **Put the mirrored term early in the bullet.** Recruiters and screeners
  read the first half of a line.
- **Leave low relevance bullets alone.** Editing them costs review time and
  gains nothing.

## Reference files

- `references/rewriting.md` — how to extract posting vocabulary, role type
  playbooks, seniority mapping, and an honest account of what the screening
  layer actually does.
- `references/docx_editing.md` — how the XML edit works, what breaks it, and
  how to fix a failed layout check.
