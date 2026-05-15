# 🏠 Real Estate ROI Prediction System

## Project Structure

```
realestate/
├── datasets/                          # Raw data files
│   ├── House Price India.csv
│   ├── House_Rent_Dataset.csv
│   ├── Hyderabad.csv
│   ├── Hyderbad_House_price.csv
│   ├── properties.csv
│   └── unified_dataset.csv            # Generated after training
│
├── training/                          # ML pipeline scripts
│   ├── data_preparation.py            # Load + merge + clean all datasets
│   ├── feature_engineering.py         # Derived features + encoding helpers
│   ├── model_training.py              # Train RF / GB / XGBoost, select best
│   ├── roi_predictor.py               # ROI calc + 5-year forecast
│   └── train.py                       # 🚀 Main training entrypoint
│
├── models/                            # Saved artefacts (after training)
│   ├── best_price_model.joblib
│   ├── best_rent_model.joblib
│   ├── encoders.joblib
│   ├── model_meta.joblib
│   ├── model_meta.json
│   ├── model_comparison.png
│   └── forecast_chart.png
│
├── backend/                           # FastAPI application
│   ├── main.py                        # FastAPI app + /predict_roi endpoint
│   └── schemas.py                     # Pydantic request / response models
│
├── Real_Estate_ROI_Prediction.ipynb   # End-to-end analysis notebook
├── requirements.txt
└── README.md
```

---

## ROI Formula

$$ROI(\%) = \frac{(FuturePropertyPrice + TotalRentEarned - PurchasePrice)}{PurchasePrice} \times 100$$

**Growth assumptions:**
| Parameter            | Value          |
|----------------------|----------------|
| Property price growth | 6% per year   |
| Rent growth          | 9% per year (8–10% range) |
| Forecast horizon     | 5 years        |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the training pipeline

```bash
cd c:\Users\91871\Downloads\realestate
python training/train.py
```

This will:
- Merge and clean all 5 datasets
- Train RandomForest, GradientBoosting, and XGBoost models
- Save the best price + rent models to `models/`
- Save encoders and metadata

### 3. Start the FastAPI server

```bash
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive Swagger UI.

### 4. Call the API

```bash
curl -X POST http://localhost:8000/predict_roi \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Banjara Hills, Hyderabad",
    "property_type": "apartment",
    "bhk": 3,
    "area": 1500,
    "price": 8500000,
    "rent": 25000,
    "property_age": 5,
    "floor": 3,
    "furnishing": "semi-furnished"
  }'
```

**Sample response:**
```json
{
  "status": "success",
  "input_summary": { "purchase_price": 8500000, "monthly_rent": 25000, ... },
  "ml_estimates": { "predicted_price": 8600000, "predicted_rent": 24500 },
  "five_year_summary": {
    "future_property_price": 11382558.0,
    "total_rent_earned": 1771793.0,
    "roi_pct": 55.93,
    "investment_rating": "Very Good"
  },
  "yearly_forecast": [
    { "year": 1, "property_price": 9265000.0, "monthly_rent": 27250.0, "roi_pct": 17.96, ... },
    ...
  ]
}
```

---

## Models Trained

| Model | Target | Purpose |
|-------|--------|---------|
| RandomForestRegressor | Price | Predict market-adjusted property price |
| GradientBoostingRegressor | Price | Alternative price estimator |
| XGBoostRegressor | Price | XGBoost-based price estimator |
| RandomForestRegressor | Rent | Predict monthly rent |
| GradientBoostingRegressor | Rent | Alternative rent estimator |
| XGBoostRegressor | Rent | XGBoost-based rent estimator |

The best model per target (highest R²) is automatically selected and saved.

---

## Input Features

| Feature | Type | Description |
|---------|------|-------------|
| `location` | str | Area / locality name |
| `property_type` | str | `apartment`, `house`, `villa`, `plot` |
| `bhk` | int | Number of bedrooms |
| `area` | float | Area in sq ft |
| `price` | float | Purchase price (₹) |
| `rent` | float | Monthly rent (₹) |
| `property_age` | float | Age of property in years |
| `floor` | int | Floor number |
| `furnishing` | str | `furnished`, `semi-furnished`, `unfurnished` |

---

## Investment Rating Legend

| ROI (5-year) | Rating |
|---|---|
| ≥ 80% | Excellent |
| ≥ 50% | Very Good |
| ≥ 30% | Good |
| ≥ 10% | Average |
| < 10%  | Below Average |
