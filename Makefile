.PHONY: setup lint format test run doctor

VENV_PYTHON := .venv/bin/python

setup:
	python3 -m venv .venv
	$(VENV_PYTHON) -m ensurepip --upgrade
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

lint:
	$(VENV_PYTHON) -m ruff check .

format:
	$(VENV_PYTHON) -m ruff format .

test:
	$(VENV_PYTHON) -m pytest

run:
	$(VENV_PYTHON) -m bio_toolkit

doctor:
	$(VENV_PYTHON) -m bio_toolkit doctor
