
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# Reproducible synthetic data
random_generator = random.Random(42)

# Generate 180 days ending October 22, 2026
end_date = date(2026, 10, 22)
start_date = end_date - timedelta(days=179)

project_root = Path(__file__).resolve().parents[1]
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

output_file = data_dir / "synthetic_black_tea_usage.csv"

records = []

for day_index in range(180):
    current_date = start_date + timedelta(days=day_index)

    # Base daily consumption
    base_usage = 0.35

    # Simulated long-term trend
    trend = day_index * 0.0005

    # Simulated weekend demand
    weekend_effect = (
        0.12 if current_date.weekday() >= 5 else 0
    )

    # Random variation
    noise = random_generator.uniform(-0.08, 0.08)

    # Calculate synthetic daily usage
    quantity_used = max(
        0,
        round(
            base_usage + trend + weekend_effect + noise,
            2
        )
    )

    records.append({
        "usage_date": current_date.isoformat(),
        "sku": "BLKTEA",
        "quantity_used": quantity_used
    })

with output_file.open("w", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "usage_date",
            "sku",
            "quantity_used"
        ]
    )

    writer.writeheader()
    writer.writerows(records)

print("Generated:", len(records), "days")
print("Saved to:", output_file)
print("First record:", records[0])
print("Last record:", records[-1])
