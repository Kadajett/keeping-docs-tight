# Evaluations

Three scenarios, each with a fixture in `test-files/` that exists and a
baseline that was measured. Run each against a fresh agent, once with the skill
loaded and once without, and compare against the baseline.

No runner ships with this file. Read the expected behavior and score by hand,
or feed it to a judge model.

## Contents

- [Eval 1: revise one page](#eval-1-revise-one-page)
- [Eval 2: find the duplication](#eval-2-find-the-duplication)
- [Eval 3: strip the tells](#eval-3-strip-the-tells)
- [Baselines](#baselines)
- [What these do not cover](#what-these-do-not-cover)

## Eval 1: revise one page

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "This README is too long and nobody reads it. Cut it without losing anything a reader needs.",
  "files": ["test-files/bloated-readme.md"],
  "expected_behavior": [
    "Runs the reverse outline BEFORE editing any sentence",
    "Cuts the configuration section, which names config/schema.go as authoritative and then explains every field and default anyway",
    "Keeps the pointer to config/schema.go",
    "Reports a before and after word count from a command it ran",
    "Leaves no em dash, no semicolon, and no sentence over 20 words",
    "Does not delete the supported-platforms table, which a reader uses"
  ]
}
```

Catches an agent that rewrites sentence one and never looks at the page shape.
The fixture trips `explains_after_pointing` at 217 words past its pointer.

## Eval 2: find the duplication

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "Audit this docs folder. What should change?",
  "files": ["test-files/example-repo/"],
  "expected_behavior": [
    "Runs docs-loop.py and quotes real numbers from its output",
    "Finds that docs/architecture.md and docs/parser.md state the token definition twice",
    "Names which copy to keep and why, rather than editing both",
    "Notices architecture.md cites src/parser.go as the contract and then restates it",
    "Does not rewrite anything before measuring"
  ]
}
```

Catches an agent that answers from intuition. The two pages carry one fact in
two wordings, which a word-overlap check misses and BM25 finds.

**Known limitation.** `docs-loop.py` resolves the repository root through git,
so scanning this fixture from inside another repository scans that repository
instead. Copy `test-files/example-repo/` somewhere outside a git tree, or run
`git init` in it, before running eval 2.

## Eval 3: strip the tells

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "Rewrite this changelog entry so it does not read like a model wrote it.",
  "files": ["test-files/model-written-changelog.md"],
  "expected_behavior": [
    "Names the tells using the rule names from voice-lint.py",
    "Removes all seven: verdict_first twice, contrast_frame twice, reader_scoring, location_over_state, recap_ending",
    "Replaces 'may improve tail latency somewhat' with a number or a visible placeholder",
    "Runs voice-lint.py and reports zero hits",
    "Keeps every fact from the original, including the setting name and where it lives",
    "Does not swap a banned word for a synonym"
  ]
}
```

Catches an agent that swaps `leverage` for `utilize` and calls it done.

## Baselines

Measured 2026-08-02 on the fixtures as committed.

| Fixture | Words | Findings | Per 1000w | Voice hits |
|---|---|---|---|---|
| `bloated-readme.md` | 456 | 22 | 48.2 | 0 |
| `model-written-changelog.md` | 110 | 12 | 109.1 | 7 |
| `example-repo/` | 2 pages | 1 duplicate pair | | |

A run that lowers these numbers while keeping every fact is a pass. A run that
lowers them by deleting a fact is a failure, and the checkers cannot tell the
difference. Read the output.

## What these do not cover

Three gaps, named rather than hidden.

**No model matrix.** The skill has been exercised on one model. The authoring
guidance asks for Haiku, Sonnet, and Opus, because a skill that reads as
over-explained to one can read as too thin to another.

**No accuracy fixture.** The highest-value check in this skill is reading the
code before believing the page, and none of these three test it. That needs a
fixture with source and a document that contradicts it.

**No long-tree fixture.** `example-repo/` has two pages. The maintenance
workflow is built for a tree that outgrew one reader, and two pages does not
exercise ranking, budgets, or the gate.
