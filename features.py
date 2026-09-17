"""
Feature engineering shared by train.py and predict.py.

Design principle: every feature used to predict energy yield at time t must
be something that is ACTUALLY KNOWN 24 hours before t. That rules out using
same-hour weather (T2M, RH2M, ALLSKY_SFC_SW_DWN at time t) as a feature,
since that's the actual future we don't have yet. Instead we use:

  1. Deterministic solar-geometry features (clear-sky GHI) — computable for
     any future timestamp regardless of weather.
  2. Cyclical time-of-day / time-of-year encodings.
  3. Lag / rolling features built ONLY from data at least 24h in the past
     (same-hour yesterday, same-hour 2 days ago, 3-day rolling mean, etc.)
     as a proxy for "recent weather pattern / persistence".
"""

import numpy as np
import pandas as pd

import config

TARGET_COL = "energy_kwh"

LAG_HOURS = [24, 48, 72]        # 1, 2, 3 days back
ROLL_WINDOW_DAYS = 3            # rolling mean window (in days, same-hour)


def add_target(df: pd.DataFrame) -> pd.DataFrame:
    """PV yield (kWh) from GHI using a simplified PVWatts-style model:
    energy_kWh = capacity_kWp * (GHI / 1000) * derate

    Note: capacity_kWp is the STC-rated DC capacity, which already reflects
    panel efficiency. Tilt is approximated as accounted for by choosing a
    near-latitude tilt (13 deg for Chennai at 13.08N), a standard rule of
    thumb that keeps GHI a reasonable proxy for plane-of-array irradiance
    without requiring a full DNI/DHI transposition model (out of scope for
    this hackathon build).
    """
    df = df.copy()
    df[TARGET_COL] = (
        config.PV_CAPACITY_KWP * (df["ALLSKY_SFC_SW_DWN"] / 1000.0) * config.PV_DERATE
    )
    # Yield can't be negative; clip tiny negative artifacts from raw data
    df[TARGET_COL] = df[TARGET_COL].clip(lower=0)
    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    hour = df.index.hour
    doy = df.index.dayofyear

    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Lag/rolling features built only from data >=24h old, using ffill-safe
    shifts on an hourly-frequency index."""
    df = df.copy()

    for col in ["ALLSKY_SFC_SW_DWN", "T2M", "RH2M", "WS2M"]:
        for lag in LAG_HOURS:
            df[f"{col}_lag{lag}h"] = df[col].shift(lag)

    # Rolling mean irradiance over the past N days ("how sunny has it been
    # recently"), computed from data that is already >=24h old (shift(24)
    # first, then roll over a ROLL_WINDOW_DAYS*24-hour window).
    shifted = df["ALLSKY_SFC_SW_DWN"].shift(24)
    window_hours = ROLL_WINDOW_DAYS * 24
    df["allsky_roll_mean_3d"] = shifted.rolling(window=window_hours, min_periods=24).mean()

    return df


def get_feature_columns():
    lag_cols = [
        f"{col}_lag{lag}h"
        for col in ["ALLSKY_SFC_SW_DWN", "T2M", "RH2M", "WS2M"]
        for lag in LAG_HOURS
    ]
    return (
        ["CLRSKY_SFC_SW_DWN", "hour_sin", "hour_cos", "doy_sin", "doy_cos"]
        + lag_cols
        + ["allsky_roll_mean_3d"]
    )


def build_future_frame(history_df: pd.DataFrame, future_clearsky: pd.Series) -> pd.DataFrame:
    """Builds the feature frame for the next N future hourly timestamps.

    history_df: gap-free hourly historical actuals (ALLSKY_SFC_SW_DWN, T2M,
                RH2M, WS2M, CLRSKY_SFC_SW_DWN), most recent data available.
    future_clearsky: Series indexed by the future timestamps to forecast,
                values = deterministic clear-sky GHI (e.g. from pvlib),
                since this is knowable in advance regardless of weather.

    Returns a DataFrame indexed by the future timestamps, with exactly the
    columns from get_feature_columns(), ready for model.predict().
    """
    history_df = history_df.copy()
    future_index = future_clearsky.index

    # Combine history + future placeholder rows so lag/rolling shifts line
    # up naturally on a single continuous hourly index. Future actual
    # weather columns are left NaN (unknown) — lag features for the future
    # rows will always resolve to historical (known) values, since the
    # forecast horizon (<=24h in this project) is shorter than the shift
    # amounts used for lags (24h+).
    future_placeholder = pd.DataFrame(index=future_index, columns=history_df.columns, dtype=float)
    future_placeholder["CLRSKY_SFC_SW_DWN"] = future_clearsky.values

    combined = pd.concat([history_df, future_placeholder])
    combined = combined[~combined.index.duplicated(keep="first")].sort_index()

    combined = add_time_features(combined)
    combined = add_lag_features(combined)

    feature_cols = get_feature_columns()
    future_features = combined.loc[future_index, feature_cols]

    missing = future_features[feature_cols].isna().any(axis=1)
    if missing.any():
        raise ValueError(
            "Some future feature rows have NaNs (likely not enough historical "
            f"lookback in history_df). Affected timestamps:\n{future_features[missing].index.tolist()}"
        )

    return future_features


def build_training_frame(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Full pipeline: raw NASA POWER df -> features + target, NaNs dropped
    (NaNs only occur in the first few days of warm-up for lag features, or
    from missing NASA POWER readings)."""
    df = raw_df.copy()

    # Ensure a complete, gap-free hourly index so lag/rolling math is valid
    full_index = pd.date_range(df.index.min(), df.index.max(), freq="h")
    df = df.reindex(full_index)
    df.index.name = "timestamp"
    df = df.astype(float).interpolate(limit=3)  # patch tiny gaps only

    df = add_target(df)
    df = add_time_features(df)
    df = add_lag_features(df)

    feature_cols = get_feature_columns()
    df = df.dropna(subset=feature_cols + [TARGET_COL])
    return df
