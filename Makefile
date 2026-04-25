.PHONY: check check-backend check-frontend dev check-hivemind

ISSUE_CHECK = python3 scripts/issue_check.py

check: check-backend check-frontend

check-backend:
	@$(ISSUE_CHECK) --renderer pytest-junit "backend tests" -- uv run pytest -q --tb=short --disable-warnings --no-header
	@$(ISSUE_CHECK) "ruff lint" -- uv run ruff check .
	@$(ISSUE_CHECK) "ruff format" -- uv run ruff format --check .
	@$(ISSUE_CHECK) "ty check" -- uv run ty check

check-frontend:
	@$(ISSUE_CHECK) --renderer vitest-json "frontend tests" -- npm --silent --prefix frontend run test -- --run --silent=passed-only
	@$(ISSUE_CHECK) "frontend check" -- npm --silent --prefix frontend run check
	@$(ISSUE_CHECK) "frontend build" -- npm --silent --prefix frontend run build

dev: check-hivemind
	hivemind Procfile.dev

check-hivemind:
	@command -v hivemind >/dev/null 2>&1 || { \
		echo "hivemind is required for make dev."; \
		echo "Install it with: brew install hivemind"; \
		exit 1; \
	}
