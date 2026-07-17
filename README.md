# commitcraft

> Smart conventional commit messages — a rule engine decides when AI is even needed.

![Demo](assets/commitcraft-demo.gif)

[![CI](https://github.com/mavesensei/commitcraft/actions/workflows/ci.yml/badge.svg)](https://github.com/mavesensei/commitcraft/actions)
[![PyPI Downloads](https://img.shields.io/pypi/dm/commitcraft-cli.svg)](https://pypi.org/project/commitcraft-cli/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What makes it different

Most "AI commit message" tools blindly send your entire diff to an LLM. commitcraft doesn't.

It first runs a **local rule engine** on your diff. README-only change? Lockfile bump? Single test file? Those get a conventional commit message generated instantly, locally, with zero AI cost. Only when changes are genuinely complex does it reach out to an LLM — and even then it sends a condensed summary, not the full diff.

**The story isn't "I used AI." It's "I built a system that decides when AI should be used."**

## Pipeline

```
git diff (staged)
    │
    ▼
Parser → extract changed files, line counts, file types
    │
    ▼
Filter → strip lockfiles, dist/, build/, *.min.js, etc.
    │
    ▼
Rule Engine → simple change? generate commit locally (zero cost)
    │              e.g. README-only → "docs: update README"
    │              lockfile-only → "chore: update lockfile"
    │
    ▼ (complex change only)
Classifier → complexity score 0-100 from:
             • file count and directory spread
             • function/class definition changes (regex)
             • test files alongside source files
             • total line count
    │
    ▼
Context Builder → condensed summary (not the full diff)
    │              ~100-500 tokens instead of thousands
    ▼
Your chosen Provider (Ollama / OpenAI / Gemini / Anthropic)
    │
    ▼
Conventional commit message
```

## Installation

```bash
pip install commitcraft-cli
commitcraft init   # one-time setup: choose your provider
```

## Quickstart

```bash
# Make some changes, then:
commitcraft commit

# Split staged changes into multiple semantic commits, one per logical change:
commitcraft commit --split

# Starting a brand-new project? Just run `commit` as usual — commitcraft detects
# an all-new-files diff and offers to generate one commit per file/module
# automatically (skip the prompt entirely and go straight to per-file commits
# with --split).
commitcraft commit

# Generate a PR description for the current branch:
commitcraft pr

# Generate release notes between two tags:
commitcraft release-notes v1.0.0..v1.1.0

# Analyze your commit history:
commitcraft history
```

## Provider setup

On first run (`commitcraft init`), you choose your provider:

| Provider | Cost | Requires |
|---|---|---|
| **Ollama** | Free (local) | Ollama installed + a model pulled |
| **OpenAI** | Your API key | `openai_api_key` in config |
| **Anthropic Claude** | Your API key | `anthropic_api_key` in config |
| **Google Gemini** | Your API key | `gemini_api_key` in config |

Your API key is stored locally at `~/.commitcraft/config.yaml`. It never leaves your machine except to call your chosen provider directly.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/adding_a_provider.md](docs/adding_a_provider.md).

## License

MIT © mavesensei
