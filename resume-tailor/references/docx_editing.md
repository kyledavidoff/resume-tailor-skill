# How the formatting survives

## The edit path

A `.docx` is a ZIP archive. The scripts unzip it, parse
`word/document.xml` with lxml, replace text inside existing runs, and zip
it back. Every other part of the archive is copied unchanged: styles,
numbering, fonts, theme, settings, section properties.

Never use python-docx to rebuild the document. Never write the text into a
template. Both discard run properties and change the rendering.

## Run level rewriting

Word splits a paragraph into `<w:r>` runs. A run holds a text element
`<w:t>` and optional run properties `<w:rPr>` with the bold, italic, size,
and font settings.

`docx_lib.plan_runs` diffs the old and new text at word level. Unchanged
words stay in their original run. New words inherit the run that owned the
text they replace. The script then deep copies each source run, clears its
text, and writes the new text into it. Run properties and run attributes
survive untouched.

If a run holds anything other than `w:rPr` and `w:t`, for example a tab, a
break, or a field, the script refuses to edit that paragraph. Company and
date lines use tabs, so they are protected automatically.

## The review file

For the review file the script adds `<w:highlight w:val="yellow"/>` to the
run properties of changed runs only. The insert respects the schema order
of `CT_RPr` children. Highlight sits after `szCs` and before `u`. Out of
order children make Word report the file as corrupt.

A run boundary is created wherever a change starts or stops, so a change
inside a run splits that run into a highlighted part and a clean part.

One limit worth telling the user. A pure deletion has no text left to
highlight. The script marks the next surviving word instead, so the eye
lands on the right place. The chat summary carries the detail.

## The layout gate

Line wrapping is decided by the renderer, not stored in the file. A
character budget alone is a guess. So `verify_layout.py` renders the source
and the output with LibreOffice, extracts every text line with pdfplumber,
and compares page count, line count, and the top coordinate of every line
with a 0.6 point tolerance.

If a bullet gains or loses a line, every following line shifts and the
check fails on the first shifted line. That message names the bullet.

LibreOffice metrics are very close to Word but not identical. Treat a pass
as strong evidence, not a proof. Ask the user to glance at the review file.

## Failure modes and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `FAIL line count` | A bullet grew or shrank past its budget | Restore or shorten that bullet |
| `FAIL page count` | Total text grew | Shorten the longest edited bullet |
| `paragraph holds non text runs` | Tried to edit a header or a date line | Do not edit that paragraph |
| Validation error in Word | Bad `rPr` child order | Use `_set_highlight`, never append raw |
| Cannot map paragraph to lines | Render text does not match the XML text | Check for a field or a smart quote mismatch |

## Smart quotes and special characters

Copy the exact characters from the source text. The right single quotation
mark U+2019 is common in Word files. A straight apostrophe in the new text
creates a false diff and a wrong highlight.
