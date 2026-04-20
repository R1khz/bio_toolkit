.PHONY: setup lint format test run doctor

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

test:
	pytest

run:
	python -m bio_toolkit

doctor:
	python -m bio_toolkit doctor

