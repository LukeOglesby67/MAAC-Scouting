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

---

## 2026-09-18 — Probe result: lineup reconstruction is viable

**Decision.** Build the lineup track. The report is not pivoting to tendencies-only.

**Why.** `make probe` against the completed 2026 season (2,824,090 rows, 6,011
games; 262 of them MAAC):

- `Substitution` is the single most common event type in the whole feed —
  795,380 rows league-wide, 37,280 across MAAC games, ~142 per game.
- Every sub row carries `athlete_id_1` (100%) and its direction parses out of
  `text` (100%, "subbing in" / "subbing out", 18,640 each).
- In/out counts balance exactly for 524 of 524 MAAC game-teams.
- Walking the events from a starter seed leaves exactly five on the floor at
  99.73% of stoppages, and 519 of 524 game-teams are clean end to end.
- Contradictions across 37,280 events: 25 subbed in while already on, 26 subbed
  out while not on. 0.14%.

Coverage is a full season per team, 29–34 games, home and away.

**Rules out.** The fallback plan. `analysis/tendencies.py` stays in the report on
its own merits, not as a hedge.

**Accepts.** ~1% of game-teams need a dirty-data policy. Small enough to decide
deliberately rather than architect around.

---

## 2026-09-18 — Seed the five from `game_rosters`, not the box score

**Decision.** Period-start lineups seed from the `game_rosters` dataset's
`starter` boolean.

**Why.** It is an explicit flag rather than something inferred from minutes, and
it is exactly five players for 12,055 of 12,058 game-teams league-wide. All 524
MAAC game-teams got a seed, so the walk never had to guess a starting point.

**Rules out.** Inferring starters from `player_box` minutes, and trusting
period-start substitution events, which are the ones ESPN drops.

---

## 2026-09-18 — Check the lineup invariant at stoppages, not at every event

**Decision.** "Exactly five on the floor" is asserted after each batch of
substitutions sharing a `(period_number, clock_display_value)`, not after each
substitution row.

**Why.** ESPN writes a substitution as several one-athlete rows in sequence —
two "subbing out" then two "subbing in". Mid-batch the set is legitimately at
three or four. Checking per row reports 22,443 violations and zero clean
game-teams; checking per batch reports 35 violations and 99% clean. The naive
check would have condemned data that is actually fine.

**Rules out.** Any per-event validation, and the conclusion it would have led to.

---

## 2026-09-18 — Shot coordinates: use the raw frame, fold the translated one

**Decision.** Shot location comes from `coordinate_x_raw` / `coordinate_y_raw`,
with the basket at (25, 0). Free throws are excluded from anything spatial.

**Why.** Two traps, both of which read as "fine" if you check `notna()`:

1. Coordinates are never null. ESPN encodes a miss as an int32-min sentinel or
   parks it at (25, 0). 98.9% of made free throws sit at (25, 0) — they have no
   location. On field-goal attempts only, 99.8% of coordinates are real.
2. CLAUDE.md warned the raw frame was geometrically wrong. It is not. Against
   the 22.15 ft arc, 3PA median 24.7 ft, 0.1% of threes fall inside the line,
   0.5% of twos outside it. That separation is as clean as this gets.

The `coordinate_x` / `coordinate_y` columns are not broken either, but they are a
**full-court** frame with baskets at (±41.75, 0). Folded to the nearer basket
they reproduce the raw numbers exactly. Measured from the origin they look like
garbage, because the origin is centre court.

**Rules out.** Building a backboard-overhang correction that was never needed.

---

## 2026-09-18 — Release assets live in a different repo than assumed

**Decision.** Ingest pulls from `sportsdataverse/sportsdataverse-data` release
tags, one tag per dataset, asset stem `{dataset}_{season}.parquet`.

**Why.** `wehoop-wbb-data` builds the data but publishes it elsewhere. Its own
`docs/datasets/*.md` name the tag for each dataset. Both are now in
`config/sources.yml`, so no URL is hardcoded.

**Also corrected.** pbp is 51–92 MB per season as parquet, not 1–2 GB, and 2.8M
rows, not 7M. The season is cheap enough to hold locally. Season 2027 is not
published yet, as expected in September.

**Rules out.** Guessing at a release URL, and the size-driven caution that was
shaping the ingest design.

---

## 2026-09-18 — Canisius was missing from the MAAC filter

**Decision.** Added Canisius. The conference filter is 13 teams.

**Why.** The config listed 12. Canisius is in the feed with 29 games. A missing
team is a silently empty report for a real opponent.

**Verified.** All 13 config names match ESPN's `home_team_name` /
`away_team_name` exactly, so no alias table is needed yet.

---

## 2026-09-18 — Test suite rewritten for this project

**Decision.** `tests/test_data_quality.py` tests scouting marts.

**Why.** The original was copied from the league-equivalency scaffold and
tested player-season uniqueness, draft-year holdout leakage, and transition
ordering, none of which exist here. Tests that validate the wrong project are
worse than no tests: they pass, and they imply coverage that is not there.

**What it tests now.** The five-per-lineup invariant, sub direction balance,
box-score seeding, stint durations summing to game time, possession
single-attribution, contradiction auditability, and floors pinned to the
probe's observed 99.0% / 99.73%.

**Note.** `test_maac_filter_covers_all_teams` originally read "all twelve MAAC
programs." The conference has thirteen and Canisius was the missing one — the
exact failure that test exists to catch, encoded as its own baseline. The count
now comes from config.

---

## 2026-09-18 — Dirty substitution policy: drop, at stint granularity

**Decision.** A stint is excluded from the marts if and only if its on-court set
is not exactly five. Contradictions that leave the set at five are logged and
kept. Excluded stints are written to an audit table with `game_id`, team, and
event index — never silently swallowed.

**Why drop rather than interpolate.** Interpolating a lineup means inventing
five players who were never observed on the floor, then attributing real
possessions and real points to them. Those possessions flow into a lineup rating
that a coaching staff reads as fact. For the volume involved, the guess is worth
less than the gap, and a gap is auditable in a way a guess is not.

**Why stint granularity and not game-team.** The headline "~1% of game-teams are
dirty" overstates the cost by more than an order of magnitude. Measured on the
2026 season:

- 8 game-teams are affected, but 5 are **non-MAAC opponents** — Richmond,
  Dartmouth, UMass Boston, Mercy, Georgetown. Their lineups are not on the
  report. Richmond alone is 35.9 of the 53.9 corrupt minutes and is irrelevant
  to every scouting question this project asks.
- Of the 3 MAAC-side cases, 2 are **size-preserving**: Sacred Heart logs 12
  contradictions and Iona 2, and in both the on-court set is correct for the
  entire game. The contradictions pair off and self-correct. Dropping on
  contradiction count would discard two clean games and fix nothing.
- That leaves **one** MAAC game-team with genuinely wrong floor time: Canisius,
  6.3 minutes in game 401813890.

So the real exposure is **6.3 team-minutes out of ~15,720, or 0.04%** — not 1%.
Dropping at game-team granularity would discard ~120 team-minutes to repair 6.3,
a 19x overcorrection, and would throw away two games that are entirely correct.

**Rules out.** Interpolation, and any handling keyed to contradiction counts
rather than to the five-on-the-floor invariant.

**Guarded by.** `MAX_DROPPED_FLOOR_SHARE` in the test suite. Dropping is only
defensible while it stays negligible; if a future run wants to drop meaningfully
more, that is a parser regression hiding behind the policy, and the build should
fail rather than quietly report on less of the season than it claims.

---

## 2026-09-18 — Ingest reads with the pyarrow dtype backend

**Decision.** `fetch()` reads with `dtype_backend="pyarrow"`.

**Why.** This is a correctness fix, not a preference. pandas' default numpy
backend has no nullable integer type, so any id column containing a null comes
back as `float64`. `game_rosters.athlete_id` is `int32` upstream with two nulls
in 2026, and the default read lands it as `double` — silently, with a pipeline
that looks clean.

That is both a rule-2 violation (type coercion at ingest) and a live bug:
`athlete_id` is the join key between the lineup walk, `player_box`, and every
per-player number on the report. A float join key is the kind of thing that
half-works for a season and then produces a report with a player missing.

**Verified.** All 12 landed extracts now match upstream column for column and
type for type, with exactly three added columns: `_source`, `_season`,
`_ingested_at`.

**Rules out.** Default-backend reads anywhere in ingest.

---

## 2026-09-18 — Cache by ETag, not by file existence

**Decision.** Downloads are cached in `data/raw/_cache` and revalidated with a
conditional GET (`If-None-Match`) against the stored ETag.

**Why.** The upstream feed rebuilds daily during the season. A plain "skip if the
file exists" cache is correct in September and quietly serves stale data in
January, which is exactly when the reports matter. A 304 costs one request and
no transfer, so the cheap path stays cheap: a full re-run against warm cache is
about 5 seconds instead of a 200 MB pull.

**Note.** The cache is not the raw layer. `data/raw/_cache` holds upstream bytes;
`data/raw/wbb/` holds what `land()` wrote with provenance. `make clean-cache`
drops the former only.

---

## 2026-09-18 — pbp schema drifts across seasons

**Finding, not yet a decision.** The pbp schema is not stable across the three
configured seasons. 2024 and 2025 are identical to each other; 2026 differs:

    only in 2026:  espn_home_wp, espn_away_wp, espn_tie_percentage,
                   points_attempted, short_description
    only in 2024:  media_id

`points_attempted` is the one that bites. The probe used it to separate twos
from threes for the geometry check, and it does not exist before 2026. Staging
either derives shot value from `type_text` / `score_value` for the older seasons
or accepts that anything built on `points_attempted` is 2026-only.

**Why it is here.** Landing raw made this visible immediately instead of at the
point where staging concatenates three seasons and pandas fills two of them with
nulls without complaining. This is the argument for rule 2 in miniature.

**Open.** Which way staging resolves it. Deriving shot value looks
straightforward, but it is a definition question, so it is yours.
