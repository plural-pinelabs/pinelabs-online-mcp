.PHONY: test fmt lint build local-run clean
.PHONY: install test fmt lint build local-run clean

# Run all tests
test:
	python -m pytest tests/ -v
install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

# Format code
fmt:
	python -m ruff format .

# Lint code
lint:
	python -m ruff check .

# Build Docker image
build:
	docker build -t pinelabs-mcp-server .

# Run locally via stdio
local-run:
	python -m cli.pinelabs_mcp_server.main stdio

# Clean caches
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache
