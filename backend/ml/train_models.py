from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
FEATURES = ["property_price", "rental_yield", "demand_index", "market_trend"]


def build_dataset(n: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)

    data = pd.DataFrame(
        {
            "property_price": rng.uniform(75_000, 2_500_000, n),
            "rental_yield": rng.uniform(2.5, 12.0, n),
            "demand_index": rng.uniform(0.1, 1.0, n),
            "market_trend": rng.uniform(0.1, 1.0, n),
        }
    )

    data["roi"] = (
        0.0000015 * data["property_price"] * 0.15
        + data["rental_yield"] * 0.8
        + data["demand_index"] * 8.5
        + data["market_trend"] * 6.5
        + rng.normal(0, 1.2, n)
    )

    conditions = [data["roi"] > 14, data["roi"] > 9]
    choices = [0, 1]
    data["risk_class"] = np.select(conditions, choices, default=2)

    return data


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    df = build_dataset()

    x = df[FEATURES]
    y_roi = df["roi"]
    y_risk = df["risk_class"]

    x_train, x_test, y_roi_train, y_roi_test, y_risk_train, y_risk_test = train_test_split(
        x, y_roi, y_risk, test_size=0.2, random_state=42
    )

    roi_model = RandomForestRegressor(n_estimators=200, random_state=42)
    roi_model.fit(x_train, y_roi_train)

    risk_model = RandomForestClassifier(n_estimators=200, random_state=42)
    risk_model.fit(x_train, y_risk_train)

    joblib.dump(roi_model, ARTIFACTS_DIR / "roi_model.joblib")
    joblib.dump(risk_model, ARTIFACTS_DIR / "risk_model.joblib")
    joblib.dump(FEATURES, ARTIFACTS_DIR / "features.joblib")

    print("Models saved to", ARTIFACTS_DIR)
    print("ROI score:", roi_model.score(x_test, y_roi_test))
    print("Risk score:", risk_model.score(x_test, y_risk_test))


if __name__ == "__main__":
    main()
