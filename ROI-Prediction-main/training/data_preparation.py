"""
data_preparation.py
-------------------
Loads, cleans, and merges all real-estate datasets into a single unified
DataFrame ready for feature engineering and model training.

Datasets used
─────────────
1. House_Rent_Dataset.csv  →  rent, BHK, area, floor, furnishing, city /locality
2. Hyderabad.csv           →  price, area, location, bedrooms
3. Hyderbad_House_price.csv→  price (Lakhs), rate_per_sqft, area, location, status
4. properties.csv          →  price, sqft price, area, bedrooms, floor, furnishing,
                               property lifespan, city, location
5. House Price India.csv   →  price, bedrooms, living area, built year (used for
                               property_age derivation)
"""





import os
import re
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")
# ──────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────────────────────

def _safe_numeric(series: pd.Series) -> pd.Series:
    """Coerce a Series to numeric, replacing non-parseable values with NaN."""
    return pd.to_numeric(series.astype(str).str.replace(",", "").str.strip(),
                         errors="coerce")


def _extract_floor_number(floor_str) -> float:
    """
    Parse floor strings like '1 out of 3', 'Ground out of 2', '5 of 14 Floor'.
    Returns the floor number as float, or NaN.
    """
    if pd.isna(floor_str):
        return np.nan
    s = str(floor_str).lower().strip()
    if s.startswith("ground"):
        return 0.0
    m = re.search(r"(\d+)\s*(?:of|out\s*of)", s)
    if m:
        return float(m.group(1))
    try:
        return float(s)
    except ValueError:
        return np.nan


def _normalize_furnishing(val) -> str:
    """Normalise furnishing labels across datasets."""
    if pd.isna(val):
        return "unfurnished"
    v = str(val).lower().strip()
    if "semi" in v:
        return "semi-furnished"
    if "unfurnish" in v:
        return "unfurnished"
    if "furnish" in v:
        return "furnished"
    return "unfurnished"


# ──────────────────────────────────────────────────────────────────────────────
# Individual dataset loaders
# ──────────────────────────────────────────────────────────────────────────────

def load_rent_dataset() -> pd.DataFrame:
    """House_Rent_Dataset.csv → rows with: rent, bhk, area, floor, furnishing,
    location, city, property_type."""
    path = os.path.join(DATASETS_DIR, "House_Rent_Dataset.csv")
    df = pd.read_csv(path)

    out = pd.DataFrame()
    out["rent"]         = _safe_numeric(df["Rent"])
    out["bhk"]          = _safe_numeric(df["BHK"])
    out["area"]         = _safe_numeric(df["Size"])
    out["floor"]        = df["Floor"].apply(_extract_floor_number)
    out["furnishing"]   = df["Furnishing Status"].apply(_normalize_furnishing)
    out["location"]     = (df["Area Locality"].fillna("") + ", " +
                           df["City"].fillna("")).str.strip(", ")
    out["city"]         = df["City"].str.strip()
    out["posted_on"]    = pd.to_datetime(df["Posted On"], errors="coerce")
    out["property_type"] = "apartment"      # rent dataset is all residential
    out["source"]       = "rent_dataset"
    return out.dropna(subset=["rent", "area"])


def load_hyderabad_dataset() -> pd.DataFrame:
    """Hyderabad.csv → rows with: price, area, location, bhk."""
    path = os.path.join(DATASETS_DIR, "Hyderabad.csv")
    df = pd.read_csv(path)

    out = pd.DataFrame()
    out["price"]        = _safe_numeric(df["Price"])
    out["area"]         = _safe_numeric(df["Area"])
    out["bhk"]          = _safe_numeric(df["No. of Bedrooms"])
    out["location"]     = df["Location"].str.strip()
    out["city"]         = "Hyderabad"
    out["property_type"] = "apartment"
    out["source"]       = "hyderabad"
    return out.dropna(subset=["price", "area"])


def load_hyderabad_price_dataset() -> pd.DataFrame:
    """Hyderbad_House_price.csv → price(Lakhs converted to ₹), area, location,
    bhk, price_per_sqft, building_status."""
    path = os.path.join(DATASETS_DIR, "Hyderbad_House_price.csv")
    df = pd.read_csv(path)

    out = pd.DataFrame()
    # price in Lakhs → absolute ₹
    raw_price = _safe_numeric(
        df["price(L)"].astype(str).str.replace("L", "").str.strip()
    )
    out["price"]        = raw_price * 1_00_000

    # rate_per_sqft → strip spaces
    rate_col = "rate_persqft"
    out["price_per_sqft"] = _safe_numeric(df[rate_col].astype(str).str.strip())

    out["area"]         = _safe_numeric(
        df["area_insqft"].astype(str).str.strip()
    )
    out["location"]     = df["location"].str.strip()
    out["city"]         = "Hyderabad"

    # infer bhk from title  (e.g. "3 BHK Apartment")
    bhk_match = df["title"].astype(str).str.extract(r"(\d+)\s*BHK", expand=False)
    out["bhk"]          = _safe_numeric(bhk_match)

    # property_type from title
    out["property_type"] = df["title"].astype(str).apply(
        lambda t: "villa" if "villa" in t.lower()
        else ("plot" if "plot" in t.lower() else "apartment")
    )
    out["building_status"] = df["building_status"].str.strip()
    out["source"]       = "hyderabad_price"
    return out.dropna(subset=["price", "area"])


def load_properties_dataset() -> pd.DataFrame:
    """properties.csv → price, area, bhk, floor, furnishing, location, city,
    property_type, property_age."""
    path = os.path.join(DATASETS_DIR, "properties.csv")
    # Very wide CSV; read only needed columns
    # Read all columns then rename; column "sqft Price " has a trailing space
    df = pd.read_csv(path, low_memory=False)
    # Strip whitespace from all column names
    df.columns = df.columns.str.strip()

    out = pd.DataFrame()
    out["price"]        = _safe_numeric(df["Price"])

    # area: prefer Carpet Area, fall back to Covered Area
    carpet = _safe_numeric(df["Carpet Area"])
    covered = _safe_numeric(df["Covered Area"])
    out["area"]         = carpet.where(carpet.notna(), covered)

    out["price_per_sqft"] = _safe_numeric(
        df["sqft Price"].astype(str).str.replace(",", "").str.strip()
    )
    out["bhk"]          = _safe_numeric(df["bedroom"])
    out["floor"]        = _safe_numeric(
        df["Floor No"].astype(str).str.extract(r"(\d+)", expand=False)
    )
    out["furnishing"]   = df["furnished Type"].apply(_normalize_furnishing)
    out["location"]     = df["Area Name"].str.strip()
    out["city"]         = df["City"].str.strip()
    out["property_type"] = df["Type of Property"].fillna("apartment").str.lower().str.strip()

    # Property Lifespan → property_age (in years)
    lifespan_map = {
        "new construction": 0, "0-1 year": 0.5, "1-5 years": 3,
        "5-10 years": 7, "10-20 years": 15, "20+ years": 25,
    }
    out["property_age"] = (
        df["Property Lifespan"].str.lower().str.strip()
        .map(lifespan_map)
    )
    out["source"]       = "properties"
    return out.dropna(subset=["price", "area"])


def load_house_price_india() -> pd.DataFrame:
    """House Price India.csv → price, area, bhk, property_age."""
    path = os.path.join(DATASETS_DIR, "House Price India.csv")
    df = pd.read_csv(path)
    CURRENT_YEAR = 2026

    out = pd.DataFrame()
    out["price"]        = _safe_numeric(df["Price"])
    out["area"]         = _safe_numeric(df["living area"])
    out["bhk"]          = _safe_numeric(df["number of bedrooms"])
    built_year          = _safe_numeric(df["Built Year"])
    out["property_age"] = (CURRENT_YEAR - built_year).clip(lower=0)
    out["location"]     = "Unknown"
    out["city"]         = "Unknown"
    out["property_type"] = "house"
    out["source"]       = "house_price_india"
    return out.dropna(subset=["price", "area"])


def load_combined_property_rates() -> pd.DataFrame:
    """
    combined_property_rates.csv → locality-level rates with yield.
    Synthesizes price/rent rows from ₹/sqft and rental-yield percentages.
    """
    path = os.path.join(DATASETS_DIR, "combined_property_rates.csv")
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    out = pd.DataFrame()
    loc_col = "Locality" if "Locality" in df.columns else df.columns[0]
    out["location"] = (
        df[loc_col].astype(str)
        .str.replace("Check Your Property Worth", "", regex=False)
        .str.strip()
    )
    out["city"] = "Hyderabad"

    seg_map = {
        "MID-SEGMENT": 2,
        "MID SEGMENT": 2,
        "PREMIUM": 3,
        "LUXURY": 4,
    }
    seg_col = "Segment" if "Segment" in df.columns else None
    if seg_col:
        out["bhk"] = df[seg_col].astype(str).str.upper().map(seg_map).fillna(2)
    else:
        out["bhk"] = 2

    rate_col = next((c for c in df.columns if "Rate" in c and "sq.ft" in c), None)
    out["price_per_sqft"] = _safe_numeric(df[rate_col]) if rate_col else np.nan

    out["area"] = 1000.0
    out["price"] = out["price_per_sqft"] * out["area"]

    yield_col = next((c for c in df.columns if "Rental Yield" in c), None)
    if yield_col:
        rental_yield = _safe_numeric(df[yield_col]).fillna(3.0) / 100.0
    else:
        rental_yield = pd.Series([0.03] * len(df))
    out["rent"] = (out["price"] * rental_yield / 12.0).round(0)

    # Keep trend columns so rent-growth can use dataset-provided locality trends.
    out["rental_yield_pct"] = _safe_numeric(df[yield_col]) if yield_col else np.nan
    y3_col = next((c for c in df.columns if "3Y Growth" in c), None)
    y5_col = next((c for c in df.columns if "5Y Growth" in c), None)
    yoy_col = next((c for c in df.columns if "YOY Growth" in c), None)
    out["rate_3y_growth_pct"] = _safe_numeric(df[y3_col]) if y3_col else np.nan
    out["rate_5y_growth_pct"] = _safe_numeric(df[y5_col]) if y5_col else np.nan
    out["rate_yoy_growth_pct"] = _safe_numeric(df[yoy_col]) if yoy_col else np.nan

    out["property_type"] = "apartment"
    out["furnishing"] = "semi-furnished"
    out["property_age"] = 5
    out["floor"] = 3
    out["source"] = "combined_property_rates"

    out = out[(out["location"].notna()) & (out["location"] != "")]
    return out.dropna(subset=["price", "area"])


def load_magicbricks_dataset() -> pd.DataFrame:
    """
    magicbricks.xlsx → locality-level average ₹/sqft snapshots.
    Uses Sheet1, strips report text, and synthesizes price/rent rows.
    """
    path = os.path.join(DATASETS_DIR, "magicbricks.xlsx")
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_excel(path, sheet_name="Sheet1")
    if df.empty:
        return pd.DataFrame()

    df.columns = [str(c).strip() for c in df.columns]

    locality_col = next((c for c in df.columns if "Locality" in c), df.columns[0])
    avg_col = next((c for c in df.columns if "Unnamed: 2" in c), None)
    if avg_col is None:
        avg_col = next((c for c in df.columns if "Average" in c), None)
    qoq_col = next((c for c in df.columns if "Unnamed: 3" in c), None)

    out = pd.DataFrame()
    out["location"] = (
        df[locality_col].astype(str)
        .str.replace("Check Your Property Worth", "", regex=False)
        .str.strip()
    )
    out = out[(out["location"] != "") & (out["location"].str.lower() != "nan")]

    if avg_col:
        out["price_per_sqft"] = _safe_numeric(df.loc[out.index, avg_col])
    else:
        out["price_per_sqft"] = np.nan

    out["city"] = "Hyderabad"
    out["area"] = 1000.0
    out["price"] = out["price_per_sqft"] * out["area"]

    # Use QoQ as a weak proxy for yield when available; otherwise default 3%.
    if qoq_col:
        qoq_pct = _safe_numeric(
            df.loc[out.index, qoq_col].astype(str).str.replace("%", "", regex=False)
        ).fillna(0)
        rental_yield = (0.03 + (qoq_pct.clip(-2, 4) / 1000.0)).clip(0.02, 0.05)
        out["rate_qoq_growth_pct"] = qoq_pct
    else:
        rental_yield = pd.Series([0.03] * len(out), index=out.index)
        out["rate_qoq_growth_pct"] = np.nan
    out["rent"] = (out["price"] * rental_yield / 12.0).round(0)

    out["bhk"] = 2
    out["property_type"] = "apartment"
    out["furnishing"] = "semi-furnished"
    out["property_age"] = 5
    out["floor"] = 3
    out["source"] = "magicbricks"

    return out.dropna(subset=["price", "area"])


# ──────────────────────────────────────────────────────────────────────────────
# Master merge
# ──────────────────────────────────────────────────────────────────────────────

UNIFIED_COLUMNS = [
    "location", "city", "property_type", "bhk", "area",
    "price", "rent", "property_age", "floor", "furnishing",
    "price_per_sqft", "rent_per_sqft", "source",
]


def build_unified_dataset(save_path: str | None = None) -> pd.DataFrame:
    """
    Load all datasets, align columns, merge, engineer base features,
    clean, and return a unified DataFrame.

    Parameters
    ----------
    save_path : str, optional
        If provided, saves the cleaned CSV to this path.

    Returns
    -------
    pd.DataFrame
    """
    print("Loading datasets …")
    rent_df    = load_rent_dataset()
    hyd_df     = load_hyderabad_dataset()
    hydp_df    = load_hyderabad_price_dataset()
    prop_df    = load_properties_dataset()
    india_df   = load_house_price_india()
    comb_df    = load_combined_property_rates()
    mb_df      = load_magicbricks_dataset()

    # Concatenate (outer-join style – missing columns become NaN)
    combined = pd.concat(
        [rent_df, hyd_df, hydp_df, prop_df, india_df, comb_df, mb_df],
        ignore_index=True, sort=False,
    )

    # Track rows where rent was not observed in raw data and will be synthesized.
    combined["rent_is_imputed"] = combined["rent"].isna()

    # Ensure derived columns exist before using them
    for col in ["price_per_sqft", "rent_per_sqft"]:
        if col not in combined.columns:
            combined[col] = np.nan

    # ── Derive price_per_sqft & rent_per_sqft ─────────────────────────────────
    # Fill price_per_sqft from price/area where missing
    mask = combined["price_per_sqft"].isna() & combined["price"].notna() & (combined["area"] > 0)
    combined.loc[mask, "price_per_sqft"] = combined.loc[mask, "price"] / combined.loc[mask, "area"]

    mask = combined["rent_per_sqft"].isna() & combined["rent"].notna() & (combined["area"] > 0)
    combined.loc[mask, "rent_per_sqft"] = combined.loc[mask, "rent"] / combined.loc[mask, "area"]

    # ── Synthesize rent for price-only rows ───────────────────────────────────
    # Typical rental yield in India ≈ 2–4 % annually; use 3 % as median.
    # monthly_rent ≈ price × 0.03 / 12
    RENTAL_YIELD = 0.03
    no_rent = combined["rent"].isna() & combined["price"].notna()
    combined.loc[no_rent, "rent"] = (
        combined.loc[no_rent, "price"] * RENTAL_YIELD / 12
    ).round(0)
    combined.loc[no_rent, "rent_per_sqft"] = (
        combined.loc[no_rent, "rent"] / combined.loc[no_rent, "area"]
    )

    # ── Synthesize price for rent-only rows ───────────────────────────────────
    no_price = combined["price"].isna() & combined["rent"].notna()
    combined.loc[no_price, "price"] = (
        combined.loc[no_price, "rent"] * 12 / RENTAL_YIELD
    ).round(0)
    combined.loc[no_price, "price_per_sqft"] = (
        combined.loc[no_price, "price"] / combined.loc[no_price, "area"]
    )

    # ── Default fills ──────────────────────────────────────────────────────────
    combined["bhk"]          = combined["bhk"].fillna(2)
    combined["floor"]        = combined["floor"].fillna(1)
    combined["property_age"] = combined["property_age"].fillna(5)
    combined["property_type"] = combined["property_type"].fillna("apartment")
    combined["furnishing"]   = combined["furnishing"].fillna("unfurnished")
    combined["location"]     = combined["location"].fillna("Unknown")
    combined["city"]         = combined["city"].fillna("Unknown")

    # ── Annual rent derived feature ────────────────────────────────────────────
    combined["annual_rent"] = combined["rent"] * 12

    # ── Sanity filters ─────────────────────────────────────────────────────────
    # Keep only rows with positive price AND area
    combined = combined[
        (combined["price"] > 0) &
        (combined["area"]  > 0) &
        (combined["rent"]  > 0)
    ].copy()

    # Remove extreme outliers using IQR on price and area
    for col in ["price", "area", "rent"]:
        q1, q3 = combined[col].quantile(0.01), combined[col].quantile(0.99)
        combined = combined[(combined[col] >= q1) & (combined[col] <= q3)]

    # Drop duplicates
    combined.drop_duplicates(
        subset=["location", "bhk", "area", "price", "rent"],
        inplace=True,
    )
    combined.reset_index(drop=True, inplace=True)

    print(f"Unified dataset: {len(combined):,} rows × {combined.shape[1]} cols")
    print(f"Columns: {list(combined.columns)}")
    if "source" in combined.columns and "rent_is_imputed" in combined.columns:
        print("Observed-rent rows by source:")
        obs = combined.loc[~combined["rent_is_imputed"], "source"].value_counts()
        print(obs.to_string())

    if save_path:
        combined.to_csv(save_path, index=False)
        print(f"Saved → {save_path}")

    return combined


def _cohort_cagr(sub: pd.DataFrame, min_count: int = 20) -> float | None:
    """
    Compute price-appreciation CAGR for a sub-DataFrame using cohort split
    (new properties vs old properties by property_age) + OLS.
    Returns None if insufficient data.
    """
    sub = sub[(sub["price"] > 0) & (sub["area"] > 0) & (sub["property_age"] >= 0)].copy()
    sub["ppsf"] = sub["price"] / sub["area"]

    estimates = []

    new_c = sub[sub["property_age"] < 3]["ppsf"]
    old_c = sub[sub["property_age"] >= 10]["ppsf"]
    if len(new_c) >= min_count and len(old_c) >= min_count:
        ppsf_new, ppsf_old = new_c.median(), old_c.median()
        mid_new = sub[sub["property_age"] < 3]["property_age"].median()
        mid_old = sub[sub["property_age"] >= 10]["property_age"].median()
        age_diff = max(mid_old - mid_new, 1)
        if ppsf_new > ppsf_old > 0:
            estimates.append((ppsf_new / ppsf_old) ** (1 / age_diff) - 1)

    ols_sub = sub[(sub["property_age"] > 0) & sub["ppsf"].notna()]
    if len(ols_sub) >= max(min_count * 2, 40):
        coeffs = np.polyfit(ols_sub["property_age"], ols_sub["ppsf"], 1)
        mean_ppsf = ols_sub["ppsf"].mean()
        if mean_ppsf > 0:
            ols_rate = -coeffs[0] / mean_ppsf
            estimates.append(ols_rate)

    if not estimates:
        return None
    return float(np.mean(estimates))


def _yield_to_rent_growth(sub: pd.DataFrame, price_growth: float,
                          min_count: int = 20) -> float | None:
    """Median gross yield × 0.75, clamped; returns None if insufficient data."""
    v = sub[(sub["rent"] > 0) & (sub["price"] > 0)]
    if len(v) < min_count:
        return None
    annual_yield = (v["rent"] * 12 / v["price"]).replace([np.inf, -np.inf], np.nan).dropna()
    if len(annual_yield) < min_count:
        return None
    return float(np.clip(max(price_growth, annual_yield.median() * 0.75), 0.03, 0.15))


def _annualize_total_growth(total_growth_pct: pd.Series, years: int) -> pd.Series:
    """Convert total multi-year growth (%) to annualized decimal growth."""
    g = pd.to_numeric(total_growth_pct, errors="coerce") / 100.0
    g = g.replace([np.inf, -np.inf], np.nan)
    # Guard against invalid compounding inputs.
    g = g.where((1.0 + g) > 0, np.nan)
    return pd.Series(np.power(1.0 + g, 1.0 / years) - 1.0, index=g.index, dtype="float64")


def _trend_columns_to_rent_growth(sub: pd.DataFrame, min_count: int = 15) -> float | None:
    """
    Estimate rent growth from locality trend columns (YOY/3Y/5Y/QoQ).
    Returns annualized decimal growth if enough trend data exists.
    """
    candidates = []

    if "rate_yoy_growth_pct" in sub.columns:
        yoy = pd.to_numeric(sub["rate_yoy_growth_pct"], errors="coerce") / 100.0
        yoy = yoy.replace([np.inf, -np.inf], np.nan).dropna()
        if len(yoy) >= min_count:
            candidates.append(yoy)

    if "rate_3y_growth_pct" in sub.columns:
        g3 = _annualize_total_growth(sub["rate_3y_growth_pct"], years=3).dropna()
        if len(g3) >= min_count:
            candidates.append(g3)

    if "rate_5y_growth_pct" in sub.columns:
        g5 = _annualize_total_growth(sub["rate_5y_growth_pct"], years=5).dropna()
        if len(g5) >= min_count:
            candidates.append(g5)

    if "rate_qoq_growth_pct" in sub.columns:
        qoq = pd.to_numeric(sub["rate_qoq_growth_pct"], errors="coerce") / 100.0
        qoq = qoq.replace([np.inf, -np.inf], np.nan)
        qoq = np.power(1.0 + qoq, 4) - 1.0
        qoq = pd.Series(qoq).dropna()
        if len(qoq) >= min_count:
            candidates.append(qoq)

    if not candidates:
        return None

    merged = pd.concat(candidates, ignore_index=True)
    if len(merged) < min_count:
        return None
    return float(np.clip(merged.median(), 0.03, 0.15))


def _posted_on_to_rent_growth(sub: pd.DataFrame,
                              min_points: int = 80,
                              min_span_days: int = 45) -> float | None:
    """
    Estimate annual rent growth from House_Rent posting dates and rent/sqft trend.
    Uses month-level medians to reduce noise from listing-level variance.
    """
    if "posted_on" not in sub.columns:
        return None

    v = sub.copy()
    v["posted_on"] = pd.to_datetime(v["posted_on"], errors="coerce")
    v = v[v["posted_on"].notna() & (v["rent"] > 0) & (v["area"] > 0)]
    if len(v) < min_points:
        return None

    v["rent_per_sqft"] = (v["rent"] / v["area"]).replace([np.inf, -np.inf], np.nan)
    v = v[v["rent_per_sqft"].notna() & (v["rent_per_sqft"] > 0)]
    if len(v) < min_points:
        return None

    span_days = (v["posted_on"].max() - v["posted_on"].min()).days
    if span_days < min_span_days:
        return None

    month_key = pd.Series(
        v["posted_on"].dt.to_period("M").astype(str),
        index=v.index,
        dtype="string",
    )
    monthly = v.groupby(month_key)["rent_per_sqft"].median().sort_index()
    if len(monthly) < 2:
        return None

    first, last = float(monthly.iloc[0]), float(monthly.iloc[-1])
    if first <= 0 or last <= 0:
        return None

    years = max(span_days / 365.25, 0.1)
    annual = (last / first) ** (1.0 / years) - 1.0
    return float(np.clip(annual, 0.03, 0.15))


def _resolve_rent_growth(sub: pd.DataFrame,
                         price_growth: float,
                         fallback_growth: float | None = None,
                         min_count_yield: int = 20) -> tuple[float, str]:
    """Resolve rent growth using trend columns/date trend first, yield as fallback."""
    rg = _trend_columns_to_rent_growth(sub, min_count=max(10, min_count_yield // 2))
    if rg is not None:
        return rg, "trend_columns"

    rg = _posted_on_to_rent_growth(sub)
    if rg is not None:
        return rg, "posted_on"

    rg = _yield_to_rent_growth(sub, price_growth, min_count=min_count_yield)
    if rg is not None:
        return rg, "yield_proxy"

    if fallback_growth is None:
        fallback_growth = float(np.clip(price_growth * 1.2, 0.03, 0.15))
    return float(np.clip(fallback_growth, 0.03, 0.15)), "fallback"


def compute_growth_rates(unified_df: pd.DataFrame) -> dict:
    """
    Derive annual price and rent growth rates from the dataset at four
    levels of granularity:

      1. Global              — full dataset
      2. Per-city            — grouped by city
      3. Per-location        — grouped by location (fine-grained)
      4. Property-type delta — how much each type deviates from its city median
      5. Furnishing delta    — rent-growth premium/discount per furnishing level

    All rates are clamped to safe bounds and stored in a nested dict that is
    persisted as part of model_meta.json.  At inference time the predictor
    looks up rates in order: location → city → global, then adds type/furnishing
    deltas.
    """
    MIN_LOC  = 20   # min rows for a location-level estimate
    MIN_CITY = 50   # min rows for a city-level estimate
    CLAMP_P  = (0.03, 0.12)
    CLAMP_R  = (0.03, 0.15)

    df = unified_df.copy()
    df["ppsf"] = (df["price"] / df["area"]).where(df["area"] > 0)

    # ── 1. Global rates ───────────────────────────────────────────────────────
    raw_pg = _cohort_cagr(df, min_count=30) or 0.06
    global_pg = float(np.clip(raw_pg, *CLAMP_P))

    if "source" in df.columns:
        source_series = df["source"].astype(str)
    else:
        source_series = pd.Series([""] * len(df), index=df.index, dtype=str)

    if "rent_is_imputed" in df.columns:
        observed_rent_mask = ~df["rent_is_imputed"].astype(bool)
    else:
        observed_rent_mask = pd.Series([True] * len(df), index=df.index)

    # Prefer observed/data-driven rent rows to avoid bias from synthetic rents.
    preferred_sources = {"rent_dataset", "combined_property_rates", "magicbricks"}
    sample = df.loc[observed_rent_mask & source_series.isin(preferred_sources)].copy()
    if len(sample) < 30:
        sample = df.loc[observed_rent_mask].copy()
    if len(sample) < 30:
        sample = df.copy()
    global_rg, global_rg_src = _resolve_rent_growth(
        sample,
        price_growth=global_pg,
        fallback_growth=float(np.clip(global_pg * 1.3, *CLAMP_R)),
        min_count_yield=30,
    )

    print(f"  [global] price={global_pg*100:.2f}%  rent={global_rg*100:.2f}%  ({global_rg_src})")

    # ── 2. Per-city rates ─────────────────────────────────────────────────────
    # Method: ppsf premium relative to global median → growth premium
    # Cities with higher ppsf have stronger demand → faster appreciation.
    # Formula: city_pg = global_pg + clip(log(city_ppsf/global_ppsf) * 1.5, -2%, +3%)
    global_ppsf = df["ppsf"].median()
    city_rates: dict[str, dict] = {}
    for city, grp in df.groupby("city"):
        if city in ("Unknown", "", None) or len(grp) < MIN_CITY:
            continue
        city_ppsf = grp["ppsf"].median()
        if global_ppsf > 0 and not pd.isna(city_ppsf) and city_ppsf > 0:
            import math
            ppsf_ratio  = city_ppsf / global_ppsf
            price_delta = float(np.clip(math.log(ppsf_ratio) * 1.5, -0.02, 0.03))
        else:
            price_delta = 0.0
        pg = float(np.clip(global_pg + price_delta, *CLAMP_P))

        # Rent growth from trend columns/date trend first, then yield fallback.
        rg, _ = _resolve_rent_growth(
            grp,
            price_growth=pg,
            fallback_growth=float(np.clip(pg * 1.2, *CLAMP_R)),
            min_count_yield=15,
        )

        city_rates[str(city)] = {
            "price_growth_rate": round(pg, 6),
            "rent_growth_rate":  round(rg, 6),
        }

    print(f"  [cities] computed rates for {len(city_rates)} cities")

    # ── 3. Per-location rates ─────────────────────────────────────────────────
    # Method: ppsf premium relative to the city median (or global if city unknown)
    # Formula: loc_pg = city_pg + clip(log(loc_ppsf/city_ppsf) * 1.0, -2%, +2%)
    city_ppsf_map = {
        city: grp["ppsf"].median()
        for city, grp in df.groupby("city")
        if city not in ("Unknown", "", None) and len(grp) >= MIN_CITY
    }
    location_rates: dict[str, dict] = {}
    for loc, grp in df.groupby("location"):
        if loc in ("Unknown", "", None) or len(grp) < MIN_LOC:
            continue
        city = grp["city"].mode().iloc[0] if "city" in grp.columns and len(grp) > 0 else "Unknown"
        city_ref = city_rates.get(str(city), {})
        city_pg  = city_ref.get("price_growth_rate", global_pg)
        ref_ppsf = city_ppsf_map.get(str(city), global_ppsf)

        loc_ppsf = grp["ppsf"].median()
        if ref_ppsf > 0 and not pd.isna(loc_ppsf) and loc_ppsf > 0:
            import math
            ppsf_ratio  = loc_ppsf / ref_ppsf
            price_delta = float(np.clip(math.log(ppsf_ratio) * 1.0, -0.02, 0.02))
        else:
            price_delta = 0.0
        pg = float(np.clip(city_pg + price_delta, *CLAMP_P))

        # Rent growth from trend columns/date trend first, then city fallback.
        rg, _ = _resolve_rent_growth(
            grp,
            price_growth=pg,
            fallback_growth=city_ref.get(
                "rent_growth_rate",
                float(np.clip(pg * 1.2, *CLAMP_R)),
            ),
            min_count_yield=10,
        )
        rg = float(np.clip(rg, *CLAMP_R))

        location_rates[str(loc)] = {
            "price_growth_rate": round(pg, 6),
            "rent_growth_rate":  round(rg, 6),
        }

    print(f"  [locations] computed rates for {len(location_rates)} locations")

    # ── 4. Property-type adjustments (delta vs global) ────────────────────────
    # We compute median ppsf per type and express it as % deviation from global.
    # That deviation becomes an additive ±delta on the growth rate.
    global_ppsf = df["ppsf"].median()
    ptype_adj: dict[str, dict] = {}
    for ptype, grp in df.groupby("property_type"):
        if len(grp) < 20:
            continue
        type_ppsf = grp["ppsf"].median()
        if global_ppsf > 0 and not pd.isna(type_ppsf):
            # premium types appreciate faster
            price_delta = float(np.clip((type_ppsf / global_ppsf - 1) * 0.03, -0.02, 0.03))
        else:
            price_delta = 0.0

        yield_delta = 0.0
        v = grp[(grp["rent"] > 0) & (grp["price"] > 0)]
        global_v = df[(df["rent"] > 0) & (df["price"] > 0)]
        if len(v) >= 20 and len(global_v) >= 20:
            type_yield = (v["rent"] * 12 / v["price"]).median()
            global_yield = (global_v["rent"] * 12 / global_v["price"]).median()
            if global_yield > 0 and not pd.isna(type_yield):
                yield_delta = float(np.clip((type_yield / global_yield - 1) * 0.02, -0.02, 0.02))

        ptype_adj[str(ptype)] = {
            "price_growth_delta": round(price_delta, 6),
            "rent_growth_delta":  round(yield_delta, 6),
        }

    print(f"  [property_type] adjustments: {ptype_adj}")

    # ── 5. Furnishing adjustments (rent-growth delta only) ────────────────────
    furnishing_adj: dict[str, float] = {}
    global_yield_v = df[(df["rent"] > 0) & (df["price"] > 0)]
    global_yield_med = (global_yield_v["rent"] * 12 / global_yield_v["price"]).median() \
        if len(global_yield_v) > 0 else 0.03
    for furn, grp in df.groupby("furnishing"):
        v = grp[(grp["rent"] > 0) & (grp["price"] > 0)]
        if len(v) < 20:
            continue
        furn_yield = (v["rent"] * 12 / v["price"]).median()
        if global_yield_med > 0 and not pd.isna(furn_yield):
            delta = float(np.clip((furn_yield / global_yield_med - 1) * 0.015, -0.015, 0.015))
        else:
            delta = 0.0
        furnishing_adj[str(furn)] = round(delta, 6)

    print(f"  [furnishing] rent-growth deltas: {furnishing_adj}")

    # ── 6. Input-feature adjustments (bhk / area / floor / age) ─────────────
    # These make ROI growth assumptions responsive to user-entered features,
    # not only location/type/furnishing.
    global_yield_med = (global_yield_v["rent"] * 12 / global_yield_v["price"]).median() \
        if len(global_yield_v) > 0 else 0.03

    def _feature_delta(sub: pd.DataFrame,
                       min_count: int = 20,
                       price_scale: float = 0.02,
                       rent_scale: float = 0.015,
                       p_clamp: tuple = (-0.015, 0.02),
                       r_clamp: tuple = (-0.015, 0.02)) -> tuple[float, float] | None:
        if len(sub) < min_count:
            return None

        sub_ppsf = sub["ppsf"].median()
        if global_ppsf > 0 and not pd.isna(sub_ppsf):
            p_delta = float(np.clip((sub_ppsf / global_ppsf - 1) * price_scale,
                                    p_clamp[0], p_clamp[1]))
        else:
            p_delta = 0.0

        v = sub[(sub["rent"] > 0) & (sub["price"] > 0)]
        if len(v) >= min_count and global_yield_med > 0:
            sub_yield = (v["rent"] * 12 / v["price"]).median()
            if not pd.isna(sub_yield):
                r_delta = float(np.clip((sub_yield / global_yield_med - 1) * rent_scale,
                                        r_clamp[0], r_clamp[1]))
            else:
                r_delta = 0.0
        else:
            r_delta = 0.0

        return round(p_delta, 6), round(r_delta, 6)

    # BHK deltas (0..10 buckets)
    bhk_adj: dict[str, dict] = {}
    df["bhk_bucket"] = df["bhk"].round().clip(lower=0, upper=10)
    for bhk_bucket, grp in df.groupby("bhk_bucket"):
        out = _feature_delta(grp, min_count=25)
        if out is None:
            continue
        p_delta, r_delta = out
        bhk_key = str(pd.Series([bhk_bucket]).astype("float64").round().astype("int64").iloc[0])
        bhk_adj[bhk_key] = {
            "price_growth_delta": p_delta,
            "rent_growth_delta": r_delta,
        }

    # Area deltas (banded)
    area_bins = [0, 800, 1200, 1800, 3000, np.inf]
    area_labels = ["<=800", "801-1200", "1201-1800", "1801-3000", ">3000"]
    df["area_band"] = pd.cut(df["area"], bins=area_bins, labels=area_labels)
    area_adj: dict[str, dict] = {}
    for band, grp in df.groupby("area_band"):
        if pd.isna(band):
            continue
        out = _feature_delta(grp, min_count=25)
        if out is None:
            continue
        p_delta, r_delta = out
        area_adj[str(band)] = {
            "price_growth_delta": p_delta,
            "rent_growth_delta": r_delta,
        }

    # Floor deltas (banded)
    floor_bins = [-1, 0, 3, 7, 15, np.inf]
    floor_labels = ["0", "1-3", "4-7", "8-15", ">15"]
    df["floor_band"] = pd.cut(df["floor"], bins=floor_bins, labels=floor_labels)
    floor_adj: dict[str, dict] = {}
    for band, grp in df.groupby("floor_band"):
        if pd.isna(band):
            continue
        out = _feature_delta(grp, min_count=25)
        if out is None:
            continue
        p_delta, r_delta = out
        floor_adj[str(band)] = {
            "price_growth_delta": p_delta,
            "rent_growth_delta": r_delta,
        }

    # Property age deltas (banded)
    age_bins = [-1, 2, 5, 10, 20, np.inf]
    age_labels = ["0-2", "3-5", "6-10", "11-20", ">20"]
    df["age_band"] = pd.cut(df["property_age"], bins=age_bins, labels=age_labels)
    age_adj: dict[str, dict] = {}
    for band, grp in df.groupby("age_band"):
        if pd.isna(band):
            continue
        out = _feature_delta(grp, min_count=25)
        if out is None:
            continue
        p_delta, r_delta = out
        age_adj[str(band)] = {
            "price_growth_delta": p_delta,
            "rent_growth_delta": r_delta,
        }

    print(f"  [bhk] adjustments: {bhk_adj}")
    print(f"  [area] adjustments: {area_adj}")
    print(f"  [floor] adjustments: {floor_adj}")
    print(f"  [age] adjustments: {age_adj}")

    # ── 7. Purchase-price and monthly-rent band adjustments ─────────────────
    price_bins = [0, 3_000_000, 6_000_000, 10_000_000, 20_000_000, np.inf]
    price_labels = ["<=30L", "30L-60L", "60L-1Cr", "1Cr-2Cr", ">2Cr"]
    df["price_band"] = pd.cut(df["price"], bins=price_bins, labels=price_labels)
    price_band_adj: dict[str, dict] = {}
    for band, grp in df.groupby("price_band"):
        if pd.isna(band):
            continue
        out = _feature_delta(grp, min_count=25)
        if out is None:
            continue
        p_delta, r_delta = out
        price_band_adj[str(band)] = {
            "price_growth_delta": p_delta,
            "rent_growth_delta": r_delta,
        }

    rent_bins = [-1, 15_000, 30_000, 60_000, np.inf]
    rent_labels = ["<=15k", "15k-30k", "30k-60k", ">60k"]
    df["rent_band"] = pd.cut(df["rent"], bins=rent_bins, labels=rent_labels)
    rent_band_adj: dict[str, dict] = {}
    for band, grp in df.groupby("rent_band"):
        if pd.isna(band):
            continue
        out = _feature_delta(grp, min_count=25)
        if out is None:
            continue
        p_delta, r_delta = out
        rent_band_adj[str(band)] = {
            "price_growth_delta": p_delta,
            "rent_growth_delta": r_delta,
        }

    print(f"  [price_band] adjustments: {price_band_adj}")
    print(f"  [rent_band] adjustments: {rent_band_adj}")

    return {
        "price_growth_rate":   round(global_pg, 6),
        "rent_growth_rate":    round(global_rg, 6),
        "forecast_years":      5,
        "city_rates":          city_rates,
        "location_rates":      location_rates,
        "property_type_adj":   ptype_adj,
        "furnishing_rent_adj": furnishing_adj,
        "bhk_adj":             bhk_adj,
        "area_adj":            area_adj,
        "floor_adj":           floor_adj,
        "age_adj":             age_adj,
        "price_band_adj":      price_band_adj,
        "rent_band_adj":       rent_band_adj,
    }

if __name__ == "__main__":
    out_path = os.path.join(DATASETS_DIR, "unified_dataset.csv")
    df = build_unified_dataset(save_path=out_path)
    rates = compute_growth_rates(df)
    print("Global rates:", rates["price_growth_rate"], rates["rent_growth_rate"])
    print("Locations computed:", len(rates["location_rates"]))
    print(df.head())
    print(df.describe())
