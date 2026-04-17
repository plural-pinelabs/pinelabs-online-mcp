# Pine Labs MCP Maintainer

Use this skill when updating the public Pine Labs MCP Server repository.

## Scope

- Add or update Pine Labs MCP tools under `pkg/pinelabs/`
- Keep documentation in `README.md`, `AGENTS.md`, and `examples/` in sync
- Preserve security requirements from `SECURITY.md`
- Keep tests under `tests/` aligned with the active public tool surface

## Repository Structure

```text
cli/pinelabs_mcp_server/     # CLI entry points
pkg/pinelabs/                # Core Pine Labs server code and tools
pkg/toolsets/                # Toolset metadata helpers
tests/                       # Public test suite
examples/                    # Public MCP client examples
```

## Required Checks

```bash
make test
make lint
```

## Rules

- Do not add hardcoded credentials or internal-only infrastructure references.
- Prefer public-safe placeholders in docs and examples.
- Do not leave commented-out feature scaffolding in public code paths.
- Update tests when changing tool parameters, registration, or behavior.