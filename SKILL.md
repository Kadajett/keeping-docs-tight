---
name: keeping-docs-tight
description: Writes and revises technical documentation in Simplified Technical English, and audits a whole doc tree for bloat, drift, and duplication. Use when writing or editing a README, AGENTS.md, runbook, CLI or API reference, error message, PR description, or changelog; when asked to tighten, shorten, or clarify prose; when a doc set has grown too large or gone stale; when checking whether docs still match the code; or when another skill needs the STE rules, the paramedic method, or the AI-tells list.
---

# Keeping docs tight

Two jobs.

- **Writing** a page a reader understands once, while doing something.
- **Keeping** a doc tree that way as a codebase outgrows one reader.

Three lenses order the work:

- **Clear**: the reader never works out what you meant.
- **Precise**: one name for one thing, and every number sourced.
- **Concise**: fewer words carry the same meaning.

Work top down. Cut a section before you polish a sentence in it. Polishing
prose you later delete is the most common way to waste a revision.

## Which workflow

- **Editing one page?** Run the [revision workflow](#revision-workflow).
- **Auditing a tree?** Run the [maintenance workflow](#maintenance-workflow).
- **Writing from scratch?** Read [the rules](#the-ste-rules) and
  [the tells](#the-tells), draft, then revise the draft.

## Revision workflow

Copy this checklist and check off items as you go:

```
- [ ] 1. Reverse outline the page
- [ ] 2. Cut and reorder at the section level
- [ ] 3. Fix build-up order
- [ ] 4. Run the paramedic method on every sentence
- [ ] 5. Run the checkers until they pass
```

### Step 1: Reverse outline

```bash
uv run scripts/docs-loop.py outline FILE
```

`outline` prints the heading tree. Under each heading it prints one line per
paragraph. Each line carries the line number, the counts, the paragraph's first
sentence, and any rule it trips.

### Step 2: Cut and reorder

Ask four questions of that outline, in order:

1. Does the order make sense?
2. What is here that the reader does not need? Cut it.
3. What does the reader need that is missing? Add it.
4. Which paragraph carries two purposes? Split it.

A paragraph has one purpose, one topic sentence, and its evidence. A paragraph
you cannot summarize in a few words is the paragraph to split.

Three shapes of waste hide at this level and nowhere else.

- **Restatement**: one idea written twice, often sections apart.
- **Throat clearing**: an opening paragraph where the writer got going and
  said nothing.
- **Over quotation**: a block quote doing work the writer owes the reader.

Move on when the outline holds only paragraphs you would defend.

### Step 3: Fix build-up order

A reader gains one ability at a time. A **scene** may only lean on a concept an
earlier scene landed. Landing a concept means the idea and its name arrive
together.

Fix what the reader walks in knowing. A scene grounds everything else before a
later scene uses it. A scene that needs an ungrounded concept has two moves.
Ground the concept first, or promote it to a prerequisite.

Demand too much up front and you shut readers out. Ground too much inside and
the opening drowns in definitions. That trade is the whole decision.

`docs-loop.py fix FILE` reports `used_before_grounded` and `ungrounded_term`.

### Step 4: The paramedic method

Seven moves, run on every sentence:

<!-- docs-loop: off -->

1. Circle the prepositions: of, in, for, on, at, from, with, by, into.
2. Box the be-verbs: is, are, was, were, be, been, being.
3. Ask where the action is.
4. Turn that action into a plain verb.
5. Move whoever does it into the subject.
6. Cut the slow start.
7. Cut the redundancy.

<!-- docs-loop: on -->

The action hides inside a noun. Find the noun, free the verb:

| Buried | Freed |
|---|---|
| This paragraph is a demonstration of the use of good style. | This paragraph shows good style. |
| We performed an analysis of the log. | We analyzed the log. |
| There is ample evidence for making changes. | The results support the change. |

Four prepositions in one sentence means a noun is doing a verb's job. `There
is`, `It is`, and `In order to` are slow starts with nothing behind them.

### Step 5: Run the checkers

```bash
uv run scripts/docs-loop.py fix FILE
```

Fix what it reports, then run it again. Repeat until it reports nothing outside
`mechanics`. If a finding is wrong, the checker has a bug or the config needs a
term. Fix that. Do not work around it.

## Maintenance workflow

For a tree that grew past what one person reads. Run it on a schedule, or
whenever the docs and the code disagree.

Copy this checklist:

```
- [ ] 1. Measure the tree
- [ ] 2. Set the budget
- [ ] 3. Find the duplication
- [ ] 4. Take the worst file
- [ ] 5. Verify every claim against the code
- [ ] 6. Re-measure and record
```

### Step 1: Measure

```bash
uv run scripts/docs-loop.py scan
```

Writes `.docs-loop.json` at the repository root and prints totals, the worst
files, and duplicate pairs. Commit that file. It holds the last 20 runs, so the
audit survives a new session, a merge, or a revert.

### Step 2: Set the budget

```bash
uv run scripts/docs-loop.py budget total=30000 ignore='vendor/*'
```

A doc tree with no ceiling grows. Pick a total, then per-file ceilings for the
pages that matter. `scan` reports every file over its ceiling.

### Step 3: Find the duplication

```bash
uv run scripts/docs-loop.py dupes
```

Ranks near-duplicate paragraphs by BM25, in and across files. BM25 weighs rare
terms, so it finds a paragraph rewritten in other words.

A large codebase holds most of its excess here. One fact gets explained in the
README, the architecture page, and the module doc. Each copy drifts.

Pick one home per fact. Delete the rest and link.

**A moved section is not a page.** A section cut from one file into another
arrives with no opening, and its heading was pitched for a different parent. Give it what a page owes before you move on: a sentence that
grounds the subject, a heading that reads standalone, and a run of the checkers
on the destination file.

Gate the destination. Cutting words out of a page improves that page's score
while the words land somewhere nobody measured. Run `docs-loop.py fix` on the
file you wrote INTO, every time.

### Step 4: Take the worst file

```bash
uv run scripts/docs-loop.py rank -n 20
```

Sorts by findings per 1000 words. Take the top file into the revision workflow.
Before deleting a page, find what links to it:

```bash
grep -rIl "the-page-name" --include='*.md' --include='*.py' . | grep -v vendor
```

Fix every inbound link in the same commit. A dead link costs more than a long
page.

### Step 5: Verify against the code

A doc audit that only reads docs makes them shorter and no truer. Read the code
behind every claim that names a symbol, a file, a flag, or a number. Confirm it
still exists.

Mark what you cannot confirm: `[UNVERIFIED: does --strict still gate on this?]`.

No checker can do this step. Stale claims are also why the docs went wrong.

### Step 6: Re-measure

```bash
uv run scripts/docs-loop.py scan
uv run scripts/docs-loop.py progress
```

`progress` prints this run against the last, by category, and names the files
that moved. Record the totals wherever the project tracks work.

## The STE rules

ASD-STE100 Simplified Technical English, a controlled language written for
aircraft maintenance manuals in 1986. It removes ambiguity by limiting words,
sentence length, and grammar. Compose in it. Do not write another way and sand
it down afterward.

**Words.** One name for one thing. The short common word: start, use, help,
make sure, before, after, about, get, show, also. One meaning per word: in this
text, `fall` means to move down and never means to decrease. American spelling.

**Verbs.** Active voice when the actor is known: "the parser reads the file".
A verb for an action: "analyze the log". One auxiliary at a time.

**Sentences.** One instruction per sentence. Instructions to 20 words,
descriptive sentences to 25. Write out every contraction. Use articles.

**Punctuation.** No semicolon, write two sentences. Prefer a comma, a colon, a
period, or parentheses over an em dash.

**Structure.** One topic per paragraph, six sentences at most. Steps go in a
numbered vertical list, one action each, imperative. Put a condition before its
command: "If the check fails, stop the run".

**Modes.** `strict` applies every rule and both length caps. Use it for
procedures, runbooks, safety text, error messages, and CLI reference.
`flavored` applies the sentence, paragraph, active-voice, and plain-verb rules,
and relaxes the word list so the text keeps range. Use it for READMEs, pull
request descriptions, briefs, and reports.

Default to flavored. Choose strict when a reader follows the text as a
procedure, or when a wrong reading costs something.

## The tells

A **tell** is a phrase that reveals the writer. The subject goes missing. Model
prose carries a known set. A reader who has seen a hundred generated documents
recognizes them before reading the content.

Six outrank the rest. Each attaches a judgment to a fact:

<!-- docs-loop: off -->

| Tell | Instead |
|---|---|
| Contrast framing: "not X, it is Y" | State what it is. |
| Counting first: "Three things." | The list already says how many. |
| Verdict first: "The good news is" | The reader decides. |
| Hedging a number: "may improve somewhat" | The number, or a visible placeholder. |
| Scoring the reader: "you did not mention" | The fact, with the reader out of it. |
| Location over state: "it sits in Settled" | "It is settled." |

<!-- docs-loop: on -->

[BANNED.md](BANNED.md) holds the full lists: AI tells, generic slop, and a
template for a project's own. Read it when editing prose that came from a
model. Read it when a checker reports `banned_word`, `marketing_adjective`, or
a `voice` rule.

The fix is never a synonym. A sentence reaching for a banned verb hides the
mechanism. Say what the thing does.

## The evidence rules

These survive both modes.

1. Never invent a specific. An unsourced number is worse than no number. Write
   a visible placeholder: `[EXACT NUMBER: p95 before the fix]`.
2. Give every measurable claim its provenance: the commit, and the run it was
   measured against.
3. Name inputs, outputs, and measured results exactly.
4. Keep every secret, token, private key, and line of customer source out of
   every document.

## The checkers

Three scripts in `scripts/`, each catching what the one before it cannot. Run
them with `uv run` and the inline script metadata installs their dependencies.
Plain `python3` runs them too, with fallbacks.

```bash
python3 scripts/ste-lint.py FILE     # mechanics  gate: em_dash 0, per100w < 1.5
python3 scripts/voice-lint.py FILE   # tells      gate: hits 0
uv run scripts/docs-loop.py fix FILE # all six    gate: nothing outside mechanics
uv run scripts/docs-loop.py scan     # the tree, stateful
```

`.docs-loop.json` at the repository root holds the state and every threshold. A
project tunes the checker there and never edits the script. Full command list,
the six categories, and the config keys: [CHECKERS.md](CHECKERS.md).

To quote a bad sentence on purpose, wrap it in a suppression marker. See
[CHECKERS.md](CHECKERS.md) for the exact syntax.

A checker reads form. A hollow paragraph in clean prose passes every gate, and
so does a wrong number. Verify the claim yourself, then run the checker.

## Self-lint

Run these before returning any text.

1. Does a sentence run longer than 20 words? Split it.
2. Is there a semicolon? Replace it with a period.
3. Is there an em dash? Replace it.
4. Is there a contraction? Expand it.
5. Is there passive voice with a known actor? Make it active.
6. Is there an "-ing" main verb, a nominalization, or a phrasal verb such as
   "spin up"? Replace it with a plain verb.
7. Is one thing named two ways? Pick one name.
8. Does a sentence carry a judgment about the fact next to it? Cut the
   judgment.

## When to reach for something else

This skill serves a reader who must understand the text exactly once, while
doing something. A reader who chose to read for interest wants voice, and STE
strips voice on purpose. Send blog posts, launch announcements, position
pieces, and anything with a byline to a skill built for published writing.

A postmortem splits. Write the timeline, the cause, and the fix here. Let a
published-writing skill own the framing around them.

## Measured effect

Six engineer-writing tasks, four conditions, scored by a heuristic linter at
violations per 100 words. Lower is cleaner.

| Condition | Claude Sonnet | GPT-5.5 |
|---|---|---|
| baseline | 4.36 | 3.54 |
| banned-words list | 4.21 (-3%) | 2.14 (-40%) |
| Orwell's six rules | 2.48 (-43%) | 1.69 (-52%) |
| the STE rules | 1.12 (-74%) | 1.76 (-50%) |

A writing system beats a word ban on both models. A word ban is unreliable: it
cut 3 percent on one model and 40 percent on the other. That is why this file
carries the rules and `BANNED.md` carries the lists.

Treat these as directional. The sample is six tasks on two models, scored by a
heuristic.

## Credits

ASD publishes ASD-STE100 free at https://asd-ste100.org and holds its
copyright. These rules are distilled from Issue 9. Do not paste it in full.

The STE rule set and `ste-lint.py` come from
https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop.
That repository declares no clear license, so treat the upstream wording as
borrowed, and not as owned.

`docs-loop.py` ranks duplicates with bm25s (https://github.com/xhluca/bm25s,
MIT) and parses with markdown-it-py.
