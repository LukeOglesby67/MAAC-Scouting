.PHONY: setup probe ingest build reports test clean

setup:
	python -m venv .venv && .venv/bin/pip install -r requirements.txt

probe:
	python scripts/probe_pbp.py

ingest:
	python -m scout.ingest.wehoop

build:
	python -m scout.transform.staging
	python -m scout.transform.marts

reports:
	python -m scout.reports.opponent

test:
	pytest tests/ -v

clean:
	rm -rf data/staging/* data/marts/*
