.PHONY: setup lint format test coverage run doctor

VENV_PYTHON := .venv/bin/python

setup:
	python3 -m venv .venv
	$(VENV_PYTHON) -m ensurepip --upgrade
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"
	@test -f .env || cp .env.example .env

lint:
	$(VENV_PYTHON) -m ruff check .

format:
	$(VENV_PYTHON) -m ruff format .

test:
	$(VENV_PYTHON) -m pytest

coverage:
	$(VENV_PYTHON) -m pytest --cov=bio_toolkit --cov-report=term-missing

run:
	$(VENV_PYTHON) -m bio_toolkit

doctor:
	$(VENV_PYTHON) -m bio_toolkit doctor
