"""
feature_engineering.py
-----------------------
Applies feature engineering and encoding to the unified DataFrame.
Returns a feature matrix X and targets y_price, y_rent ready for modelling.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ── Constants ────────────────────────────────────────────────────────────────
CATEGORICAL_COLS  = ["location", "property_type", "furnishing"]
NUMERIC_FEATURES  = [
    "bhk", "area", "property_age", "floor",
]
# Full feature list used during training (categorical label-encoded appended)
FEATURE_COLS = NUMERIC_FEATURES + [f"{c}_enc" for c in CATEGORICAL_COLS]


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add / recalculate derived columns.
    Works in-place on a copy – original is unchanged.
    These are kept in the dataset for downstream ROI calculations, but are not
    part of the model feature set unless explicitly included in FEATURE_COLS.
    """
    df = df.copy()
    df["annual_rent"]     = df["rent"] * 12
    df["price_per_sqft"]  = df["price"] / df["area"].replace(0, np.nan)
    df["rent_per_sqft"]   = df["rent"]  / df["area"].replace(0, np.nan)
    return df


def encode_categoricals(
    df: pd.DataFrame,
    encoders: dict | None = None,
    fit: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """
    Label-encode categorical columns.

    Parameters
    ----------
    df       : input DataFrame
    encoders : dict of pre-fitted LabelEncoders (required when fit=False)
    fit      : if True, fit new encoders; if False, use provided encoders

    Returns
    -------
    (encoded_df, encoders_dict)
    """
    df = df.copy()
    if encoders is None:
        encoders = {}

    for col in CATEGORICAL_COLS:
        le_col = f"{col}_enc"
        if fit:
            le = LabelEncoder()
            encoded = le.fit_transform(df[col].astype(str).fillna("unknown"))
            df[le_col] = pd.Series(encoded, index=df.index)
            encoders[col] = le
        else:
            le = encoders[col]
            # Handle unseen labels by mapping to 0
            known = set(le.classes_)
            df[le_col] = df[col].astype(str).fillna("unknown").apply(
                lambda v: v if v in known else le.classes_[0]
            )
            df[le_col] = le.transform(df[le_col])

    return df, encoders


def build_feature_matrix(
    df: pd.DataFrame,
    encoders: dict | None = None,
    fit: bool = True,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series, dict]:
    """
    Full pipeline: derive features → encode → return X, y_price, y_rent,
    and a rent-quality mask for rent-model training.

    Returns
    -------
    X        : feature matrix  (pd.DataFrame)
    y_price  : target – property price  (pd.Series)
    y_rent   : target – monthly rent    (pd.Series)
    rent_mask: True for rows eligible for rent model training (pd.Series)
    encoders : fitted LabelEncoders
    """
    df = add_derived_features(df)
    df, encoders = encode_categoricals(df, encoders=encoders, fit=fit)

    # Drop rows where any feature has NaN
    df.dropna(subset=FEATURE_COLS + ["price", "rent"], inplace=True)

    X       = df[FEATURE_COLS].copy()
    y_price = df["price"].copy()
    y_rent  = df["rent"].copy()

    # Keep rent model focused on observed/data-driven rents.
    if "rent_is_imputed" in df.columns:
        allowed_sources = {"rent_dataset", "combined_property_rates", "magicbricks"}
        if "source" in df.columns:
            rent_mask = (~df["rent_is_imputed"]) | df["source"].isin(allowed_sources)
        else:
            rent_mask = ~df["rent_is_imputed"]
    else:
        rent_mask = pd.Series([True] * len(df), index=df.index)

    return X, y_price, y_rent, rent_mask, encoders


def prepare_single_input(
    input_dict: dict,
    encoders: dict,
    scaler=None,
) -> pd.DataFrame:
    """
    Convert a single property dict into a feature-matrix row for inference.

    Parameters
    ----------
    input_dict : property details (keys = raw column names)
    encoders   : fitted LabelEncoders from training  
    scaler     : optional fitted scaler (unused currently – placeholder)

    Returns
    -------
    pd.DataFrame with exactly the columns in FEATURE_COLS
    """
    row = {
        "bhk":           float(input_dict.get("bhk", 2)),
        "area":          float(input_dict.get("area", 1000)),
        "property_age":  float(input_dict.get("property_age", 5)),
        "floor":         float(input_dict.get("floor", 1)),
    }

    for col in CATEGORICAL_COLS:
        le = encoders[col]
        val = str(input_dict.get(col, "unknown"))
        if val not in le.classes_:
            val = le.classes_[0]
        row[f"{col}_enc"] = int(le.transform([val])[0])

    return pd.DataFrame([row])[FEATURE_COLS]
