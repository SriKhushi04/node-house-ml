import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import config
import predict

app = FastAPI(title="GridShare ML API")

# Add CORS middleware for frontend calls
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "GridShare ML",
        "model": "XGBoost"
    }


@app.get("/forecast")
def get_forecast():
    try:
        # Generate fresh forecast using existing predict.py logic
        predict.main()

        # Read generated forecast output
        with open(config.FORECAST_OUTPUT_PATH, "r") as f:
            data = json.load(f)

        forecast_items = data.get("forecast", [])

        return {
            "buildingId": "b01",
            "location": "Chennai",
            "capacityKwp": config.PV_CAPACITY_KWP,
            "model": "XGBoost",
            "horizonHours": config.FORECAST_HORIZON_HOURS,
            "source": "NASA POWER",
            "forecast": forecast_items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")

