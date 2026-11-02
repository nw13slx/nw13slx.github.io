# Cold-read prompt

Send this to a brand-new `general-purpose` agent, one agent per proposed line. Fill the slots and send nothing else: no task history, no paper abstract, no intended meaning. The reader must see exactly what a site visitor sees.

```text
You are reading one line on a scientist's personal homepage. You know nothing else about her.
The page is deliberately terse: it never states authorship roles, venues, or citation counts,
so do not flag their absence. Lines are short on purpose; do not ask for more explanation. Use no tools and open no links; answer from the text alone.

Section heading: {heading, e.g. "ML force fields" or "2022 – Now, Researcher at Microsoft Research AI for Science"}
Line before it: {plain text of the previous list item, or of the previous sentence in a timeline paragraph; "none" if there is none}
The line: {proposed line as plain text, with each link written as [link text](url)}
Line after it: {plain text, or "none"}

Answer in JSON only, with these keys:
- "paraphrase": one sentence on what this line tells you about her work.
- "link_guess": for each link, what you expect to find when you click it.
- "fits_heading": true if the line belongs under this heading, false otherwise.
- "unclear": words or phrases you had to guess at, or that read oddly. Empty list if none.
- "cut": words you could delete with no loss of meaning. Empty list if none.
```

## Check the answer

1. Parse the JSON, stripping a code fence if there is one. If it does not parse or a key is missing, send the same prompt to a new agent once; if that fails too, show the raw reply to the user.
2. Never fix an `unclear` item by adding words when the line would end up longer than its neighbours (see the length range in `references/wording-rules.md`); move or cut instead. The line passes when `paraphrase` and `link_guess` match the intended meaning you wrote down (a reader would click for the right reason), `fits_heading` is true, and no `unclear` item is about this line and fixable by changing at most three words without adding a new term. Ignore items about other lines on the page. Treat `cut` as advice: take a cut only when the line still reads right without the word, and take it without another round.
3. If the line fails, revise it and cold-read the new version with another new agent. If `fits_heading` is false, move the line rather than reword it.
4. Stop after three rounds. Carry the version with the fewest fixable `unclear` items into Step 5, and list the other versions with their reader replies below it.
