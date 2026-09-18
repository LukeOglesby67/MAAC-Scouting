"""Opponent tendencies from play-by-play.

Does not depend on substitution data, so this is the fallback if lineup
reconstruction turns out to be impossible, and a component of the report either
way.

  - Pace and possession estimates
  - Shot distribution by zone, where coordinates exist
  - Personnel usage: who shoots, from where, in what situations
  - Late-clock and end-of-period behavior
  - Turnover and foul profile
"""


def team_profile():
    raise NotImplementedError


def personnel_profile():
    raise NotImplementedError
