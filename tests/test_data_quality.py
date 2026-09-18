"""Data quality tests for the scouting marts.

These run against the marts, not the code. A pipeline that executes cleanly and
produces wrong lineups is the failure mode that matters here, and it is the one
an interviewer will ask about.

Baselines below come from the probe run on 2026-09-18 across 262 MAAC games:

    Substitution is the most common event type in the feed
    37,280 substitution rows across MAAC games (~142/game)
    in/out perfectly balanced: 18,640 each, across all 524 game-teams
    519/524 game-teams (99.0%) reconstruct cleanly
    12,956/12,991 sub batches (99.73%) apply cleanly
    25 in-already-on, 26 out-not-on contradictions

Those are the observed numbers. If a future run drops below the thresholds
here, something changed in the feed, and the tests should catch it rather than
letting bad lineups flow into a report a coaching staff actually reads.
"""
import pytest

# Observed baselines with a little headroom. Tighten once in-season data lands.
MIN_CLEAN_GAME_TEAMS = 0.97   # observed 0.990
MIN_CLEAN_SUB_BATCHES = 0.99  # observed 0.9973

# Drop budget. Observed 6.3 corrupt team-minutes across ~15,720 in 2026 =
# 0.04%. A run that wants to drop meaningfully more than this is not applying
# the policy, it is hiding a parser regression behind it.
MAX_DROPPED_FLOOR_SHARE = 0.005  # observed 0.0004


# --- events mart -----------------------------------------------------------

@pytest.mark.skip(reason="enable once the events mart exists")
def test_events_ordered_within_game():
    """Events are strictly ordered within each game. Reconstruction walks them
    in sequence, so an out-of-order feed silently corrupts every lineup
    downstream without raising anything."""


@pytest.mark.skip(reason="enable once the events mart exists")
def test_substitution_direction_parses():
    """Every substitution row resolves to exactly one of in or out, and the two
    balance per game-team. The probe found them balanced exactly (18,640 each
    across all 524 game-teams), so any imbalance means the text format changed
    and the parser is now wrong."""


@pytest.mark.skip(reason="enable once the events mart exists")
def test_substitutions_carry_athlete_id():
    """athlete_id_1 is never null on a substitution row. A name-only sub cannot
    be resolved reliably, and dropping it silently loses a player swap."""


# --- stints mart -----------------------------------------------------------

@pytest.mark.skip(reason="enable once the stints mart exists")
def test_five_players_per_lineup():
    """Every stint has exactly five players per team. This is the core
    invariant of the whole project. Anything else means an event was missed,
    misapplied, or applied out of order."""


@pytest.mark.skip(reason="enable once the stints mart exists")
def test_starters_seeded_from_box_not_pbp():
    """Each period's opening five comes from the box score. Period-start
    substitutions are frequently missing from the play-by-play, so seeding from
    events produces lineups that are confidently wrong."""


@pytest.mark.skip(reason="enable once the stints mart exists")
def test_clean_reconstruction_rate():
    """At least MIN_CLEAN_GAME_TEAMS of game-teams reconstruct with no
    contradiction. Below that, investigate the feed before trusting any report
    built on top of it."""


@pytest.mark.skip(reason="enable once the stints mart exists")
def test_contradictions_recorded_not_dropped():
    """Contradictions (subbing in a player already on the floor, subbing out a
    player who is not) are logged with game_id and event index, never silently
    swallowed. The policy is in docs/decisions.md; the audit trail is what makes
    it defensible."""


@pytest.mark.skip(reason="enable once the stints mart exists")
def test_only_size_violating_stints_dropped():
    """A stint is excluded if and only if its on-court set is not five.

    Contradictions that leave the set at five are bookkeeping noise, not wrong
    lineups: in the probe, Sacred Heart had 12 contradictions and Iona 2, with
    the correct five on the floor the entire game. Dropping on contradiction
    count instead of on the size invariant would discard two clean games to fix
    neither. See MAX_DROPPED_FLOOR_SHARE."""


@pytest.mark.skip(reason="enable once the stints mart exists")
def test_stint_durations_sum_to_game_time():
    """Per team, stint durations sum to regulation plus any overtime. A gap
    means lost floor time, which quietly corrupts every per-possession rate on
    the report."""


@pytest.mark.skip(reason="enable once the stints mart exists")
def test_dropped_floor_time_within_budget():
    """Excluded floor time stays under MAX_DROPPED_FLOOR_SHARE. This is the
    tripwire on the drop policy: dropping is only defensible while it stays
    negligible, so the moment it stops being negligible the build should fail
    rather than quietly report on less of the season than it claims."""


@pytest.mark.skip(reason="enable once the stints mart exists")
def test_possessions_attributed_once():
    """Each possession is attributed to exactly one lineup. Double-attribution
    inflates both lineups' ratings and is invisible in aggregate."""


# --- games mart ------------------------------------------------------------

@pytest.mark.skip(reason="enable once the games mart exists")
def test_maac_filter_covers_all_teams():
    """All thirteen MAAC programs appear. A team missing entirely almost always
    means an ESPN naming mismatch in config/sources.yml, not an absence of
    games. Count is read from config, never hardcoded here: the scaffold said
    twelve and Canisius was the one missing, which is exactly the failure this
    test exists to catch."""


@pytest.mark.skip(reason="enable once the games mart exists")
def test_no_duplicate_games():
    """One row per game_id. Duplicates double-count possessions and skew every
    rate stat on the report."""
