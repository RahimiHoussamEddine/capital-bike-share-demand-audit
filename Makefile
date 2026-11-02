PYTHON ?= .venv/bin/python
export PIP_CACHE_DIR := .cache/pip
export TMPDIR := $(CURDIR)/.tmp
export PYTHONPATH := $(CURDIR)/src

.PHONY: install-dev lock fetch build verify test quality check-deps app api

install-dev:
	mkdir -p .tmp .cache/pip
	$(PYTHON) -m pip install --only-binary=:all: --no-cache-dir -r requirements.lock

lock:
	$(PYTHON) -m pip freeze --all > requirements.lock

fetch:
	$(PYTHON) -m bike_share_audit.fetch

build:
	$(PYTHON) -m bike_share_audit.build

verify:
	$(PYTHON) -m bike_share_audit.verify

test:
	$(PYTHON) -m pytest

quality:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

check-deps:
	$(PYTHON) -m pip check

app:
	$(PYTHON) -m streamlit run app.py

api:
	$(PYTHON) -m uvicorn bike_share_audit.api:app --host 0.0.0.0 --port 8000
