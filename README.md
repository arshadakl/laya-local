# laya-local

[![CI](https://github.com/arshadakl/laya-local/actions/workflows/ci.yml/badge.svg)](https://github.com/arshadakl/laya-local/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/laya-local.svg)](https://pypi.org/project/laya-local/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-black)](https://github.com/astral-sh/ruff)

> A local-first Malayalam/English assistant for Windows that turns voice or text commands into safe, structured actions using Laya.

## Features

- **Multilingual intent recognition** — understands Malayalam, English, and Manglish via Laya multilingual (322M params, runs locally)
- **Voice or text input** — push-to-talk with faster-whisper speech-to-text, or type commands directly
- **Safe by design** — whitelist-based action executor, no arbitrary command execution
- **Local-first** — all processing happens on your machine, no cloud APIs needed
- **Extensible** — add custom actions via YAML config

## Quick Start

### Prerequisites

- Windows 10/11
- Python 3.11+
- Microphone (for voice commands)

### Installation

```bash
git clone https://github.com/arshadakl/laya-local.git
cd laya-local
pip install -e ".[dev]"
```

### Usage

```bash
# Text mode (type commands)
laya-local --text

# Voice mode (push-to-talk with right Ctrl)
laya-local --voice

# Both (default)
laya-local
```

### Example Commands

| Language | Command | Action |
|----------|---------|--------|
| Malayalam | "Chrome തുറക്കൂ" | Opens Chrome |
| English | "Open VS Code" | Opens VS Code |
| Manglish | "Chrome thurakku" | Opens Chrome |
| Malayalam | "ശബ്ദം കുറയ്ക്കൂ" | Volume down |
| English | "Shutdown" | Shuts down PC |

## Configuration

Copy `config.example.yaml` to `config.yaml` and customize:

```yaml
whisper:
  model: "small"        # tiny, base, small, medium, large-v3
  device: "cpu"         # cpu or cuda

laya:
  model: "convaiinnovations/laya-multilingual"

tts:
  enabled: false        # Enable voice responses
  language: "en"

listener:
  trigger_key: "ctrl"   # Push-to-talk key
  sample_rate: 16000
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linter
ruff check .
ruff format .

# Type check
mypy src/
```

## Architecture

```
Voice/Text Input
     ↓
[faster-whisper]  Speech → Text (local)
     ↓
[Laya Multilingual]  Text → Structured Intent (322M)
     ↓
[Action Router]  Whitelist dispatch → Python execution
     ↓
Windows (apps, files, system controls, websites)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

[Apache-2.0](LICENSE)
