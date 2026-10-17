"""Create a reproducible synthetic dataset for EastLink Distribution.

Real company logistics data is confidential, so the generator is calibrated to
published patterns (monsoon delays, festival demand peaks, road-dominated freight).
Replace the CSVs in data/raw/ with real data (same schema) and the rest of the
pipeline works unchanged.
"""
import numpy as np
import pandas as pd
from .config import *

rng = np.random.default_rng(SEED)


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def make_master():
    wh = pd.DataFrame([(k, v[0], v[1], v[2], v[3]) for k, v in WAREHOUSES.items()],
                      columns=["warehouse_id", "name", "lat", "lon", "daily_capacity"])
    towns = list(CUSTOMER_TOWNS.items())
    segs = rng.choice(["Grocery", "Pharmacy", "Modern_Trade", "E-commerce"], len(towns),
                      p=[0.35, 0.25, 0.2, 0.2])
    cust = pd.DataFrame({
        "customer_id": [f"C{i:03d}" for i in range(len(towns))],
        "town": [t[0] for t in towns],
        "lat": [t[1][0] for t in towns], "lon": [t[1][1] for t in towns],
        "segment": segs,
        "base_daily_demand": rng.lognormal(mean=3.6, sigma=0.55, size=len(towns)).round(1),
    })
    return wh, cust


def make_daily_demand(cust):
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    n = len(dates)
    trend = 1 + 0.12 * np.arange(n) / n
    dow = np.array([1.00, 1.03, 1.02, 1.04, 1.10, 1.18, 0.85])[dates.dayofweek]
    festival = np.ones(n)
    for y in (2023, 2024):  # Durga Puja/Diwali window, Poila Baisakh (approx.)
        festival[(dates >= f"{y}-10-01") & (dates <= f"{y}-11-15")] *= 1.35
        festival[(dates >= f"{y}-04-10") & (dates <= f"{y}-04-20")] *= 1.12
    monsoon = np.where(dates.month.isin([6, 7, 8, 9]), 0.93, 1.0)
    rows = []
    for _, c in cust.iterrows():
        d = c.base_daily_demand * trend * dow * festival * monsoon * rng.lognormal(0, 0.18, n)
        rows.append(pd.DataFrame({"date": dates, "customer_id": c.customer_id,
                                  "demand_units": d.round(1)}))
    return pd.concat(rows, ignore_index=True)


def make_shipments(wh, cust, n=22000):
    dates = pd.to_datetime(rng.choice(pd.date_range(START_DATE, END_DATE), n))
    c = cust.sample(n, replace=True, random_state=SEED).reset_index(drop=True)
    dists = np.stack([haversine(c.lat, c.lon, w.lat, w.lon) for w in wh.itertuples()], axis=1)
    nearest = dists.argmin(1)
    # 80% dispatched from nearest warehouse; 20% mis-allocated (stock-outs, poor planning)
    choice = np.where(rng.random(n) < 0.8, nearest, rng.integers(0, len(wh), n))
    road_km = dists[np.arange(n), choice] * rng.uniform(1.22, 1.38, n)
    weight = rng.gamma(4, 260, n).clip(40, 9000)
    veh = np.where(weight < 700, "Tata_Ace", np.where(weight < 2800, "Eicher_Pro", "Truck_10T"))
    month = np.asarray(dates.month)
    rain = ((np.isin(month, [6, 7, 8, 9]) & (rng.random(n) < 0.55)) | (rng.random(n) < 0.06)).astype(int)
    traffic = np.clip(rng.normal(1.0, 0.18, n) + 0.12 * c.town.isin(["Kolkata", "Howrah"]).values, 0.6, 2.0)
    exp = rng.integers(0, 15, n)
    speed = (42 - 6 * rain - 7 * (traffic - 1) + 0.25 * exp + rng.normal(0, 2.5, n)).clip(18, 55)
    load_time = 0.6 + weight / 6000
    planned = road_km / 40 + load_time
    actual = road_km / speed + load_time + rng.exponential(0.25, n) + 1.0 * rain * (rng.random(n) < 0.15)
    cpk = np.array([VEHICLES[v][1] for v in veh])
    cost = road_km * cpk * (1 + 0.1 * rain) + 250
    df = pd.DataFrame({
        "shipment_id": [f"S{i:06d}" for i in range(n)], "date": dates,
        "warehouse_id": wh.warehouse_id.values[choice], "customer_id": c.customer_id,
        "distance_km": road_km.round(1), "weight_kg": weight.round(0), "vehicle_type": veh,
        "rain_flag": rain, "traffic_index": traffic.round(2), "driver_experience_yrs": exp,
        "planned_hours": planned.round(2), "actual_hours": actual.round(2), "cost_inr": cost.round(0),
    })
    # --- inject realistic data-quality problems for the cleaning stage ---
    df.loc[rng.choice(n, int(0.02 * n), replace=False), "traffic_index"] = np.nan
    df.loc[rng.choice(n, int(0.01 * n), replace=False), "weight_kg"] = np.nan
    df.loc[rng.choice(n, 40, replace=False), "actual_hours"] *= 8       # GPS / entry errors
    df = pd.concat([df, df.sample(60, random_state=SEED)], ignore_index=True)  # duplicates
    df.loc[rng.choice(len(df), 30, replace=False), "vehicle_type"] = "tata ace "  # label noise
    return df


def main():
    wh, cust = make_master()
    demand, ship = make_daily_demand(cust), make_shipments(wh, cust)
    wh.to_csv(RAW_DIR / "warehouses.csv", index=False)
    cust.to_csv(RAW_DIR / "customers.csv", index=False)
    demand.to_csv(RAW_DIR / "daily_demand.csv", index=False)
    ship.to_csv(RAW_DIR / "shipments.csv", index=False)
    print(f"warehouses={len(wh)} customers={len(cust)} demand_rows={len(demand)} shipments={len(ship)}")


if __name__ == "__main__":
    main()
