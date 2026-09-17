"""
Pulls hourly historical data from the NASA POWER API for the configured
location and date range, and caches it to a local CSV so repeated runs
(training, experimentation) don't have to hit the API every time.

NASA POWER hourly endpoint docs:
https://power.larc.nasa.gov/docs/services/api/temporal/hourly/

No API key required.
"""

import os
import time
import requests
import pandas as pd

import config

BASE_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"

# The hourly endpoint restricts how large a single request's date range can
# be, so we pull it year by year and concatenate. This also makes retries
# on a single failed chunk cheap.
CHUNK_DAYS = 365


def _daterange_chunks(start_str, end_str, chunk_days=CHUNK_DAYS):
    start = pd.to_datetime(start_str, format="%Y%m%d")
    end = pd.to_datetime(end_str, format="%Y%m%d")
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + pd.Timedelta(days=chunk_days - 1), end)
        chunks.append((cur.strftime("%Y%m%d"), chunk_end.strftime("%Y%m%d")))
        cur = chunk_end + pd.Timedelta(days=1)
    return chunks


def _fetch_chunk(start, end, max_retries=3):
    params = {
        "start": start,
        "end": end,
        "latitude": config.LATITUDE,
        "longitude": config.LONGITUDE,
        "community": config.NASA_COMMUNITY,
        "parameters": ",".join(config.NASA_PARAMETERS),
        "format": "JSON",
        "time-standard": "UTC",
    }

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            param_data = payload["properties"]["parameter"]
            df = pd.DataFrame(param_data)
            # Index looks like "YYYYMMDDHH" strings -> parse to datetime
            df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
            df.index.name = "timestamp"
            return df
        except Exception as e:  # noqa: BLE001 - want to retry on anything
            last_err = e
            print(f"  chunk {start}-{end} attempt {attempt} failed: {e}")
            time.sleep(2 * attempt)

    raise RuntimeError(
        f"Failed to fetch chunk {start}-{end} after {max_retries} attempts: {last_err}"
    )


def fetch_historical_data(force_refresh=False):
    """
    Returns a DataFrame indexed by hourly UTC timestamp with columns
    matching config.NASA_PARAMETERS. Uses a local CSV cache unless
    force_refresh=True.
    """
    os.makedirs(config.DATA_DIR, exist_ok=True)

    if os.path.exists(config.RAW_CSV_PATH) and not force_refresh:
        print(f"Loading cached data from {config.RAW_CSV_PATH}")
        df = pd.read_csv(config.RAW_CSV_PATH, index_col="timestamp", parse_dates=True)
        return df

    print(
        f"Fetching NASA POWER hourly data for ({config.LATITUDE}, {config.LONGITUDE}) "
        f"from {config.START_DATE} to {config.END_DATE}..."
    )

    chunks = _daterange_chunks(config.START_DATE, config.END_DATE)
    frames = []
    for i, (start, end) in enumerate(chunks, 1):
        print(f"  [{i}/{len(chunks)}] pulling {start} -> {end}")
        frames.append(_fetch_chunk(start, end))

    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="first")]

    # NASA POWER uses -999 as a missing-value sentinel
    df = df.replace(-999, pd.NA)
    df = df.replace(-999.0, pd.NA)

    df.to_csv(config.RAW_CSV_PATH, index_label="timestamp")
    print(f"Saved {len(df)} rows to {config.RAW_CSV_PATH}")
    return df


if __name__ == "__main__":
    data = fetch_historical_data()
    print(data.head())
    print(data.tail())
    print(data.isna().sum())
