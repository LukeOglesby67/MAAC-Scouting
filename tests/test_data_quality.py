"""Data quality tests.

These run against the marts, not the code. A pipeline that executes cleanly
and produces wrong numbers is the failure mode that matters, and it is the
one that separates an engineering project from a notebook.
"""
import pytest


@pytest.mark.skip(reason="enable once marts exist")
def test_player_season_unique():
    """One row per player-season-league. Duplicates mean the join is wrong."""


@pytest.mark.skip(reason="enable once marts exist")
def test_no_null_keys():
    """player_id, season, and league are never null."""


@pytest.mark.skip(reason="enable once marts exist")
def test_minutes_plausible():
    """No player-season exceeds the theoretical maximum minutes for its league."""


@pytest.mark.skip(reason="enable once marts exist")
def test_no_holdout_leakage():
    """No player in the holdout draft years appears in the training set."""


@pytest.mark.skip(reason="enable once marts exist")
def test_transitions_ordered():
    """In every transition row, the pre-NBA season precedes the NBA season."""
