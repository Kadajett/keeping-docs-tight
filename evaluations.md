# Evaluations

Three scenarios that test the gaps this skill exists to close. Run each against
a fresh agent, once with the skill loaded and once without, and compare.

No runner ships with this file. Read the expected behavior and score by hand,
or feed it to a judge model.

## Contents

- [Eval 1: revise one page](#eval-1-revise-one-page)
- [Eval 2: audit a tree](#eval-2-audit-a-tree)
- [Eval 3: strip the tells](#eval-3-strip-the-tells)
- [Baseline failures](#baseline-failures-without-the-skill)

## Eval 1: revise one page

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "This README is too long and nobody reads it. Cut it in half without losing information.",
  "files": ["test-files/bloated-readme.md"],
  "expected_behavior": [
    "Runs the reverse outline BEFORE editing any sentence",
    "Cuts or merges whole sections, and names which ones it cut and why",
    "Reports a before and after word count from a command it actually ran",
    "Runs a checker on the result and reports the score",
    "Leaves no em dash, no semicolon, and no sentence over 20 words",
    "Does not delete a claim it cannot verify: marks it [UNVERIFIED: ...] instead"
  ]
}
```

Catches: an agent that rewrites sentence one and never looks at the page shape.

## Eval 2: audit a tree

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "Our docs folder has grown to 80 files and half of it is probably wrong. Where do we start?",
  "files": ["test-files/example-repo/"],
  "expected_behavior": [
    "Runs docs-loop.py scan and quotes the real totals it printed",
    "Runs dupes and names specific duplicate pairs with file and line numbers",
    "Ranks the files and picks a starting file with a reason",
    "Reads the code to check at least one claim, rather than only reading docs",
    "Commits or names .docs-loop.json so the next session can run progress",
    "Does not rewrite anything before measuring"
  ]
}
```

Catches: an agent answering "start with the biggest file" from intuition. Also
an agent that shortens docs without checking whether they are true.

## Eval 3: strip the tells

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "Rewrite this changelog entry so it does not read like a model wrote it.",
  "files": ["test-files/model-written-changelog.md"],
  "expected_behavior": [
    "Names the specific tells it found, using the rule names from BANNED.md",
    "Removes contrast framing, counting before listing, and verdict-first phrasing",
    "Replaces a hedged measurement with the number, or a visible placeholder",
    "Runs voice-lint.py and reports zero hits",
    "Keeps every fact from the original",
    "Does not swap a banned word for a synonym"
  ]
}
```

Catches: an agent that swaps `leverage` for `utilize` and calls it done.

## Baseline failures without the skill

Measured before writing this skill, on real documents:

- A page revised sentence by sentence stayed the same length, because the
  agent never questioned whether a section belonged.
- Twelve documents described a tool surface that the code no longer had. No
  agent noticed, because none read the code.
- A hand-written duplicate-detection pass missed a paraphrased paragraph
  entirely. It needed a literal word-sequence match.
- Two identical audit runs reported different totals, because a set iterated in
  a different order. The delta read as a regression.

Each is a gap in this skill's coverage. Add an evaluation when you find another.
