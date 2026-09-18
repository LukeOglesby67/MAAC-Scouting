# Decision log

Running record of choices and the reasoning behind them. The point is that in
March I can explain why something is the way it is, and that an interviewer
reading this repo sees judgment rather than just code.

Format: date, decision, why, what it rules out.

---

## 2026-09-XX — Separate repo from league-equivalency

**Decision.** Scouting is its own repo, not a track inside a shared platform.

**Why.** The only shared code is a config loader and an ingestion helper, about
80 lines of boilerplate. The data does not overlap at all: this is women's
college basketball, the translation model is men's. Different sources,
different players, different grain. They also have different deadlines, and
coupling them would let the November season crunch shape decisions in a model
that should be built slowly.

**Rules out.** Shared modules between the two. Duplicate the boilerplate without
guilt.

---

## 2026-09-XX — Raw layer is untransformed

**Decision.** Ingest lands source data unchanged, with only provenance columns.

**Why.** Re-pulling to undo an early cleaning choice is expensive and, mid-season,
disruptive.

**Rules out.** Cleaning at ingest time, however tempting.

---

## 2026-09-XX — wehoop release artifacts, not scraping

**Decision.** Data comes from the processed parquet artifacts published by
sportsdataverse/wehoop-wbb-data, not from scraping ESPN game by game.

**Why.** Scraping is weeks of work plus rate limiting and the season starts in
November. The artifacts are clean and language-agnostic, which also means
staying in Python despite wehoop being an R package.

**Rules out.** Per-game scraping, and any dependency on R.

**Accepts.** A dependency on someone else's publishing cadence. If the artifacts
go stale mid-season, in-season refresh needs a fallback.

---

## 2026-09-XX — Probe before building

**Decision.** scripts/probe_pbp.py runs before any analysis code is written.

**Why.** Lineup reconstruction is the differentiator and it depends entirely on
substitution events being present and reliable. ESPN college feeds are
inconsistent about this. An hour spent confirming beats five weeks spent
assuming.

---

## 2026-09-XX — The deliverable is paper

**Decision.** Reports render as a printable one-page sheet per opponent, not a
dashboard or web app.

**Why.** Coaches read a sheet before a game. The most common failure of student
analytics work is building a beautiful interactive tool nobody opens.

**Rules out.** Any web frontend in this repo.
