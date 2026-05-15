"""
risk_model_training.py
----------------------
Train a real-estate investment risk classifier for Hyderabad properties.

Risk target rules:
  - Low (0):    ROI >= 15 and rental_yield >= 5
  - Medium (1): 8 <= ROI < 15
  - High (2):   otherwise
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Allow imports from this directory
sys.path.insert(0, os.path.dirname(__file__))

from data_preparation import build_unified_dataset, compute_growth_rates

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")
os.makedirs(MODELS_DIR, exist_ok=True)

RISK_MAP = {"Low": 0, "Medium": 1, "High": 2}
RISK_LABELS = {0: "Low Risk", 1: "Medium Risk", 2: "High Risk"}
FURNISHING_MAP = {"unfurnished": 0, "semi-furnished": 1, "furnished": 2}

_RISK_MODEL = None
_RISK_PREPROCESS = None


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Element-wise safe division returning NaN where denominator is zero."""
    out = numerator / denominator.replace(0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan)


def _infer_maintenance_cost(df: pd.DataFrame) -> pd.Series:
    """Infer maintenance if missing using a conservative rent-based proxy."""
    if "maintenance_cost" in df.columns:
        return pd.to_numeric(df["maintenance_cost"], errors="coerce")
    monthly_rent = pd.to_numeric(df["monthly_rent"], errors="coerce")
    return (monthly_rent * 0.10).round(0)


def _compute_rowwise_roi(df: pd.DataFrame) -> pd.Series:
    """Compute ROI (%) using per-row growth rates and investment horizon."""
    price = pd.to_numeric(df["price"], errors="coerce")
    monthly_rent = pd.to_numeric(df["monthly_rent"], errors="coerce")
    years = pd.to_numeric(df["investment_years"], errors="coerce").clip(lower=1)

    app_rate = pd.to_numeric(df["annual_appreciation_rate"], errors="coerce") / 100.0
    rent_growth = pd.to_numeric(df["rental_growth_rate"], errors="coerce") / 100.0

    future_price = price * np.power(1.0 + app_rate, years)
    # Geometric-series rent accumulation with rent-growth fallback for zero growth.
    rent_factor = np.where(
        np.abs(rent_growth) > 1e-9,
        (np.power(1.0 + rent_growth, years) - 1.0) / rent_growth,
        years,
    )
    total_rent = monthly_rent * 12.0 * rent_factor

    roi = _safe_div((future_price + total_rent - price), price) * 100.0
    return roi


def _assign_risk_level(df: pd.DataFrame) -> pd.Series:
    """Apply rule-based target labeling from ROI and rental yield."""
    roi = pd.to_numeric(df["ROI"], errors="coerce")
    rental_yield = pd.to_numeric(df["rental_yield"], errors="coerce")

    low_mask = (roi >= 15.0) & (rental_yield >= 5.0)
    med_mask = (roi >= 8.0) & (roi < 15.0)

    risk = np.select(
        [low_mask, med_mask],
        ["Low", "Medium"],
        default="High",
    )
    return pd.Series(risk, index=df.index)


def _encode_furnishing(series: pd.Series) -> pd.Series:
    """Ordinal encoding for furnishing status."""
    s = (
        series.astype(str)
        .str.lower()
        .str.strip()
        .replace({"nan": "unfurnished"})
    )
    return s.map(FURNISHING_MAP).fillna(FURNISHING_MAP["unfurnished"]).astype(int)


def prepare_data(cleaned_df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.Series, dict]:
    """
    Prepare Hyderabad risk-classification dataset.

    Returns
    -------
    X : encoded feature matrix
    y : numeric risk target (Low=0, Medium=1, High=2)
    preprocess_artifacts : encoders and metadata needed for inference
    """
    if cleaned_df is None:
        unified_path = os.path.join(DATASETS_DIR, "unified_dataset.csv")
        cleaned_df = build_unified_dataset(save_path=unified_path)

    df = cleaned_df.copy()

    # Keep Hyderabad-only subset for the requested risk model scope.
    city_col = df.get("city", pd.Series(["Unknown"] * len(df)))
    df = df[city_col.astype(str).str.lower().str.contains("hyderabad", na=False)].copy()
    if df.empty:
        raise ValueError("No Hyderabad records found after filtering.")

    # Align naming with required feature specification.
    if "floors" not in df.columns:
        df["floors"] = pd.to_numeric(df.get("floor", 1), errors="coerce")
    if "monthly_rent" not in df.columns:
        df["monthly_rent"] = pd.to_numeric(df.get("rent", np.nan), errors="coerce")
    if "bath" not in df.columns:
        df["bath"] = pd.to_numeric(df.get("bhk", 2), errors="coerce").clip(lower=1)
    df["maintenance_cost"] = _infer_maintenance_cost(df)
    if "investment_years" not in df.columns:
        df["investment_years"] = 5

    # Bring data-driven growth-rate priors from existing training logic.
    growth = compute_growth_rates(cleaned_df)
    global_app = float(growth["price_growth_rate"] * 100.0)
    global_rent_growth = float(growth["rent_growth_rate"] * 100.0)
    city_rates = growth.get("city_rates", {})

    if "annual_appreciation_rate" not in df.columns:
        df["annual_appreciation_rate"] = df["city"].astype(str).apply(
            lambda c: city_rates.get(c, {}).get("price_growth_rate", global_app / 100.0) * 100.0
        )
    if "rental_growth_rate" not in df.columns:
        df["rental_growth_rate"] = df["city"].astype(str).apply(
            lambda c: city_rates.get(c, {}).get("rent_growth_rate", global_rent_growth / 100.0) * 100.0
        )

    # Rental yield % for risk logic.
    df["rental_yield"] = _safe_div(df["monthly_rent"] * 12.0, df["price"]) * 100.0

    # ROI from previous model if present; else derive with the same investment formula.
    if "ROI" not in df.columns:
        df["ROI"] = _compute_rowwise_roi(df)
    else:
        df["ROI"] = pd.to_numeric(df["ROI"], errors="coerce")

    # Build target.
    df["risk_level"] = _assign_risk_level(df)
    df["risk_level_num"] = df["risk_level"].map(RISK_MAP).astype(int)

    feature_cols = [
        "location",
        "price",
        "area",
        "bhk",
        "bath",
        "floors",
        "furnishing",
        "property_age",
        "monthly_rent",
        "maintenance_cost",
        "annual_appreciation_rate",
        "rental_growth_rate",
        "investment_years",
        "ROI",
    ]

    for col in feature_cols:
        if col not in df.columns:
            df[col] = np.nan

    # Ensure no nulls.
    X_raw = df[feature_cols].copy()
    y = df["risk_level_num"].copy()

    numeric_cols = [c for c in feature_cols if c not in ["location", "furnishing"]]
    for col in numeric_cols:
        X_raw[col] = pd.to_numeric(X_raw[col], errors="coerce")
        X_raw[col] = X_raw[col].fillna(X_raw[col].median())

    X_raw["location"] = X_raw["location"].astype(str).fillna("Unknown")
    X_raw["furnishing"] = X_raw["furnishing"].astype(str).fillna("unfurnished")

    # Required encodings.
    location_encoder = LabelEncoder()
    X_raw["location"] = location_encoder.fit_transform(X_raw["location"])
    X_raw["furnishing"] = _encode_furnishing(X_raw["furnishing"])

    # Final no-null assertion.
    X_raw = X_raw.fillna(0)

    preprocess_artifacts = {
        "feature_cols": feature_cols,
        "location_encoder": location_encoder,
        "furnishing_map": FURNISHING_MAP,
        "risk_map": RISK_MAP,
        "default_numeric": {c: float(X_raw[c].median()) for c in numeric_cols},
    }
    return X_raw, y, preprocess_artifacts


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[RandomForestClassifier, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Train RandomForest risk classifier with requested hyperparameters."""
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model, X_train, X_test, y_train, y_test


def evaluate_model(
    model: RandomForestClassifier,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict:
    """Compute requested classification metrics and overfitting diagnostics."""
    y_pred = model.predict(X_test)

    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, y_pred)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        y_pred,
        average="weighted",
        zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
    report = classification_report(
        y_test,
        y_pred,
        labels=[0, 1, 2],
        target_names=["Low", "Medium", "High"],
        zero_division=0,
    )

    return {
        "accuracy": test_acc,
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "precision_weighted": precision,
        "recall_weighted": recall,
        "f1_weighted": f1,
        "confusion_matrix": cm,
        "classification_report": report,
        "y_pred": y_pred,
    }


def _transform_input(input_data: dict, preprocess_artifacts: dict) -> np.ndarray:
    """Apply training-time preprocessing to one inference payload."""
    feature_cols = preprocess_artifacts["feature_cols"]
    location_encoder: LabelEncoder = preprocess_artifacts["location_encoder"]
    furnishing_map = preprocess_artifacts["furnishing_map"]
    default_numeric = preprocess_artifacts["default_numeric"]

    row = {}
    for col in feature_cols:
        if col in ("location", "furnishing"):
            row[col] = input_data.get(col)
        else:
            row[col] = input_data.get(col, default_numeric.get(col, 0.0))

    # Encode location with fallback for unseen labels.
    loc = str(row.get("location", "Unknown"))
    known = set(location_encoder.classes_)
    if loc not in known:
        loc = location_encoder.classes_[0]
    row["location"] = int(location_encoder.transform([loc])[0])

    furn = str(row.get("furnishing", "unfurnished")).lower().strip()
    row["furnishing"] = int(furnishing_map.get(furn, furnishing_map["unfurnished"]))

    for col in feature_cols:
        if col not in ["location", "furnishing"]:
            try:
                row[col] = float(row[col])
            except (TypeError, ValueError):
                row[col] = float(default_numeric.get(col, 0.0))

    return np.array([[row[c] for c in feature_cols]], dtype=float)


def _predict_risk_with_artifacts(input_data: dict, model, preprocess_artifacts: dict) -> str:
    """Predict risk label from one property payload using explicit artifacts."""
    vector = _transform_input(input_data, preprocess_artifacts)
    pred = int(model.predict(vector)[0])

    if pred == 0:
        return "Low Risk"
    if pred == 1:
        return "Medium Risk"
    return "High Risk"


def predict_risk(input_data) -> str:
    """
    Required single-argument helper shape for integration.

    This uses module-level loaded/trained artifacts and accepts either a raw
    feature dict or an already-encoded feature vector list.
    """
    global _RISK_MODEL, _RISK_PREPROCESS

    if _RISK_MODEL is None or _RISK_PREPROCESS is None:
        model_path = os.path.join(MODELS_DIR, "risk_model.pkl")
        preprocess_path = os.path.join(MODELS_DIR, "risk_preprocess.joblib")
        _RISK_MODEL = joblib.load(model_path)
        _RISK_PREPROCESS = joblib.load(preprocess_path)

    if isinstance(input_data, dict):
        pred_label = _predict_risk_with_artifacts(input_data, _RISK_MODEL, _RISK_PREPROCESS)
        return pred_label

    pred = int(_RISK_MODEL.predict([input_data])[0])
    if pred == 0:
        return "Low Risk"
    if pred == 1:
        return "Medium Risk"
    return "High Risk"


def run_risk_training_pipeline() -> dict:
    """Run full pipeline and print required outputs."""
    print("=" * 60)
    print("REAL ESTATE INVESTMENT RISK MODEL TRAINING")
    print("=" * 60)

    X, y, preprocess_artifacts = prepare_data(cleaned_df=None)
    print(f"Prepared dataset: {X.shape[0]:,} rows x {X.shape[1]} features")
    print("Class distribution:")
    print(y.value_counts().sort_index().rename(index={0: "Low", 1: "Medium", 2: "High"}))

    model, X_train, X_test, y_train, y_test = train_model(X, y)
    metrics = evaluate_model(model, X_train, X_test, y_train, y_test)

    print("\n1) Accuracy score")
    print(f"Accuracy: {metrics['accuracy']:.4f}")

    print("\n2) Classification report")
    print(metrics["classification_report"])

    print("\n3) Confusion matrix")
    print(metrics["confusion_matrix"])

    print("\n4) Feature importance")
    feature_importance = pd.DataFrame(
        {
            "feature": X.columns,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    print(feature_importance.to_string(index=False))

    print("\nOverfitting check (train vs test accuracy)")
    print(f"Train accuracy: {metrics['train_accuracy']:.4f}")
    print(f"Test accuracy : {metrics['test_accuracy']:.4f}")
    print(f"Gap           : {metrics['train_accuracy'] - metrics['test_accuracy']:.4f}")

    model_path = os.path.join(MODELS_DIR, "risk_model.pkl")
    preprocess_path = os.path.join(MODELS_DIR, "risk_preprocess.joblib")
    report_path = os.path.join(MODELS_DIR, "risk_model_report.json")

    # Required model artifact.
    joblib.dump(model, model_path)
    joblib.dump(preprocess_artifacts, preprocess_path)

    serializable_metrics = {
        "accuracy": metrics["accuracy"],
        "train_accuracy": metrics["train_accuracy"],
        "test_accuracy": metrics["test_accuracy"],
        "precision_weighted": metrics["precision_weighted"],
        "recall_weighted": metrics["recall_weighted"],
        "f1_weighted": metrics["f1_weighted"],
        "confusion_matrix": metrics["confusion_matrix"].tolist(),
        "classification_report": metrics["classification_report"],
        "feature_importance": feature_importance.to_dict(orient="records"),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(serializable_metrics, f, indent=2)

    print(f"\nSaved model      -> {model_path}")
    print(f"Saved preprocess -> {preprocess_path}")
    print(f"Saved report     -> {report_path}")

    print("\n5) Sample predictions")
    for i in range(min(5, len(X_test))):
        row = X_test.iloc[i]
        sample_payload = {col: row[col] for col in X.columns}
        # Reverse engineered display labels are not required for demonstration.
        pred_text = RISK_LABELS[int(model.predict([row.values])[0])]
        actual_text = RISK_LABELS[int(y_test.iloc[i])]
        print(f"Sample {i+1}: predicted={pred_text} | actual={actual_text}")

    return {
        "model": model,
        "preprocess": preprocess_artifacts,
        "metrics": serializable_metrics,
        "model_path": model_path,
    }


if __name__ == "__main__":
    run_risk_training_pipeline()