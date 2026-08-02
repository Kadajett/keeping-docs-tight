# The checkers

Three scripts enforce the rules in `SKILL.md`. This page covers what each one
reads, every command, every configuration key, and the gate that makes a fix
non-optional.

## Contents

- [Install and run](#install-and-run) - dependencies, uv, fallbacks
- [ste-lint.py](#ste-lintpy) - mechanics, one file
- [voice-lint.py](#voice-lintpy) - AI tells, one file
- [docs-loop.py](#docs-looppy) - all six categories, the whole tree, stateful
- [The six categories](#the-six-categories) - what each one checks
- [Configuration](#configuration) - every key in .docs-loop.json
- [Suppressing a quoted example](#suppressing-a-quoted-example)
- [gate: making the fix non-optional](#gate-making-the-fix-non-optional)
- [What a checker cannot do](#what-a-checker-cannot-do)

## Install and run

| Script | Reads | Scope | Gate |
|---|---|---|---|
| `ste-lint.py` | mechanics | one file | `em_dash` 0, `per100w` under 1.5 |
| `voice-lint.py` | AI tells | one file | `hits` 0 |
| `docs-loop.py` | all six categories | the whole tree, stateful | nothing outside `mechanics` |

`ste-lint.py` and `voice-lint.py` need only the Python standard library.

`docs-loop.py` carries Python Enhancement Proposal (PEP) 723 inline script
metadata naming `bm25s` and `markdown-it-py`. Run it with `uv run` and both
install with no virtual environment to manage:

```bash
uv run scripts/docs-loop.py scan
```

Plain `python3 scripts/docs-loop.py scan` works too, at lower quality. Ranking
falls back from `bm25s` to SQLite FTS5 `bm25()` to a k-gram overlap. Parsing
falls back from `markdown-it-py` to a regex reader.

## ste-lint.py

Counts long sentences, semicolons, contractions, and passive voice. Also
`-ing` main verbs, nominalizations, phrasal verbs, banned words, marketing
adjectives, modal hedges, long paragraphs, and em dashes. Prints violations
per 100 words.

It cannot tell a quoted example from real usage. A page that quotes a ban list
scores high and is fine. Read that page through `docs-loop.py fix` instead,
which honors the suppression marker.

## voice-lint.py

Eleven rules for the sentence shapes in `BANNED.md` list 1:
`contrast_frame`, `count_first`, `verdict_first`, `reader_scoring`,
`self_narration`, `location_over_state`, `preamble`, `recap_ending`,
`contrast_construction`, `negative_parallelism`, `rule_of_three`.

Prints a line number, a rule name, and the exact text. Exits 1 on any hit, so
it gates a commit.

Two of the eleven are scored by volume. The shape they catch is legitimate when
it is rare.

<!-- voice-lint: off -->
`negative_parallelism` needs three negations in one breath. "Not demoted, not
deferred, and not logged" fires.
<!-- voice-lint: on --> A two-item prohibition list passes, since that
is content. On this repository the two-negation form matched 20 times and 17
were real rules lists.

`rule_of_three` counts triples per 1000 words and fires only above 2.0 with at
least three present. Three genuine list items are fine. Three parallel
adjectives used as cadence, page after page, is a tell.

## docs-loop.py

```bash
uv run scripts/docs-loop.py scan                 # analyze the tree, save a run
uv run scripts/docs-loop.py rank -n 20           # worst files first
uv run scripts/docs-loop.py outline FILE         # reverse outline, flags inline
uv run scripts/docs-loop.py fix FILE             # every finding in one file
uv run scripts/docs-loop.py compare A.md B.md    # files head to head
uv run scripts/docs-loop.py dupes                # near-duplicate paragraphs
uv run scripts/docs-loop.py progress             # this run against the last
uv run scripts/docs-loop.py budget total=30000   # set a ceiling or an ignore glob
```

`scan` walks every markdown file in the repository. It skips symlinks, hidden
directories, and the ignore globs. Pass explicit paths to narrow it.

## The six categories

| Category | Checks |
|---|---|
| `structure` | heading depth, paragraph length, a paragraph carrying more than one point, hollow sections, throat clearing, mermaid count, code density per section, orphan sections, missing openings |
| `redundancy` | repeated phrases, near-duplicate paragraphs in and across files, over-quotation |
| `precision` | undefined acronyms, one thing named two ways, a term used before the page lands it |
| `conciseness` | the paramedic method: preposition chains, buried verbs, slow starts, long sentences, be-verb rate, contractions, compactable phrases |
| `voice` | the eight rules from `voice-lint.py` |
| `mechanics` | the rules from `ste-lint.py` |

### When a section explains what it just pointed at

`explains_after_pointing` names a section that cites an authority (a module
doc, a contract, a definition) and then keeps going for more than
`explain_after_pointer_words`. It reports a candidate, not a violation, because
only a reader can tell background from a copy.

It reproduces the judgment that cut one section from 1,310 words to 396. Run
against that section before the cut, it named it at 996 words past the pointer,
and it went quiet after.

### When a moved section pretends to be a page

`orphan_section` fires on a file with one heading and real prose under it. That
shape is a section someone carved out of a larger file. It reads worse than
anything written as a page, because it opens mid-thought.

`no_opening` fires when the first heading arrives before `page_opening_words`
of prose. A page grounds its subject before its first section.

Both came from one incident. Four sections moved out of an `AGENTS.md` into
their own files, and nobody ran a checker on the destinations. The two smallest
scored 52 and 36 findings per 1000 words, against 8 and 15 for the two pages
written as pages.

### Contractions against compactable phrases

`compaction_ratio` reports both counts on one line. They are the same failure
at two scales: the text is longer than the meaning. A page with no contractions
and thirty long phrases still fails that test.

Phrase matching flattens newlines first. A hard-wrapped document splits a
two-word phrase across a line break, and `load\nbearing` escaped every check
until it did not.

`compactable_phrase` names each phrase and its shorter exact form, from a table
of 40: `in order to` means `to`, `due to the fact that` means `because`, `has
the ability to` means `can`.

## Configuration

`.docs-loop.json` at the repository root holds the last 20 runs and every
setting. Commit it. `progress` needs it after a new session, a merge, or a
revert.

The script names no project. Run it anywhere and it writes its own defaults.

| Key | Holds |
|---|---|
| `caps.heading_depth` | deepest allowed heading level, default 3 |
| `caps.section_words` | one scene, default 400 |
| `caps.code_blocks_per_section` | default 2 |
| `caps.mermaid_per_page` | default 1 |
| `caps.paragraph_sentences` | default 6 |
| `caps.sentence_words` | default 20 |
| `caps.prepositions_per_sentence` | default 4 |
| `caps.be_verbs_per_sentence` | default 0.8 |
| `caps.quote_ratio` | quoted words over prose words, default 0.15 |
| `caps.repeated_phrase_len` | n-gram length, default 5 |
| `caps.repeated_phrase_floor` | occurrences before it counts, default 3 |
| `caps.duplicate_threshold` | BM25 score against a self-match, default 0.55 |
| `caps.duplicate_min_words` | shortest paragraph compared, default 25 |
| `caps.ground_window` | lines allowed between first use and grounding, default 6 |
| `ignore` | glob patterns to skip |
| `budgets` | per-file word ceilings |
| `total_budget` | the whole tree's word ceiling |
| `acronyms_ok` | acronyms this project uses without spelling out |
| `terms` | groups where one thing must not carry two names |

### Which ranker ran

Every run records its ranker. The three do not agree on totals, so `progress`
prints a warning when it changed. A switch of invocation is not a change in the
docs.

## Suppressing a quoted example

A page that quotes a bad sentence on purpose wraps it in a marker. Open with
`<!-- docs-loop: off -->` and close with `<!-- docs-loop: on -->`. The
`voice-lint` spelling of the marker works the same way, and both scripts honor
both spellings. YAML frontmatter is skipped without a marker.

Use it for quoted examples and ban lists. A suppressed region holding real
prose defeats the checker.

## gate: making the fix non-optional

Every other command reports. A report can go unread, and one did: four sections
moved into new files, the checkers flagged them, and nobody looked for three
iterations.

`gate` scores only the markdown you staged and exits non-zero when a file got
worse than its floor.

```bash
uv run docs-loop.py gate              # score the staged markdown
uv run docs-loop.py gate FILE ...     # or name the files
uv run docs-loop.py gate --accept     # record today's counts as the new floor
uv run docs-loop.py install-hook      # write a pre-commit hook that calls it
```

| `gate.mode` | Refuses when |
|---|---|
| `ratchet` (default) | a staged file exceeds its floor, or trips a hard rule |
| `hard` | a staged file trips a hard rule |
| `advisory` | never. It prints and passes |

`gate.hard_rules` defaults to `em_dash`, `semicolon`, `contraction`: the rules
with a cap of zero, which no floor should ever forgive.

Text a tool writes is scored as absent. `generated_regions` in
`.docs-loop.json` takes `[open, close]` marker pairs, and the built-in list
covers the `bd setup` blocks and any file marked `<!-- GENERATED FILE`.
Scoring a machine-written region fails a commit over text the author cannot
fix, and a gate you cannot pass gets bypassed.

`gate.baseline` holds the floor. With none recorded, `gate` falls back to the
newest `scan`. Raise it deliberately with `--accept`, never silently.

`install-hook` respects `core.hooksPath` and refuses to overwrite a hook you
already have, printing the line to add instead.

## What a checker cannot do

It reads form. A hollow paragraph in clean prose passes every gate. A wrong
number passes every gate. Verify the claim yourself, then run the checker.
