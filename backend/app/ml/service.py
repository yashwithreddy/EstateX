import logging
from pathlib import Path

import joblib
import numpy as np
import math

logger = logging.getLogger(__name__)

MODEL_DIR = Path("ml/artifacts")
ROI_MODEL_PATH = MODEL_DIR / "roi_model.joblib"
RISK_MODEL_PATH = MODEL_DIR / "risk_model.joblib"
FEATURES_PATH = MODEL_DIR / "features.joblib"


class MLService:
    def __init__(self) -> None:
        self._roi_model = None
        self._risk_model = None
        self._features = ["property_price", "rental_yield", "demand_index", "market_trend"]
        self._fallback_mode = True

    def preload(self) -> str:
        self._ensure_loaded()
        return "fallback" if self._fallback_mode else "model_loaded"

    def _ensure_loaded(self) -> None:
        if self._roi_model is not None and self._risk_model is not None:
            return

        if not ROI_MODEL_PATH.exists() or not RISK_MODEL_PATH.exists() or not FEATURES_PATH.exists():
            logger.warning("ML artifacts missing. Using fallback predictions.")
            self._fallback_mode = True
            return

        try:
            self._roi_model = joblib.load(ROI_MODEL_PATH)
            self._risk_model = joblib.load(RISK_MODEL_PATH)
            self._features = joblib.load(FEATURES_PATH)
            self._fallback_mode = False
            logger.info("ML artifacts loaded from %s", MODEL_DIR)
        except Exception:
            logger.exception("Failed to load ML artifacts. Falling back to deterministic predictions.")
            self._fallback_mode = True

    def _to_vector(self, payload: dict) -> np.ndarray:
        return np.array([[payload[key] for key in self._features]], dtype=float)

    def _fallback_roi(self, payload: dict) -> dict:
        roi = (
            payload["rental_yield"] * 0.9
            + payload["demand_index"] * 8.0
            + payload["market_trend"] * 6.0
            + (payload["property_price"] / 1_000_000) * 0.4
        )
        spread = max(1.2, abs(roi) * 0.12)
        return {
            "predicted_roi_percent": round(float(roi), 4),
            "confidence_interval": [round(float(roi - spread), 4), round(float(roi + spread), 4)],
        }

    def predict_roi(self, payload: dict) -> dict:
        self._ensure_loaded()
        if self._fallback_mode:
            return self._fallback_roi(payload)

        x = self._to_vector(payload)
        prediction = float(self._roi_model.predict(x)[0])
        if hasattr(self._roi_model, "estimators_"):
            tree_preds = np.array([tree.predict(x)[0] for tree in self._roi_model.estimators_], dtype=float)
            std = float(np.std(tree_preds))
        else:
            std = abs(prediction) * 0.1

        interval = [round(prediction - 1.96 * std, 4), round(prediction + 1.96 * std, 4)]
        return {"predicted_roi_percent": round(prediction, 4), "confidence_interval": interval}

    def _fallback_risk(self, payload: dict) -> dict:
        # Normalize price into 0-1 range using a log scale to avoid extreme jumps.
        price = max(1.0, float(payload.get("property_price", 1.0)))
        price_factor = (math.log10(price) - 6.0) / 2.0
        price_factor = min(1.0, max(0.0, price_factor))

        # Combine inputs for a wider spread across properties.
        score = (
            payload["demand_index"] * 0.35
            + payload["market_trend"] * 0.35
            + (payload["rental_yield"] / 12.0) * 0.15
            + (1.0 - price_factor) * 0.15
        )
        score = min(1.0, max(0.0, score))

        # Map score into a 10-80 percent band for visible variation.
        percent = 10.0 + score * 70.0
        prob = max(0.10, min(0.80, percent / 100.0))

        level = self._risk_level_from_score(prob)
        return {"risk_level": level, "probability_score": round(float(prob), 4)}

    @staticmethod
    def _risk_level_from_score(probability: float) -> str:
        percent = probability * 100.0
        if percent >= 50.0:
            return "High"
        if percent >= 26.0:
            return "Medium"
        return "Low"

    def _fallback_rental_yield(self, payload: dict) -> dict:
        base = 4.0
        demand = float(payload.get("demand_index", 0.0))
        trend = float(payload.get("market_trend", 0.0))
        price = max(1.0, float(payload.get("property_price", 1.0)))
        price_factor = (math.log10(price) - 6.0) / 2.0
        price_factor = min(1.0, max(0.0, price_factor))
        yield_hint = float(payload.get("rental_yield", 0.0))
        hint_factor = min(1.0, max(0.0, yield_hint / 12.0)) - 0.5

        offset = (
            (demand - 0.5) * 0.9
            + (trend - 0.5) * 0.7
            + (0.5 - price_factor) * 0.6
            + hint_factor * 0.4
        )
        predicted = base + offset
        predicted = max(3.0, min(5.0, predicted))
        spread = max(0.2, abs(predicted) * 0.08)
        lower = max(3.0, predicted - spread)
        upper = min(5.0, predicted + spread)
        return {
            "predicted_rental_yield_percent": round(float(predicted), 4),
            "confidence_interval": [round(float(lower), 4), round(float(upper), 4)],
        }

    def predict_risk(self, payload: dict) -> dict:
        self._ensure_loaded()
        if self._fallback_mode:
            return self._fallback_risk(payload)

        x = self._to_vector(payload)
        probabilities = self._risk_model.predict_proba(x)[0]
        max_prob = float(np.max(probabilities))
        level = self._risk_level_from_score(max_prob)
        return {"risk_level": level, "probability_score": round(max_prob, 4)}

    def predict_rental_yield(self, payload: dict) -> dict:
        self._ensure_loaded()
        # No dedicated rental-yield model yet; use deterministic fallback for now.
        return self._fallback_rental_yield(payload)


ml_service = MLService()
