---
name: keeping-docs-tight
description: Writes and revises technical documentation in Simplified Technical English, and audits a whole doc tree for bloat, drift, and duplication. Use when writing or editing a README, AGENTS.md, runbook, CLI or API reference, error message, PR description, or changelog; when asked to tighten, shorten, or clarify prose; when a doc set has grown too large or gone stale; when checking whether docs still match the code; or when another skill needs the STE rules, the paramedic method, or the AI-tells list.
---

# Keeping docs tight

Cut before you polish. A sentence you improve and then delete is a wasted
revision.

Of every paragraph, ask: **can I remove this and lose no concept?** While the
answer is yes, keep cutting. No page has a right length, and no word count is
the target.

Read the code before you believe the page. A document describing a bug that is
already fixed does more damage than a long one, because a reader acts on it.
Verify every claim that names a symbol, a file, a flag, or a number.

When the text names an authority and then explains it anyway, cut the
explanation and keep the pointer. The copy drifts from what it copies.

A score never tells you a page is done. The checkers read form. They cannot see
an over-explained idea or a false claim, and those are most of the work.

Gate the file you wrote INTO. Cutting words out of a page improves that page
while the words land somewhere nobody measured.

When you finish a page, go find the next one. A doc tree stays tight because
somebody keeps looking, and goes slack the moment nobody does.

## What to read next

| You are | Read |
|---|---|
| editing one page | the [revision workflow](#revision-workflow) below |
| auditing a tree | the [maintenance workflow](#maintenance-workflow) below |
| writing a sentence | [STE.md](STE.md). Compose in it. Sanding afterward does not work |
| editing prose a model wrote | [BANNED.md](BANNED.md) |
| running a checker | [CHECKERS.md](CHECKERS.md) |

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

### Step 2: Cut what the reader does not need

This is the step the checkers cannot help with, and the step that removes real
words. A page can score 8 findings per 1000 and still be twice as long as it
should be. Run these six tests before you touch a sentence.

**The pointer test.** The highest-yield test by a wide margin. Every rule it
drops still exists where a gate enforces it. `docs-loop.py fix` reports the
candidates as `explains_after_pointing`, so you do not have to spot them
yourself.

**The enforcement test.** Is the rule already held by a test, a type, a gate,
or a compiler error? Then the page says the rule exists and names what holds
it. It does not restate the rule. Prose restating an enforced rule will one day
contradict it, and the reader believes the prose.

**The decision test.** A guide serves someone about to do a thing. Write down
the decisions they have to make. Every paragraph that helps none of them is
background, and background belongs somewhere a reader chooses to go.

**The incident test.** Was this written the day a bug was found? That prose
carries the whole investigation. The lesson is one or two sentences. The
investigation belongs in the commit message and in the test that holds it now.

**The topic count.** Name what the section is about in one sentence. If you
cannot, it is not a section, it is a pile. Split it into sections or reduce it
to a map: a table of the things and where each one lives.

**The earned-words test.** Would a reader use every line? A 16-row checklist of
every place a new language must appear earns 250 words, because someone works
down it. Eight paragraphs of what changed in which iteration earn none, because
git holds that already.

Then the shape questions:

1. Does the order make sense?
2. What does the reader need that is missing? Add it.
3. Which paragraph carries two purposes? Split it.

A paragraph has one purpose, one topic sentence, and its evidence. A paragraph
you cannot summarize in a few words is the paragraph to split.

Three shapes of waste hide at this level and nowhere else.

- **Restatement**: one idea written twice, often sections apart.
- **Throat clearing**: an opening paragraph where the writer got going and
  said nothing.
- **Over quotation**: a block quote doing work the writer owes the reader.

Move on when every remaining paragraph carries an idea the reader needs, and
nothing else does.

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

### Do I need this anecdote?

Ask this at each sentence, in the same pass. No script asks it for you.

An anecdote is a sentence about the writing. It carries the number a past
revision produced, or the other tool that proved the idea somewhere else. Ask
who acts on it. Nobody does. Cut the anecdote and keep the rule.

- **A number the reader never uses.** Keep a number the reader compares
  against or types. A number that only says the method worked once is
  decoration.
- **Another project as proof.** What held in another library proves nothing
  here, and the reader cannot check it. State the rule and let it stand.

A skill file has the least room of all. An agent reads it, spends context on
every word, and needs no story to follow a rule. An anecdote in a skill file
costs tokens and persuades nobody.

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

### Step 0: Find the docs

No two projects put their docs in the same place. Before measuring, look:

| Layout | Where |
|---|---|
| plain repo | `docs/`, `documentation/`, and markdown at the root |
| Docusaurus, Nextra | `website/docs/`, `.mdx` |
| Hugo, Astro, Eleventy | `content/` |
| Next.js, Storybook | `src/pages/`, `*.stories.mdx` |
| decision records | `adr/`, `decisions/`, `rfcs/` |
| monorepo | a `README.md` per package |
| project rules | `.github/`, `AGENTS.md`, `CLAUDE.md` |
| beside the code | rustdoc, docstrings, jsdoc |

`scan` walks the whole tree and takes `.md`, `.mdx`, `.markdown`, and `.mdown`.
It skips hidden directories, so `.github/` needs naming. Three settings in
`.docs-loop.json` handle the rest:

```json
{
  "extensions": [".md", ".mdx", ".rst"],
  "include_hidden": [".github"],
  "skip_dirs": ["generated", "i18n"]
}
```

Source-comment docs are out of scope here. Generate them, then run this on the
output.

### Step 1: Measure

```bash
uv run scripts/docs-loop.py scan
```

Writes `.docs-loop.json` at the repository root and prints totals, the worst
files, and duplicate pairs. Commit that file. It holds the last 20 runs, so the
audit survives a new session, a merge, or a revert.

### Step 2: Decide what pressure you want

A word budget is optional and blunt. It says a page is long. It never says
which words to cut. Set one only when a tree has outgrown anyone's attention
and you want a number to argue with:

```bash
uv run scripts/docs-loop.py budget total=30000 ignore='vendor/*'
```

Treat every ceiling as a question. When a page lands over one and each
remaining word is earned, raise the ceiling and record why. Cutting a fact to
reach a number chosen before anyone read the page is the failure this skill
exists to prevent.

`gate` is the pressure that works, and it needs no number: a file may not get
worse than it was. See [CHECKERS.md](CHECKERS.md).

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

## How much to trust yourself

Match your caution to what breaks.

**Judgment, no script.** Whether an idea is over-explained. Whether a claim is
still true. Whether a page earns its length. Whether an anecdote serves any
reader. No checker sees these, and guessing is the job.

**Judgment, then a script confirms.** Whether a section repeats what it points
at, whether two pages say one thing, whether a page opens. Reach for the
finding, then decide. The checker names candidates and you rule.

**Script, no judgment.** Em dashes, semicolons, contractions, and the ratchet.
These have one right answer, and the gate holds it. Do not argue with them,
and do not raise a floor to avoid one.

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
uv run scripts/docs-loop.py gate     # refuse a change that made a file worse
```

`gate` is the one that survives a forgetful agent. The other three report, and a
report can go unread. `gate` scores only the markdown you staged, compares each
file against its recorded floor, and exits non-zero when one got worse. Wire it
into a commit hook and the step stops being optional:

```bash
uv run scripts/docs-loop.py install-hook   # writes a pre-commit hook
uv run scripts/docs-loop.py gate --accept  # record today's counts as the floor
```

Three modes in `.docs-loop.json` under `gate.mode`. `ratchet` is the default: a
file may not exceed its floor, which is always achievable, so nobody disables
it. `hard` blocks only on em dashes, semicolons and contractions. `advisory`
prints and always passes.

A gate nobody can pass gets bypassed, and a bypassed gate enforces nothing. That
is why the default is a ratchet and not zero.

`.docs-loop.json` at the repository root holds the state and every threshold. A
project tunes the checker there and never edits the script. Full command list,
the six categories, and the config keys: [CHECKERS.md](CHECKERS.md).

To quote a bad sentence on purpose, wrap it in a suppression marker. See
[CHECKERS.md](CHECKERS.md) for the exact syntax.

A checker reads form. A hollow paragraph in clean prose passes every gate, and
so does a wrong number. Verify the claim yourself, then run the checker.

## When to reach for something else

This skill serves a reader who must understand the text exactly once, while
doing something. A reader who chose to read for interest wants voice, and STE
strips voice on purpose. Send blog posts, launch announcements, position
pieces, and anything with a byline to a skill built for published writing.

A postmortem splits. Write the timeline, the cause, and the fix here. Let a
published-writing skill own the framing around them.

## Credits

ASD publishes ASD-STE100 free at https://asd-ste100.org and holds its
copyright. These rules are distilled from Issue 9. Do not paste it in full.

The STE rule set and `ste-lint.py` come from
https://github.com/woosal1337/blog/tree/main/videos/ep01-the-cure-for-ai-slop.
That repository declares no clear license, so treat the upstream wording as
borrowed, and not as owned.

`docs-loop.py` ranks duplicates with bm25s (https://github.com/xhluca/bm25s,
MIT) and parses with markdown-it-py.
