import pandas as pd
import requests
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/nflverse/nflverse-pbp/master/data"


def get_play_by_play(year: int) -> pd.DataFrame:
    """Download play-by-play data for a given year.

    Data is cached locally under ``data/`` to avoid repeated downloads.
    """
    filename = Path("data") / f"play_by_play_{year}.csv.gz"
    if filename.exists():
        return pd.read_csv(filename, compression="gzip")

    url = f"{BASE_URL}/play_by_play_{year}.csv.gz"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_bytes(resp.content)
    return pd.read_csv(filename, compression="gzip")
