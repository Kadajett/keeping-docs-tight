<!-- docs-loop: off -->

# The ban lists

## Contents

- [List 1: AI tells](#list-1-ai-tells) - openers, closers, sentence shapes,
  vocabulary, formatting
- [List 2: generic slop](#list-2-generic-slop) - long words, marketing
  adjectives, intensifiers, phrasal verbs, nominalizations, slow starts
- [List 3: your project's list](#list-3-your-projects-list) - the template, and
  where to put it

A word ban is the weakest tool here. It cut 3 percent on one model and 40
percent on another in the measurement in `SKILL.md`. The rules in that file do
the work. These lists catch what survives.

The fix is never a synonym. A sentence that needs a banned word hides its
mechanism. Say what the thing does.

---

## List 1: AI tells

These reveal the writer instead of the subject. A reader who has seen generated
documents recognizes them before reading the content.

### Openers that say nothing

Certainly. Of course. Absolutely. Great question. You are absolutely right.
Excellent point. I would be happy to. Let me explain. Let me break this down.
Let us dive in. Here is the thing. To be clear. First, the news. I want to
start by. Before we begin. It is important to note. It should be noted. It is
worth noting. Please note that. As mentioned above. As we discussed.

Delete the opener. Start with the fact.

### Closers that add nothing

I hope this helps. Let me know if you have questions. Feel free to reach out.
Would you like me to. Happy to elaborate. In conclusion. To summarize. In
summary. Ultimately. At the end of the day. All in all. In essence. The key
takeaway is. This is a great starting point.

End on the last real point.

### Sentence shapes

| Shape | Example | Instead |
|---|---|---|
| Contrast framing | It is not a bug, it is a race condition. | It is a race condition. |
| Not just X but Y | Not just faster but safer. | Faster and safer. |
| A is B rather than C | It is a design decision rather than a bug. | It is a design decision. |
| Counting before listing | Three things. Two corrections. | The list already says how many. |
| Verdict before fact | The good news is the tests pass. | The tests pass. |
| Scoring the reader | You did not mention the migration. | The migration runs first. |
| Location over state | Both sit in the Settled section. | Both are settled. |
| Hedged measurement | This may improve resolution somewhat. | 7 of 189 call sites resolve. |
| Templated audience | Whether you are a beginner or an expert. | Delete it. |
| Rule of three as cadence | clear, concise, and actionable | Say the one that is true. |
| Trailing dramatization | ...triggering a chain of events. | Delete the clause. |
| Staccato fragments | It was not. It could not be. | One sentence, stated. |
| Rhetorical question | So what does this mean? | State what it means. |

### Vocabulary

delve, showcase, underscore (verb), pivotal, realm, tapestry, beacon,
multifaceted, meticulous, intricate, leverage (verb), foster, robust, holistic,
nuanced, commendable, paramount, seamless, fast-paced, ever-evolving, landscape
(metaphorical), synergy, game-changer, paradigm shift, deep dive, unpack
(meaning explain), elevate (metaphorical), empower, harness (verb), journey
(metaphorical), cutting-edge, best-in-class, world-class, revolutionize,
supercharge, testament to, navigate the complexities, at its core, the beauty
of, think of it as, essentially, fundamentally.

### Formatting tells

- Emoji as tone decoration.
- A bulleted list where two sentences of prose would carry the argument.
- Bold-lead "Term: definition" walls that make every line look equally
  important.
- A heading that restates the question it answers.
- Signposting a short answer: "First... Second... Finally..." across three
  sentences.
- Bolding a phrase in most paragraphs, which makes the bolding mean nothing.

---

## List 2: generic slop

Bad in any prose, from any writer.

### Long word for short

| Wrote | Write |
|---|---|
| utilize, leverage | use |
| facilitate | help |
| ensure | make sure |
| prior to | before |
| subsequent to | after |
| regarding, concerning | about |
| obtain, acquire | get |
| demonstrate | show |
| commence, initiate | start |
| terminate | stop, end |
| additionally, furthermore, moreover | also |
| in order to | to |
| due to the fact that | because |
| in the event that | if |
| a variety of, numerous, myriad, plethora | several, or the number |
| aforementioned | this |
| whilst, amongst | while, among |
| comprehensive | say what it covers |

### Marketing adjectives

seamless, robust, powerful, cutting-edge, effortless, world-class,
next-generation, revolutionary, blazing, lightning-fast, elegant, delightful,
turnkey, best-in-class, state-of-the-art, game-changing, first-class,
battle-tested, enterprise-grade, unlock, unleash.

### Empty intensifiers

very, truly, incredibly, extremely, really, quite, rather, fairly, somewhat,
significantly (with no number), dramatically (with no number).

### Phrasal verbs

spin up, spin down, reach out, dive into, kick off, roll out, tear down, ramp
up, circle back, drill down, touch base, loop in.

Use the plain verb: start, stop, contact, read, build, remove, increase.

### Nominalizations

A nominalization is a verb wearing a noun costume. It drags a be-verb and two
prepositions along with it.

perform an analysis of, conduct a review of, provide a description of, make a
decision about, give consideration to, carry out an evaluation of, is a
demonstration of, is an indication of, has the ability to, is in agreement
with.

Free the verb: analyze, review, describe, decide, consider, evaluate,
demonstrate, indicate, can, agrees.

### Slow starts

There is. There are. It is. This is a. In order to. The fact that. What matters
is that.

---

## List 3: your project's list

Lists 1 and 2 apply to any repository. List 3 is yours: the words your team
read wrong once, the house style, and the terms that must never carry two
names.

Put the machine-readable half in `.docs-loop.json` at your repository root, so
the checkers enforce it and nobody edits a skill file:

```json
{
  "acronyms_ok": ["MCP", "GHSA", "TOON"],
  "terms": [
    ["stored graph", "symbol index"],
    ["axiom", "rule", "constraint"]
  ]
}
```

`acronyms_ok` stops `undefined_acronym` firing on names your readers know.
Every `terms` group is a set of words that mean one thing, and a page using two
of them gets a `synonym_drift` finding.

Write the prose half in a repo doc, not here. A good entry names the word and
the incident:

> **Banned: "unreachable".** A reader took it as "impossible forever". It meant
> "broken in the shipped binary". One word cost an exchange.

A word earns its ban by going wrong once. A list assembled from taste grows
without limit and nobody reads it.

<!-- docs-loop: on -->
