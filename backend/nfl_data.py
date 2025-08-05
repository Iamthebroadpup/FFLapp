import pandas as pd
import requests
from pathlib import Path

# Base download URL for nflverse play-by-play data releases
BASE_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp"


def get_play_by_play(year: int) -> pd.DataFrame:
    """Download play-by-play data for a given year.

    Data is cached locally under ``data/`` to avoid repeated downloads.
    Files are stored as ``.parquet``.
    """
    filename = Path("data") / f"play_by_play_{year}.parquet"
    if filename.exists():
        return pd.read_parquet(filename)

    url = f"{BASE_URL}/play_by_play_{year}.parquet"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_bytes(resp.content)
    return pd.read_parquet(filename)
