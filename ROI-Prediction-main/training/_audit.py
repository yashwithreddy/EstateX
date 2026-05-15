"""
_audit.py — Dashboard validation script.
Run: python training/_audit.py
"""
import sys, os, json, math, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

def section(title): print(f"\n{'═'*64}\n  {title}\n{'═'*64}")

# ── Load models
price_model = joblib.load(os.path.join(MODELS_DIR, "best_price_model.joblib"))
rent_model  = joblib.load(os.path.join(MODELS_DIR, "best_rent_model.joblib"))
encoders    = joblib.load(os.path.join(MODELS_DIR, "encoders.joblib"))

# ── Build test row
from feature_engineering import prepare_single_input, FEATURE_COLS
inp = {"location":"Banjara Hills","city":"Hyderabad","property_type":"apartment",
       "bhk":3,"area":1500,"price":7500000,"rent":25000,
       "property_age":5,"floor":3,"furnishing":"semi-furnished"}
X_row = prepare_single_input(inp, encoders)

# ────────────────────────────────────────────────────────────────────────────
section("1. ARE THE TWO MODELS ACTUALLY DIFFERENT OBJECTS?")
same_obj = price_model is rent_model
print(f"  price_model is rent_model  : {same_obj}  ← should be False")
print(f"  price_model type           : {type(price_model).__name__}")
print(f"  rent_model  type           : {type(rent_model).__name__}")
# Probe internals to see if they're trained on same target
if hasattr(price_model, 'init_'):
    print(f"  price_model.init_  : {price_model.init_}")
    print(f"  rent_model.init_   : {rent_model.init_}")

# ────────────────────────────────────────────────────────────────────────────
section("2. ML PREDICTIONS — RAW OUTPUT OF EACH MODEL")
ml_price = float(price_model.predict(X_row)[0])
ml_rent  = float(rent_model.predict(X_row)[0])
print(f"  ML Price predict(X_row)  : ₹{ml_price:,.2f}")
print(f"  ML Rent  predict(X_row)  : ₹{ml_rent:,.2f}")
print(f"  Are they identical?      : {abs(ml_price - ml_rent) < 1}")
print()
print("  EXPECTED:")
print("  ML Price should be total property value (~₹50L–₹1Cr for 3BHK Banjara Hills)")
print("  ML Rent  should be monthly rent (~₹20K–₹50K for semi-furnished 3BHK)")

# Broad sanity range test
price_in_range = 1_000_000 <= ml_price <= 100_000_000   # ₹10L–₹10Cr
rent_in_range  = 5_000    <= ml_rent  <= 200_000         # ₹5K–₹2L/month
print(f"\n  Price in realistic range (₹10L–10Cr): {price_in_range}  ← {'✓' if price_in_range else '✗ FAIL'}")
print(f"  Rent  in realistic range (₹5K–2L/mo): {rent_in_range}   ← {'✓' if rent_in_range else '✗ FAIL'}")

# ────────────────────────────────────────────────────────────────────────────
section("3. MARKET-ADJ PRICE vs USER PRICE (NEW BLEND POLICY)")
user_price = 7_500_000.0
user_rent  = 25_000.0
# New policy: price = user price (no ML blend); rent = clamped blend
blend_price = user_price   # 100% user price
ml_rent_clamped = float(max(user_rent * 0.50, min(user_rent * 1.50, ml_rent)))
blend_rent  = 0.70 * user_rent + 0.30 * ml_rent_clamped
print(f"  User-entered price        : ₹{user_price:,.0f}")
print(f"  ML price estimate (ref)   : ₹{ml_price:,.2f}  (informational — not blended into ROI)")
print(f"  Base price for ROI        : ₹{blend_price:,.2f}  ← user price, no blend")
print(f"  Deviation from user price : 0.0%  ✓ (user price used directly)")

print(f"\n  User-entered rent         : ₹{user_rent:,.0f}/mo")
print(f"  ML rent estimate          : ₹{ml_rent:,.2f}/mo")
print(f"  ML rent (clamped ±50%)    : ₹{ml_rent_clamped:,.2f}/mo")
print(f"  Market-adj rent  (70/30)  : ₹{blend_rent:,.2f}/mo")
rent_deviation_pct = (blend_rent - user_rent) / user_rent * 100
print(f"  Deviation from user rent  : {rent_deviation_pct:+.1f}%  ← {'OK' if abs(rent_deviation_pct) < 25 else '⚠ LARGE DEVIATION'}")

# ────────────────────────────────────────────────────────────────────────────
section("4. ROI FORMULA VERIFICATION")
pg, rg = 0.12, 0.1092
base_price = blend_price   # = user_price under new policy
base_rent  = blend_rent    # = clamped rent blend

total_rent_yr5 = sum(base_rent * (1+rg)**t * 12 for t in range(1,6))
future_price_yr5 = base_price * (1+pg)**5
roi = (future_price_yr5 + total_rent_yr5 - base_price) / base_price * 100

print(f"  Base price (adj)          : ₹{base_price:,.2f}")
print(f"  Base rent  (adj)          : ₹{base_rent:,.2f}/mo")
print(f"  Future price Year 5       : ₹{future_price_yr5:,.2f}")
print(f"  Total rent earned Y1-Y5   : ₹{total_rent_yr5:,.2f}")
print(f"  Manual ROI calculation    : {roi:.2f}%")

# verify monthly×12×5 simple approximation
simple_rent = base_rent * 12 * 5
print(f"\n  Simple (flat) rent×12×5   : ₹{simple_rent:,.2f}")
print(f"  Actual (compounding)      : ₹{total_rent_yr5:,.2f}")
print(f"  Difference                : ₹{total_rent_yr5 - simple_rent:,.2f}  (compounding premium)")

# ────────────────────────────────────────────────────────────────────────────
section("5. WHAT IF WE USE USER VALUES DIRECTLY (NO ML BLEND)?")
bp2 = user_price
br2 = user_rent
total_rent_yr5_correct = sum(br2 * (1+rg)**t * 12 for t in range(1,6))
future_price_yr5_correct = bp2 * (1+pg)**5
roi_correct = (future_price_yr5_correct + total_rent_yr5_correct - bp2) / bp2 * 100
print(f"  User price                : ₹{bp2:,.0f}")
print(f"  User rent                 : ₹{br2:,.0f}/mo")
print(f"  Future price Year 5       : ₹{future_price_yr5_correct:,.2f}")
print(f"  Total rent earned Y1-Y5   : ₹{total_rent_yr5_correct:,.2f}")
print(f"  Correct ROI (user values) : {roi_correct:.2f}%")

# ────────────────────────────────────────────────────────────────────────────
section("6. FEATURE LEAKAGE CHECK")
from feature_engineering import FEATURE_COLS
leaked = [c for c in FEATURE_COLS if c in ("price_per_sqft","rent_per_sqft","annual_rent")]
print(f"  FEATURE_COLS: {FEATURE_COLS}")
print(f"  Derived features in model inputs: {leaked}  ← {'LEAK DETECTED' if leaked else '✓ No leakage'}")

# ────────────────────────────────────────────────────────────────────────────
section("7. TRAINING DATA DISTRIBUTION (from saved encoders check)")
meta_path = os.path.join(MODELS_DIR, "model_meta.json")
with open(meta_path) as f:
    meta = json.load(f)
print(f"  Price model R²  : {meta.get('price_r2', 'N/A')}")
print(f"  Rent  model R²  : {meta.get('rent_r2',  'N/A')}")
print(f"  Price model name: {meta.get('price_model_name','N/A')}")
print(f"  Rent  model name: {meta.get('rent_model_name', 'N/A')}")
loc_count = len(meta.get("location_rates", {}))
city_count = len(meta.get("city_rates", {}))
print(f"  Locations in rate table : {loc_count}")
print(f"  Cities in rate table    : {city_count}")

# ────────────────────────────────────────────────────────────────────────────
section("8. CORRECTED ESTIMATES TABLE")
print(f"  {'Metric':<35} {'Current (Buggy)':<22} {'Corrected':<22}")
print(f"  {'-'*35} {'-'*22} {'-'*22}")
print(f"  {'ML Price Estimate':<35} ₹{ml_price:>18,.0f}   ₹{user_price:>18,.0f}")
print(f"  {'ML Rent Estimate (monthly)':<35} ₹{ml_rent:>18,.0f}   ₹{user_rent:>18,.0f}")
print(f"  {'Market-Adj Price (base for ROI)':<35} ₹{blend_price:>18,.0f}   ₹{user_price:>18,.0f}  ✓ exact (no blend)")
print(f"  {'Market-Adj Rent (base for ROI)':<35} ₹{blend_rent:>18,.0f}   ₹{user_rent:>18,.0f}  (blend within ±50%)")
print(f"  {'Future Price (Year 5)':<35} ₹{future_price_yr5:>18,.0f}   ₹{future_price_yr5_correct:>18,.0f}")
print(f"  {'Total Rent Earned (5 yr)':<35} ₹{total_rent_yr5:>18,.0f}   ₹{total_rent_yr5_correct:>18,.0f}")
print(f"  {'5-Year ROI':<35} {roi:>18.2f}%   {roi_correct:>18.2f}%")
print()
