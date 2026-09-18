"""Config loading. Every module reads paths and parameters from here."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW, STAGING, MARTS = DATA / "raw", DATA / "staging", DATA / "marts"


def load(name: str = "sources") -> dict:
    with open(ROOT / "config" / f"{name}.yml") as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    for p in (RAW, STAGING, MARTS):
        p.mkdir(parents=True, exist_ok=True)


def maac_teams() -> list[str]:
    return load()["maac"]["teams"]
