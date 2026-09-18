"""Reconstruct five-man lineups from play-by-play substitution events.

This is the hard part and the part no other MAAC scouting sheet has. The NCAA
does not publish lineup data the way the NBA does, so it has to be derived.

Approach:
  1. Seed each period's starting five from the box score, not from the
     play-by-play. Period-start substitutions are frequently missing.
  2. Walk events in order, applying each substitution to the on-court set.
  3. Validate continuously: the on-court set must always be exactly five per
     team. When it is not, the feed dropped an event.
  4. Attribute possessions and points to whichever lineup was on the floor.

Expect the validation to fail on real data. That is normal and the interesting
engineering question is what you do about it. Options are dropping the affected
stint, interpolating from the next known-good state, or flagging and excluding.
Whatever you choose, write it in docs/decisions.md, because an interviewer will
ask how you handled dirty data and this is the answer.

Run scripts/probe_pbp.py before writing any of this. If substitution events are
absent, none of it is possible and the report pivots.
"""


def build_stints():
    raise NotImplementedError


def lineup_ratings():
    raise NotImplementedError
