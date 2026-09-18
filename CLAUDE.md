# CLAUDE.md

Project instructions. Read this before doing anything in this repo.

## What this is

An automated opponent scouting pipeline for MAAC women's basketball. It ingests
women's college basketball play-by-play, derives lineup and tendency data, and
generates a one-page scouting report per opponent.

**The stakeholder is real.** Quinnipiac's women's basketball program hired an
entirely new staff in April 2026 under head coach Roman Owen. Nobody on that
staff has scouted a MAAC opponent, and their season starts in November. The
first report goes to them as a finished artifact, unsolicited, to demonstrate
the thing rather than offer to build it.

**The deadline is the season.** Early November. That shapes every tradeoff:
prefer the version that ships.

## How to work with me on this

This repo is a portfolio project. Its value depends entirely on my being able
to explain and defend every part of it in a technical interview. Code I did not
reason through is worth less than no code.

So:

- **Do not write large amounts of code unprompted.** Propose an approach, let me
  react, then implement the piece we agreed on.
- **The tedious parts are yours.** HTTP handling, retries, parquet IO, argument
  parsing, boilerplate, test scaffolding. Write those freely.
- **The judgment calls are mine.** Lineup reconstruction logic, how to handle
  dirty or missing substitution events, what goes on the report, how to define a
  possession. Talk these through with me, do not just decide.
- **When I am wrong, say so.** Do not implement something I asked for if you
  think it is a mistake. Tell me why first.
- **Ask before adding a dependency.** Small dependency surface is deliberate.

## Hard rules

**1. Run `make probe` before writing any analysis code.**
`scripts/probe_pbp.py` answers the question the whole project depends on: do
the MAAC play-by-play feeds actually contain substitution events and shot
coordinates? ESPN's college feeds are inconsistent about both and mid-major
coverage is thinner than power conference. If substitutions are absent or
unreliable, lineup reconstruction is impossible and the report pivots to
tendencies, shot distribution, and on/off approximations. That finding changes
the plan, so it comes first.

**2. Raw is untouched.** Ingest modules land source data unchanged, with only
provenance columns added by `land()` in `ingest/base.py`. No renaming, no type
coercion, no filtering at ingest. Cleaning happens in `transform/`. A bad
cleaning decision made in September is unrecoverable in November without
re-pulling everything.

**3. Never read raw from downstream.** raw to staging to marts. Analysis and
reports read marts only.

**4. The output is a printable page, not a dashboard.** Coaches read a sheet
before a game. They do not open interactive tools. Build whatever tooling I want
for myself, but the deliverable is paper.

**5. Notebooks are exploration only.** Nothing in `src/` imports from
`notebooks/`. If a notebook produces something worth keeping, it moves into
`src/` as a real module with a test.

**6. Write in `docs/decisions.md` as we go.** Every non-obvious choice gets an
entry: what was decided, why, and what it rules out. This is the file an
interviewer reads to see judgment rather than just code. Prompt me to write one
when we make a real decision and I forget.

## The data

**Source:** `sportsdataverse/wehoop-wbb-data` publishes processed women's
college basketball play-by-play, team box scores, and player box scores as
GitHub release artifacts. They are parquet files.

**Do not scrape ESPN.** Per-game scraping is weeks of work plus rate limiting,
and the season starts in November.

**Do not switch to R.** wehoop is an R package and its Python port has been
stale since 2021, but the release artifacts are just files. Python reads them
fine. This project stays in Python.

**Size:** roughly 7 million rows and 1 to 2 GB per season. Pull only the seasons
in `config/sources.yml`. Currently 2024 through 2026. Do not load everything.

**Known gotchas:**
- Shot coordinates exist "where available." Mid-major coverage is spotty.
  Check the populated rate before building anything on them.
- The coordinate scale is a 25x47 half-court in feet, with the basket at
  roughly (25, 0). That is geometrically wrong because of backboard overhang,
  so translations are needed for anything spatial.
- Seed each period's starting five from the box score, not the play-by-play.
  Period-start substitutions are frequently missing.
- Verify ESPN's exact team naming before trusting the MAAC filter in config.

## Architecture

```
src/scout/
  config.py          paths and parameters, everything reads from here
  ingest/
    base.py          land() contract, provenance columns, raw only
    wehoop.py        women's CBB pbp, team box, player box
  transform/
    staging.py       raw to typed, ordered, standardized events
    marts.py         games, events, stints, player_game
  analysis/
    lineups.py       five-man lineups reconstructed from substitutions
    tendencies.py    pace, shot distribution, personnel, late-clock
  reports/
    opponent.py      one-page report rendering
```

`analysis/tendencies.py` deliberately does not depend on substitution data. It
is the fallback if the probe comes back bad, and part of the report either way.

## Conventions

- Python 3.11+, pandas, parquet via pyarrow
- pytest, tests live in `tests/`
- Data quality tests matter more than unit tests here. A pipeline that runs
  clean and produces wrong numbers is the failure mode that counts.
- Type hints on function signatures
- Config over hardcoding, always

## Out of scope

- Men's basketball. This is a women's basketball project and the data sources
  are different.
- The league equivalency model. That is a separate repo. Do not reference it,
  import from it, or suggest merging them.
- Any interactive or web frontend.
- Predictive modeling of game outcomes. This is descriptive scouting.

## Current state

Scaffolded. Every module is a stub raising NotImplementedError with a docstring
explaining what goes in it. Nothing has been implemented yet.

Next step: `make probe`.
