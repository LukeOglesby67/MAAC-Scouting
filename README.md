# maac-scouting

Automated opponent scouting reports for MAAC women's basketball, built from play-by-play.

## What it does

Ingests women's college basketball play-by-play, derives five-man lineup ratings and team tendencies, and generates a one-page scouting report per opponent.

```
wehoop artifacts ──> data/raw ──> data/staging ──> data/marts ──> one-page reports
                     (untouched)  (typed, MAAC)    (games,
                                                    stints,
                                                    tendencies)
```

## Why

Quinnipiac's women's basketball program hired an entirely new staff in April 2026. Nobody there has scouted a MAAC opponent and the season starts in November. Mid-major programs have no analytics budget and no lineup data, because the NCAA doesn't publish it the way the NBA does.

## The hard part

Five-man lineups have to be reconstructed from substitution events in the play-by-play. ESPN's college feeds are inconsistent about these, especially for mid-majors, so `make probe` runs first to confirm the data supports it before anything is built on top.

## Data

`sportsdataverse/wehoop-wbb-data` publishes processed women's college basketball play-by-play, team box, and player box as GitHub release artifacts. Parquet files, so no scraping and no R despite wehoop being an R package.

Roughly 7M rows per season. Seasons are scoped in `config/sources.yml`.

## Running it

```bash
make setup     # install dependencies
make probe     # FIRST. confirms substitutions and shot coordinates exist
make ingest    # release artifacts -> data/raw
make build     # raw -> staging -> marts
make reports   # generate one-pagers
make test
```

## Status

Probe is done and it came back good: substitution events are present and
reconstructable for MAAC games (99% of game-teams walk clean), and field-goal
coordinates are real 99.8% of the time. The lineup track is on.
`docs/decisions.md` is the running log of choices and why.

- [x] Probe: substitutions and coordinates confirmed for MAAC ([findings](docs/decisions.md))
- [x] wehoop release ingestion (4 datasets x 3 seasons, schema-verified)
- [ ] Staging: typed, ordered, MAAC-filtered events
- [ ] Games mart
- [ ] Lineup reconstruction from substitutions
- [ ] Tendencies and personnel profiles
- [ ] One-page report renderer
- [ ] Scheduled in-season refresh
