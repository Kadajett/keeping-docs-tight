import re, sys, json, glob, os

MARKETING = ["seamless","seamlessly","robust","powerful","cutting-edge","effortless","effortlessly",
    "world-class","next-generation","revolutionary","blazing","lightning-fast","elegant","delightful",
    "turnkey","best-in-class","state-of-the-art","game-changing","first-class","battle-tested",
    "enterprise-grade","supercharge","unlock","unleash","empower","empowers"]
# Kept in step with BANNED.md list 1 by scripts/check-banned-sync.py. A word
# documented as banned and not listed here is a word nobody checks.
HOUSE = ["delve","delves","delved","showcase","showcases","showcased","pivotal",
    "realm","realms","tapestry","beacon","multifaceted","meticulous","meticulously",
    "intricate","intricately","foster","fosters","fostering","holistic","nuanced",
    "commendable","paramount","fast-paced","ever-evolving","synergy","game-changer",
    "deep dive","elevate","elevates","elevating","empower","empowers","empowering",
    "harness","harnesses","harnessing","journey","journeys","cutting-edge",
    "best-in-class","world-class","revolutionize","revolutionizes","supercharge",
    "load-bearing","load bearing","testament to","navigate the complexities",
    "think of it as","the beauty of",
    "at its core","the beauty of","essentially","fundamentally","underscores",
    "underscoring","paradigm shift"]
BANNED = ["begin","begins","commence","commences","initiate","initiates","originate",
    "utilize","utilizes","utilizing","leverage","leverages","leveraging","facilitate","facilitates",
    "ensure","ensures","ensuring","prior to","subsequent to","obtain","obtains","acquire","acquires",
    "demonstrate","demonstrates","additionally","furthermore","moreover","comprehensive","comprehensively",
    "utilization","aforementioned","henceforth","therein","whilst","amongst","numerous","myriad","plethora",
    "in order to","a variety of","in the event that","due to the fact that","it is important to note"]
PHRASAL = ["spin up","spin down","reach out","dive into","dives into","diving into","kick off","kicks off",
    "roll out","rolls out","tear down","ramp up","circle back","drill down","spun up","reaching out"]
MODAL_HEDGE = ["it is important to note","it should be noted","it is worth noting","please note that",
    "as mentioned","as noted above"]
BE = r"(?:am|is|are|was|were|be|been|being)"
PP_IRREG = r"(?:done|made|sent|read|built|kept|held|set|put|run|written|shown|given|taken|found|got|gotten|seen|known|thrown|drawn)"

def flatten(t):
    """Collapse newlines so a phrase that wraps a line still matches."""
    return re.sub(r"[ \t]*\n[ \t]*", " ", t)


def strip_code(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    return t

def sentences(text):
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not s: continue
        s = re.sub(r"^\s*#{1,6}\s*", "", s)
        s = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", s)
        if not s: continue
        parts = re.split(r"(?<=[.!?:])\s+(?=[A-Z0-9\"'\-])", s)
        for p in parts:
            p = p.strip()
            if p: out.append(p)
    return out

def wc(s):
    return len([w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-/]*", s)])

def count_ci(text, phrases):
    n = 0; hits = []
    low = flatten(text).lower()
    for ph in phrases:
        for m in re.finditer(r"(?<![a-z])" + re.escape(ph) + r"(?![a-z])", low):
            n += 1; hits.append(ph)
    return n, hits

SCOPED = [
    ("underscore (verb)", r"\bunderscor(?:e|es|ed|ing)\s+(?:the|that|this|how|why|a\b)"),
    ("unpack (explain)",
     r"\bunpack(?:s|ing|ed)?\s+(?:this|that|it)\b|"
     r"\bunpack(?:s|ing|ed)?\s+the\s+(?:concept|idea|logic|reasoning|argument|"
     r"implication|implications|meaning|nuance|details|thinking)\b"),
    ("landscape (metaphorical)",
     r"\b(?:current|evolving|competitive|technology|technical|security|vendor|"
     r"market|regulatory|threat|business|digital|modern|shifting)\s+landscape\b|"
     r"\blandscape\s+of\s+(?:vendors|tools|options|solutions|providers|threats)\b"),
]
SCOPED = [(name, re.compile(pat, re.I)) for name, pat in SCOPED]


def count_scoped(text):
    text = flatten(text)
    n, hits = 0, []
    for name, pat in SCOPED:
        found = pat.findall(text)
        if found:
            n += len(found)
            hits.append(name)
    return n, hits


def lint(text):
    raw = text
    text = strip_code(text)
    sents = sentences(text)
    words = sum(wc(s) for s in sents) or 1
    v = {}
    longs = [(wc(s), s) for s in sents if wc(s) > 20]
    v["long_sentence(>20w)"] = len(longs)
    v["semicolon"] = text.count(";")
    v["contraction"] = (len(re.findall(r"\b\w+['’](?:t|re|ve|ll|d|m)\b", text))
        + len(re.findall(r"\b(?:it|he|she|that|there|what|who|here|let|how|where)['’]s\b", text, re.I)))
    v["passive_voice"] = len(re.findall(rf"\b{BE}\s+(?:\w+ed|{PP_IRREG})\b", text, re.I))
    v["ing_main_verb"] = len(re.findall(rf"\b{BE}\s+\w+ing\b", text, re.I))
    v["nominalization"] = len(re.findall(r"\b(?:perform(?:s|ed)?|conduct(?:s|ed)?|provide(?:s|d)?|carry out|carries out|make use of|makes use of)\b", text, re.I)) + len(re.findall(r"\b\w{4,}(?:tion|ment|ance|ence)\s+of\b", text, re.I))
    v["phrasal_verb"], _ = count_ci(text, PHRASAL)
    v["banned_word"], bh = count_ci(text, BANNED + HOUSE)
    sn, sh = count_scoped(text)
    v["banned_word"] += sn
    bh += sh
    v["marketing_adjective"], mh = count_ci(text, MARKETING)
    v["modal_hedge"], _ = count_ci(text, MODAL_HEDGE)
    paras = [p for p in re.split(r"\n\s*\n", raw) if p.strip()]
    v["long_paragraph(>6s)"] = sum(1 for p in paras if len(sentences(strip_code(p))) > 6)
    em = raw.count("—") + raw.count("–")
    total = sum(v.values())
    per100 = {k: round(x*100.0/words, 2) for k, x in v.items()}
    return {
        "words": words, "sentences": len(sents),
        "violations": v, "total": total,
        "total_per100w": round(total*100.0/words, 2),
        "em_dash(slop-marker)": em,
        "longest_sentence_words": (max(longs)[0] if longs else max((wc(s) for s in sents), default=0)),
        "sample_marketing": list(dict.fromkeys(mh))[:6],
        "sample_banned": list(dict.fromkeys(bh))[:6],
    }

if __name__ == "__main__":
    files = sys.argv[1:] or []
    if not files:
        print(json.dumps(lint(sys.stdin.read()), indent=2)); sys.exit(0)
    exp = []
    for f in files: exp += sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f]
    for f in exp:
        with open(f) as fh: r = lint(fh.read())
        print(f"{os.path.basename(f):32} words={r['words']:4d} total={r['total']:3d} per100w={r['total_per100w']:6.2f} em_dash={r['em_dash(slop-marker)']:2d}")
