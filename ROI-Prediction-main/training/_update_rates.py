"""Standalone script: recompute granular growth rates and update model_meta.json."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from data_preparation import build_unified_dataset, compute_growth_rates

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
META_PATH  = os.path.join(MODELS_DIR, "model_meta.json")

print("Building unified dataset …")
df = build_unified_dataset()

print("\nComputing granular growth rates …")
rates = compute_growth_rates(df)

# Merge into existing model_meta.json (keep model R² / names)
with open(META_PATH) as f:
    meta = json.load(f)

meta.update(rates)

with open(META_PATH, "w") as f:
    json.dump(meta, f, indent=2)

n_cities = len(rates["city_rates"])
n_locs   = len(rates["location_rates"])
print(f"\n✓ Saved model_meta.json — {n_cities} cities, {n_locs} locations")
print("\nCity rates:")
for city, cr in rates["city_rates"].items():
    print(f"  {city:20s}  price={cr['price_growth_rate']*100:.2f}%  rent={cr['rent_growth_rate']*100:.2f}%")
print("\nSample locations:")
for loc, lr in list(rates["location_rates"].items())[:10]:
    print(f"  {loc:30s}  price={lr['price_growth_rate']*100:.2f}%  rent={lr['rent_growth_rate']*100:.2f}%")
print("\nProperty-type adjustments:")
for pt, adj in rates["property_type_adj"].items():
    print(f"  {pt:25s}  price_delta={adj['price_growth_delta']*100:+.2f}%  rent_delta={adj['rent_growth_delta']*100:+.2f}%")
