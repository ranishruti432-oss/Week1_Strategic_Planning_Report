"""Smoke tests: run with  pytest -q"""
import numpy as np
import pandas as pd
from src import generate_data, data_cleaning, optimization as opt


def test_cleaning_removes_problems():
    wh, cust = generate_data.make_master()
    ship = generate_data.make_shipments(wh, cust, n=2000)
    clean, audit = data_cleaning.clean_shipments(ship)
    assert clean.shipment_id.is_unique
    assert clean.isna().sum().sum() == 0
    assert set(clean.vehicle_type) <= {"Tata_Ace", "Eicher_Pro", "Truck_10T"}


def test_allocation_respects_capacity_and_demand():
    wh, cust = generate_data.make_master()
    dem = pd.Series(np.full(len(cust), 30.0), index=cust.customer_id)
    out = opt.allocate(cust, wh, dem)
    x = out["assignment"]
    assert np.allclose(x.sum(axis=1), 30.0)
    assert (x.sum(axis=0).values <= wh.daily_capacity.values + 1e-6).all()


def test_routing_beats_direct_trips():
    pts = np.array([[22.9, 88.4], [23.2, 88.5], [23.4, 88.5], [22.7, 88.5]])
    routes, opt_km, direct_km, nn_km, nv, nc = opt.plan_routes((22.68, 88.29), pts, np.full(4, 500.0))
    assert opt_km < direct_km and sorted(i for r in routes for i in r) == [1, 2, 3, 4]
