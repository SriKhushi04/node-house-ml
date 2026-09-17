"""
Generates the next-24-hour solar PV energy yield forecast for the B01
representative fixed-site installation.

Run:
    python predict.py

Prints and saves (outputs/forecast_next_24h.json) JSON in the exact shape
the GridShare backend expects:

{
  "forecast": [
    {"timestamp": "...", "predictedEnergyKWh": 3.42},
    ...
  ]
}

How future clear-sky irradiance is obtained:
NASA POWER only has historical / near-real-time data — it has no future
values. CLRSKY_SFC_SW_DWN is a deterministic function of solar geometry
(location + time only, independent of actual weather), so instead of
pulling it from NASA POWER we compute it directly with pvlib for the next
24 hours. All other features (lags, rolling averages) are built from the
most recent historical actuals, per features.build_future_frame().
"""

import json

import numpy as np
import pandas as pd
import xgboost as xgb
from pvlib.location import Location

import config
import features
from fetch_data import fetch_historical_data


def get_future_clearsky_ghi(last_timestamp: pd.Timestamp, horizon_hours: int) -> pd.Series:
    """Deterministic clear-sky GHI for the next `horizon_hours` hours,
    computed with pvlib's Ineichen clear-sky model (UTC-indexed to match
    NASA POWER's UTC timestamps)."""
    site = Location(config.LATITUDE, config.LONGITUDE, tz="UTC")
    future_index = pd.date_range(
        start=last_timestamp + pd.Timedelta(hours=1),
        periods=horizon_hours,
        freq="h",
        tz="UTC",
    )
    clearsky = site.get_clearsky(future_index, model="ineichen")
    ghi = clearsky["ghi"]
    ghi.index = ghi.index.tz_localize(None)  # match NASA POWER's tz-naive UTC index
    return ghi


def main():
    print("=== 1. Loading trained model ===")
    model = xgb.XGBRegressor()
    model.load_model(config.MODEL_PATH)

    with open(config.FEATURE_LIST_PATH) as f:
        feature_cols = json.load(f)

    print("=== 2. Loading historical data (for lag features) ===")
    raw_df = fetch_historical_data()  # uses cache, won't re-hit the API
    full_index = pd.date_range(raw_df.index.min(), raw_df.index.max(), freq="h")
    history_df = raw_df.reindex(full_index).astype(float).interpolate(limit=3)
    history_df.index.name = "timestamp"

    last_timestamp = history_df.index.max()
    print(f"Most recent historical timestamp available: {last_timestamp}")

    print(f"=== 3. Computing deterministic clear-sky GHI for next {config.FORECAST_HORIZON_HOURS}h ===")
    future_clearsky = get_future_clearsky_ghi(last_timestamp, config.FORECAST_HORIZON_HOURS)

    print("=== 4. Building future feature frame ===")
    future_features = features.build_future_frame(history_df, future_clearsky)
    future_features = future_features[feature_cols]  # enforce exact training order

    print("=== 5. Predicting ===")
    preds = model.predict(future_features)
    preds = np.clip(preds, 0, None)

    forecast = [
        {
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "predictedEnergyKWh": round(float(val), 2),
        }
        for ts, val in zip(future_features.index, preds)
    ]

    output = {"forecast": forecast}

    with open(config.FORECAST_OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved forecast to {config.FORECAST_OUTPUT_PATH}\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
