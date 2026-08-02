#!/usr/bin/env python3
"""Catch the rhetoric ste-lint.py cannot see.

ste-lint.py checks mechanics: sentence length, passive voice, banned words.
This checks the moves that are grammatically clean and still dishonest, the
ones that attach a judgment to a fact instead of stating the fact.

    python3 voice-lint.py FILE [FILE...]

Exit 1 if any file has a hit, so it can gate a commit.
Suppress a quoted example between <!-- voice-lint: off --> and <!-- ... on -->.
The <!-- docs-loop: --> marker works too. YAML frontmatter is skipped.
"""
import re, sys

RULES = [
    # State what the thing IS. Never negate a strawman first.
    ("contrast_frame", r"\bnot\s+(?:just|only|merely)\b|,\s*not\s+\w|\bit\s+is\s+not\s+\w+[,.]\s*it\s+is\b|\brather than\b"),
    # The list already says how many. Do not announce the count.
    ("count_first", r"\b(?:one|two|three|four|five|six|\d+)\s+(?:things|reasons|corrections|consequences|points|items|notes|failures|problems|changes|takeaways)\b"),
    # Do not label a result before the reader sees it.
    ("verdict_first", r"\b(?:the (?:good|bad) news|unfortunately|fortunately|importantly|notably|interestingly|the upshot|the headline|worth noting|the short version|the honest version)\b"),
    # The reader is not the subject of a fact about a file.
    ("reader_scoring", r"\byou\s+(?:did\s*n[o']t|missed|failed to|forgot|never|may not have|overlooked)\b|\bas you (?:know|noted|said)\b|\bunlike your\b"),
    # The docs are the subject, not the writer.
    ("self_narration", r"(?:^|(?<=[.!?]\s))\s*(?:I\s+(?:added|wrote|have|will|think|want|should|decided|noticed)|Let me|I'?m going to)\b"),
    # Say the state. Do not say where the state is filed.
    ("location_over_state", r"\b(?:sits?|lives?|resides?)\s+in\b|\bcan be found\b|\bis located\b"),
    # Announcing that you will speak is not speaking.
    ("preamble", r"\b(?:here'?s the thing|to be clear|let'?s (?:dive|break this down|unpack)|first the news|it is important to note|it should be noted)\b"),
    # End on the last real point.
    ("recap_ending", r"\b(?:in conclusion|to summarize|in essence|ultimately|at the end of the day|all in all)\b"),
    # Two or more negations in one parallel run. "Not demoted, not deferred,
    # not logged." The reader collects denials and never receives the fact.
    # Three negations in one breath is cadence. Two is a rules list, which is
    # legitimate content, so the third is what makes this fire.
    ("negative_parallelism",
     r"\b(?:not|never|no|neither|nor)\b[^.!?\n]{2,50}?[,;]\s*(?:and\s+|but\s+|or\s+)?"
     r"\b(?:not|never|no|nor)\b[^.!?\n]{2,50}?[,;]\s*(?:and\s+|but\s+|or\s+)?"
     r"\b(?:not|never|no|nor)\b"),
    # The writer certifies their own honesty. A fact needs no character
    # reference from the person stating it, and the certificate is a closing
    # remark that credits the writer instead of informing the reader.
    ("self_certifying",
     r"\b(?:and )?I (?:will not|won'?t|am not|'?m not|do not|don'?t)\s+"
     r"(?:pretend|claim|hide|sugar-?coat|gloss|dress)\b|"
     r"\bI(?:'?ll| will)?\s+(?:want|need|have|try|am going)?\s*to be\s+"
     r"(?:honest|blunt|frank|direct|straight|transparent|upfront)\b|"
     r"\b(?:let me be|being)\s+(?:honest|blunt|frank|direct|straight)\b|"
     r"\b(?:in all honesty|full transparency|no sugar-?coating|"
     r"the honest (?:version|answer|truth)|honestly speaking)\b|"
     r"\b(?:named|stated|reported|said)\s+rather than\s+"
     r"(?:hidden|hiding|buried|burying|glossed|pretending)\b|"
     r"\brather than\s+(?:hiding|glossing over|burying|pretending|"
     r"sugar-?coating|dressing)\b|"
     r"\b(?:honestly|candidly|frankly),|"
     # the discourse-marker form, which needs the comma: "I told him to be
     # honest" is a fact about someone, not a certificate about the writer
     r"\bto be (?:honest|blunt|frank|direct|straight)(?:\s+with you)?\s*,"),
    # Contrast built as structure rather than as one stated fact.
    ("contrast_construction",
     r"\b(?:instead of|as opposed to|in contrast to|far from|less .{2,20} than it is|"
     r"more .{2,20} than it is|what .{2,25} is not)\b|"
     r"\bwhile\s+[^,.\n]{5,40},\s*(?:it|they|this|that)\b"),
]

RULES = [(name, re.compile(pat, re.I | re.M)) for name, pat in RULES]

# A triple reads as cadence when it repeats. Three real list items do not, so
# this one is scored by density over the page and never per match.
TRIPLE = re.compile(
    r"\b(\w+(?:ly)?)\s*,\s*(\w+(?:ly)?)\s*,\s*and\s+(\w+(?:ly)?)\b", re.I)
TRIPLE_PER_1000W = 2.0


def rule_of_three(text, words):
    """Triples per 1000 words, and the triples themselves. Over the rate, they
    are cadence. Under it, they are a list."""
    hits = [m.group(0) for m in TRIPLE.finditer(text)]
    rate = 1000.0 * len(hits) / max(words, 1)
    return hits, rate


def strip_noise(text):
    """Blank out code and suppressed regions, keeping line numbers intact."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))

    text = re.sub(r"```.*?```", blank, text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", blank, text)
    text = re.sub(r"<!--\s*(?:voice-lint|docs-loop):\s*off\s*-->.*?"
                  r"<!--\s*(?:voice-lint|docs-loop):\s*on\s*-->",
                  blank, text, flags=re.S | re.I)
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
    return text


def lint(path):
    raw = open(path, encoding="utf-8").read()
    text = strip_noise(raw)
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-/]*", text)) or 1
    starts = [m.start() for m in re.finditer(r"\n", text)]

    hits = []
    for name, pat in RULES:
        for m in pat.finditer(text):
            line = sum(1 for s in starts if s < m.start()) + 1
            hits.append((line, name, m.group(0).strip()))
    hits.sort()

    triples, rate = rule_of_three(text, words)
    if rate > TRIPLE_PER_1000W and len(triples) >= 3:
        hits.append((0, "rule_of_three",
                     f"{len(triples)} triples, {rate:.1f} per 1000 words: "
                     + "; ".join(t.strip() for t in triples[:3])))
        hits.sort()

    for line, name, found in hits:
        print(f"  {line:>4}  {name:<21} {found}")
    print(f"{path:<32} words={words:>5} hits={len(hits):>3} "
          f"per100w={100.0 * len(hits) / words:6.2f}")
    return len(hits)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(1 if sum(lint(p) for p in sys.argv[1:]) else 0)
