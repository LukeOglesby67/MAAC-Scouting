"""Women's college basketball ingestion via wehoop release artifacts.

Why this and not scraping: the sportsdataverse/wehoop-wbb-data repo builds
already-processed play-by-play, box score, and roster data and publishes it as
GitHub release assets on sportsdataverse/sportsdataverse-data. They are parquet
files. Downloading them takes minutes, works from Python despite wehoop being an
R package, and avoids ESPN rate limiting entirely. Scraping game by game is the
version of this project that does not finish before the season starts.

Size: pbp is 51-92 MB per season as parquet. All four datasets for 2024-2026 is
about 215 MB, so the working set fits locally without ceremony.

RAW MEANS RAW. Nothing here filters to the MAAC, renames a column, or coerces a
type. The MAAC filter lives in transform/, because a filter applied at ingest is
a filter you cannot undo in November without re-pulling the season.
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import requests

from scout.config import ROOT, ensure_dirs, load
from scout.ingest.base import land

# Downloaded assets are cached here so a re-run does not re-pull 200 MB. This is
# a download cache, not the raw layer: the raw layer is what land() writes.
CACHE = ROOT / "data" / "raw" / "_cache"

TIMEOUT = 60
RETRIES = 4


def asset_url(dataset: str, season: int) -> str:
    """Build a release asset URL from config. No URL is hardcoded anywhere."""
    cfg = load()["wbb"]
    try:
        tag, stem = cfg["release_tags"][dataset], cfg["file_stems"][dataset]
    except KeyError as exc:
        raise KeyError(
            f"dataset {dataset!r} has no release tag or file stem in "
            f"config/sources.yml (known: {sorted(cfg['release_tags'])})"
        ) from exc
    return f"{cfg['release_base']}/{tag}/{stem}_{season}.parquet"


def download(url: str, dest: Path, *, refresh: bool = False) -> Path:
    """Download with retries, resumable-by-restart, and a conditional GET.

    The upstream feed rebuilds daily during the season, so a plain "skip if the
    file exists" cache would quietly serve stale data mid-season. Instead the
    asset's ETag is stored next to it and sent back as If-None-Match: unchanged
    upstream costs one 304 and no transfer, changed upstream re-pulls.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    etag_file = dest.with_suffix(dest.suffix + ".etag")

    headers = {}
    if dest.exists() and not refresh and etag_file.exists():
        headers["If-None-Match"] = etag_file.read_text().strip()

    delay = 2
    for attempt in range(1, RETRIES + 1):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=TIMEOUT) as r:
                if r.status_code == 304:
                    print(f"  unchanged upstream, using cache: {dest.name}")
                    return dest
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                total = int(r.headers.get("content-length", 0))
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
                if total and tmp.stat().st_size != total:
                    raise OSError(
                        f"short read: got {tmp.stat().st_size} of {total} bytes"
                    )
                tmp.rename(dest)
                if r.headers.get("etag"):
                    etag_file.write_text(r.headers["etag"])
                print(f"  downloaded {dest.name} ({dest.stat().st_size / 1e6:.0f} MB)")
                return dest
        except (requests.RequestException, OSError) as exc:
            if attempt == RETRIES:
                raise
            print(f"  attempt {attempt}/{RETRIES} failed ({exc}); retrying in {delay}s")
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def fetch(dataset: str, season: int, *, refresh: bool = False) -> pd.DataFrame:
    """Download one season of one dataset and read it unchanged.

    dataset is one of the keys in config's release_tags: pbp, team_box,
    player_box, shots, game_rosters.

    dtype_backend="pyarrow" is load-bearing, not a preference. pandas' default
    numpy backend has no nullable integer, so any id column containing a null
    comes back as float64: game_rosters.athlete_id is int32 upstream with two
    nulls, and the default read silently lands it as double. That breaks the
    join key every downstream mart depends on, and it violates the no-coercion
    rule while looking like a clean ingest. With the arrow backend the landed
    schema matches upstream exactly, column for column.
    """
    url = asset_url(dataset, season)
    print(f"{dataset} {season}: {url}")
    path = download(url, CACHE / f"{dataset}_{season}.parquet", refresh=refresh)
    return pd.read_parquet(path, dtype_backend="pyarrow")


def main() -> None:
    cfg = load()["wbb"]
    ap = argparse.ArgumentParser(description="Land wehoop release assets into data/raw.")
    ap.add_argument("--dataset", action="append", choices=sorted(cfg["release_tags"]),
                    help="dataset to pull; repeatable. Default: config's datasets.")
    ap.add_argument("--season", action="append", type=int,
                    help="season end-year; repeatable. Default: config's seasons.")
    ap.add_argument("--refresh", action="store_true",
                    help="bypass the ETag check and re-download. Use if a cached "
                         "asset looks wrong; in-season staleness is handled already.")
    args = ap.parse_args()

    ensure_dirs()
    datasets = args.dataset or cfg["datasets"]
    seasons = args.season or cfg["seasons"]
    out = ROOT / cfg["raw_path"]

    landed = []
    for dataset in datasets:
        for season in seasons:
            df = fetch(dataset, season, refresh=args.refresh)
            path = land(df, out / dataset, season, f"wbb_{dataset}")
            landed.append((dataset, season, len(df), path))

    print(f"\nlanded {len(landed)} extracts:")
    for dataset, season, n, path in landed:
        print(f"  {dataset:14} {season}  {n:>9,} rows  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
