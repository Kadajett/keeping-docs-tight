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
- [Eval 4: catch the false claims](#eval-4-catch-the-false-claims)
- [Eval 5: audit a tree](#eval-5-audit-a-tree)
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

## Eval 4: catch the false claims

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "Is docs/retry.md still accurate?",
  "files": ["test-files/accuracy-repo/"],
  "expected_behavior": [
    "Reads src/retry.go before answering",
    "Finds 'up to five times' against MaxAttempts = 3",
    "Finds 'every failure is retried, including a 4xx' against the 4xx branch that returns ErrClientError",
    "Finds 'set MaxAttempts to zero to disable' against a loop starting at 1, where zero disables nothing",
    "Finds 'backoff is linear' against sleep *= 2",
    "Finds 'retry.Run' against the exported function Do",
    "Does not report the page as fine because the checkers score it clean"
  ]
}
```

The most important evaluation here, and the one no checker can help with. The
page carries five contradictions with its own source and scores 1 finding at
13.9 per 1000 words, which reads as a nearly clean page.

## Eval 5: audit a tree

```json
{
  "skills": ["keeping-docs-tight"],
  "query": "Our docs have gotten away from us. Where do we start?",
  "files": ["test-files/long-tree/"],
  "expected_behavior": [
    "Runs scan and quotes real totals, then ranks",
    "Does not start with docs/deploy.md, which ranks worst at 107.1 per 1000 words on 28 words. A rate over a short page is noise",
    "Starts with docs/configuration.md, which carries the most actual work at 256 words and 39.1",
    "Notices it names src/config.rs as authoritative and then restates the reasoning",
    "Finds docs/postings.md and docs/data-model.md carry one fact in two wordings, reported at 85 percent",
    "Reads src/limits.rs and catches docs/batching.md claiming 1000 against MAX_BATCH = 500",
    "Notices docs/currency.md opens on a heading with nothing grounding it",
    "Does not treat docs/batching.md as healthy because it scores zero findings"
  ]
}
```

Nine pages ranking from 107.1 findings per 1000 words down to 0.0, so ranking
has something to rank. Three traps: the page that ranks worst is 28 words long
and its rate means nothing, the page that scores zero states a false limit, and
the duplicate is a paraphrase that only BM25 finds.

## Baselines

Measured 2026-08-02 on the fixtures as committed.

| Fixture | Words | Findings | Per 1000w | Voice hits |
|---|---|---|---|---|
| `bloated-readme.md` | 456 | 22 | 48.2 | 0 |
| `model-written-changelog.md` | 110 | 12 | 109.1 | 7 |
| `example-repo/` | 2 pages | 1 duplicate pair | | |
| `accuracy-repo/docs/retry.md` | 72 | 1 | 13.9 | 0 |
| `long-tree/` | 579 across 9 files | 21 | 36.3 | 1 |

The two rows above are the point. `retry.md` scores 13.9 and contradicts its
source five times. `long-tree/docs/batching.md` scores 0.0 and states a limit
of 1000 against a `MAX_BATCH` of 500.

Re-measure these after touching a fixture. An earlier version of this table
said 1,084 words and 101 findings for `long-tree/`, measured before a fixture
edit and never checked again. A fresh clone caught it.

A run that lowers these numbers while keeping every fact is a pass. A run that
lowers them by deleting a fact is a failure, and the checkers cannot tell the
difference. Read the output.

## What these do not cover

One gap, named here so nobody discovers it by surprise.

**No model matrix.** The skill has been exercised on one model. The authoring
guidance asks for Haiku, Sonnet, and Opus, because a skill that reads as
over-explained to one can read as too thin to another.

**No model matrix, and no way to build one from inside a session.** Running
these against Haiku, Sonnet, and Opus is a task for whoever owns the skill.
Load it, run eval 4 on each model, and compare how many of the five
contradictions each one finds.
