.PHONY: install run

install:
	uv sync --all-groups --all-packages

run:
	uv run python -m http_load_balancer
