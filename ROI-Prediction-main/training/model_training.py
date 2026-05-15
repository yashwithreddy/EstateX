"""
model_training.py
-----------------
Trains RandomForest, GradientBoosting, and XGBoost regressors to predict:
  - future property price
  - monthly rent

Evaluates each model and persists the best one along with encoders.
"""

import os
import joblib
import warnings
import numpy as np
import pandas as pd

from sklearn.ensemble        import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics         import r2_score, mean_absolute_error, mean_squared_error

try:
    from xgboost import XGBRegressor
    _XGBOOST_AVAILABLE = True
except ImportError:
    XGBRegressor = None  # type: ignore
    _XGBOOST_AVAILABLE = False
    warnings.warn("xgboost not installed – XGBoost model will be skipped.")

warnings.filterwarnings("ignore")

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Model definitions
# ─────────────────────────────────────────────────────────────────────────────

def _get_candidates() -> dict:
    train_all = os.getenv("TRAIN_ALL_MODELS", "0") == "1"
    candidates = {
        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
        ),
    }

    if train_all:
        candidates["GradientBoosting"] = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            random_state=42,
        )
        if _XGBOOST_AVAILABLE and XGBRegressor is not None:
            candidates["XGBoost"] = XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.08,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbosity=0,
                n_jobs=-1,
            )
    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation helper
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str = "",
    target_name: str = "",
) -> dict:
    """Return a dict of evaluation metrics."""
    y_pred = model.predict(X_test)
    r2  = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)

    print(f"  [{model_name}] {target_name}")
    print(f"    R²   = {r2:.4f}")
    print(f"    MAE  = {mae:,.2f}")
    print(f"    RMSE = {rmse:,.2f}")

    return {"r2": r2, "mae": mae, "mse": mse, "rmse": rmse,
            "model_name": model_name, "target": target_name}


# ─────────────────────────────────────────────────────────────────────────────
# Training pipeline
# ─────────────────────────────────────────────────────────────────────────────

def train_models(
    X: pd.DataFrame,
    y_price: pd.Series,
    y_rent: pd.Series,
    rent_mask: pd.Series | None = None,
    test_size: float = 0.20,
    random_state: int = 42,
) -> dict:
    """
    Train all candidate models for price and rent targets.
    Select the best model for each target based on R².
    Save artefacts to the models/ directory.

    Returns
    -------
    results : dict with keys 'price' and 'rent', each holding the best model
              and its metrics.
    """
    print("\n" + "=" * 60)
    print("Splitting data …")
    X_train, X_test, yp_train, yp_test = train_test_split(
        X, y_price, test_size=test_size, random_state=random_state
    )
    if rent_mask is not None:
        X_rent = X.loc[rent_mask].copy()
        y_rent_filtered = y_rent.loc[rent_mask].copy()
    else:
        X_rent = X
        y_rent_filtered = y_rent

    xr_train, xr_test, yr_train, yr_test = train_test_split(
        X_rent, y_rent_filtered, test_size=test_size, random_state=random_state
    )

    print(f"Train: {len(X_train):,}  |  Test: {len(X_test):,}\n")
    print(f"Rent train rows (quality-filtered): {len(X_rent):,}")

    price_candidates = _get_candidates()   # fresh model objects for price
    rent_candidates  = _get_candidates()   # separate fresh model objects for rent
    results = {"price": {}, "rent": {}}

    # ── Train price models ────────────────────────────────────────────────────
    print("─" * 60)
    print("Training PRICE models …")
    best_price_r2    = -np.inf
    best_price_model = None
    best_price_name  = ""
    price_metrics    = {}

    for name, model in price_candidates.items():
        model.fit(X_train, yp_train)
        metrics = evaluate_model(model, X_test, yp_test, name, "PRICE")
        price_metrics[name] = metrics
        if metrics["r2"] > best_price_r2:
            best_price_r2    = metrics["r2"]
            best_price_model = model
            best_price_name  = name

    print(f"\n  ★ Best PRICE model: {best_price_name}  (R²={best_price_r2:.4f})")

    # ── Train rent models ─────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("Training RENT models …")
    best_rent_r2    = -np.inf
    best_rent_model = None
    best_rent_name  = ""
    rent_metrics    = {}

    for name, model in rent_candidates.items():
        model.fit(xr_train, yr_train)
        metrics = evaluate_model(model, xr_test, yr_test, name, "RENT")
        rent_metrics[name] = metrics
        if metrics["r2"] > best_rent_r2:
            best_rent_r2    = metrics["r2"]
            best_rent_model = model
            best_rent_name  = name

    print(f"\n  ★ Best RENT model: {best_rent_name}  (R²={best_rent_r2:.4f})")

    # ── Persist ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Saving models …")

    price_path = os.path.join(MODELS_DIR, "best_price_model.joblib")
    rent_path  = os.path.join(MODELS_DIR, "best_rent_model.joblib")
    meta_path  = os.path.join(MODELS_DIR, "model_meta.joblib")

    joblib.dump(best_price_model, price_path)
    joblib.dump(best_rent_model,  rent_path)
    joblib.dump(
        {
            "price_model_name": best_price_name,
            "rent_model_name":  best_rent_name,
            "price_r2":         best_price_r2,
            "rent_r2":          best_rent_r2,
            "price_metrics":    price_metrics,
            "rent_metrics":     rent_metrics,
        },
        meta_path,
    )
    print(f"  → {price_path}")
    print(f"  → {rent_path}")
    print(f"  → {meta_path}")

    return {
        "price": {
            "model":      best_price_model,
            "model_name": best_price_name,
            "r2":         best_price_r2,
            "metrics":    price_metrics,
        },
        "rent": {
            "model":      best_rent_model,
            "model_name": best_rent_name,
            "r2":         best_rent_r2,
            "metrics":    rent_metrics,
        },
    }


def load_models() -> tuple:
    """
    Load saved price and rent models from disk.

    Returns
    -------
    (price_model, rent_model, meta)
    """
    price_path = os.path.join(MODELS_DIR, "best_price_model.joblib")
    rent_path  = os.path.join(MODELS_DIR, "best_rent_model.joblib")
    meta_path  = os.path.join(MODELS_DIR, "model_meta.joblib")

    price_model = joblib.load(price_path)
    rent_model  = joblib.load(rent_path)
    meta        = joblib.load(meta_path)

    return price_model, rent_model, meta
