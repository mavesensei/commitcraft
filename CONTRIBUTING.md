# Contributing to commitcraft

## Development setup

```bash
git clone https://github.com/[YOUR-GITHUB]/commitcraft
cd commitcraft
pip install -e ".[dev]"
pytest
```

## Adding a new rule to the rule engine

Rules live in `commitcraft/analysis/rule_engine.py`. Each rule is a function with this signature:

```python
def my_rule(paths: list[str]) -> RuleResult | None:
    # return RuleResult(matched=True, message="type: message", rule_name="my_rule")
    # return None if this rule doesn't match
```

Add your function to the `_RULES` list. Rules are evaluated in order — first match wins.

Write tests in `tests/test_rule_engine.py` before adding the rule.

## Adding a new provider

See [docs/adding_a_provider.md](docs/adding_a_provider.md).

## Running tests

```bash
pytest tests/ -v --cov=commitcraft --cov-report=term-missing
```

## Linting

```bash
ruff check commitcraft/ tests/
```
