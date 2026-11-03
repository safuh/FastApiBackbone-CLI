# Contributing

## Development

Requires Python 3.11+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest
```

## Scope

The CLI generates independent FastApiBackbone-derived backend projects. Keep template acquisition deterministic, validate archive contents before extraction, and never overwrite a non-empty destination.

Do not add PydanticAI or Flutter to generated projects. Preserve Pydantic and the canonical FastApiBackbone source architecture.
