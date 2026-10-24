
import pandas as pd
from math import sqrt
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# 1. Load synthetic dataset
project_root = Path(__file__).resolve().parents[1]

file_path = (
    project_root / "data" / "synthetic_black_tea_usage.csv"
)

df = pd.read_csv(file_path)

df["usage_date"] = pd.to_datetime(df["usage_date"])

df = df.sort_values("usage_date").reset_index(drop=True)


# 2. Feature Engineering

# FIXED: Use day_of_week instead of deprecated dayofweek
df["day_of_week"] = df["usage_date"].dt.day_of_week

df["day_index"] = range(len(df))

df["lag_1"] = df["quantity_used"].shift(1)

df["lag_7"] = df["quantity_used"].shift(7)

df["moving_avg_7"] = (
    df["quantity_used"].shift(1).rolling(7).mean()
)

df["moving_avg_30"] = (
    df["quantity_used"].shift(1).rolling(30).mean()
)

# Remove rows without enough historical data
df = df.dropna().copy()


# 3. Select features and target
features = [
    "day_of_week",
    "day_index",
    "lag_1",
    "lag_7",
    "moving_avg_7",
    "moving_avg_30"
]

X = df[features]
y = df["quantity_used"]


# 4. Chronological Train/Test Split
# Last 30 days are reserved for testing
split_index = len(df) - 30

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


# 5. Train Random Forest Model
model = RandomForestRegressor(
    n_estimators=200,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)


# 6. Machine Learning Predictions
ml_predictions = model.predict(X_test)


# 7. Moving Average Baseline
baseline_predictions = df["moving_avg_7"].iloc[
    split_index:
]


# 8. Evaluate Both Models
def evaluate(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = sqrt(mean_squared_error(actual, predicted))

    return mae, rmse


ml_mae, ml_rmse = evaluate(
    y_test,
    ml_predictions
)

baseline_mae, baseline_rmse = evaluate(
    y_test,
    baseline_predictions
)


# 9. Display Results
print("\n===== SMARTOPS ML FORECAST EVALUATION =====")

print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))

print("\nMoving Average Baseline")
print(f"MAE:  {baseline_mae:.4f}")
print(f"RMSE: {baseline_rmse:.4f}")

print("\nRandom Forest Regression")
print(f"MAE:  {ml_mae:.4f}")
print(f"RMSE: {ml_rmse:.4f}")

print("\n===== FEATURE IMPORTANCE =====")

for feature, importance in sorted(
    zip(features, model.feature_importances_),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{feature}: {importance:.4f}")


# 10. Save evaluation results for SmartOps Dashboard
import json

predictions = []

test_dates = df["usage_date"].iloc[split_index:]

for date, actual, baseline, ml in zip(
    test_dates,
    y_test,
    baseline_predictions,
    ml_predictions
):
    predictions.append({
        "date": date.strftime("%Y-%m-%d"),
        "actual": float(actual),
        "moving_average": float(baseline),
        "random_forest": float(ml)
    })

evaluation_data = {
    "dataset": "Synthetic Black Tea Usage",
    "evaluation_type": "One-day-ahead backtest",
    "training_samples": len(X_train),
    "testing_samples": len(X_test),
    "metrics": {
        "moving_average": {
            "mae": float(baseline_mae),
            "rmse": float(baseline_rmse)
        },
        "random_forest": {
            "mae": float(ml_mae),
            "rmse": float(ml_rmse)
        }
    },
    "feature_importance": {
        feature: float(importance)
        for feature, importance in zip(
            features,
            model.feature_importances_
        )
    },
    "predictions": predictions
}

output_file = project_root / "data" / "ml_evaluation.json"

with output_file.open("w", encoding="utf-8") as file:
    json.dump(evaluation_data, file, indent=2)

print("\nSaved ML evaluation to:", output_file)
