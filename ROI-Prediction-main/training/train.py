"""
train.py
--------
End-to-end training pipeline:
  1. Load + merge datasets
  2. Feature engineering
  3. Train & evaluate models
  4. Save models and encoders
"""

import os
import sys
import json
import joblib

# Allow imports from this directory
sys.path.insert(0, os.path.dirname(__file__))

from data_preparation    import build_unified_dataset, compute_growth_rates
from feature_engineering import build_feature_matrix
from model_training      import train_models

MODELS_DIR   = os.path.join(os.path.dirname(__file__), "..", "models")
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")
os.makedirs(MODELS_DIR, exist_ok=True)


def run_training_pipeline():
    print("=" * 60)
    print("REAL ESTATE ROI — MODEL TRAINING PIPELINE")
    print("=" * 60)

    # ── Step 1: Build unified dataset ────────────────────────────────────────
    unified_path = os.path.join(DATASETS_DIR, "unified_dataset.csv")
    df = build_unified_dataset(save_path=unified_path)

    # ── Step 2: Feature engineering ──────────────────────────────────────────
    print("\nBuilding feature matrix …")
    X, y_price, y_rent, rent_mask, encoders = build_feature_matrix(df, fit=True)
    print(f"Feature matrix: {X.shape}")
    print(f"Price target   – min={y_price.min():,.0f}  max={y_price.max():,.0f}")
    print(f"Rent target    – min={y_rent.min():,.0f}   max={y_rent.max():,.0f}")
    print(f"Rent training rows (quality filter) = {int(rent_mask.sum()):,}/{len(rent_mask):,}")
    if "rent_is_imputed" in df.columns:
        print(f"Observed rent rows                = {int((~df['rent_is_imputed']).sum()):,}")
        print(f"Imputed rent rows                 = {int(df['rent_is_imputed'].sum()):,}")

    # Save encoders (needed at inference time)
    encoders_path = os.path.join(MODELS_DIR, "encoders.joblib")
    joblib.dump(encoders, encoders_path)
    print(f"\nEncoders saved → {encoders_path}")

    # ── Step 2b: Compute data-driven growth rates ────────────────────────────
    print("\nComputing growth rates from datasets …")
    growth_rates = compute_growth_rates(df)
    print(f"  price_growth_rate = {growth_rates['price_growth_rate']*100:.2f}%/yr")
    print(f"  rent_growth_rate  = {growth_rates['rent_growth_rate']*100:.2f}%/yr")

    # ── Step 3: Train models ─────────────────────────────────────────────────
    results = train_models(X, y_price, y_rent, rent_mask=rent_mask)

    # ── Step 4: Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print(f"  Best PRICE model : {results['price']['model_name']}"
          f"  R²={results['price']['r2']:.4f}")
    print(f"  Best RENT model  : {results['rent']['model_name']}"
          f"  R²={results['rent']['r2']:.4f}")
    print("=" * 60)

    # ── Step 5: Save model metadata (growth rates + model names + R²) ────────
    meta = {
        # global scalar rates
        "price_growth_rate":   growth_rates["price_growth_rate"],
        "rent_growth_rate":    growth_rates["rent_growth_rate"],
        "forecast_years":      growth_rates.get("forecast_years", 5),
        # granular lookup tables
        "city_rates":          growth_rates.get("city_rates", {}),
        "location_rates":      growth_rates.get("location_rates", {}),
        "property_type_adj":   growth_rates.get("property_type_adj", {}),
        "furnishing_rent_adj": growth_rates.get("furnishing_rent_adj", {}),
        "bhk_adj":             growth_rates.get("bhk_adj", {}),
        "area_adj":            growth_rates.get("area_adj", {}),
        "floor_adj":           growth_rates.get("floor_adj", {}),
        "age_adj":             growth_rates.get("age_adj", {}),
        "price_band_adj":      growth_rates.get("price_band_adj", {}),
        "rent_band_adj":       growth_rates.get("rent_band_adj", {}),
        # model info
        "price_model_name":    results["price"]["model_name"],
        "price_r2":            round(results["price"]["r2"], 4),
        "rent_model_name":     results["rent"]["model_name"],
        "rent_r2":             round(results["rent"]["r2"], 4),
    }
    meta_json_path = os.path.join(MODELS_DIR, "model_meta.json")
    with open(meta_json_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nModel metadata saved → {meta_json_path}")
    print(json.dumps(meta, indent=2))

    return results


if __name__ == "__main__":
    run_training_pipeline()
