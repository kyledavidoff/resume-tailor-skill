# Rewriting method

## 1. Extract the posting's vocabulary

Read the posting twice. Build four lists:

- **Nouns the employer repeats.** Example: due diligence, financial models,
  investment materials, value creation, market mapping, portfolio company
  performance, stakeholders.
- **Verb phrases.** Example: conduct, build and maintain, monitor, support,
  prepare, contribute, synthesize.
- **Tools and named systems.** Example: SQL, PitchBook, CapIQ, Excel,
  Salesforce, Power BI.
- **Metrics and scale words.** Example: fund size, deal count, years of
  experience, sector names, geography.

Rank the list. Terms in the title, in the first responsibility bullet, and
in the "about you" section carry the most weight. Terms in the boilerplate
about the firm carry the least.

Then check each term against the resume. Three buckets:

- **Present already.** Do nothing. Do not restate it twice.
- **Present in different words.** This is the work. Swap the resume's word
  for the posting's word where the meaning is the same.
- **Absent.** Leave it out and report it. This is the gap list.

## 2. Role type playbooks

The role type decides which bullet leads inside each job.

| Posting type | Lead with |
|---|---|
| Corporate development | Financial modeling, valuation, deal execution, diligence, integration |
| Investment | Sourcing, thesis development, diligence, portfolio construction, LP reporting |
| Operations or platform | Fundraising, systems building, process design, portfolio support |
| Strategic partnerships | Origination, negotiation, stakeholder management, partner counts |
| Strategy and operations | Structured problem solving, analysis, recommendations, implementation |

Inside a bullet, move the relevant clause to the front. Inside a role, move
the most relevant bullet to the top. Do not move bullets between roles.

## 3. Seniority mapping

| Posting language | Use |
|---|---|
| Lead, own, drive, set strategy | Led, owned, drove |
| Support, contribute, assist, participate | Supported, executed, contributed |
| Conduct, prepare, build, maintain | Conducted, prepared, built, maintained |

One limit: never downgrade a true claim to match a junior posting. If the
person led a fund origination, the bullet says led. Understating real
seniority costs more at the human screen than it gains at the filter.

## 4. Density

Aim for three or four mirrored terms per bullet. Past that the bullet reads
like a keyword list and the human screen fails it. The screening funnel has
two gates and the second one is a person.

## 5. What the screening layer actually does

Be honest with the user about this. The picture is mixed:

- Most modern systems, including Greenhouse, Lever, Workday, and iCIMS,
  parse the resume into fields and let a recruiter search and filter. Hard
  automatic rejection on a keyword score is now uncommon. It was more
  common in older Taleo style deployments and some enterprise setups.
- Recruiters search literal strings. If the posting says "market mapping"
  and the resume says "landscape reports", the search misses.
- Several vendors now add an LLM matching layer on top. Greenhouse markets
  an AI talent matching tool, and some postings disclose it. LLM screeners
  reward literal overlap too, and they also read for coherence.
- Most parsing failures come from layout, not wording. Tables, text boxes,
  multiple columns, and content inside headers or footers break parsers.
  Check the source file for these and tell the user if the layout is a risk.

Where the two goals conflict, placement resolves it. Put the posting's term
in the first half of the bullet and keep the rest of the sentence in the
person's own voice. That reads naturally to a human and still matches a
literal search.

## 6. The length constraint shapes the work

Equal line count means the rewrite trades words instead of adding them.
Every mirrored term costs one of the original words in the same bullet.
Expect one to three swapped phrases per bullet, not a rewrite. Bullets whose
last rendered line is nearly full can only take equal length swaps. The
inventory script reports this per bullet.
