"""
Trains the XGBoost solar-yield forecasting model.

Run:
    python train.py

Outputs (in outputs/):
    xgb_solar_model.json     - trained model
    feature_list.json        - exact feature column order the model expects
    metrics.json             - RMSE / MAE on the held-out test set
    predicted_vs_actual.png  - plot for the hackathon deliverable
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

import config
import features
from fetch_data import fetch_historical_data

# ----------------------------------------------------------------------
# Documented hyperparameters (per hackathon requirement: model type,
# features, and hyperparameters must be stated explicitly)
# ----------------------------------------------------------------------
XGB_PARAMS = dict(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
)

TEST_FRACTION = 0.2  # minimum 20% held out, per problem statement


def time_based_split(df: pd.DataFrame, test_fraction: float = TEST_FRACTION):
    split_idx = int(len(df) * (1 - test_fraction))
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    return train_df, test_df


def main():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    print("=== 1. Loading historical NASA POWER data ===")
    raw_df = fetch_historical_data()

    print("=== 2. Building features + target ===")
    df = features.build_training_frame(raw_df)
    feature_cols = features.get_feature_columns()
    print(f"Rows after feature engineering / dropna: {len(df)}")
    print(f"Feature columns ({len(feature_cols)}): {feature_cols}")

    print("=== 3. Time-based train/test split ===")
    train_df, test_df = time_based_split(df)
    print(f"Train: {len(train_df)} rows ({train_df.index.min()} -> {train_df.index.max()})")
    print(f"Test:  {len(test_df)} rows ({test_df.index.min()} -> {test_df.index.max()})")
    print(f"Test fraction: {len(test_df) / len(df):.3f}")

    X_train, y_train = train_df[feature_cols], train_df[features.TARGET_COL]
    X_test, y_test = test_df[feature_cols], test_df[features.TARGET_COL]

    print("=== 4. Training XGBoost ===")
    print(f"Hyperparameters: {XGB_PARAMS}")
    model = xgb.XGBRegressor(**XGB_PARAMS)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    print("=== 5. Evaluating on held-out test set ===")
    preds = model.predict(X_test)
    preds = np.clip(preds, 0, None)  # yield can't be negative

    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae = float(mean_absolute_error(y_test, preds))
    print(f"RMSE: {rmse:.4f} kWh")
    print(f"MAE:  {mae:.4f} kWh")

    metrics = {
        "rmse_kwh": rmse,
        "mae_kwh": mae,
        "test_rows": len(test_df),
        "train_rows": len(train_df),
        "test_fraction": len(test_df) / len(df),
        "hyperparameters": XGB_PARAMS,
        "feature_columns": feature_cols,
    }
    with open(config.METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {config.METRICS_PATH}")

    print("=== 6. Saving model + feature list ===")
    model.save_model(config.MODEL_PATH)
    with open(config.FEATURE_LIST_PATH, "w") as f:
        json.dump(feature_cols, f, indent=2)
    print(f"Saved model to {config.MODEL_PATH}")

    print("=== 7. Plotting predicted vs actual (last 7 days of test set) ===")
    plot_slice = test_df.iloc[-24 * 7 :].copy()
    plot_preds = np.clip(model.predict(plot_slice[feature_cols]), 0, None)

    plt.figure(figsize=(14, 5))
    plt.plot(plot_slice.index, plot_slice[features.TARGET_COL], label="Actual", linewidth=1.5)
    plt.plot(plot_slice.index, plot_preds, label="Predicted", linewidth=1.5, linestyle="--")
    plt.title("Solar PV Energy Yield — Predicted vs Actual (last 7 days of test set)")
    plt.xlabel("Timestamp")
    plt.ylabel("Energy Yield (kWh)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(config.PLOT_PATH, dpi=150)
    print(f"Saved plot to {config.PLOT_PATH}")

    print("\nDone.")


if __name__ == "__main__":
    main()
