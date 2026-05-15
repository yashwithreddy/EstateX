"""
roi_predictor.py
----------------
Core prediction logic:
  - Loads trained models + encoders
  - Applies growth assumptions
  - Calculates ROI
  - Produces a 5-year year-by-year forecast
"""

import os
import json
import joblib
import numpy as np
from typing import Any

from feature_engineering import prepare_single_input

# ── Growth rates ──────────────────────────────────────────────────────────────
# Loaded from models/model_meta.json (computed from the actual datasets at
# training time by compute_growth_rates() in data_preparation.py).
# If the file is missing, sensible fallbacks are used.

MODELS_DIR    = os.path.join(os.path.dirname(__file__), "..", "models")
ENCODERS_PATH = os.path.join(MODELS_DIR, "encoders.joblib")
_META_PATH    = os.path.join(MODELS_DIR, "model_meta.json")

_FALLBACK_PRICE_GROWTH = 0.06
_FALLBACK_RENT_GROWTH  = 0.09
_FALLBACK_YEARS        = 5

def _load_meta() -> dict:
    """Load model_meta.json; return defaults if unavailable."""
    try:
        with open(_META_PATH, "r") as f:
            meta = json.load(f)
        pg = float(meta.get("price_growth_rate", _FALLBACK_PRICE_GROWTH))
        rg = float(meta.get("rent_growth_rate",  _FALLBACK_RENT_GROWTH))
        fy = int(meta.get("forecast_years",       _FALLBACK_YEARS))
        loc_n  = len(meta.get("location_rates", {}))
        city_n = len(meta.get("city_rates", {}))
        print(f"[roi_predictor] Growth rates loaded from model_meta.json — "
              f"price={pg*100:.2f}%/yr  rent={rg*100:.2f}%/yr  "
              f"({loc_n} locations, {city_n} cities)")
        return {
            "price_growth_rate":   pg,
            "rent_growth_rate":    rg,
            "forecast_years":      fy,
            "location_rates":      meta.get("location_rates", {}),
            "city_rates":          meta.get("city_rates", {}),
            "property_type_adj":   meta.get("property_type_adj", {}),
            "furnishing_rent_adj": meta.get("furnishing_rent_adj", {}),
            "bhk_adj":             meta.get("bhk_adj", {}),
            "area_adj":            meta.get("area_adj", {}),
            "floor_adj":           meta.get("floor_adj", {}),
            "age_adj":             meta.get("age_adj", {}),
            "price_band_adj":      meta.get("price_band_adj", {}),
            "rent_band_adj":       meta.get("rent_band_adj", {}),
        }
    except FileNotFoundError:
        print(f"[roi_predictor] model_meta.json not found; using defaults "
              f"({_FALLBACK_PRICE_GROWTH*100:.0f}%/{_FALLBACK_RENT_GROWTH*100:.0f}%)")
        return {
            "price_growth_rate":   _FALLBACK_PRICE_GROWTH,
            "rent_growth_rate":    _FALLBACK_RENT_GROWTH,
            "forecast_years":      _FALLBACK_YEARS,
            "location_rates":      {},
            "city_rates":          {},
            "property_type_adj":   {},
            "furnishing_rent_adj": {},
            "bhk_adj":             {},
            "area_adj":            {},
            "floor_adj":           {},
            "age_adj":             {},
            "price_band_adj":      {},
            "rent_band_adj":       {},
        }

_meta = _load_meta()
PRICE_GROWTH_RATE = _meta["price_growth_rate"]
RENT_GROWTH_RATE  = _meta["rent_growth_rate"]
FORECAST_YEARS    = _meta["forecast_years"]

# ── Granular rate lookup ──────────────────────────────────────────────────────

def _resolve_growth_rates(location: str, city: str = "",
                          property_type: str = "apartment",
                          furnishing: str = "semi-furnished",
                          bhk: int = 2,
                          area: float = 1200,
                          floor: int = 1,
                          property_age: float = 5.0,
                          purchase_price: float = 0.0,
                          monthly_rent: float = 0.0) -> dict:
    """
    Resolve price and rent growth rates for a specific property by priority:

      1. location-level rate (most specific)
      2. city-level rate
      3. global rate (fallback)

    Then apply property-type and furnishing additive deltas derived from data.

    Returns dict with:
      price_growth_rate, rent_growth_rate,
      rate_source  ("location" | "city" | "global")
    """
    loc_rates  = _meta.get("location_rates", {})
    city_rates = _meta.get("city_rates", {})
    ptype_adj  = _meta.get("property_type_adj", {})
    furn_adj   = _meta.get("furnishing_rent_adj", {})
    bhk_adj    = _meta.get("bhk_adj", {})
    area_adj   = _meta.get("area_adj", {})
    floor_adj  = _meta.get("floor_adj", {})
    age_adj    = _meta.get("age_adj", {})
    price_band_adj = _meta.get("price_band_adj", {})
    rent_band_adj  = _meta.get("rent_band_adj", {})

    # ── 1. Base rates: location → city → global ───────────────────────────────
    loc_key = str(location).strip()
    source = "global"
    pg = PRICE_GROWTH_RATE
    rg = RENT_GROWTH_RATE

    # Try exact location match first
    if loc_key in loc_rates:
        pg     = loc_rates[loc_key]["price_growth_rate"]
        rg     = loc_rates[loc_key]["rent_growth_rate"]
        source = "location"
    else:
        # Try partial / city-prefix match (e.g. "Banjara Hills, Hyderabad" → "Hyderabad")
        city_key = str(city).strip() if city else ""
        # infer city from location string (everything after last comma)
        if not city_key and "," in loc_key:
            city_key = loc_key.rsplit(",", 1)[-1].strip()

        if city_key and city_key in city_rates:
            pg     = city_rates[city_key]["price_growth_rate"]
            rg     = city_rates[city_key]["rent_growth_rate"]
            source = "city"
        else:
            # Fuzzy city search – pick the city_rates key that appears in loc_key
            for ck in city_rates:
                if ck.lower() in loc_key.lower():
                    pg     = city_rates[ck]["price_growth_rate"]
                    rg     = city_rates[ck]["rent_growth_rate"]
                    source = "city"
                    break

    base_pg = float(pg)
    base_rg = float(rg)
    applied = {}
    total_pg_delta = 0.0
    total_rg_delta = 0.0

    # ── 2. Property-type delta ────────────────────────────────────────────────
    ptype_key = str(property_type).strip().lower()
    if ptype_key in ptype_adj:
        adj = ptype_adj[ptype_key]
        p_delta = float(adj.get("price_growth_delta", 0.0))
        r_delta = float(adj.get("rent_growth_delta",  0.0))
        pg  = float(np.clip(pg + p_delta, 0.03, 0.12))
        rg  = float(np.clip(rg + r_delta, 0.03, 0.15))
        total_pg_delta += p_delta
        total_rg_delta += r_delta
        applied["property_type"] = {
            "bucket": ptype_key,
            "price_growth_delta": round(p_delta, 6),
            "rent_growth_delta": round(r_delta, 6),
        }
    else:
        applied["property_type"] = {
            "bucket": ptype_key,
            "price_growth_delta": 0.0,
            "rent_growth_delta": 0.0,
        }

    # ── 3. Furnishing rent delta ───────────────────────────────────────────────
    furn_key = str(furnishing).strip().lower()
    if furn_key in furn_adj:
        r_delta = float(furn_adj[furn_key])
        rg = float(np.clip(rg + r_delta, 0.03, 0.15))
        total_rg_delta += r_delta
        applied["furnishing"] = {
            "bucket": furn_key,
            "price_growth_delta": 0.0,
            "rent_growth_delta": round(r_delta, 6),
        }
    else:
        applied["furnishing"] = {
            "bucket": furn_key,
            "price_growth_delta": 0.0,
            "rent_growth_delta": 0.0,
        }

    # ── 4. BHK / area / floor / age adjustments ─────────────────────────────
    def _apply_pair_delta(name: str, table: dict, key: str):
        nonlocal pg, rg, total_pg_delta, total_rg_delta
        if key in table:
            adj = table[key]
            p_delta = float(adj.get("price_growth_delta", 0.0))
            r_delta = float(adj.get("rent_growth_delta", 0.0))
            pg = float(np.clip(pg + p_delta, 0.03, 0.12))
            rg = float(np.clip(rg + r_delta, 0.03, 0.15))
            total_pg_delta += p_delta
            total_rg_delta += r_delta
            applied[name] = {
                "bucket": key,
                "price_growth_delta": round(p_delta, 6),
                "rent_growth_delta": round(r_delta, 6),
            }
        else:
            applied[name] = {
                "bucket": key,
                "price_growth_delta": 0.0,
                "rent_growth_delta": 0.0,
            }

    bhk_key = str(int(np.clip(round(float(bhk)), 0, 10)))
    _apply_pair_delta("bhk", bhk_adj, bhk_key)

    area_val = float(area)
    if area_val <= 800:
        area_key = "<=800"
    elif area_val <= 1200:
        area_key = "801-1200"
    elif area_val <= 1800:
        area_key = "1201-1800"
    elif area_val <= 3000:
        area_key = "1801-3000"
    else:
        area_key = ">3000"
    _apply_pair_delta("area", area_adj, area_key)

    floor_val = float(floor)
    if floor_val <= 0:
        floor_key = "0"
    elif floor_val <= 3:
        floor_key = "1-3"
    elif floor_val <= 7:
        floor_key = "4-7"
    elif floor_val <= 15:
        floor_key = "8-15"
    else:
        floor_key = ">15"
    _apply_pair_delta("floor", floor_adj, floor_key)

    age_val = float(property_age)
    if age_val <= 2:
        age_key = "0-2"
    elif age_val <= 5:
        age_key = "3-5"
    elif age_val <= 10:
        age_key = "6-10"
    elif age_val <= 20:
        age_key = "11-20"
    else:
        age_key = ">20"
    _apply_pair_delta("property_age", age_adj, age_key)

    # Purchase price band
    price_val = float(purchase_price)
    if price_val <= 3_000_000:
        price_band_key = "<=30L"
    elif price_val <= 6_000_000:
        price_band_key = "30L-60L"
    elif price_val <= 10_000_000:
        price_band_key = "60L-1Cr"
    elif price_val <= 20_000_000:
        price_band_key = "1Cr-2Cr"
    else:
        price_band_key = ">2Cr"
    _apply_pair_delta("purchase_price", price_band_adj, price_band_key)

    # Monthly rent band
    rent_val = float(monthly_rent)
    if rent_val <= 15_000:
        rent_band_key = "<=15k"
    elif rent_val <= 30_000:
        rent_band_key = "15k-30k"
    elif rent_val <= 60_000:
        rent_band_key = "30k-60k"
    else:
        rent_band_key = ">60k"
    _apply_pair_delta("monthly_rent", rent_band_adj, rent_band_key)

    return {
        "price_growth_rate": round(pg, 6),
        "rent_growth_rate":  round(rg, 6),
        "rate_source":       source,
        "applied_adjustments": {
            "base_rates": {
                "price_growth_rate": round(base_pg, 6),
                "rent_growth_rate": round(base_rg, 6),
            },
            "totals": {
                "price_growth_delta": round(total_pg_delta, 6),
                "rent_growth_delta": round(total_rg_delta, 6),
            },
            "by_feature": applied,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Investment rating
# ─────────────────────────────────────────────────────────────────────────────

def _investment_rating(roi_pct: float) -> str:
    if roi_pct >= 80:
        return "Excellent"
    elif roi_pct >= 50:
        return "Very Good"
    elif roi_pct >= 30:
        return "Good"
    elif roi_pct >= 10:
        return "Average"
    else:
        return "Below Average"


# ─────────────────────────────────────────────────────────────────────────────
# ROI calculation helpers
# ─────────────────────────────────────────────────────────────────────────────

def calculate_roi(
    purchase_price: float,
    future_price: float,
    total_rent_earned: float,
) -> float:
    """ROI (%) = ((future_price + total_rent - purchase_price) / purchase_price) * 100"""
    if purchase_price <= 0:
        return 0.0
    return ((future_price + total_rent_earned - purchase_price) / purchase_price) * 100


def project_year(
    year: int,
    current_price: float,
    current_monthly_rent: float,
    price_growth_rate: float = None,
    rent_growth_rate: float = None,
) -> dict:
    """
    Project values for a forecast year where Year 0 is the baseline input year.
    Growth is applied from Year 1 onward.

    Returns price, monthly rent, and cumulative rent up to `year`.
    """
    pg = price_growth_rate if price_growth_rate is not None else PRICE_GROWTH_RATE
    rg = rent_growth_rate  if rent_growth_rate  is not None else RENT_GROWTH_RATE

    # Year 0 is baseline; Year N applies N growth steps.
    growth_steps = max(year, 0)
    future_price = current_price * ((1 + pg) ** growth_steps)

    # Total rent = Σ monthly_rent * (1 + rg)^t * 12  for t in 1..year
    # So Year 0 has zero rent earned, and Year 1 is the first forecast year.
    if year <= 0:
        total_rent_earned = 0.0
    else:
        total_rent_earned = sum(
            current_monthly_rent * ((1 + rg) ** t) * 12
            for t in range(1, year + 1)
        )
    # Monthly rent during this forecast year
    monthly_rent_at_year = current_monthly_rent * ((1 + rg) ** growth_steps)

    return {
        "future_price":       round(future_price, 2),
        "monthly_rent":       round(monthly_rent_at_year, 2),
        "total_rent_earned":  round(total_rent_earned, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main predictor class
# ─────────────────────────────────────────────────────────────────────────────

class ROIPredictor:
    """Singleton-like wrapper that loads models once and exposes predict()."""

    _instance = None

    def __init__(self):
        self.price_model  = None
        self.rent_model   = None
        self.encoders     = None
        self._loaded      = False

    def load(self):
        """Load models, encoders, and latest growth rates from disk."""
        price_path = os.path.join(MODELS_DIR, "best_price_model.joblib")
        rent_path  = os.path.join(MODELS_DIR, "best_rent_model.joblib")

        self.price_model = joblib.load(price_path)
        self.rent_model  = joblib.load(rent_path)
        self.encoders    = joblib.load(ENCODERS_PATH)

        # Refresh growth rates from model_meta.json in case models were retrained
        global PRICE_GROWTH_RATE, RENT_GROWTH_RATE, FORECAST_YEARS, _meta
        fresh = _load_meta()
        _meta             = fresh
        PRICE_GROWTH_RATE = fresh["price_growth_rate"]
        RENT_GROWTH_RATE  = fresh["rent_growth_rate"]
        FORECAST_YEARS    = fresh["forecast_years"]

        self._loaded = True
        print("Models loaded successfully.")

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    def predict(self, input_dict: dict) -> dict:
        """
        Full ROI prediction for a single property.

        Parameters
        ----------
        input_dict : dict with keys:
            location, property_type, bhk, area, price, rent,
            property_age, floor, furnishing

        Returns
        -------
        dict with ROI, forecast, and investment rating.
        """
        self._ensure_loaded()

        # ── Build feature row ─────────────────────────────────────────────────
        X_row = prepare_single_input(input_dict, self.encoders)

        # ── Predict base price & rent using ML models ─────────────────────────
        # If the user provides actual price/rent, the ML adjustment acts as a
        # market-adjusted "fair value"; we blend 70 % user-provided + 30 % model.
        user_price = float(input_dict["price"])
        user_rent  = float(input_dict["rent"])

        ml_price   = float(self.price_model.predict(X_row)[0])
        ml_rent    = float(self.rent_model.predict(X_row)[0])

        # Price: use the user's actual purchase price as the investment base.
        # The ML market estimate is displayed for reference only — blending it
        # into the denominator would distort ROI relative to what the investor
        # actually paid.
        base_price = user_price

        # Rent: use user-entered rent as baseline so Year 1 exactly reflects
        # the initial values provided by the user.
        base_rent = user_rent

        # ── Resolve location/feature-specific growth rates ────────────────────
        resolved = _resolve_growth_rates(
            location      = input_dict.get("location", ""),
            city          = input_dict.get("city", ""),
            property_type = input_dict.get("property_type", "apartment"),
            furnishing    = input_dict.get("furnishing", "semi-furnished"),
            bhk           = input_dict.get("bhk", 2),
            area          = input_dict.get("area", 1200),
            floor         = input_dict.get("floor", 1),
            property_age  = input_dict.get("property_age", 5),
            purchase_price = input_dict.get("price", 0),
            monthly_rent   = input_dict.get("rent", 0),
        )
        eff_pg = resolved["price_growth_rate"]
        eff_rg = resolved["rent_growth_rate"]
        rate_src = resolved["rate_source"]

        # ── 0..5 year forecast using resolved rates ───────────────────────────
        yearly_forecast = []
        for yr in range(0, FORECAST_YEARS + 1):
            proj = project_year(yr, base_price, base_rent,
                                price_growth_rate=eff_pg,
                                rent_growth_rate=eff_rg)
            roi  = calculate_roi(base_price, proj["future_price"],
                                 proj["total_rent_earned"])
            yearly_forecast.append({
                "year":              yr,
                "property_price":    proj["future_price"],
                "monthly_rent":      proj["monthly_rent"],
                "annual_rent":       round(proj["monthly_rent"] * 12, 2),
                "total_rent_earned": proj["total_rent_earned"],
                "roi_pct":           round(roi, 2),
                "investment_rating": _investment_rating(roi),
            })

        # ── Final 5-year summary ──────────────────────────────────────────────
        final = yearly_forecast[-1]

        return {
            "input_summary": {
                "purchase_price":     user_price,
                "monthly_rent":       user_rent,
                "market_adj_price":   base_price,
                "market_adj_rent":    base_rent,
                "location":           input_dict.get("location"),
                "property_type":      input_dict.get("property_type"),
                "bhk":                input_dict.get("bhk"),
                "area_sqft":          input_dict.get("area"),
            },
            "ml_estimates": {
                "predicted_price": round(ml_price, 2),
                "predicted_rent":  round(ml_rent, 2),
            },
            "five_year_summary": {
                "future_property_price": final["property_price"],
                "total_rent_earned":     final["total_rent_earned"],
                "roi_pct":               final["roi_pct"],
                "investment_rating":     final["investment_rating"],
                "price_growth_rate_pct": round(eff_pg * 100, 2),
                "rent_growth_rate_pct":  round(eff_rg * 100, 2),
                "forecast_years":        FORECAST_YEARS,
                "rate_source":           rate_src,
            },
            "applied_adjustments": resolved.get("applied_adjustments", {}),
            "yearly_forecast": yearly_forecast,
        }


# Module-level singleton
predictor = ROIPredictor()


def predict_roi(input_dict: dict) -> dict:
    """Convenience function wrapping ROIPredictor.predict()."""
    return predictor.predict(input_dict)
