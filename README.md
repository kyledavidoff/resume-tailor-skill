# Resume Tailor

A Claude skill that rewrites the wording of your resume to match one job posting. The formatting stays identical, and the skill invents nothing.

The full skill text is in [`resume-tailor/SKILL.md`](resume-tailor/SKILL.md).

## What it does

- Mirrors the exact words the job posting uses, such as nouns, tools, and verb phrases.
- Rewords and reorders your real experience. It never adds an employer, title, date, metric, tool, or outcome that your resume does not contain.
- Keeps every number exactly as written.
- Keeps fonts, margins, spacing, bullet count, line count, and page count identical. It edits the text inside your original file. It does not rebuild the document.
- Checks the layout after each edit. If a line moves, it fixes the bullet and builds again.

## What you get back

1. **Submission file.** A clean `.docx`, ready to send.
2. **Review file.** The same `.docx` with every changed word highlighted in yellow.
3. **Change summary.** Which posting requirement each bullet now covers, which requirements your resume does not show, and which edits are a stretch.

## What you need

- Your resume as an editable `.docx` file. A PDF does not work.
- One job posting, as a link or pasted text.

## Install

**Claude apps.** Download the `resume-tailor` folder and zip it. Then upload the zip in your Claude settings, in the Skills section.

**Claude Code.** Copy the `resume-tailor` folder into your skills folder:

```
cp -r resume-tailor ~/.claude/skills/
```

The scripts need LibreOffice (`soffice`), `pdfplumber`, and `lxml`. Claude apps usually include them. In Claude Code, install them yourself.

## How to use it

Attach your resume and the posting, then ask Claude to tailor it. Any of these prompts work:

- "Tailor my resume to this job."
- "Make my resume fit this role."
- "Add the keywords from this posting to my resume."

## Files

| Path | Purpose |
|---|---|
| `resume-tailor/SKILL.md` | Instructions and workflow for Claude |
| `resume-tailor/references/rewriting.md` | How to pull vocabulary from a posting and rewrite bullets |
| `resume-tailor/references/docx_editing.md` | How the XML edit works and how to fix a failed layout check |
| `resume-tailor/scripts/inspect_resume.py` | Lists each bullet and how many characters it can safely hold |
| `resume-tailor/scripts/apply_edits.py` | Builds the submission file and the review file |
| `resume-tailor/scripts/verify_layout.py` | Confirms the new file has the same layout as the original |
| `resume-tailor/scripts/docx_lib.py` | Shared helpers for the scripts |
