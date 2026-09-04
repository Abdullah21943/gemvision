"""Train the XGBoost gemstone price-regression model.

Corresponds to proposal Phase 3 / Objective 5: predict price from type,
carat, cut and clarity, using the Kaggle "gemstone-price-prediction" dataset.

The dataset is a diamonds-style pricing dataset and may not ship a
"gem_type" column (in which case every row is effectively the same gem
type). This script auto-detects common column-name variants and, if no
type column exists, falls back to a constant "Diamond" type so the API
contract (gem_type/carat/cut/clarity/color -> price) still holds. Check
the printed "Detected columns" line after your first run and adjust
COLUMN_ALIASES below if it guessed wrong for your downloaded CSV.

Usage:
    python ml/train_price_model.py

Output:
    backend/models/price_model.joblib
    backend/models/price_encoders.joblib
    ml/reports/price_model_metrics.txt
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data" / "gemstone-price-prediction"
BACKEND_MODELS_DIR = ML_DIR.parent / "backend" / "models"
REPORTS_DIR = ML_DIR / "reports"

# First matching alias (case-insensitive) in the CSV wins for each field.
COLUMN_ALIASES = {
    "gem_type": ["gem_type", "gemstone", "type", "stone", "species"],
    "carat": ["carat", "weight", "carat_weight"],
    "cut": ["cut", "cut_quality"],
    "clarity": ["clarity"],
    "color": ["color", "colour"],
    "price": ["price", "price_usd", "value"],
}


def _find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    return None


def load_dataset() -> pd.DataFrame:
    csv_files = list(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise SystemExit(
            f"No CSV found in {DATA_DIR}. Run `python ml/download_datasets.py` first."
        )
    df = pd.read_csv(csv_files[0])
    print(f"Loaded {csv_files[0].name}: {df.shape[0]} rows, columns={list(df.columns)}")
    return df


def main() -> None:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from xgboost import XGBRegressor

    df = load_dataset()

    resolved = {field: _find_column(df, aliases) for field, aliases in COLUMN_ALIASES.items()}
    print(f"Detected columns: {resolved}")

    for required in ("carat", "cut", "clarity", "price"):
        if resolved[required] is None:
            raise SystemExit(
                f"Could not find a '{required}' column in the dataset. "
                f"Available columns: {list(df.columns)}. "
                "Add the real column name to COLUMN_ALIASES in this script."
            )

    work = pd.DataFrame()
    work["carat"] = df[resolved["carat"]]
    work["cut"] = df[resolved["cut"]].astype(str)
    work["clarity"] = df[resolved["clarity"]].astype(str)
    work["color"] = df[resolved["color"]].astype(str) if resolved["color"] else "Unknown"
    work["gem_type"] = df[resolved["gem_type"]].astype(str) if resolved["gem_type"] else "Diamond"
    work["price"] = df[resolved["price"]]

    work = work.dropna()

    encoders: dict[str, LabelEncoder] = {}
    for col in ("gem_type", "cut", "clarity", "color"):
        encoder = LabelEncoder()
        work[col] = encoder.fit_transform(work[col])
        encoders[col] = encoder

    feature_cols = ["carat", "gem_type", "cut", "clarity", "color"]
    X = work[feature_cols]
    y = work["price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    metrics = f"RMSE={rmse:.2f}  MAE={mae:.2f}  R2={r2:.4f}"
    print(metrics)

    BACKEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    import joblib

    model_path = BACKEND_MODELS_DIR / "price_model.joblib"
    encoders_path = BACKEND_MODELS_DIR / "price_encoders.joblib"
    joblib.dump(model, model_path)
    joblib.dump(encoders, encoders_path)
    (REPORTS_DIR / "price_model_metrics.txt").write_text(metrics, encoding="utf-8")

    print(f"Saved model -> {model_path}")
    print(f"Saved encoders -> {encoders_path}")


if __name__ == "__main__":
    main()
