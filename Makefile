.PHONY: check check-backend check-frontend dev check-hivemind

check: check-backend check-frontend

check-backend:
	uv run pytest -q
	uv run ruff check .
	uv run ruff format --check .
	uv run ty check

check-frontend:
	cd frontend && npm run test -- --run
	cd frontend && npm run check
	cd frontend && npm run build

dev: check-hivemind
	hivemind Procfile.dev

check-hivemind:
	@command -v hivemind >/dev/null 2>&1 || { \
		echo "hivemind is required for make dev."; \
		echo "Install it with: brew install hivemind"; \
		exit 1; \
	}
