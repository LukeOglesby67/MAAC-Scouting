"""Shared ingestion contract.

Rule for every ingest module: land the source's data unchanged.
No renaming, no type coercion, no filtering. Cleaning happens in transform/.
If ingestion transforms, a bad decision made in July is unrecoverable in November
without re-hitting the source.
"""
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd


def land(df: pd.DataFrame, path: Path, season: int, source: str) -> Path:
    """Write a raw extract with provenance columns attached."""
    path.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["_source"] = source
    df["_season"] = season
    df["_ingested_at"] = datetime.now(timezone.utc).isoformat()

    out = path / f"{source}_{season}.parquet"
    df.to_parquet(out, index=False)
    print(f"landed {len(df):,} rows -> {out}")
    return out
