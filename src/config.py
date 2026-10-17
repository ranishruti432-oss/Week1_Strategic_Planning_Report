"""Central configuration: paths, random seed, scenario constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUT_DIR = ROOT / "outputs"
FIG_DIR = OUT_DIR / "figures"

for _d in (RAW_DIR, PROCESSED_DIR, OUT_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SEED = 42
START_DATE = "2023-01-01"
END_DATE = "2024-12-31"
FORECAST_HOLDOUT_DAYS = 60

# Scenario: "EastLink Distribution" - regional FMCG / pharma distributor, Eastern India.
# name, lat, lon, daily capacity (units)
WAREHOUSES = {
    "WH_KOL": ("Kolkata (Dankuni)", 22.68, 88.29, 900),
    "WH_HAL": ("Haldia", 22.06, 88.07, 550),
    "WH_DGP": ("Durgapur", 23.55, 87.32, 700),
}

# Approximate coordinates (lat, lon) of delivery towns
CUSTOMER_TOWNS = {
    "Kolkata": (22.57, 88.36), "Howrah": (22.59, 88.31), "Barasat": (22.72, 88.48),
    "Kalyani": (22.98, 88.43), "Chinsurah": (22.90, 88.40), "Ranaghat": (23.18, 88.57),
    "Krishnanagar": (23.40, 88.50), "Basirhat": (22.66, 88.87), "Uluberia": (22.47, 88.10),
    "Diamond Harbour": (22.19, 88.19), "Tamluk": (22.30, 87.92), "Contai": (21.78, 87.75),
    "Digha": (21.63, 87.55), "Ghatal": (22.67, 87.72), "Arambagh": (22.88, 87.79),
    "Bardhaman": (23.23, 87.86), "Bolpur": (23.67, 87.72), "Suri": (23.91, 87.53),
    "Bankura": (23.23, 87.07), "Asansol": (23.68, 86.98), "Dhanbad": (23.80, 86.43),
    "Purulia": (23.33, 86.36), "Jhargram": (22.45, 86.99), "Midnapore": (22.42, 87.32),
    "Kharagpur": (22.35, 87.32), "Jamshedpur": (22.80, 86.20), "Ranchi": (23.34, 85.31),
    "Balasore": (21.49, 86.93), "Bhadrak": (21.06, 86.52), "Cuttack": (20.46, 85.88),
    "Bhubaneswar": (20.30, 85.82), "Berhampore": (24.10, 88.25), "Malda": (25.00, 88.14),
    "Raiganj": (25.62, 88.13), "Balurghat": (25.22, 88.77), "Jalpaiguri": (26.52, 88.72),
    "Siliguri": (26.72, 88.43), "Cooch Behar": (26.32, 89.45), "Durgapur": (23.52, 87.31),
    "Haldia": (22.03, 88.06),
}

# capacity (kg), cost per km (INR)
VEHICLES = {"Tata_Ace": (750, 14), "Eicher_Pro": (3000, 22), "Truck_10T": (9000, 34)}
