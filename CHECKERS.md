# Why the checks exist

The scripts document themselves. Run one with no arguments to see its commands.
Read `CFG_DEFAULTS` in `docs-loop.py` for every setting, each with a comment.

```bash
python3 scripts/ste-lint.py FILE     # mechanics, stdlib only
python3 scripts/voice-lint.py FILE   # eleven AI tells, stdlib only
uv run   scripts/docs-loop.py        # its own command list
```

This page holds what a script cannot say about itself. Every check below earned
its place by something going wrong once, and the incident is the reason it has
the shape it has.

## Two checks score by volume

`negative_parallelism` needs three negations in one breath. At two it matched
20 times on one repository, and 17 of those were real prohibition lists. Two
negations is content. Three is cadence.

`rule_of_three` counts triples per 1000 words and fires only above the rate.
Three genuine list items are fine. Three parallel adjectives as cadence, page
after page, is a tell.

Both report a candidate. A check that cries wolf gets ignored.

## explains_after_pointing

The highest-yield judgment in this skill, made mechanical. A section that cites
a module doc or a contract and then keeps going is usually reproducing what it
cited.

Derived from one section that ran 996 words past its pointer. Cutting it to the
map and dropping the copy took 1,310 words to 396, and every rule it dropped
still exists where a gate enforces it. It went quiet after the cut and stayed
quiet on five other files.

## orphan_section and no_opening

Four sections moved out of an `AGENTS.md` into their own files, and nobody ran a
checker on the destinations. The two smallest scored 52 and 36 findings per 1000
words against 8 and 15 for pages written as pages.

A moved section arrives with no opening and a heading pitched for a different
parent. `orphan_section` catches one heading over real prose. `no_opening`
catches a heading arriving before the page grounds its subject.

## Phrase matching flattens newlines first

Documents hard-wrap, so `load bearing` split across a line break and escaped
every multi-word check in the tool. Every phrasal verb and compactable phrase
had the same hole.

## Generated regions are scored as absent

The gate refused a commit over em dashes inside a `bd setup` block. That block
regenerates, so the author cannot fix it, and a gate you cannot pass gets
bypassed. Name your own in `generated_regions` as `[open, close]` marker pairs.

## The ban list is enforced, not only written

`BANNED.md` once documented 28 words the checker never looked at, including
`load-bearing` and `delve`. The prose list was written by hand and the checker
arrays came from upstream. `scripts/check-banned-sync.py` fails when they drift.

Three words carry a parenthetical scope in that list, so each gets a context
pattern. A blanket ban would hit the underscore character, unpacking a tarball,
and landscape orientation. All three pass.

## gate, and why it ratchets

Every other command reports, and a report can go unread. One did: the checkers
flagged four moved files and nobody looked for three iterations.

`gate` scores only the staged markdown and exits non-zero when a file got worse
than its floor. The default mode is `ratchet`. A tree carrying a thousand
findings fails a zero gate on its first commit, gets `--no-verify`d, and
enforces nothing after that. A ratchet is always passable, and the count can
only fall.

Raise a floor with `gate --accept`, never silently.

## Suppressing a quoted example

Wrap it in `<!-- docs-loop: off -->` and `<!-- docs-loop: on -->`. The
`voice-lint` spelling works too, and both scripts honor both. YAML frontmatter
is skipped without a marker.

Use it for quoted examples and ban lists. A suppressed region holding real prose
defeats the checker.

## What a checker cannot do

It reads form. A hollow paragraph in clean prose passes every gate. A wrong
number passes every gate. Verify the claim yourself, then run the checker.
