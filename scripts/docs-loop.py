#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["bm25s", "markdown-it-py"]
# ///
"""docs-loop.py - the stateful documentation cleanup loop.

Runs every check we have over a whole doc tree, keeps the results in a state
file, and reports what changed since the last run. It parses markdown, so it
knows a heading from a paragraph from a fenced code block, and it reads across
files, so it can find the same paragraph written twice in two places.

    docs-loop.py scan [PATH ...]     analyze, save a run, print the report
    docs-loop.py rank [-n N]         worst files first, from the saved run
    docs-loop.py outline FILE        reverse outline: what each paragraph does
    docs-loop.py fix FILE            every finding in one file, line by line
    docs-loop.py compare FILE FILE   two files head to head
    docs-loop.py dupes [PATH ...]    near-duplicate paragraphs across files
    docs-loop.py progress            this run against the previous one
    docs-loop.py budget PATH=N       set a word ceiling for one path
    docs-loop.py gate [FILE ...]     refuse a change that makes a file worse
    docs-loop.py gate --accept       record today's counts as the new floor
    docs-loop.py install-hook        wire gate into this repo's pre-commit

Checks, by category:

  structure    heading depth, paragraph length, multi-purpose paragraphs,
               hollow sections, throat clearing, mermaid count, code density
  redundancy   repeated phrases, near-duplicate paragraphs in and across
               files ranked by BM25, over-quotation
  precision    undefined acronyms, two names for one thing, terms used before
               the page grounds them
  conciseness  the paramedic method: prepositions, be-verbs, hidden actions,
               slow starts, long sentences
  voice        the eight rhetoric rules from voice-lint.py
  mechanics    the STE rules from ste-lint.py

State and configuration live in .docs-loop.json at the repository root. It
holds the last 20 runs, so the loop survives a new session, a merge, or a
revert. Every threshold, ignore glob, word budget, known acronym, and term
group lives there too. This file carries no project in it: run it in any
repository and it writes its own defaults.

    docs-loop.py budget total=30000 ignore='data/*'

Dependencies: none required, and better with two. Run it with `uv run` and the
inline metadata above installs them:

    uv run docs-loop.py scan          bm25s + markdown-it-py
    python3 docs-loop.py scan         whatever is already importable

Ranking falls back from bm25s (github.com/xhluca/bm25s, MIT) to SQLite FTS5
`bm25()` to a k-gram overlap. Parsing falls back from markdown-it-py to a regex
reader. Every path produces the same report, at different quality.
"""
import importlib.util as _il
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict, namedtuple
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {".git", "target", "node_modules", ".venv", "dist", "build", ".next"}
STATE_NAME = ".docs-loop.json"
MAX_RUNS = 20

# ---------------------------------------------------------------- sibling tools


def _load(name, filename):
    path = os.path.join(HERE, filename)
    if not os.path.exists(path):
        return None
    spec = _il.spec_from_file_location(name, path)
    mod = _il.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


STE = _load("ste_lint", "ste-lint.py")
VOICE = _load("voice_lint", "voice-lint.py")

# ------------------------------------------------------------------- parsing

Block = namedtuple("Block", "kind line text lang level")

FENCE = re.compile(r"^\s*(```+|~~~+)\s*(\w*)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
COMMENT_OPEN = re.compile(r"<!--")
COMMENT_CLOSE = re.compile(r"-->")


SUPPRESS = re.compile(
    r"<!--\s*(?:docs-loop|voice-lint):\s*off\s*-->.*?<!--\s*(?:docs-loop|voice-lint):\s*on\s*-->",
    re.S | re.I)


FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)

# Regions a tool writes and rewrites. Scoring them fails a commit over text the
# author cannot fix, and a gate you cannot pass gets bypassed. Configure more
# in .docs-loop.json under `generated_regions`, as [open, close] marker pairs.
GENERATED_DEFAULT = [
    ["<!-- BEGIN BEADS INTEGRATION", "<!-- END BEADS INTEGRATION"],
    ["<!-- BEGIN BEADS CODEX SETUP", "<!-- END BEADS CODEX SETUP"],
    ["<!-- GENERATED FILE", ""],
]
_GENERATED = list(GENERATED_DEFAULT)


def set_generated_regions(pairs):
    """Called from config() so a project can name its own generated blocks."""
    global _GENERATED
    _GENERATED = list(GENERATED_DEFAULT) + [p for p in pairs if p not in GENERATED_DEFAULT]


def desuppress(text):
    """Blank quoted examples, frontmatter, and machine-written regions."""
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    text = SUPPRESS.sub(blank, FRONTMATTER.sub(blank, text))
    for open_marker, close_marker in _GENERATED:
        if close_marker:
            pat = re.escape(open_marker) + r".*?" + re.escape(close_marker) + r"[^\n]*"
        else:
            pat = re.escape(open_marker) + r"[^\n]*"
        text = re.sub(pat, blank, text, flags=re.S)
    return text


CONTAINERS = {"blockquote": "quote", "bullet_list": "list", "ordered_list": "list",
              "table": "table"}

try:
    from markdown_it import MarkdownIt
    _MD = MarkdownIt("commonmark").enable("table")
except Exception:
    _MD = None


def parse(text):
    """Split markdown into typed blocks that remember their line number.

    Uses markdown-it-py when it is installed, because a CommonMark parser
    beats a regex at nested lists, setext headings, and indented code. Falls
    back to the regex reader so the tool still runs with no dependency.
    """
    text = desuppress(text)
    if _MD is None:
        return parse_regex(text)
    lines = text.split("\n")
    blocks, tokens, i = [], _MD.parse(text), 0
    while i < len(tokens):
        t = tokens[i]
        if t.level > 0:
            i += 1
            continue
        kind = CONTAINERS.get(t.type[:-5]) if t.type.endswith("_open") else None
        if kind:
            close, depth = t.type[:-5] + "_close", 0
            start = i
            while i < len(tokens):
                if tokens[i].type == t.type:
                    depth += 1
                elif tokens[i].type == close:
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            span = t.map or [0, 0]
            blocks.append(Block(kind, span[0] + 1, "\n".join(lines[span[0]:span[1]]), "", 0))
            i += 1
            continue
        if t.type == "heading_open":
            inline = tokens[i + 1] if i + 1 < len(tokens) else None
            blocks.append(Block("heading", (t.map or [0])[0] + 1,
                                (inline.content if inline else "").strip(), "",
                                int(t.tag[1])))
            i += 3
            continue
        if t.type == "paragraph_open":
            inline = tokens[i + 1] if i + 1 < len(tokens) else None
            span = t.map or [0, 0]
            blocks.append(Block("para", span[0] + 1,
                                "\n".join(lines[span[0]:span[1]]), "", 0))
            i += 3
            continue
        if t.type == "fence" or t.type == "code_block":
            span = t.map or [0, 0]
            blocks.append(Block("code", span[0] + 1, t.content,
                                (t.info or "").split()[0] if t.info else "", 0))
            i += 1
            continue
        if t.type == "html_block":
            span = t.map or [0, 0]
            blocks.append(Block("comment", span[0] + 1, t.content, "", 0))
            i += 1
            continue
        i += 1
    return blocks


def parse_regex(text):
    """The dependency-free reader. Same output shape as parse()."""
    lines = text.split("\n")
    blocks, i = [], 0
    while i < len(lines):
        raw, start = lines[i], i + 1
        fence = FENCE.match(raw)
        if fence:
            marker, lang, body = fence.group(1), fence.group(2), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(marker[:3]):
                body.append(lines[i])
                i += 1
            i += 1
            blocks.append(Block("code", start, "\n".join(body), lang or "", 0))
            continue
        if COMMENT_OPEN.search(raw):
            body = [raw]
            while i < len(lines) and not COMMENT_CLOSE.search(lines[i]):
                i += 1
                if i < len(lines):
                    body.append(lines[i])
            i += 1
            blocks.append(Block("comment", start, "\n".join(body), "", 0))
            continue
        head = HEADING.match(raw)
        if head:
            blocks.append(Block("heading", start, head.group(2).strip(), "", len(head.group(1))))
            i += 1
            continue
        if not raw.strip():
            i += 1
            continue
        kind = ("quote" if raw.lstrip().startswith(">")
                else "table" if raw.lstrip().startswith("|")
                else "list" if LIST_ITEM.match(raw)
                else "para")
        body = []
        while i < len(lines) and lines[i].strip() and not HEADING.match(lines[i]) \
                and not FENCE.match(lines[i]):
            body.append(lines[i])
            i += 1
        blocks.append(Block(kind, start, "\n".join(body), "", 0))
    return blocks


MASK_NUM = re.compile(r"(\d)\.(\d)")
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(`\"'\[])")


def sentences(text, per_line=False):
    """Split prose into sentences.

    A paragraph wraps across source lines, so join it first. A list wraps too,
    but each item is its own unit, so keep those apart.
    """
    text = MASK_NUM.sub(r"\1·\2", text)
    chunks = text.split("\n") if per_line else [re.sub(r"\s*\n\s*", " ", text)]
    out = []
    for chunk in chunks:
        chunk = LIST_ITEM.sub("", chunk).strip()
        if chunk:
            out += [s.replace("·", ".").strip() for s in SPLIT.split(chunk) if s.strip()]
    return out


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-/]*", text)


def strip_inline(text):
    return re.sub(r"`[^`\n]*`", " ", text)


# ------------------------------------------------------------- macro checks

# The text names an authority and keeps explaining. The copy drifts from the
# thing it copies, and the reader who needs that depth is one click away. This
# is judgment, not a rule, so it names a candidate rather than a violation.
POINTER = re.compile(
    r"\b(?:read (?:its|the|that) (?:module doc|docstring|source)|"
    r"its module doc (?:is|owns|carries)|documented in|"
    r"the (?:contract|authority|authoritative \w+) (?:is|lives|for)|"
    r"authoritative definition|see \[|defined in|owns the rule)\b", re.I)

PIVOTS = re.compile(
    r"\b(?:however|although|meanwhile|separately|in addition|also|conversely|"
    r"on the other hand|that said|by contrast)\b", re.I)
CONCRETE = re.compile(r"`|\d|\b[A-Z][a-z]{2,}\b")


def macro(blocks, findings, caps):
    """Structure, redundancy, and the shape of the page."""
    counts = Counter()
    section, section_words, section_code, first_para_of_section = None, 0, 0, True
    section_pointer_at = None
    quote_words = prose_words = 0
    mermaid = 0

    def close_section():
        if section and section_pointer_at is not None:
            after = section_words - section_pointer_at
            if after >= caps["explain_after_pointer_words"]:
                findings.append((section[0], "structure", "explains_after_pointing",
                                 f"{section[1]!r} names an authority then continues for "
                                 f"{after} words. Judge it: keep the pointer, cut what "
                                 f"repeats what it points at"))
                counts["explains_after_pointing"] += 1
        if section and section_words > caps["section_words"]:
            findings.append((section[0], "structure", "long_section",
                             f"{section[1]!r} runs {section_words} words, over the {caps['section_words']} word scene cap"))
            counts["long_section"] += 1
        if section and section_code > caps["code_blocks_per_section"]:
            findings.append((section[0], "structure", "code_density",
                             f"{section[1]!r} holds {section_code} fenced blocks, over the cap of {caps['code_blocks_per_section']}"))
            counts["code_density"] += 1

    for idx, b in enumerate(blocks):
        if b.kind == "heading":
            close_section()
            section, section_words, section_code, first_para_of_section = (b.line, b.text), 0, 0, True
            section_pointer_at = None
            if b.level > caps["heading_depth"]:
                findings.append((b.line, "structure", "deep_heading",
                                 f"level {b.level} heading {b.text!r}, deeper than {caps['heading_depth']}"))
                counts["deep_heading"] += 1
            nxt = blocks[idx + 1] if idx + 1 < len(blocks) else None
            if nxt and nxt.kind == "heading" and nxt.level > b.level:
                pass
            elif nxt and nxt.kind == "heading":
                findings.append((b.line, "structure", "hollow_section",
                                 f"{b.text!r} holds no prose before the next heading"))
                counts["hollow_section"] += 1
            continue

        if b.kind == "code":
            section_code += 1
            if b.lang == "mermaid":
                mermaid += 1
            continue

        if b.kind == "quote":
            quote_words += len(words(b.text))
            continue

        if b.kind not in ("para", "list"):
            continue

        text = strip_inline(b.text)
        n = len(words(text))
        prose_words += n
        if section_pointer_at is None and POINTER.search(b.text):
            section_pointer_at = section_words
        section_words += n
        sents = sentences(b.text, per_line=(b.kind == "list"))

        if b.kind == "para":
            if len(sents) > caps["paragraph_sentences"]:
                findings.append((b.line, "structure", "long_paragraph",
                                 f"{len(sents)} sentences, over the cap of {caps['paragraph_sentences']}"))
                counts["long_paragraph"] += 1
            pivots = len(PIVOTS.findall(text))
            if pivots >= 2 and len(sents) >= 3:
                findings.append((b.line, "structure", "multi_purpose",
                                 f"{pivots} pivot words in one paragraph, so it carries more than one point"))
                counts["multi_purpose"] += 1
            if first_para_of_section and n >= 25 and not CONCRETE.search(b.text):
                findings.append((b.line, "structure", "throat_clearing",
                                 "opening paragraph names no identifier, number, or proper noun"))
                counts["throat_clearing"] += 1
            first_para_of_section = False

    close_section()

    # A section that was moved into its own file is not yet a page. It arrives
    # with no opening, and its heading was pitched for a different parent. This
    # fired on docs/stored-graph.md and docs/surfaces.md, both one-section files
    # carved out of AGENTS.md, both worse per word than anything hand-written.
    h2s = [b for b in blocks if b.kind == "heading" and b.level == 2]
    # Everything before the first level-2 heading, not just the first block.
    # An opening can be a sentence, then a list, then a paragraph.
    opener_words = 0
    for b in blocks:
        if b.kind == "heading" and b.level == 2:
            break
        if b.kind in ("para", "list"):
            opener_words += len(words(strip_inline(b.text)))
    if len(h2s) <= 1 and prose_words >= 80:
        findings.append((h2s[0].line if h2s else 1, "structure", "orphan_section",
                         f"one section and {prose_words} words: a moved section, "
                         f"not yet a page. Grow it or fold it into a bigger page"))
        counts["orphan_section"] += 1
    elif h2s and opener_words < caps["page_opening_words"]:
        findings.append((h2s[0].line, "structure", "no_opening",
                         f"the first section starts after {opener_words} words. A page "
                         f"grounds its subject before its first heading"))
        counts["no_opening"] += 1

    if mermaid > caps["mermaid_per_page"]:
        findings.append((0, "structure", "mermaid_count",
                         f"{mermaid} mermaid diagrams, over the cap of "
                         f"{caps['mermaid_per_page']} per page"))
        counts["mermaid_count"] += mermaid - 1

    if prose_words and quote_words / prose_words > caps["quote_ratio"]:
        findings.append((0, "redundancy", "over_quotation",
                         f"quotes are {100 * quote_words // prose_words}% of prose, over "
                         f"{int(caps['quote_ratio'] * 100)}%"))
        counts["over_quotation"] += 1

    return counts, prose_words, mermaid


def repeated_phrases(prose, findings, n=5, floor=3):
    toks = [w.lower() for w in words(prose)]
    grams = Counter(" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1))
    hits = 0
    for gram, count in grams.most_common():
        if count < floor:
            break
        if len(set(gram.split())) < 4:
            continue
        findings.append((0, "redundancy", "repeated_phrase", f"{gram!r} appears {count} times"))
        hits += 1
        if hits >= 5:
            break
    return hits


# --------------------------------------------------------- precision checks

ACRO = re.compile(r"\b([A-Z]{2,6})\b")
CAPS_RUN = re.compile(r"\b[A-Z]{2,}\b(?:\s+\b[A-Z]{2,}\b)+")
ACRO_OK = {"CLI", "API", "MCP", "CI", "JSON", "TOML", "YAML", "URL", "HTTP", "HTTPS",
           "SQL", "AST", "IR", "OK", "ID", "UTC", "TODO", "FIXME", "AND", "OR", "NOT",
           "PR", "OSS", "STE", "GNU", "CPU", "RAM", "PATH", "HTML", "CSS", "SVG", "PDF",
           "AI", "ML", "OS", "IO", "UI", "UX", "DB", "CVE", "CPU", "GPU", "SDK", "IDE",
           "README", "MIT", "BSD", "GPL", "LICENSE", "UTF", "ASCII", "REST", "GRPC",
           "IN", "IS", "IT", "AS", "AT", "BE", "BY", "DO", "IF", "NO", "ON", "OF", "TO",
           "WE", "AN", "SO", "UP", "US"}


def precision(blocks, findings, terms_config, extra_acronyms=()):
    counts = Counter()
    prose_blocks = [b for b in blocks if b.kind in ("para", "list", "heading")]
    full = "\n".join(b.text for b in prose_blocks)

    ok = ACRO_OK | set(extra_acronyms)
    defined = set(re.findall(r"\(([A-Z]{2,6})\)", full))
    seen = set()
    for b in prose_blocks:
        text = strip_inline(b.text)
        # An all-caps run is emphasis, not an acronym. "TRIAGE IN PROGRESS".
        emphasis = set()
        for run in CAPS_RUN.findall(text):
            emphasis.update(run.split())
        text = re.sub(r"\b[A-Z]{2,}\.[a-z]{1,5}\b", " ", text)
        for acro in ACRO.findall(text):
            if acro in ok or acro in defined or acro in seen or acro in emphasis:
                continue
            # A word that also appears in lower case is emphasis. "FAILED" / "failed".
            if re.search(r"\b" + re.escape(acro.lower()) + r"\b", strip_inline(full)):
                continue
            seen.add(acro)
            findings.append((b.line, "precision", "undefined_acronym",
                             f"{acro} appears with no 'Full Name (ACRO)' anywhere in the file"))
            counts["undefined_acronym"] += 1

    low = full.lower()
    for group in terms_config:
        present = [t for t in group if re.search(r"\b" + re.escape(t.lower()) + r"\b", low)]
        if len(present) > 1:
            findings.append((0, "precision", "synonym_drift",
                             f"one thing named {len(present)} ways: {', '.join(present)}"))
            counts["synonym_drift"] += 1
    return counts


BOLD = re.compile(r"\*\*([^*\n]{3,40})\*\*")
TICK = re.compile(r"`([A-Za-z_][A-Za-z0-9_.:]{2,40})`")
# A filename or a path names itself. It needs no grounding scene.
SELF_NAMING = re.compile(r"\.(?:md|rs|py|sh|toml|json|ya?ml|txt|lock|jsonl|tsx?|jsx?)$|/")


def grounding(blocks, findings, window, limit=8):
    """A scene may only lean on a concept an earlier scene landed."""
    counts = Counter()
    first_use, grounded = {}, {}
    for b in blocks:
        if b.kind in ("code", "comment"):
            continue
        for term in sorted({t.lower() for t in TICK.findall(b.text)}):
            first_use.setdefault(term, b.line)
        if b.kind == "heading":
            for term in sorted({t.lower() for t in TICK.findall(b.text)}):
                grounded.setdefault(term, b.line)
            continue
        if b.kind == "table":
            # The first cell of a row defines the row. A definition table grounds.
            for n, row in enumerate(b.text.split("\n")):
                cells = row.split("|")
                if len(cells) < 3:
                    continue
                for term in sorted({t.lower() for t in TICK.findall(cells[1])}):
                    grounded.setdefault(term, b.line + n)
            continue
        for term in sorted({t.lower() for t in BOLD.findall(b.text)}):
            grounded.setdefault(term, b.line)
        for m in re.finditer(r"`([A-Za-z_][A-Za-z0-9_.:]{2,40})`\s+(?:is|are|means|names|holds|reads)\b",
                             b.text):
            grounded.setdefault(m.group(1).lower(), b.line)

    body = "\n".join(b.text for b in blocks if b.kind not in ("code", "comment")).lower()
    reported = 0
    for term, use_line in sorted(first_use.items(), key=lambda kv: kv[1]):
        if reported >= limit:
            break
        if SELF_NAMING.search(term):
            continue
        uses = len(re.findall(r"`" + re.escape(term) + r"`", body))
        if uses < 3:
            continue
        g = grounded.get(term)
        if g is None:
            findings.append((use_line, "precision", "ungrounded_term",
                             f"`{term}` is used {uses} times and the page never lands it"))
            counts["ungrounded_term"] += 1
            reported += 1
        elif use_line < g - window:
            findings.append((use_line, "precision", "used_before_grounded",
                             f"`{term}` is used here and grounded later, at line {g}"))
            counts["used_before_grounded"] += 1
            reported += 1
    return counts


# ------------------------------------------------- conciseness: the paramedic

PREPS = ("of in about for onto into on at from with by over under through between "
         "among during before after against within without across behind beyond upon "
         "toward towards per via").split()
PREP_RE = re.compile(r"\b(?:" + "|".join(PREPS) + r")\b", re.I)
BE_RE = re.compile(r"\b(?:is|are|was|were|be|been|being)\b", re.I)
NOMINAL = re.compile(r"\b\w{4,}(?:tion|ment|ance|ence|ity|ness|sis)\b", re.I)
# "sentence" ends in -ence and hides no verb. Neither do these.
PLAIN_NOUNS = re.compile(
    r"\b(?:sentence|evidence|reference|difference|preference|experience|audience|"
    r"science|silence|licence|license|entity|city|community|quality|security|"
    r"priority|utility|ability|density|identity|parity|analysis|basis|thesis)\b", re.I)
HIDDEN_ACTION = re.compile(
    r"\b(?:is|are|was|were)\s+(?:a|an|the)\s+\w{4,}(?:tion|ment|ance|ence|ity|sis)\b", re.I)
VERBY_NOUN = re.compile(
    r"\b(?:perform|performs|performed|conduct|conducts|make|makes|made|provide|provides|"
    r"give|gives|carry out|carries out|undertake|undertakes)\s+(?:a|an|the)?\s*\w+"
    r"(?:tion|ment|ance|sis|ysis)\b", re.I)
# A phrase with a shorter exact equivalent. The left side means the right side
# and costs more words to say it.
COMPACTABLE = {
    "in order to": "to", "due to the fact that": "because",
    "in the event that": "if", "in view of the fact that": "because",
    "for the reason that": "because", "in spite of the fact that": "although",
    "despite the fact that": "although", "at this point in time": "now",
    "at the present time": "now", "in the near future": "soon",
    "for the purpose of": "to", "with regard to": "about",
    "with respect to": "about", "in relation to": "about",
    "has the ability to": "can", "have the ability to": "can",
    "is able to": "can", "are able to": "can",
    "take into consideration": "consider", "make a decision": "decide",
    "reach a conclusion": "conclude", "give consideration to": "consider",
    "a large number of": "many", "a small number of": "a few",
    "the majority of": "most", "a sufficient number of": "enough",
    "prior to": "before", "subsequent to": "after",
    "in close proximity to": "near", "by means of": "by",
    "during the course of": "during", "in the absence of": "without",
    "on a regular basis": "regularly", "in a timely manner": "promptly",
    "there is a need for": "needs", "it is possible that": "may",
    "in the process of": "", "of the fact that": "that",
    "as a consequence of": "because of", "in the majority of cases": "usually",
}
COMPACT_RE = re.compile(
    r"(?<![a-z])(" + "|".join(re.escape(k) for k in
                              sorted(COMPACTABLE, key=len, reverse=True)) + r")(?![a-z])",
    re.I)
CONTRACTION_RE = re.compile(r"\b\w+['\u2019](?:t|re|ve|ll|d|m)\b|"
                            r"\b(?:it|he|she|that|there|what|who|here|let|how|where)"
                            r"['\u2019]s\b", re.I)

SLOW_START = re.compile(
    r"^(?:There\s+(?:is|are|was|were)|It\s+is|This\s+is\s+a|In\s+order\s+to|"
    r"The\s+fact\s+that|What\s+.{3,30}\s+is\s+that)\b", re.I)


def compaction(blocks, findings):
    """Contractions against phrases that have a shorter exact form.

    Both are the same failure at different scales: the text is longer than the
    meaning. Reported together so the ratio is visible, because a page with no
    contractions and thirty long phrases is not the tidy page it looks like.
    """
    counts = Counter()
    text = "\n".join(strip_inline(b.text) for b in blocks
                      if b.kind in ("para", "list", "quote", "heading"))

    contractions = CONTRACTION_RE.findall(text)
    seen = Counter()
    for b in blocks:
        if b.kind not in ("para", "list", "quote", "heading"):
            continue
        for m in COMPACT_RE.finditer(strip_inline(b.text)):
            phrase = m.group(1).lower()
            seen[phrase] += 1
            findings.append((b.line, "conciseness", "compactable_phrase",
                             f"{m.group(1)!r} means {COMPACTABLE[phrase]!r}"
                             if COMPACTABLE[phrase] else
                             f"{m.group(1)!r} can be cut"))
    counts["compactable_phrase"] = sum(seen.values())
    counts["contraction"] = len(contractions)
    if contractions or seen:
        findings.append((0, "conciseness", "compaction_ratio",
                         f"{len(contractions)} contractions to expand, "
                         f"{sum(seen.values())} phrases to compact"))
    return counts


def paramedic(blocks, findings, caps):
    counts = Counter()
    total_sentences = be = 0
    for b in blocks:
        if b.kind not in ("para", "list", "quote"):
            continue
        for raw_s in sentences(b.text, per_line=(b.kind == "list")):
            s = strip_inline(raw_s)
            total_sentences += 1
            be += len(BE_RE.findall(s))
            n = len(words(s))
            preps = len(PREP_RE.findall(s))
            if preps >= caps["prepositions_per_sentence"]:
                findings.append((b.line, "conciseness", "preposition_chain",
                                 f"{preps} prepositions in one sentence: {s[:70]!r}"))
                counts["preposition_chain"] += 1
            hidden = HIDDEN_ACTION.search(s) or VERBY_NOUN.search(s)
            if hidden and not PLAIN_NOUNS.search(hidden.group(0)):
                findings.append((b.line, "conciseness", "hidden_action",
                                 f"the verb is buried in a noun: {s[:70]!r}"))
                counts["hidden_action"] += 1
            if SLOW_START.match(s):
                findings.append((b.line, "conciseness", "slow_start",
                                 f"the sentence starts with filler: {s[:70]!r}"))
                counts["slow_start"] += 1
            if n > caps["sentence_words"]:
                findings.append((b.line, "conciseness", "long_sentence",
                                 f"{n} words, over the cap of {caps['sentence_words']}: {s[:70]!r}"))
                counts["long_sentence"] += 1
    counts["be_verbs"] = 0
    if total_sentences and be / total_sentences > caps["be_verbs_per_sentence"]:
        findings.append((0, "conciseness", "be_verb_rate",
                         f"{be} be-verbs across {total_sentences} sentences, over "
                         f"{caps['be_verbs_per_sentence']} per sentence"))
        counts["be_verb_rate"] = 1
    return counts


# -------------------------------------------------------- voice and mechanics


def voice(path, findings):
    counts = Counter()
    if not VOICE:
        return counts
    raw = open(path, encoding="utf-8").read()
    text = VOICE.strip_noise(raw)
    starts = [m.start() for m in re.finditer(r"\n", text)]
    for name, pat in VOICE.RULES:
        for m in pat.finditer(text):
            line = sum(1 for s in starts if s < m.start()) + 1
            findings.append((line, "voice", name, m.group(0).strip()))
            counts[name] += 1
    return counts


def mechanics(path, findings):
    counts = Counter()
    if not STE:
        return counts
    r = STE.lint(desuppress(open(path, encoding="utf-8").read()))
    for name, n in r["violations"].items():
        if n and not name.startswith("long_sentence") and not name.startswith("long_paragraph"):
            counts[name] = n
            findings.append((0, "mechanics", name, f"{n} occurrences"))
    em = r["em_dash(slop-marker)"]
    if em:
        counts["em_dash"] = em
        findings.append((0, "mechanics", "em_dash", f"{em} em dashes, and the cap is 0"))
    return counts


# ------------------------------------------------------------ cross-file work


def shingles(text, k=5):
    """Word k-grams. The fallback similarity when SQLite has no FTS5."""
    toks = [w.lower() for w in words(text)]
    return {" ".join(toks[i:i + k]) for i in range(len(toks) - k + 1)}


try:
    import bm25s as _bm25s
except Exception:
    _bm25s = None


def _rank_bm25s(entries, threshold, top_k):
    """Rank every paragraph against every other with bm25s.

    Queries with the whole paragraph. BM25 already discounts common terms, so
    picking rare ones by hand is work the ranking function does better.
    """
    corpus = [e[2] for e in entries]
    tokens = _bm25s.tokenize(corpus, stopwords="en", show_progress=False)
    index = _bm25s.BM25()
    index.index(tokens, show_progress=False)
    hits, scores = index.retrieve(tokens, k=min(top_k + 1, len(corpus)),
                                  show_progress=False)

    seen, pairs = set(), []
    for i in range(len(corpus)):
        row = list(zip(hits[i], scores[i]))
        self_score = next((sc for d, sc in row if d == i), None)
        if not self_score or self_score <= 0:
            continue
        for j, score in row:
            j = int(j)
            if j == i:
                continue
            key = (min(i, j), max(i, j))
            if key in seen:
                continue
            ratio = float(score) / float(self_score)
            if ratio >= threshold:
                seen.add(key)
                pairs.append((round(ratio, 2), entries[i][:2], entries[j][:2],
                              re.sub(r"\s+", " ", entries[i][2])[:80]))
    return pairs


def _fts5_available():
    try:
        db = sqlite3.connect(":memory:")
        db.execute("CREATE VIRTUAL TABLE t USING fts5(body)")
        db.execute("SELECT bm25(t) FROM t WHERE t MATCH 'x'").fetchall()
        return True
    except sqlite3.OperationalError:
        return False


def ranker_name():
    """Which implementation will rank. Recorded in every run.

    The three rankers do not agree on totals, so a switch would read as a
    change in the docs. progress() says so instead of reporting a phantom.
    """
    if _bm25s is not None:
        return "bm25s"
    return "fts5" if _fts5_available() else "kgram"


def near_duplicates(paragraphs, threshold=0.55, min_words=25, top_k=6):
    """Paragraphs that say the same thing, ranked by BM25.

    BM25 weighs rare terms, so it finds a paragraph rewritten in other words. A
    k-gram overlap cannot, because it needs the literal word sequence. Saying
    one thing twice in two ways is the redundancy a doc audit exists to find.

    Three implementations, best first: bm25s, then SQLite FTS5 `bm25()`, then
    a k-gram overlap. None of the math is hand-rolled above the fallback.

    Returns (ratio, (path, line), (path, line), sample), ratio in 0..1 where
    1.0 means the match scored as well as the paragraph matching itself.
    """
    entries = [(p, ln, t) for p, ln, t in paragraphs if len(words(t)) >= min_words]
    if len(entries) < 2:
        return []
    if _bm25s is not None:
        pairs = _rank_bm25s(entries, threshold, top_k)
        pairs.sort(key=lambda p: (-p[0], p[1], p[2]))
        return pairs
    if not _fts5_available():
        return _near_duplicates_shingle(entries, threshold=0.45)

    db = sqlite3.connect(":memory:")
    db.execute("CREATE VIRTUAL TABLE p USING fts5(body, tokenize='porter unicode61')")
    db.executemany("INSERT INTO p(rowid, body) VALUES (?, ?)",
                   [(i + 1, e[2]) for i, e in enumerate(entries)])

    df, termsets = Counter(), []
    for _, _, text in entries:
        terms = {w.lower() for w in words(text) if len(w) > 3}
        termsets.append(terms)
        df.update(terms)

    seen, pairs = set(), []
    for i, terms in enumerate(termsets):
        # Query by this paragraph's rarest terms. A common word matches everything.
        query = sorted(terms, key=lambda w: (df[w], w))[:14]
        if len(query) < 4:
            continue
        match = " OR ".join('"%s"' % w.replace('"', "") for w in query)
        try:
            rows = db.execute(
                "SELECT rowid, bm25(p) FROM p WHERE p MATCH ? ORDER BY bm25(p), rowid LIMIT ?",
                (match, top_k + 1)).fetchall()
        except sqlite3.OperationalError:
            continue
        self_score = next((sc for rid, sc in rows if rid == i + 1), None)
        if not self_score:
            continue
        for rowid, score in rows:
            j = rowid - 1
            if j == i:
                continue
            key = (min(i, j), max(i, j))
            if key in seen:
                continue
            ratio = score / self_score
            if ratio >= threshold:
                seen.add(key)
                pairs.append((round(ratio, 2), entries[i][:2], entries[j][:2],
                              re.sub(r"\s+", " ", entries[i][2])[:80]))
    pairs.sort(reverse=True)
    return pairs


def _near_duplicates_shingle(entries, threshold=0.45):
    """Jaccard over word k-grams. Used only when FTS5 is missing."""
    scored = [(p, ln, t, shingles(t)) for p, ln, t in entries]
    index = defaultdict(list)
    for i, (_, _, _, sh) in enumerate(scored):
        for g in sh:
            index[g].append(i)
    shared = Counter()
    for bucket in index.values():
        if len(bucket) > 12:
            continue
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                shared[(bucket[a], bucket[b])] += 1
    pairs = []
    for (i, j), n in shared.items():
        if n < 3:
            continue
        si, sj = scored[i][3], scored[j][3]
        jac = len(si & sj) / len(si | sj)
        if jac >= threshold:
            pairs.append((round(jac, 2), scored[i][:2], scored[j][:2],
                          re.sub(r"\s+", " ", scored[i][2])[:80]))
    pairs.sort(reverse=True)
    return pairs


# ------------------------------------------------------------------ analysis

CATEGORIES = ["structure", "redundancy", "precision", "conciseness", "voice", "mechanics"]


def analyze(path, cfg):
    raw = open(path, encoding="utf-8").read()
    blocks = parse(raw)
    findings = []

    counts = Counter()
    caps = cfg["caps"]
    mac, prose_words, mermaid = macro(blocks, findings, caps)
    counts.update(mac)
    prose = "\n".join(strip_inline(b.text) for b in blocks if b.kind in ("para", "list"))
    counts["repeated_phrase"] = repeated_phrases(
        prose, findings, caps["repeated_phrase_len"], caps["repeated_phrase_floor"])
    counts.update(precision(blocks, findings, cfg["terms"], cfg["acronyms_ok"]))
    counts.update(grounding(blocks, findings, caps["ground_window"]))
    counts.update(paramedic(blocks, findings, caps))
    counts.update(compaction(blocks, findings))
    counts.update(voice(path, findings))
    counts.update(mechanics(path, findings))

    by_cat = Counter()
    for _, cat, _, _ in findings:
        by_cat[cat] += 1

    total_words = len(words(raw))
    return {
        "path": path,
        "words": total_words,
        "prose_words": prose_words,
        "blocks": len(blocks),
        "headings": sum(1 for b in blocks if b.kind == "heading"),
        "paragraphs": sum(1 for b in blocks if b.kind == "para"),
        "code_blocks": sum(1 for b in blocks if b.kind == "code"),
        "mermaid": mermaid,
        "findings": len(findings),
        "per1000w": round(1000.0 * len(findings) / max(total_words, 1), 1),
        "by_category": {c: by_cat.get(c, 0) for c in CATEGORIES},
        "counts": dict(counts),
        "_findings": findings,
        "_paragraphs": [(path, b.line, b.text) for b in blocks if b.kind == "para"],
    }


# --------------------------------------------------------------------- state


def repo_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return os.getcwd()


def state_path():
    return os.environ.get("DOCS_LOOP_STATE") or os.path.join(repo_root(), STATE_NAME)


CFG_DEFAULTS = {
    # Every threshold lives here. A project that wants different limits edits
    # .docs-loop.json and never edits this file.
    "caps": {
        "heading_depth": 3,          # deeper than this and the page has sub-sub-topics
        "section_words": 400,        # one scene, not a chapter
        "code_blocks_per_section": 2,
        "mermaid_per_page": 1,
        "paragraph_sentences": 6,
        "sentence_words": 20,
        "prepositions_per_sentence": 4,   # the paramedic method
        "be_verbs_per_sentence": 0.8,
        "quote_ratio": 0.15,         # quoted words over prose words
        "repeated_phrase_len": 5,
        "repeated_phrase_floor": 3,
        "duplicate_threshold": 0.55,  # BM25 score against a self-match
        "duplicate_min_words": 25,
        "ground_window": 6,          # a lead-in before a definition table is fine
        "page_opening_words": 25,    # what a page owes before its first heading
        "explain_after_pointer_words": 150,  # prose after naming an authority
    },
    # How `gate` behaves. A gate nobody can pass gets bypassed, and a bypassed
    # gate enforces nothing, so "ratchet" is the default: a file may not get
    # worse than its recorded floor, which is always achievable.
    "gate": {
        "mode": "ratchet",           # ratchet | hard | advisory
        "hard_rules": ["em_dash", "semicolon", "contraction"],
        "baseline": {},              # path -> findings, written by --accept
    },
    # Acronyms this project uses without spelling out. The built-in list holds
    # only names a general technical reader knows.
    # [open, close] marker pairs for text a tool writes. Scored as absent.
    "generated_regions": [],
    "acronyms_ok": [],
    # Groups where one thing must not carry two names. Empty until a project
    # names its own: [["stored graph", "symbol index"], ...]
    "terms": [],
    "ignore": [],
    "budgets": {},
    "total_budget": None,
}


def config(state):
    """State over defaults, one level deep, so a partial caps block still works."""
    cfg = {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
           for k, v in CFG_DEFAULTS.items()}
    for key, val in state.items():
        if key == "runs":
            continue
        if isinstance(val, dict) and isinstance(cfg.get(key), dict):
            cfg[key].update(val)
        elif val or val == 0:
            cfg[key] = val
    set_generated_regions(cfg.get("generated_regions") or [])
    return cfg


def load_state():
    p = state_path()
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {"version": 1, "runs": []}


def save_state(state):
    state["runs"] = state["runs"][-MAX_RUNS:]
    with open(state_path(), "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1, sort_keys=True)


def head_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return "unknown"


# ----------------------------------------------------------------- discovery


def shortpath(path, width):
    """Truncate from the left and SAY so, or a reader misreads the parent."""
    return path if len(path) <= width else "\u2026" + path[-(width - 1):]


def discover(paths, ignore=()):
    """Every markdown file under paths, minus symlinks and ignored globs.

    A symlink is skipped because CLAUDE.md points at AGENTS.md here. Counting
    both doubles the word total and reports a 100 percent duplicate that no
    edit can remove.
    """
    import fnmatch
    out = []
    for p in paths or ["."]:
        if os.path.isfile(p):
            out.append(p)
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
                       and not os.path.islink(os.path.join(root, d))]
            out += [os.path.join(root, f) for f in files
                    if f.endswith(".md") and not os.path.islink(os.path.join(root, f))]
    root = repo_root()
    rel = sorted({os.path.relpath(os.path.abspath(f), root) for f in out})
    return [f for f in rel if not any(fnmatch.fnmatch(f, g) for g in ignore)]


# ------------------------------------------------------------------ commands


def cmd_scan(argv):
    state = load_state()
    cfg = config(state)
    root = repo_root()
    cwd = os.getcwd()
    os.chdir(root)
    try:
        files = discover([os.path.relpath(os.path.abspath(os.path.join(cwd, a)), root)
                          for a in argv] if argv else None, cfg["ignore"])
        results, paragraphs = {}, []
        for f in files:
            try:
                r = analyze(f, cfg)
            except Exception as exc:
                print(f"  SKIP {f}: {exc}")
                continue
            paragraphs += r.pop("_paragraphs")
            results[f] = r

        dupes = near_duplicates(paragraphs, cfg["caps"]["duplicate_threshold"],
                                cfg["caps"]["duplicate_min_words"])
        for jac, (pa, la), (pb, lb), _ in dupes:
            for p, line in ((pa, la), (pb, lb)):
                results[p]["_findings"].append(
                    (line, "redundancy", "near_duplicate",
                     f"{int(jac * 100)}% overlap with {pb if p == pa else pa}:{lb if p == pa else la}"))
                results[p]["findings"] += 1
                results[p]["by_category"]["redundancy"] += 1

        totals = Counter()
        total_words = 0
        for r in results.values():
            total_words += r["words"]
            for c in CATEGORIES:
                totals[c] += r["by_category"][c]
            r["per1000w"] = round(1000.0 * r["findings"] / max(r["words"], 1), 1)

        run = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "commit": head_commit(),
            "ranker": ranker_name(),
            "files": {f: {k: v for k, v in r.items()
                          if not k.startswith("_") and k != "counts"}
                      for f, r in results.items()},
            "totals": {"files": len(results), "words": total_words,
                       "findings": sum(totals.values()), **dict(totals)},
        }
        state["runs"].append(run)
        save_state(state)
        report(run, state, dupes)
    finally:
        os.chdir(cwd)


def report(run, state, dupes=()):
    t = run["totals"]
    print(f"\n{t['files']} files   {t['words']:,} words   {t['findings']} findings"
          f"   {1000.0 * t['findings'] / max(t['words'], 1):.1f} per 1000 words")
    budget = config(state)["total_budget"]
    if budget:
        over = t["words"] - budget
        print(f"budget {budget:,} words   {'OVER by' if over > 0 else 'under by'} {abs(over):,}")
    print("\n" + "  ".join(f"{c}={t.get(c, 0)}" for c in CATEGORIES))

    rows = sorted(run["files"].items(), key=lambda kv: -kv[1]["findings"])[:15]
    print(f"\n{'file':<44}{'words':>7}{'find':>6}{'/1kw':>7}   worst category")
    for f, r in rows:
        worst = max(r["by_category"].items(), key=lambda kv: kv[1])
        print(f"{shortpath(f, 43):<44}{r['words']:>7}{r['findings']:>6}{r['per1000w']:>7.1f}"
              f"   {worst[0]} ({worst[1]})")

    budgets = config(state)["budgets"]
    over = [(f, r["words"], budgets[f]) for f, r in run["files"].items()
            if f in budgets and r["words"] > budgets[f]]
    if over:
        print("\nover a per-file ceiling:")
        for f, w, b in sorted(over, key=lambda x: x[2] - x[1]):
            print(f"  {f:<48}{w:>7} words, ceiling {b}")

    if dupes:
        print(f"\n{len(dupes)} near-duplicate paragraph pairs (top 5):")
        for jac, (pa, la), (pb, lb), sample in dupes[:5]:
            print(f"  {int(jac * 100):>3}%  {pa}:{la}  <->  {pb}:{lb}")
            print(f"        {sample}...")


def cmd_rank(argv):
    n = int(argv[argv.index("-n") + 1]) if "-n" in argv else 20
    state = load_state()
    if not state["runs"]:
        sys.exit("no run saved. run: docs-loop.py scan")
    run = state["runs"][-1]
    rows = sorted(run["files"].items(), key=lambda kv: -kv[1]["per1000w"])[:n]
    print(f"{'file':<48}{'words':>7}{'/1kw':>7}   " + " ".join(f"{c[:4]:>5}" for c in CATEGORIES))
    for f, r in rows:
        cats = " ".join(f"{r['by_category'][c]:>5}" for c in CATEGORIES)
        print(f"{shortpath(f, 47):<48}{r['words']:>7}{r['per1000w']:>7.1f}   {cats}")


def cmd_outline(argv):
    if not argv:
        sys.exit("usage: docs-loop.py outline FILE")
    path = argv[0]
    blocks = parse(open(path, encoding="utf-8").read())
    state = load_state()
    r = analyze(path, config(state))
    flagged = defaultdict(list)
    for line, cat, rule, _ in r["_findings"]:
        flagged[line].append(rule)

    print(f"\nreverse outline: {path}   {r['words']} words, "
          f"{r['headings']} headings, {r['paragraphs']} paragraphs\n")
    for b in blocks:
        if b.kind == "heading":
            print(f"\n{'  ' * (b.level - 1)}{'#' * b.level} {b.text}   [line {b.line}]")
        elif b.kind == "para":
            sents = sentences(b.text)
            purpose = re.sub(r"\s+", " ", sents[0])[:88] if sents else ""
            marks = ",".join(sorted(set(flagged.get(b.line, []))))
            print(f"      {b.line:>4}  ({len(sents)}s/{len(words(b.text)):>3}w) {purpose}"
                  + (f"\n              -> {marks}" if marks else ""))
        elif b.kind == "code":
            print(f"      {b.line:>4}  [code:{b.lang or 'text'}, {len(b.text.splitlines())} lines]")
        elif b.kind in ("table", "quote", "list"):
            print(f"      {b.line:>4}  [{b.kind}, {len(words(b.text))}w]")
    print("\nAsk of this outline: does the order make sense? Does any paragraph")
    print("carry two purposes? What is present that the reader does not need?")


def cmd_fix(argv):
    if not argv:
        sys.exit("usage: docs-loop.py fix FILE")
    path = argv[0]
    state = load_state()
    r = analyze(path, config(state))
    print(f"\n{path}   {r['words']} words   {r['findings']} findings   {r['per1000w']}/1kw")
    print("  " + "  ".join(f"{c}={r['by_category'][c]}" for c in CATEGORIES) + "\n")
    for line, cat, rule, detail in sorted(r["_findings"], key=lambda f: (f[0], f[1])):
        loc = f"{line:>5}" if line else "    -"
        print(f"{loc}  {cat:<12}{rule:<22}{detail}")


def cmd_compare(argv):
    if len(argv) < 2:
        sys.exit("usage: docs-loop.py compare FILE FILE [FILE ...]")
    state = load_state()
    rs = [analyze(p, config(state)) for p in argv]
    width = max(len(os.path.basename(r["path"])) for r in rs) + 2
    rows = [("words", "words"), ("prose_words", "prose words"), ("paragraphs", "paragraphs"),
            ("code_blocks", "code blocks"), ("mermaid", "mermaid"),
            ("findings", "findings"), ("per1000w", "per 1000 words")]
    print("\n" + f"{'metric':<16}" + "".join(f"{os.path.basename(r['path'])[:width - 2]:>{width}}"
                                             for r in rs))
    for key, label in rows:
        print(f"{label:<16}" + "".join(f"{r[key]:>{width}}" for r in rs))
    for c in CATEGORIES:
        print(f"{c:<16}" + "".join(f"{r['by_category'][c]:>{width}}" for r in rs))
    best = min(rs, key=lambda r: r["per1000w"])
    print(f"\ncleanest per word: {best['path']} at {best['per1000w']} findings per 1000 words")


def cmd_dupes(argv):
    state = load_state()
    cfg = config(state)
    root = repo_root()
    cwd = os.getcwd()
    os.chdir(root)
    try:
        files = discover([os.path.relpath(os.path.abspath(os.path.join(cwd, a)), root)
                          for a in argv] if argv else None, cfg["ignore"])
        paragraphs = []
        for f in files:
            for b in parse(open(f, encoding="utf-8").read()):
                if b.kind == "para":
                    paragraphs.append((f, b.line, b.text))
        pairs = near_duplicates(paragraphs)
        print(f"\n{len(pairs)} near-duplicate paragraph pairs across {len(files)} files\n")
        for jac, (pa, la), (pb, lb), sample in pairs:
            print(f"{int(jac * 100):>3}%  {pa}:{la}\n      {pb}:{lb}\n      {sample}...\n")
    finally:
        os.chdir(cwd)


def cmd_progress(argv):
    state = load_state()
    runs = state["runs"]
    if len(runs) < 2:
        sys.exit("need two runs. run: docs-loop.py scan")
    prev, cur = runs[-2], runs[-1]
    print(f"\n{prev['date']} ({prev['commit']})  ->  {cur['date']} ({cur['commit']})\n")
    if prev.get("ranker") != cur.get("ranker"):
        print(f"  ranker changed: {prev.get('ranker')} -> {cur.get('ranker')}. "
              f"Redundancy counts are not comparable across this line.\n")
    for key in ["files", "words", "findings"] + CATEGORIES:
        a, b = prev["totals"].get(key, 0), cur["totals"].get(key, 0)
        print(f"{key:<14}{a:>9,}{b:>9,}{b - a:>+9,}")
    gone = set(prev["files"]) - set(cur["files"])
    new = set(cur["files"]) - set(prev["files"])
    if gone:
        print(f"\nremoved ({len(gone)}): " + ", ".join(sorted(gone)[:10]))
    if new:
        print(f"\nadded ({len(new)}): " + ", ".join(sorted(new)[:10]))
    moved = [(f, cur["files"][f]["findings"] - prev["files"][f]["findings"])
             for f in set(prev["files"]) & set(cur["files"])
             if cur["files"][f]["findings"] != prev["files"][f]["findings"]]
    for f, d in sorted(moved, key=lambda x: x[1])[:10]:
        print(f"  {d:>+5}  {f}")


def changed_markdown():
    """Staged markdown, falling back to everything changed against HEAD."""
    for args in (["diff", "--cached", "--name-only", "--diff-filter=ACM"],
                 ["diff", "--name-only", "--diff-filter=ACM", "HEAD"]):
        out = subprocess.run(["git"] + args, capture_output=True, text=True)
        files = [f for f in out.stdout.split("\n") if f.endswith(".md")]
        if files:
            return [f for f in files if os.path.exists(f)]
    return []


def cmd_gate(argv):
    """Refuse a change that makes a file worse than its recorded floor."""
    state = load_state()
    cfg = config(state)
    gate = cfg["gate"]
    root = repo_root()
    cwd = os.getcwd()
    os.chdir(root)
    try:
        explicit = [a for a in argv if not a.startswith("-")]
        files = explicit or changed_markdown()
        files = [f for f in files if not any(
            __import__("fnmatch").fnmatch(f, g) for g in cfg["ignore"])]
        if not files:
            print("docs gate: no markdown staged")
            return 0

        floor = dict(gate.get("baseline") or {})
        if not floor and state["runs"]:
            floor = {p: r["findings"] for p, r in state["runs"][-1]["files"].items()}

        rows, hard, worse = [], [], []
        for f in files:
            r = analyze(f, cfg)
            counts = r["counts"]
            was = floor.get(f)
            rows.append((f, was, r["findings"]))
            for rule in gate["hard_rules"]:
                if counts.get(rule):
                    hard.append((f, rule, counts[rule]))
            if was is not None and r["findings"] > was:
                worse.append((f, was, r["findings"]))

        if "--accept" in argv:
            state.setdefault("gate", {})
            state["gate"] = dict(gate)
            state["gate"]["baseline"] = {f: n for f, _, n in rows} | floor | \
                {f: n for f, _, n in rows}
            save_state(state)
            print(f"docs gate: floor recorded for {len(rows)} files")
            return 0

        print(f"\ndocs gate: {len(rows)} file(s), mode={gate['mode']}")
        for f, was, now in rows:
            delta = "" if was is None else f"{was} -> {now}"
            mark = "  new" if was is None else ("  WORSE" if now > was else
                                               ("  ok" if now == was else f"  ok  -{was - now}"))
            print(f"  {f:<44}{delta:>12}{mark}")
        for f, rule, n in hard:
            print(f"  {rule:<14}{f}  x{n}  hard rule")

        if gate["mode"] == "advisory":
            print("\n(advisory; commit proceeds)")
            return 0
        if hard:
            print(f"\nREFUSED by a hard rule. Run: docs-loop.py fix {hard[0][0]}")
            return 1
        if gate["mode"] == "ratchet" and worse:
            print(f"\nREFUSED. A file you touched got worse.")
            print(f"Run: docs-loop.py fix {worse[0][0]}")
            print("Or accept the new floor deliberately: docs-loop.py gate --accept")
            return 1
        print("\nclean")
        return 0
    finally:
        os.chdir(cwd)


HOOK = """#!/usr/bin/env bash
# Written by `docs-loop.py install-hook`. Scores only the markdown you staged.
# Bypass with `git commit --no-verify`.
set -euo pipefail
exec {runner} {script} gate
"""


def cmd_install_hook(argv):
    root = repo_root()
    hooks = subprocess.run(["git", "config", "core.hooksPath"],
                           capture_output=True, text=True).stdout.strip()
    hook_dir = os.path.join(root, hooks) if hooks else os.path.join(
        subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True,
                       text=True).stdout.strip(), "hooks")
    os.makedirs(hook_dir, exist_ok=True)
    path = os.path.join(hook_dir, "pre-commit")
    script = os.path.abspath(__file__)
    runner = "uv run --quiet" if subprocess.run(
        ["which", "uv"], capture_output=True).returncode == 0 else "python3"
    body = HOOK.format(runner=runner, script=script)

    if os.path.exists(path):
        existing = open(path, encoding="utf-8").read()
        if script in existing:
            print(f"already installed: {path}")
            return 0
        print(f"a pre-commit hook already exists at {path}")
        print("Add this line to it yourself, so nothing of yours is lost:")
        print(f"  {runner} {script} gate")
        return 1
    open(path, "w", encoding="utf-8").write(body)
    os.chmod(path, 0o755)
    print(f"installed: {path}")
    return 0


def cmd_budget(argv):
    state = load_state()
    if not argv:
        cfg = config(state)
        print(json.dumps({k: v for k, v in cfg.items() if k != "runs"}, indent=1))
        return
    for arg in argv:
        key, _, val = arg.partition("=")
        if key == "total":
            state["total_budget"] = int(val)
        elif key == "ignore":
            state.setdefault("ignore", []).append(val)
        else:
            state.setdefault("budgets", {})[key] = int(val)
    save_state(state)
    print(f"saved to {state_path()}")


COMMANDS = {"scan": cmd_scan, "rank": cmd_rank, "outline": cmd_outline, "fix": cmd_fix,
            "compare": cmd_compare, "dupes": cmd_dupes, "progress": cmd_progress,
            "budget": cmd_budget, "gate": cmd_gate, "install-hook": cmd_install_hook}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]) or 0)
