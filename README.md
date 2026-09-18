# GridShare — Solar Forecast ML Module

Standalone module that trains an XGBoost model to forecast the next 24
hours of hourly solar PV energy yield for the "B01" representative
fixed-site installation, using NASA POWER historical data. Fully separate
from the GridShare Node.js backend — nothing here touches it.

## 1. Setup

```bash
cd ml-model
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Verify connectivity

```bash
python smoketest.py
```
This confirms your machine can reach the NASA POWER API and that pvlib's
clear-sky model runs correctly, before you commit to a full 3-year pull.

## 3. Train

```bash
python train.py
```
First run downloads ~3 years of hourly data from NASA POWER (chunked by
year, cached to `data/nasa_power_raw.csv` so it's only pulled once) and
trains the model. Outputs land in `outputs/`:
- `xgb_solar_model.json` — trained model
- `feature_list.json` — exact feature order the model expects
- `metrics.json` — RMSE / MAE / R² on the held-out test set
- `predicted_vs_actual.png` — plot for the hackathon deliverable

## 4. Predict the next 24 hours

```bash
python predict.py
```
Outputs `outputs/forecast_next_24h.json` in the exact shape the GridShare
backend expects:
```json
{
  "forecast": [
    {"timestamp": "2026-09-19T08:00:00", "predictedEnergyKWh": 3.42},
    ...
  ]
}
```

## Documented assumptions (per hackathon boundary conditions)

| Assumption | Value |
|---|---|
| Location | Chennai — 13.08°N, 80.27°E |
| PV capacity | 5 kWp |
| Tilt | 13° (≈ latitude, standard fixed-tilt rule of thumb) |
| Panel efficiency | 19% (documentation only — already reflected in the kWp STC rating) |
| System derate | 0.85 |
| Historical data | 3 years, hourly, NASA POWER `RE` community |
| Forecast horizon | 24 hours ahead |
| Train/test split | Time-based (no shuffling), 20% held out for test |

## Methodology notes

**Target variable.** NASA POWER doesn't provide energy yield directly —
it's derived from `ALLSKY_SFC_SW_DWN` (all-sky GHI, W/m²) via a simplified
PVWatts-style formula:
```
energy_kWh = capacity_kWp * (GHI / 1000) * derate
```
This uses GHI as a proxy for plane-of-array irradiance, a standard
simplification for near-latitude fixed-tilt systems; a full DNI/DHI
transposition model was out of scope for this build.

**Avoiding lookahead leakage.** A forecast made 24h ahead can't use actual
future weather as an input — that defeats the point. Every feature is
either:
- **Deterministic and knowable in advance**: clear-sky GHI
  (`CLRSKY_SFC_SW_DWN` historically, computed via `pvlib`'s Ineichen model
  for future timestamps since NASA POWER has no future data) and cyclical
  time-of-day/time-of-year encodings.
- **Lagged ≥24h**: same-hour actuals from 1/2/3 days ago, plus a 3-day
  rolling mean of irradiance, as a persistence/pattern signal.

**Model.** `XGBRegressor`, `n_estimators=500`, `max_depth=6`,
`learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`,
`min_child_weight=3`, `objective=reg:squarederror`. Full hyperparameters
are also saved into `outputs/metrics.json` for the writeup.

## Next step: integrating into GridShare

Not done yet by design — model should be validated standalone first. Once
you're happy with the metrics, the plan is:
1. Wrap `predict.py`'s logic in a small FastAPI/Flask service (or a single
   endpoint) that returns the same JSON shape.
2. Node backend's `services/` layer calls that service and forwards the
   JSON to the new "Solar Forecast" tab.
3. Per-house scaling (once B02–B05 get their own kWp values) is just
   `predictedEnergyKWh * (house_kwp / 5.0)` — no retraining needed.
