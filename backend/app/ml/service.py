import logging
from pathlib import Path

import joblib
import numpy as np

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
        score = payload["demand_index"] * 0.45 + payload["market_trend"] * 0.35 + (payload["rental_yield"] / 12.0) * 0.2
        if score >= 0.68:
            level, prob = "Low", min(0.98, 0.6 + score / 3)
        elif score >= 0.48:
            level, prob = "Medium", 0.55
        else:
            level, prob = "High", min(0.95, 0.6 + (0.5 - score))
        return {"risk_level": level, "probability_score": round(float(prob), 4)}

    def predict_risk(self, payload: dict) -> dict:
        self._ensure_loaded()
        if self._fallback_mode:
            return self._fallback_risk(payload)

        x = self._to_vector(payload)
        probabilities = self._risk_model.predict_proba(x)[0]
        idx = int(np.argmax(probabilities))
        labels = ["Low", "Medium", "High"]
        return {"risk_level": labels[idx], "probability_score": round(float(probabilities[idx]), 4)}


ml_service = MLService()
