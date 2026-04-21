# Changelog

## 0.1.2

- Added Chocolatey distribution (`choco install pinelabs-mcp`) — thin wrapper that installs the official `pinelabs-mcp-server` from PyPI and registers a `pinelabs-mcp-server` shim on PATH (named distinctly from the npm `pinelabs-mcp` CLI to avoid collision; both can be installed side by side).
- Added `.github/workflows/chocolatey-publish.yml` (manual `workflow_dispatch`) for packing, local install/uninstall validation on `windows-latest`, and pushing to community.chocolatey.org.

## 0.1.0

- Initial public repository packaging.
- Public documentation, examples, and CI scaffolding.
- `cli/` + `pkg/` repository structure for the Pine Labs MCP Server.
