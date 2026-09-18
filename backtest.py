"""
Backtest the trained GridShare solar forecasting model on multiple
24-hour periods from the held-out test period.

The model is NOT retrained.

For every backtest date:
- Only historical data before that date is used for lag features.
- Clear-sky GHI is calculated deterministically using pvlib.
- The trained XGBoost model predicts the next 24 hours.
- Predictions are compared against actual historical energy yield.
"""

import json
import os

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pvlib.location import Location

import config
import features


# ----------------------------------------------------------------------
# Dates to test
# All dates are inside the held-out test period.
# ----------------------------------------------------------------------

BACKTEST_DATES = [
    "2026-01-15",
    "2026-02-15",
    "2026-03-15",
    "2026-04-15",
    "2026-05-15",
]


# ----------------------------------------------------------------------
# Same clear-sky calculation as predict.py
# ----------------------------------------------------------------------

def get_future_clearsky_ghi(
    forecast_start: pd.Timestamp,
    horizon_hours: int
) -> pd.Series:
    """
    Calculate deterministic clear-sky GHI for the forecast period.

    Uses the exact same pvlib Ineichen model and UTC convention
    as predict.py.
    """

    site = Location(
        config.LATITUDE,
        config.LONGITUDE,
        tz="UTC"
    )

    future_index = pd.date_range(
        start=forecast_start,
        periods=horizon_hours,
        freq="h",
        tz="UTC",
    )

    clearsky = site.get_clearsky(
        future_index,
        model="ineichen"
    )

    ghi = clearsky["ghi"]

    # Match NASA POWER's timezone-naive UTC index
    ghi.index = ghi.index.tz_localize(None)

    return ghi


# ----------------------------------------------------------------------
# 1. Load trained model
# ----------------------------------------------------------------------

print("=== 1. Loading trained model ===")

model = xgb.XGBRegressor()
model.load_model(config.MODEL_PATH)

with open(config.FEATURE_LIST_PATH, "r") as f:
    feature_cols = json.load(f)

print(f"Loaded model from {config.MODEL_PATH}")
print(f"Using {len(feature_cols)} features.")


# ----------------------------------------------------------------------
# 2. Load historical NASA POWER data
# ----------------------------------------------------------------------

print("\n=== 2. Loading historical data ===")

raw_df = pd.read_csv(
    config.RAW_CSV_PATH,
    index_col="timestamp",
    parse_dates=True,
)

raw_df = raw_df.sort_index()

full_index = pd.date_range(
    raw_df.index.min(),
    raw_df.index.max(),
    freq="h"
)

raw_df = (
    raw_df
    .reindex(full_index)
    .astype(float)
    .interpolate(limit=3)
)

raw_df.index.name = "timestamp"

print(
    f"Historical data: "
    f"{raw_df.index.min()} -> {raw_df.index.max()}"
)


# ----------------------------------------------------------------------
# 3. Build target using the same feature engineering as training
# ----------------------------------------------------------------------

print("\n=== 3. Building target data ===")

full_df = features.build_training_frame(raw_df)

print(f"Usable rows: {len(full_df)}")


# ----------------------------------------------------------------------
# 4. Run backtests
# ----------------------------------------------------------------------

print("\n=== 4. Running 24-hour backtests ===")

results = []

for date_string in BACKTEST_DATES:

    print(f"\n--- Testing {date_string} ---")

    forecast_start = pd.Timestamp(date_string)

    # --------------------------------------------------------------
    # We want exactly 24 hours:
    #
    # date 00:00
    # date 01:00
    # ...
    # date 23:00
    # --------------------------------------------------------------

    future_index = pd.date_range(
        start=forecast_start,
        periods=config.FORECAST_HORIZON_HOURS,
        freq="h",
    )

    # --------------------------------------------------------------
    # CRITICAL:
    # Only data BEFORE the forecast date is available to the model.
    # --------------------------------------------------------------

    history_df = raw_df.loc[
        raw_df.index < forecast_start
    ].copy()

    print(
        f"Historical cutoff: "
        f"{history_df.index.max()}"
    )

    # --------------------------------------------------------------
    # Calculate future clear-sky GHI.
    # This is deterministic and therefore legitimately known
    # for the forecast period.
    # --------------------------------------------------------------

    future_clearsky = get_future_clearsky_ghi(
        forecast_start,
        config.FORECAST_HORIZON_HOURS
    )

    # --------------------------------------------------------------
    # Build lag/rolling/time features.
    # --------------------------------------------------------------

    future_features = features.build_future_frame(
        history_df,
        future_clearsky
    )

    # Ensure exact feature order used during training.
    future_features = future_features[feature_cols]

    # --------------------------------------------------------------
    # Predict
    # --------------------------------------------------------------

    predictions = model.predict(
        future_features
    )

    predictions = np.clip(
        predictions,
        0,
        None
    )

    # --------------------------------------------------------------
    # Actual historical energy yield
    # --------------------------------------------------------------

    actual = full_df.loc[
        future_index,
        "energy_kwh"
    ].to_numpy()

    # --------------------------------------------------------------
    # Metrics
    # --------------------------------------------------------------

    mae = mean_absolute_error(
        actual,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predictions
        )
    )
    r2 = r2_score(actual, predictions)

    actual_total = actual.sum()
    predicted_total = predictions.sum()

    results.append({
        "date": date_string,
        "mae_kwh": float(mae),
        "rmse_kwh": float(rmse),
        "r2": float(r2),
        "actual_total_kwh": float(actual_total),
        "predicted_total_kwh": float(predicted_total),
    })

    print(f"MAE:              {mae:.4f} kWh")
    print(f"RMSE:             {rmse:.4f} kWh")
    print(f"R²:               {r2:.4f}")
    print(f"Actual total:     {actual_total:.2f} kWh")
    print(f"Predicted total:  {predicted_total:.2f} kWh")


# ----------------------------------------------------------------------
# 5. Save results
# ----------------------------------------------------------------------

results_df = pd.DataFrame(results)

os.makedirs(
    config.OUTPUT_DIR,
    exist_ok=True
)

output_path = os.path.join(
    config.OUTPUT_DIR,
    "backtest_results.csv"
)

results_df.to_csv(
    output_path,
    index=False
)


# ----------------------------------------------------------------------
# 6. Summary
# ----------------------------------------------------------------------

print("\n=== 5. Backtest summary ===")

print(
    results_df.to_string(index=False)
)

print("\nAverage MAE:")
print(
    f"{results_df['mae_kwh'].mean():.4f} kWh"
)

print("\nAverage RMSE:")
print(
    f"{results_df['rmse_kwh'].mean():.4f} kWh"
)

print("\nAverage R²:")
print(
    f"{results_df['r2'].mean():.4f}"
)

print(
    f"\nSaved results to {output_path}"
)

print("\nBacktest complete.")