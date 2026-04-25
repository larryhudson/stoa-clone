.PHONY: dev check-hivemind

dev: check-hivemind
	hivemind Procfile.dev

check-hivemind:
	@command -v hivemind >/dev/null 2>&1 || { \
		echo "hivemind is required for make dev."; \
		echo "Install it with: brew install hivemind"; \
		exit 1; \
	}
