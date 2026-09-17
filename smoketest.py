"""
Run this FIRST, before train.py, to confirm your local environment can
actually reach the NASA POWER API and that pvlib is working.

    python smoketest.py
"""

import requests
import config


def check_nasa_api():
    print("Checking NASA POWER API connectivity...")
    params = {
        "start": "20240101",
        "end": "20240102",
        "latitude": config.LATITUDE,
        "longitude": config.LONGITUDE,
        "community": config.NASA_COMMUNITY,
        "parameters": ",".join(config.NASA_PARAMETERS),
        "format": "JSON",
    }
    resp = requests.get(
        "https://power.larc.nasa.gov/api/temporal/hourly/point",
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    sample_param = config.NASA_PARAMETERS[0]
    sample = data["properties"]["parameter"][sample_param]
    print(f"  OK — got {len(sample)} hourly rows for {sample_param}")
    first_key = next(iter(sample))
    print(f"  Example: {first_key} -> {sample[first_key]}")


def check_pvlib():
    print("Checking pvlib clear-sky computation...")
    from pvlib.location import Location
    import pandas as pd

    site = Location(config.LATITUDE, config.LONGITUDE, tz="UTC")
    times = pd.date_range("2024-06-01 00:00", periods=24, freq="h", tz="UTC")
    clearsky = site.get_clearsky(times)
    peak = clearsky["ghi"].max()
    print(f"  OK — computed 24h clear-sky curve, peak GHI = {peak:.1f} W/m^2")


if __name__ == "__main__":
    check_nasa_api()
    check_pvlib()
    print("\nEnvironment looks good. You can run: python train.py")
