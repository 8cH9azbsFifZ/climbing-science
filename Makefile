.PHONY: test lint docs docs-serve bump-patch bump-minor clean install build check-dist check-refs

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

lint:
	python -m ruff check src/ tests/
	python -m ruff format --check src/ tests/

check-refs:
	python scripts/check_citations.py

format:
	python -m ruff format src/ tests/
	python -m ruff check --fix src/ tests/

docs:
	mkdocs build

docs-serve:
	mkdocs serve

build: clean
	python -m build
	twine check dist/*

check-dist:
	twine check dist/*

bump-patch:
	bump-my-version bump patch
	@echo "--- Updating CHANGELOG.md ---"
	@echo "Remember to update CHANGELOG.md with changes for this version."

bump-minor:
	bump-my-version bump minor
	@echo "--- Updating CHANGELOG.md ---"
	@echo "Remember to update CHANGELOG.md with changes for this version."

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info site/ .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
