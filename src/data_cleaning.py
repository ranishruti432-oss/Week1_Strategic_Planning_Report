"""Stage 2 - Data cleaning & feature engineering."""
import numpy as np
import pandas as pd
from .config import RAW_DIR, PROCESSED_DIR

LATE_TOLERANCE_H = 0.5  # a delivery is "on time" if it arrives within 30 min of plan


def load_raw():
    ship = pd.read_csv(RAW_DIR / "shipments.csv", parse_dates=["date"])
    demand = pd.read_csv(RAW_DIR / "daily_demand.csv", parse_dates=["date"])
    cust = pd.read_csv(RAW_DIR / "customers.csv")
    wh = pd.read_csv(RAW_DIR / "warehouses.csv")
    return ship, demand, cust, wh


def clean_shipments(ship: pd.DataFrame):
    """Return (clean_df, audit_dict). Every step is logged for the audit trail."""
    audit = {"rows_raw": len(ship)}
    df = ship.drop_duplicates(subset="shipment_id").copy()
    audit["duplicates_removed"] = audit["rows_raw"] - len(df)

    # Standardise labels, e.g. "tata ace " -> "Tata_Ace"
    vehicle_map = {"tata_ace": "Tata_Ace", "eicher_pro": "Eicher_Pro", "truck_10t": "Truck_10T"}
    df["vehicle_type"] = df["vehicle_type"].str.strip().str.lower().str.replace(" ", "_").map(vehicle_map)
    audit["missing_before"] = df[["traffic_index", "weight_kg"]].isna().sum().to_dict()

    # Impute: weight by vehicle-type median, traffic by warehouse median
    df["weight_kg"] = df["weight_kg"].fillna(df.groupby("vehicle_type")["weight_kg"].transform("median"))
    df["traffic_index"] = df["traffic_index"].fillna(df.groupby("warehouse_id")["traffic_index"].transform("median"))

    # Outliers: actual duration > 4x planned is treated as a recording error
    ratio = df["actual_hours"] / df["planned_hours"]
    mask = ratio > 4
    audit["outliers_removed"] = int(mask.sum())
    df = df[~mask].copy()

    # Feature engineering
    df["delay_hours"] = df["actual_hours"] - df["planned_hours"]
    df["late"] = (df["delay_hours"] > LATE_TOLERANCE_H).astype(int)
    df["month"] = df["date"].dt.month
    df["dow"] = df["date"].dt.dayofweek
    df["cost_per_km"] = df["cost_inr"] / df["distance_km"]
    df["cost_per_tonne_km"] = df["cost_inr"] / (df["weight_kg"] / 1000 * df["distance_km"])
    audit["rows_clean"] = len(df)
    audit["remaining_nulls"] = int(df.isna().sum().sum())
    return df.reset_index(drop=True), audit


def run():
    ship, demand, cust, wh = load_raw()
    clean, audit = clean_shipments(ship)
    clean.to_csv(PROCESSED_DIR / "shipments_clean.csv", index=False)
    return clean, demand, cust, wh, audit


if __name__ == "__main__":
    print(run()[-1])
