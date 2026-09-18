"""DAY ONE SCRIPT. Run this before building anything else.

Answers the one question the whole scouting project depends on:
does the women's college play-by-play actually contain substitution events,
and does it contain shot coordinates, for MAAC games specifically?

ESPN's college feeds are inconsistent about both, and mid-major coverage is
thinner than power conference coverage. If substitutions are missing or
unreliable, lineup reconstruction is impossible and the report pivots to
personnel tendencies and shot distribution instead. Find that out in an hour,
not in week five.

Usage:
    python scripts/probe_pbp.py [--season 2026]
"""
import argparse
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scout.config import load, RAW  # noqa: E402

CACHE = RAW / "_probe_cache"

# NCAA women's three-point line. Used to sanity check the coordinate frame:
# if the geometry is right, threes sit outside it and twos inside.
THREE_ARC, THREE_CORNER = 22.15, 21.65
# ESPN encodes "no coordinate" two ways, neither of them null.
SENTINEL = -2e8          # int32 minimum leaking through as a float
NULL_ISLAND = (25.0, 0.0)  # raw-frame centre point, used for free throws


def asset_url(dataset: str, season: int) -> str:
    cfg = load()["wbb"]
    return f"{cfg['release_base']}/{cfg['release_tags'][dataset]}/{cfg['file_stems'][dataset]}_{season}.parquet"


def fetch(url: str) -> Path:
    """Download once, reuse after. 50-90 MB per season; no point re-pulling."""
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / url.rsplit("/", 1)[-1]
    if dest.exists():
        print(f"using cached {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
        return dest
    print(f"downloading {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dest)
    print(f"cached -> {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
    return dest


def maac_games(pbp: pd.DataFrame, teams: list[str]) -> pd.DataFrame:
    """Every game with a MAAC team on EITHER side. Home-only is half the season."""
    return pbp[pbp.home_team_name.isin(teams) | pbp.away_team_name.isin(teams)]


def check_naming(pbp: pd.DataFrame, teams: list[str]) -> None:
    print("\n=== 1. team naming (config vs ESPN) ===")
    feed = set(pd.concat([pbp.home_team_name, pbp.away_team_name]).dropna())
    missing = [t for t in teams if t not in feed]
    print(f"{len(teams) - len(missing)}/{len(teams)} config names match ESPN exactly")
    if missing:
        print(f">>> NOT FOUND IN FEED: {missing}. Fix config before trusting the filter.")


def check_coverage(pbp: pd.DataFrame, teams: list[str]) -> None:
    print("\n=== 2. coverage (games per team, home + away) ===")
    for t in sorted(teams):
        g = pbp[(pbp.home_team_name == t) | (pbp.away_team_name == t)]
        print(f"  {t:18} games={g.game_id.nunique():3}  rows={len(g):7,}")


def check_subs(m: pd.DataFrame, rosters: pd.DataFrame) -> None:
    """The question the project lives or dies on.

    Walk each game-team's substitutions and check the on-court set stays at five.
    ESPN logs a substitution as a batch of separate one-athlete rows (two 'subbing
    out' then two 'subbing in'), so the set legitimately dips below five *mid
    batch*. Checking after every row reports a violation on every substitution and
    tells you nothing. The invariant only holds at stoppage boundaries.
    """
    print("\n=== 3. substitution events ===")
    subs = m[m.type_text == "Substitution"].copy()
    if subs.empty:
        print(">>> NO SUBSTITUTION EVENTS. Lineup reconstruction is off the table.")
        print(">>> Pivot the report to tendencies, shot distribution, and on/off proxies.")
        return

    subs["dir"] = subs.text.str.extract(r"subbing (in|out)", expand=False)
    print(f"  {len(subs):,} sub events over {m.game_id.nunique()} games "
          f"({len(subs) / m.game_id.nunique():.0f} per game)")
    print(f"  direction parsed from text: {subs['dir'].notna().mean():.1%} "
          f"({subs['dir'].value_counts().to_dict()})")
    print(f"  carry athlete_id_1: {subs.athlete_id_1.notna().mean():.1%}")

    bal = subs.groupby(["game_id", "team_id"])["dir"].value_counts().unstack(fill_value=0)
    bal["diff"] = bal.get("in", 0) - bal.get("out", 0)
    print(f"  game-teams with in/out balanced: {(bal['diff'] == 0).mean():.1%}")

    # Seed from the box score, not the play-by-play: period-start subs are
    # frequently missing, but game_rosters carries an explicit starter flag.
    starters = (rosters[rosters.starter]
                .groupby(["game_id", "team_id"]).athlete_id.apply(set).to_dict())
    subs = subs.sort_values(["game_id", "team_id", "period_number", "game_play_number"])

    stats, bad = Counter(), Counter()
    for (gid, tid), grp in subs.groupby(["game_id", "team_id"]):
        seed = starters.get((gid, int(tid)))
        if seed is None:
            stats["no_seed"] += 1
            continue
        stats["game_teams"] += 1
        on = set(seed)
        for _, batch in grp.groupby(["period_number", "clock_display_value"], sort=False):
            stats["batches"] += 1
            for _, e in batch.iterrows():
                a = int(e.athlete_id_1)
                if e["dir"] == "in":
                    stats["sub_in_already_on"] += a in on
                    on.add(a)
                else:
                    stats["sub_out_not_on"] += a not in on
                    on.discard(a)
            if len(on) != 5:
                stats["batch_violations"] += 1
                bad[(gid, tid)] += 1

    gt, b = stats["game_teams"], stats["batches"]
    print(f"\n  --- lineup walk: seed starters, apply subs, check size at each stoppage ---")
    print(f"  game-teams walked:  {gt:,} (no roster seed: {stats['no_seed']})")
    print(f"  clean game-teams:   {gt - len(bad):,}/{gt:,} = {(gt - len(bad)) / gt:.1%}")
    print(f"  clean sub batches:  {b - stats['batch_violations']:,}/{b:,} = "
          f"{1 - stats['batch_violations'] / b:.2%}")
    print(f"  contradictions:     {stats['sub_in_already_on']} in-already-on, "
          f"{stats['sub_out_not_on']} out-not-on (of {len(subs):,} events)")
    verdict = "VIABLE" if (gt - len(bad)) / gt > 0.9 else "PROBLEMATIC"
    print(f"  >>> lineup reconstruction: {verdict}")


def check_coords(m: pd.DataFrame) -> None:
    """Coordinates are never null, which is not the same as being present.

    notna() reads 100% because ESPN fills misses with an int32-min sentinel or
    parks them at the raw-frame centre point. Free throws are the bulk of that.
    Measure on field-goal attempts only.
    """
    print("\n=== 4. shot coordinates ===")
    sh = m[m.shooting_play == True]  # noqa: E712
    fg = sh[~sh.type_text.str.contains("FreeThrow", na=False)].copy()
    sent = (fg.coordinate_x_raw < SENTINEL) | (fg.coordinate_y_raw < SENTINEL)
    island = (fg.coordinate_x_raw == NULL_ISLAND[0]) & (fg.coordinate_y_raw == NULL_ISLAND[1])
    usable = fg[~sent & ~island]
    print(f"  shooting plays {len(sh):,}, of which field-goal attempts {len(fg):,}")
    print(f"  naive notna():      {fg.coordinate_x_raw.notna().mean():.1%}  <- misleading")
    print(f"  int32-min sentinel: {sent.mean():.2%}")
    print(f"  at null island {NULL_ISLAND}: {island.mean():.2%}")
    print(f"  USABLE:             {len(usable):,} = {len(usable) / len(fg):.1%}")

    # Geometry check. Raw frame is a half court with the basket at (25, 0).
    # The translated frame is a FULL court with baskets at (+/-41.75, 0), so it
    # must be folded to the nearer basket before it means anything.
    is3 = usable.score_value.where(usable.scoring_play, usable.points_attempted) == 3
    d_raw = np.hypot(usable.coordinate_x_raw - 25, usable.coordinate_y_raw)
    d_tr = np.minimum(np.hypot(usable.coordinate_x - 41.75, usable.coordinate_y),
                      np.hypot(usable.coordinate_x + 41.75, usable.coordinate_y))
    print(f"\n  --- geometry check against the {THREE_ARC} ft arc ---")
    for lbl, d in (("raw, basket (25,0)", d_raw), ("translated, folded to +/-41.75", d_tr)):
        print(f"  {lbl:32} 3PA median {d[is3].median():5.1f} ft | "
              f"3PA inside line {(d[is3] < THREE_CORNER).mean():5.1%} | "
              f"2PA outside line {(d[~is3] > THREE_ARC).mean():5.1%}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--season", type=int, default=2026,
                    help="season end-year; 2026 is the completed 2025-26 season")
    args = ap.parse_args()

    teams = load()["maac"]["teams"]
    pbp = pd.read_parquet(fetch(asset_url("pbp", args.season)))
    print(f"\nloaded {len(pbp):,} rows, {pbp.game_id.nunique():,} games "
          f"(season {args.season})")

    check_naming(pbp, teams)
    m = maac_games(pbp, teams)
    print(f"\nMAAC-involved: {len(m):,} rows, {m.game_id.nunique():,} games")
    check_coverage(pbp, teams)

    rosters = pd.read_parquet(fetch(asset_url("game_rosters", args.season)))
    check_subs(m, rosters[rosters.game_id.isin(set(m.game_id))])
    check_coords(m)


if __name__ == "__main__":
    main()
