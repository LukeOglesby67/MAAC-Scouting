"""Women's college basketball ingestion via wehoop release artifacts.

Why this and not scraping: the sportsdataverse/wehoop-wbb-data repo publishes
already-processed play-by-play, team box, and player box data as GitHub release
assets. They are parquet files. Downloading them takes minutes, works from
Python despite wehoop being an R package, and avoids ESPN rate limiting
entirely. Scraping game by game is the version of this project that does not
finish before the season starts.

Size warning: every season is roughly 7 million rows and 1-2 GB. Pull only the
seasons in config. For MAAC scouting, 2024-2026 is plenty.

Player box scores from here feed BOTH tracks: scouting needs them for personnel
context, and the translation model needs NCAA production as an input. Land them
once.
"""
import pandas as pd

from scout.config import load, ensure_dirs, ROOT
from scout.ingest.base import land


def fetch(dataset: str, season: int) -> pd.DataFrame:
    """Download one season of one dataset from the wehoop release assets.

    dataset is one of: pbp, team_box, player_box.
    TODO: confirm the release tag and asset filename pattern from
    github.com/sportsdataverse/wehoop-wbb-data releases, then build the URL
    from config rather than hardcoding it here.
    """
    raise NotImplementedError


def main() -> None:
    ensure_dirs()
    cfg = load()["wbb"]
    out = ROOT / cfg["raw_path"]
    for dataset in cfg["datasets"]:
        for season in cfg["seasons"]:
            df = fetch(dataset, season)
            land(df, out / dataset, season, f"wbb_{dataset}")


if __name__ == "__main__":
    main()
