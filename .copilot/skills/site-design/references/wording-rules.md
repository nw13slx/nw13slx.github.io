# Wording rules for a new line

The page is short, so every word on it carries weight. These rules come from the lines already in `index.html`; when a rule and the page disagree, follow the page and fix this file.

## Skip trivial updates

A visitor gains nothing from a new link to something the page already shows. Strike a row when it is:

- a new version, extension, or follow-up of an artifact already linked (MatterSim-MT when MatterSim is on the page), even under a new name;
- a dataset, benchmark, or application paper whose only news is the same model run on another system;
- an erratum, thesis chapter, workshop version, or conference abstract of a paper already linked;
- a paper where she is a middle author and that names no artifact people know by name.

Keep a row only when it adds a new artifact, a new result, or a new research theme to the page. A first public code release of a model she worked on counts as news, even when its paper is not out or an earlier version is already linked; link the repo.

## Where a work goes

Use the full author list you confirmed in Step 3. "Led" means first or last author, or the user says she led it.

| Kind of work | Timeline (top) | Research (bottom) |
|---|---|---|
| Led | Add a link to the paragraph of the role she held when she did the work, not when it was published. | Add a bullet under the matching `<h2>`. |
| Middle author on a named artifact (a model or code people know by name) | Add the name to the role's `Contributor to ...` or project list. | Add the name to a matching list, e.g. `Active learning: A, B, C.`; if no list fits, add a short bullet under the closest `<h2>`. |

Open a new `<h2>` only when no existing heading fits; ask the user for the heading word. When a work does not fit the table, say so in Step 5 and let the user place it.

## How a line reads

Measure the page first: `sed -E 's/<a href="[^"]*">([^<]*)<\/a>/[\1]/g; s/<[^>]+>//g' index.html | awk 'NF{print NF" | "$0}'`. Most bullets run 4–7 words and timeline lines 5–8; the longest bullet runs 15. Stay within the longest line under the same heading, because one long line makes the whole page read longer.

- Say what the work computes or shows, not only what it covers: `all-atom dynamics and Boltzmann distributions of proteins` says what BioEmu2 computes, while a bare `proteins, nucleic acids, ligands` reads like a feature list. Where it fits, use the mission line's terms (timescale, lengthscale, first principles).
- Write the shortest true version first, then add a word only when a cold reader misreads the line without it. Drop anything a visitor gets from the link or the heading: "open-source" for a GitHub link, "protein" under Protein, the model's full feature list.
- Leave out promotional or category words: foundation, state-of-the-art, novel, powerful, comprehensive, open-source. Name the thing and what it covers.
- Prefer joining the list shape (`Theme: <a>A</a>, <a>B</a>.`) or a bare list after a colon (`1D: dislocations in A, B.`) over a new descriptive clause.

- Link text is the artifact's short name (`MatterSim`, `NequIP`) or a two-to-four-word noun phrase for the result (`multitask collective variable learning`). Never the paper title.
- A research bullet is `<a>Name</a>: one clause on what it does or shows.` or `Theme: <a>A</a>, <a>B</a>.` Match the shape of the line it follows.
- A timeline line is a noun phrase with the links inside it, ending with a period. No verbs unless the neighbours use them.
- Leave out authorship words (first-authored, co-), venue names, citation counts, and "highly cited"; the link speaks for itself.
- Use `·` and `–` the way the page does; replace em dashes with a comma or a full stop.
- Write formulas with Unicode subscripts and superscripts (`CeO₂`, `10²⁵`).
- Link the published DOI (`https://doi.org/...`) when it exists, otherwise `https://arxiv.org/abs/<id>` without a version suffix.

## Leave old lines alone

Keep the words and links of every existing line as they are, including old arXiv links whose journal version has since appeared. The only change allowed on an existing line is a new link appended to the end of a list.

## HTML shape

Keep the minimal style already on the page: `<li>` without a closing tag, no classes, no new CSS, no new files. The last `<li>` of each list carries `</ul>`; when you append after it, move `</ul>` to the new line and count that as part of the same edit.
