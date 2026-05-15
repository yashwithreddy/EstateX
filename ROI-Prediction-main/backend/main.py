"""
main.py
-------
FastAPI application exposing:
  POST /predict_roi  →  ROI prediction + 5-year forecast
  GET  /health       →  service health check
  GET  /             →  API info

Run with:
  uvicorn backend.main:app --reload --port 8000
  (from the project root: c:\\Users\\91871\\Downloads\\realestate)
"""

import os
import sys
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Path setup ────────────────────────────────────────────────────────────────
# Add the training/ directory so roi_predictor can import feature_engineering
TRAINING_DIR = os.path.join(os.path.dirname(__file__), "..", "training")
sys.path.insert(0, TRAINING_DIR)

# Also add backend/ directory itself to path so 'schemas' module resolves
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)
from roi_predictor import predict_roi        # noqa: E402  # pylint: disable=wrong-import-position
from risk_model_training import predict_risk  # noqa: E402  # pylint: disable=wrong-import-position
from schemas import (
    PropertyInput,
    ROIPredictionResponse,
    RiskPredictionRequest,
    RiskPredictionResponse,
)  # noqa: E402  # pylint: disable=wrong-import-position

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Real Estate ROI Predictor",
    description=(
        "ML-powered API to predict Return on Investment (ROI) for "
        "real estate properties in India, with 5-year year-wise forecasting."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "service": "Real Estate ROI Predictor",
        "version": "1.0.0",
        "endpoints": {
            "POST /predict_roi": "Predict ROI and 5-year forecast",
            "POST /predict_risk": "Predict investment risk level",
            "GET  /health":      "Service health check",
            "GET  /docs":        "Swagger UI",
            "GET  /redoc":       "ReDoc UI",
        },
    }


@app.get("/health", tags=["Info"])
def health():
    return {"status": "ok"}


@app.post(
    "/predict_roi",
    response_model=ROIPredictionResponse,
    tags=["Prediction"],
    summary="Predict real estate ROI and 5-year investment forecast",
)
def predict_roi_endpoint(payload: PropertyInput):
    """
    Accepts property details and returns:
    - ML-estimated price and rent
    - 5-year ROI calculation
    - Year-by-year forecast table
    - Investment rating
    """
    try:
        input_dict = payload.model_dump()

        # Compute optional fields if not provided
        if input_dict.get("price_per_sqft") is None:
            input_dict["price_per_sqft"] = (
                input_dict["price"] / max(input_dict["area"], 1)
            )
        if input_dict.get("rent_per_sqft") is None:
            input_dict["rent_per_sqft"] = (
                input_dict["rent"] / max(input_dict["area"], 1)
            )

        logger.info(
            "Prediction request: location=%s  price=%.0f  rent=%.0f",
            input_dict["location"], input_dict["price"], input_dict["rent"],
        )

        result = predict_roi(input_dict)
        return {**result, "status": "success"}

    except FileNotFoundError as exc:
        logger.error("Model file not found: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Models not found. Please run the training pipeline first: "
                "python training/train.py"
            ),
        )
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post(
    "/predict_risk",
    response_model=RiskPredictionResponse,
    tags=["Prediction"],
    summary="Predict real estate investment risk level",
)
def predict_risk_endpoint(payload: RiskPredictionRequest):
    """
    Predict investment risk (Low / Medium / High) using trained risk_model.pkl.

    Feature construction uses the incoming payload plus ROI/growth signals from
    the ROI predictor pipeline to keep both models aligned.
    """
    try:
        input_dict = payload.model_dump()

        roi_result = predict_roi(input_dict)
        five_year = roi_result.get("five_year_summary", {})

        risk_input = {
            "location": input_dict["location"],
            "price": float(input_dict["price"]),
            "area": float(input_dict["area"]),
            "bhk": int(input_dict["bhk"]),
            "bath": int(input_dict.get("bath") or input_dict["bhk"]),
            "floors": float(input_dict.get("floor", 1)),
            "furnishing": input_dict.get("furnishing", "unfurnished"),
            "property_age": float(input_dict.get("property_age", 5)),
            "monthly_rent": float(input_dict["rent"]),
            "maintenance_cost": float(
                input_dict.get("maintenance_cost")
                if input_dict.get("maintenance_cost") is not None
                else input_dict["rent"] * 0.10
            ),
            "annual_appreciation_rate": float(five_year.get("price_growth_rate_pct", 6.0)),
            "rental_growth_rate": float(five_year.get("rent_growth_rate_pct", 9.0)),
            "investment_years": int(input_dict.get("investment_years", 5)),
            "ROI": float(five_year.get("roi_pct", 0.0)),
        }

        rental_yield_pct = (
            (risk_input["monthly_rent"] * 12.0 / max(risk_input["price"], 1.0)) * 100.0
        )
        risk_input["rental_yield"] = float(rental_yield_pct)

        model_risk_level = predict_risk(risk_input)

        # Use the business rule as the final risk label so output changes
        # consistently with ROI + rental-yield thresholds.
        roi_value = risk_input["ROI"]
        if roi_value >= 15.0 and rental_yield_pct >= 5.0:
            risk_level = "Low Risk"
        elif 8.0 <= roi_value < 15.0:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"

        risk_code_map = {"Low Risk": 0, "Medium Risk": 1, "High Risk": 2}
        risk_code = risk_code_map.get(risk_level, 2)

        logger.info(
            "Risk request: location=%s  roi=%.2f%%  yield=%.2f%%  risk=%s  model=%s",
            input_dict["location"],
            risk_input["ROI"],
            rental_yield_pct,
            risk_level,
            model_risk_level,
        )

        return {
            "status": "success",
            "risk_level": risk_level,
            "risk_code": risk_code,
            "model": "BusinessRule + RandomForestClassifier",
            "inputs_used": risk_input,
        }

    except FileNotFoundError as exc:
        logger.error("Risk model artifact not found: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Risk model artifacts not found. Please run: "
                "python training/risk_model_training.py"
            ),
        )
    except Exception as exc:
        logger.exception("Unexpected risk prediction error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

# ── Static frontend ───────────────────────────────────────────────────────────
_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
