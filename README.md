# keeping-docs-tight

An [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview).
It writes technical documentation a reader understands once. It keeps a large
doc tree that way.

Two jobs:

- **Writing.** Simplified Technical English (ASD-STE100), the paramedic method,
  and a list of the phrases that make prose read like a model wrote it.
- **Keeping.** A stateful checker that scores a whole doc tree across six
  categories, finds paragraphs that say one thing twice, and reports what moved
  since the last run.

## Install

```bash
git clone https://github.com/Kadajett/keeping-docs-tight \
  ~/.claude/skills/keeping-docs-tight
```

Claude Code loads it from there. For other agents, point them at `SKILL.md`.

## The checkers on their own

The three scripts work with no agent involved.

```bash
python3 scripts/ste-lint.py   FILE   # sentence length, passive voice, banned words
python3 scripts/voice-lint.py FILE   # the eight AI tells
uv run   scripts/docs-loop.py scan   # the whole tree, stateful
```

`ste-lint.py` and `voice-lint.py` need only the Python standard library.
`docs-loop.py` carries Python Enhancement Proposal (PEP) 723 inline metadata,
so `uv run` installs `bm25s` and `markdown-it-py` for it. Plain `python3` runs it too, with fallbacks.

`.docs-loop.json` at your repository root holds every threshold. The scripts
name no project.

## Layout

```
SKILL.md         what to do, then the two workflows
STE.md           how to write the sentence
BANNED.md        three ban lists, and where your project's list goes
CHECKERS.md      every command, every category, every config key
evaluations.md   three scenarios, with fixtures in test-files/
scripts/         the three checkers
```

## Credits

See the Credits section in `SKILL.md`.

## License

MIT for everything in this repository. ASD-STE100 itself is published free by
ASD at https://asd-ste100.org and remains their copyright.
