"""
Central configuration for the GridShare Solar Forecast model.
All assumptions declared here so they can be cited directly in the
hackathon writeup / documentation.
"""

from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# 1. Location — Chennai
# ----------------------------------------------------------------------
LATITUDE = 13.08
LONGITUDE = 80.27
TIMEZONE = "Asia/Kolkata"  # UTC+5:30, no DST

# ----------------------------------------------------------------------
# 2. Representative PV system — "B01"
# ----------------------------------------------------------------------
PV_CAPACITY_KWP = 5.0     # rated DC capacity at STC (1000 W/m^2, 25C)
PV_TILT_DEG = 13.0        # fixed tilt, ~ latitude (standard rule of thumb)
PV_EFFICIENCY = 0.19      # panel efficiency (documented assumption; already
                           # implicitly reflected in the kWp STC rating —
                           # kept here for documentation completeness)
PV_DERATE = 0.85          # system losses / derate factor (inverter loss,
                           # wiring, soiling, temperature effects, etc.)

# ----------------------------------------------------------------------
# 3. Historical data range — 3 years of hourly data
# ----------------------------------------------------------------------
# NASA POWER hourly data has a short reporting lag (data usually available
# up to ~2-3 days before "today"). We anchor END_DATE a few days in the
# past to avoid requesting a window that doesn't exist yet.
START_DATE = "20230601"
END_DATE = "20260531"
# ----------------------------------------------------------------------
# 4. NASA POWER API parameters pulled
# ----------------------------------------------------------------------
# ALLSKY_SFC_SW_DWN : actual (all-sky) GHI, W/m^2  -> used to build target
# CLRSKY_SFC_SW_DWN : theoretical clear-sky GHI, W/m^2 -> fully deterministic
#                     from solar geometry, so it is KNOWN in advance and is
#                     safe to use as a feature for next-day forecasting
# T2M               : temperature at 2m, deg C
# RH2M              : relative humidity at 2m, %
# WS2M              : wind speed at 2m, m/s
NASA_PARAMETERS = [
    "ALLSKY_SFC_SW_DWN",
    "CLRSKY_SFC_SW_DWN",
    "T2M",
    "RH2M",
    "WS2M",
]
NASA_COMMUNITY = "RE"  # Renewable Energy community

# ----------------------------------------------------------------------
# 5. Forecast horizon
# ----------------------------------------------------------------------
FORECAST_HORIZON_HOURS = 24

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
DATA_DIR = "data"
OUTPUT_DIR = "outputs"
RAW_CSV_PATH = f"{DATA_DIR}/nasa_power_raw.csv"
MODEL_PATH = f"{OUTPUT_DIR}/xgb_solar_model.json"
FEATURE_LIST_PATH = f"{OUTPUT_DIR}/feature_list.json"
METRICS_PATH = f"{OUTPUT_DIR}/metrics.json"
PLOT_PATH = f"{OUTPUT_DIR}/predicted_vs_actual.png"
FORECAST_OUTPUT_PATH = f"{OUTPUT_DIR}/forecast_next_24h.json"
