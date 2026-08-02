# Composing in Simplified Technical English

How to write the sentence once you know what it should say. `SKILL.md` decides
what belongs on the page. This file decides how it reads.

## Contents

- [The rules](#the-ste-rules) - words, verbs, sentences, punctuation, structure
- [Modes](#the-ste-rules) - strict for procedures, flavored for everything else
- [Self-lint](#self-lint) - eight checks before you return any text
- [Why a system beats a word ban](#measured-effect)

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

