# Contributing to LAAF

Thank you for contributing to the Logic-layer Automated Attack Framework!

## Ways to Contribute

- **New taxonomy techniques** — extend E/S/M/L/T categories
- **New platform adapters** — add support for more LLM APIs
- **Empirical results** — share bypass rate data from authorised evaluations
- **Bug fixes** — see open issues
- **Documentation** — improve guides and API reference

## Development Setup

```bash
git clone https://github.com/qorvexconsulting1/laaf
cd laaf
pip install -e ".[dev]"
```

## Adding a New Technique

1. Choose the appropriate category file: `laaf/taxonomy/{encoding,structural,semantic,layered,triggers}.py`
2. Implement an `apply(instruction: str) -> str` function
3. Create a `Technique` instance with a unique ID (e.g. `E12` for the next encoding technique)
4. Register it: `_REGISTRY.register(_t)`
5. Add a test in `tests/unit/test_taxonomy.py`
6. Update technique count assertions

## Adding a New Platform

1. Create `laaf/platforms/myplatform_platform.py`
2. Subclass `AbstractPlatform` and implement `send()` and `default_model`
3. Register in `laaf/platforms/__init__.py` `get_platform()` factory
4. Add to CLI choices in `laaf/cli/main.py`

## Pull Request Checklist

- [ ] `pytest tests/` passes
- [ ] `ruff check laaf/` passes
- [ ] New techniques include unit tests
- [ ] No hardcoded API keys or credentials
- [ ] PR description explains the security research value

## Code Style

- Python 3.11+, type hints throughout
- `ruff` for linting (line length: 100)
- Docstrings for all public functions

## Ethical Guidelines

All contributions must comply with the responsible use policy in [SECURITY.md](SECURITY.md).
