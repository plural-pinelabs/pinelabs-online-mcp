# Contributing

## Development Setup

1. Create a virtual environment.
2. Install the project with development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Common Commands

```bash
make test
make fmt
make lint
make local-run
```

## Pull Requests

- Keep changes focused and minimal.
- Add or update tests for behavior changes.
- Do not introduce hardcoded credentials, internal endpoints, or private infrastructure references.
- Preserve the security controls documented in `SECURITY.md`.

## Tooling Guidance

- Runtime code lives under `cli/` and `pkg/`.
- Tests live under `tests/`.
- Public examples live under `examples/`.
