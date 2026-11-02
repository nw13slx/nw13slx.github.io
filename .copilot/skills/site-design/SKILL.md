---
name: site-design
description: >-
  Edit, audit, or update the personal GitHub Pages site (one plain index.html),
  including adding new papers, code releases, or roles found on Google Scholar,
  ORCID, and GitHub.
  Use when the user says "site design", "github.io", "my website", "add my new
  paper to the site", "update my website from Scholar", "my repo is public", or "what's missing on my
  homepage". NOT for general web dev, and NOT for writing a paper abstract
  (use the paper skills).
---

The whole site is `index.html` (home timeline, `#research`) plus `avatar.jpg`.
Keep it as few lines as possible; it only has to read well on phone and laptop.
Read and follow `references/site-rules.md` for content and commit policy.

To add new entries, run the steps below in order. For any other edit, apply it
directly, then run Step 4 on every line you wrote and Step 6.

## →[lite] Step 1 — List works missing from the page

Run `python3 .copilot/skills/site-design/scripts/fetch_works.py` from the repo root.
It finds the newest work already linked on the page and lists only works from that
year on; older works stay off the list, because that part of the page is settled.
Tell the user the cutoff year and the ORCID coverage line it prints first.
The table lists Scholar and ORCID works, plus public GitHub repos the user owns,
opened pull requests in, or was active in during the last 90 days and that were
created from the cutoff year on (`source` = `github`), with an `on site` column; rows
marked **no** are the candidates. `other version` means the page already links a
preprint or journal twin, and `follow-up of X` means the title starts with an
artifact name the page already links; skip both. Each `url` is a best-effort DOI or arXiv match,
and Scholar cuts long author lists short; Step 3 checks both for the rows the user picks.

## →[lite] Step 2 — Let the user pick

Read and follow the "Skip trivial updates" section of `references/wording-rules.md`
to strike more rows, and tell the user in one line which rows you struck and why.
Ask the user with `ask_user` (multi-select; a numbered list if `ask_user` is not
available) which remaining **no** rows to add. Merge a preprint and its journal version into
one option and offer the DOI; they can have different titles, so pair rows by
author list. In the same form, ask
whether anything outside papers changed: role, affiliation, or a new research
theme. Add nothing the user did not pick, because the page is curated, not a
publication list.

## →[heavy] Step 3 — Draft each line

Leave every existing line's words and links as they are; a new work becomes a new
line, or a link appended to the end of an existing list. This keeps the settled
part of the page settled, and it means a cold read covers every change.

For each picked item, confirm the title and full author list with
`curl -s https://api.crossref.org/works/<doi>` or
`curl -s "https://export.arxiv.org/api/query?id_list=<id>"`, then read and follow
`references/wording-rules.md` to decide placement and wording.
For each item, write a table in your reply with one row per line:

- where it goes (quote the line it follows),
- the intended meaning in one plain sentence, taken from the user's own words; ask her for the one claim the line must carry instead of summarising the README or abstract,
- the exact HTML line, and its word count next to the page's range.

Steps 4 and 5 reuse this table. Skip `polish-informal` here: it is built for
messages, and the cold read in Step 4 does this job for one-line page text.

## →[heavy] Step 4 — Cold-read every line

Read and follow `references/cold-read.md`. Spawn one new agent per proposed
line, in parallel, and revise until the line passes the check there or three
rounds are spent. Use a new agent for every round, because a reader that has
seen the earlier draft is no longer cold.

## →[lite] Step 5 — Show the user, one line at a time

For each line, show the placement, the HTML, the plain-text render, the intended
meaning, and the final cold reader's paraphrase. Ask with `ask_user`: accept,
reword (free text), or drop. If the user supplies their own wording, use it as
written. If you change any word yourself, other than a cut the cold reader
suggested, return to Step 4 for that line.

## →[lite] Step 6 — Apply and check

1. Edit `index.html` with the accepted lines only.
2. Check every new or changed link with `curl -sIL -o /dev/null -w '%{http_code}' <url>`
   and report anything not 200. DOI and publisher sites often return 403 to curl,
   so check those by eye in a browser.
3. Show `git --no-pager diff index.html`.
4. Commit only when the user asks, then follow the commit section of `references/site-rules.md`.

## Gotchas

- ORCID's public record stops at 2020, so treat Scholar as the main source and ORCID as a cross-check.
- Scholar keeps year-less duplicate records of the same paper; the script drops those when a dated row shares the title stem, but check the remaining rows for duplicates by eye.
- Scholar sometimes returns a CAPTCHA instead of the profile; the script exits with a message. Ask the user to paste the Scholar list instead.
- Crossref answers 429 when hit quickly; the script retries, but a row with an empty `url` may still be a rate-limit miss, so look it up by hand.
- Crossref title search can return a supplementary-file DOI (`.s001`); the script skips those, but confirm every URL before it goes on the page.
- A preprint and its journal version can carry different titles (e.g. the Au surface reconstruction paper); match them by author list.
- The cutoff comes from arXiv IDs and Crossref dates of page links, so a recent arXiv link sets it even when the user thinks of that work as last year's; tell the user the year in Step 2.
- Drafts drift long and promotional (an early BioEmu2 line ran 16 words with "open-source foundation model"); the page's bullets run 4–7 words, so check the count before the cold read. Cutting too far fails as well: `BioEmu2: proteins, nucleic acids, ligands.` passed the cold read but missed the claim the user wanted (all-atom dynamics and Boltzmann distributions), because the intended meaning was the agent's, not hers.
- Cold readers always suggest a word to cut; treat `cut` as advice or the loop never ends.
- Cold readers still flag missing roles and comment on neighbouring links; ignore both, since the page omits roles on purpose and other lines are out of scope.
- If the user is away at Step 2, draft and cold-read every candidate, then save the edit as a patch outside the repo for review instead of editing `index.html`.
- A line under Catalysis needs a reaction or catalytic process in it; readers judge bare surface-structure work as off-heading.
- A repo released with squashed history may not list the user as a contributor; the script finds it through her pull requests and public events, but events reach back only 90 days, so ask the user about repos released earlier.
- Some works on the page (BioEmu, enhanced diffusion sampling) are not on the Scholar profile, so "not on Scholar" does not mean "remove from the page".
