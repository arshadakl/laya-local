# Contributing to laya-local

Thank you for considering contributing to laya-local! This document outlines the process for contributing to the project.

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/laya-local.git
   cd laya-local
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Branch Strategy

- `main` — stable releases only, never push directly
- `dev` — active development, integration branch
- `feat/<name>` — new features
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation changes
- `chore/<name>` — maintenance tasks

Always branch from `dev` and submit PRs back to `dev`.

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/). All commits must match this format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Types

| Type | Description | SemVer |
|------|-------------|--------|
| `feat` | A new feature | MINOR |
| `fix` | A bug fix | PATCH |
| `docs` | Documentation only | — |
| `style` | Formatting (no code change) | — |
| `refactor` | Code change (no feature/fix) | — |
| `perf` | Performance improvement | PATCH |
| `test` | Adding/fixing tests | — |
| `build` | Build system changes | — |
| `ci` | CI configuration | — |
| `chore` | Maintenance | — |

### Examples

```
feat: add push-to-talk listener with VAD
feat(actions): add application launcher
fix(transcriber): handle empty audio buffer
docs: update installation instructions
test(classifier): add Malayalam command tests
chore(deps): bump faster-whisper to 1.1.0
```

## Code Standards

- **Type hints**: All public functions must have type hints (enforced by mypy strict mode)
- **Line length**: 88 characters max (enforced by ruff)
- **No print statements**: Use `structlog` for logging (enforced by ruff T20)
- **Tests**: Every module needs tests, aim for ≥80% coverage
- **Docstrings**: All public functions use Google-style docstrings

## Pull Request Process

1. Create a feature branch from `dev`
2. Make your changes following the code standards
3. Run the full quality suite:
   ```bash
   ruff check .
   ruff format --check .
   mypy src/
   pytest
   ```
4. Submit PR to `dev` branch
5. PR title must follow conventional commit format
6. Wait for CI checks to pass and review approval

## Reporting Issues

Use GitHub Issues with the appropriate template:
- Bug report: steps to reproduce, expected vs actual behavior
- Feature request: use case, proposed solution
