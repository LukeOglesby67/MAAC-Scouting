.PHONY: setup probe ingest build reports test clean

# Everything runs out of .venv against src/ on the path. No install step, no
# packaging metadata, no dependency on the ambient python.
PY := .venv/bin/python
RUN := PYTHONPATH=src $(PY)

setup:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

probe:
	$(RUN) scripts/probe_pbp.py

ingest:
	$(RUN) -m scout.ingest.wehoop

build:
	$(RUN) -m scout.transform.staging
	$(RUN) -m scout.transform.marts

reports:
	$(RUN) -m scout.reports.opponent

test:
	$(RUN) -m pytest tests/ -v

clean:
	rm -rf data/staging/* data/marts/*

# The download cache is 200 MB and separate from the raw layer. Dropping it
# forces a re-pull; dropping data/raw loses the landed extracts themselves.
clean-cache:
	rm -rf data/raw/_cache
