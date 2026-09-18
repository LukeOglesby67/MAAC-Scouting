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
    python scripts/probe_pbp.py
"""
import pandas as pd

# The wehoop project publishes processed data as GitHub release artifacts in
# sportsdataverse/wehoop-wbb-data. Confirm the exact release tag and asset
# filename from that repo's releases page, then set it here. Parquet reads
# fine from a URL, which is why none of this needs R.
PBP_URL = None  # e.g. ".../espn_womens_college_basketball_pbp_2026.parquet"

QUINNIPIAC = "Quinnipiac"


def main() -> None:
    if PBP_URL is None:
        raise SystemExit(
            "Set PBP_URL first. Go to github.com/sportsdataverse/wehoop-wbb-data,\n"
            "open Releases, and copy the play-by-play asset URL for the season you want."
        )

    pbp = pd.read_parquet(PBP_URL)
    print(f"loaded {len(pbp):,} rows, {pbp['game_id'].nunique():,} games")
    print(f"\ncolumns:\n{list(pbp.columns)}")

    # 1. Are substitution events present at all?
    types = pbp["type_text"].value_counts()
    print(f"\n--- event types ({len(types)}) ---")
    print(types.to_string())
    subs = types[types.index.str.contains("sub", case=False, na=False)]
    print(f"\nsubstitution-like events: {len(subs)} types, {subs.sum():,} rows")
    if subs.empty:
        print(">>> NO SUBSTITUTION EVENTS. Lineup reconstruction is off the table.")
        print(">>> Pivot the report to tendencies, shot distribution, and on/off proxies.")

    # 2. Do they carry the player going in AND out? Reconstruction needs both.
    if not subs.empty:
        sample = pbp[pbp["type_text"].isin(subs.index)].head(10)
        print("\n--- sample substitution rows ---")
        print(sample[[c for c in ("text", "athlete_id_1", "athlete_id_2", "team_id")
                      if c in sample.columns]].to_string())

    # 3. Shot coordinates: present, and how often?
    coord_cols = [c for c in pbp.columns if "coordinate" in c.lower()]
    print(f"\n--- shot coordinates ---\ncolumns: {coord_cols}")
    for c in coord_cols:
        print(f"{c}: {pbp[c].notna().mean():.1%} populated")

    # 4. Does it actually cover Quinnipiac and the MAAC?
    team_cols = [c for c in pbp.columns if "team" in c.lower() and "name" in c.lower()]
    if team_cols:
        col = team_cols[0]
        qu = pbp[pbp[col].astype(str).str.contains(QUINNIPIAC, case=False, na=False)]
        print(f"\nQuinnipiac rows: {len(qu):,} across {qu['game_id'].nunique()} games")
        if qu.empty:
            print(">>> Check the team naming convention before assuming no coverage.")


if __name__ == "__main__":
    main()
