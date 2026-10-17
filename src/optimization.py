"""Stage 4c - Prescriptive analytics.

1. Warehouse->customer allocation as a capacitated transportation LP (scipy.linprog)
2. Vehicle routing (CVRP) with the Clarke-Wright savings heuristic + 2-opt improvement
"""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from .generate_data import haversine

ROAD_FACTOR = 1.3  # road distance ~ 1.3 x straight-line distance


def dist_matrix(a_lat, a_lon, b_lat, b_lon):
    return ROAD_FACTOR * haversine(np.asarray(a_lat)[:, None], np.asarray(a_lon)[:, None],
                                   np.asarray(b_lat)[None, :], np.asarray(b_lon)[None, :])


# ----------------------------------------------------------- 1. allocation LP
def allocate(cust, wh, demand_per_customer, observed_mix=None):
    D = dist_matrix(cust.lat, cust.lon, wh.lat, wh.lon)        # customers x warehouses
    nC, nW = D.shape
    c = D.flatten()                                            # cost = km per unit
    A_eq = np.zeros((nC, nC * nW))
    for i in range(nC):
        A_eq[i, i * nW:(i + 1) * nW] = 1
    A_ub = np.zeros((nW, nC * nW))
    for j in range(nW):
        A_ub[j, j::nW] = 1
    res = linprog(c, A_ub=A_ub, b_ub=wh.daily_capacity.values, A_eq=A_eq,
                  b_eq=demand_per_customer.values, bounds=(0, None), method="highs")
    x = res.x.reshape(nC, nW)
    opt_unit_km = float((x * D).sum() / x.sum())
    out = {"status": res.message, "optimised_avg_km_per_unit": opt_unit_km,
           "warehouse_load_units": dict(zip(wh.warehouse_id, x.sum(0).round(1))),
           "assignment": pd.DataFrame(x, index=cust.customer_id, columns=wh.warehouse_id)}
    if observed_mix is not None:     # share of each customer's volume actually dispatched from each WH
        w = observed_mix.reindex(index=cust.customer_id, columns=wh.warehouse_id).fillna(0).values
        out["current_avg_km_per_unit"] = float((w * demand_per_customer.values[:, None] * D).sum()
                                               / demand_per_customer.sum())
    return out


# --------------------------------------------------------------- 2. routing
def _route_len(route, d):
    pts = [0] + route + [0]
    return sum(d[pts[k], pts[k + 1]] for k in range(len(pts) - 1))


def savings_vrp(d, load, capacity, max_km=1200):
    """d: (n+1)x(n+1) distance matrix, node 0 = depot. load: array len n+1 (load[0]=0)."""
    n = len(load) - 1
    routes = {i: [i] for i in range(1, n + 1)}
    where = {i: i for i in range(1, n + 1)}
    sav = sorted(((d[0, i] + d[0, j] - d[i, j], i, j) for i in range(1, n + 1)
                  for j in range(i + 1, n + 1)), reverse=True)
    for s, i, j in sav:
        if s <= 0:
            break
        ri, rj = where[i], where[j]
        if ri == rj:
            continue
        a, b = routes[ri], routes[rj]
        if sum(load[a]) + sum(load[b]) > capacity:
            continue
        # i and j must be route endpoints
        if a[-1] == i and b[0] == j:   new = a + b
        elif a[0] == i and b[-1] == j: new = b + a
        elif a[-1] == i and b[-1] == j: new = a + b[::-1]
        elif a[0] == i and b[0] == j:  new = a[::-1] + b
        else:
            continue
        if _route_len(new, d) > max_km:
            continue
        routes[ri] = new
        del routes[rj]
        for node in new:
            where[node] = ri
    return list(routes.values())


def two_opt(route, d):
    best, improved = route[:], True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for k in range(i + 1, len(best)):
                cand = best[:i] + best[i:k + 1][::-1] + best[k + 1:]
                if _route_len(cand, d) < _route_len(best, d) - 1e-9:
                    best, improved = cand, True
    return best


def nearest_neighbour_vrp(d, load, capacity, max_km=1200):
    """Simple dispatcher-style baseline: always drive to the closest unserved customer."""
    unserved, routes = set(range(1, len(load))), []
    while unserved:
        route, cur, cap = [], 0, capacity
        while True:
            cands = [j for j in unserved if load[j] <= cap and _route_len(route + [j], d) <= max_km]
            if not cands:
                break
            nxt = min(cands, key=lambda j: d[cur, j])
            route.append(nxt); unserved.discard(nxt); cap -= load[nxt]; cur = nxt
        if not route:                       # single customer exceeds limits: serve alone
            j = unserved.pop(); route = [j]
        routes.append(route)
    return routes


def plan_routes(depot_xy, cust_xy, load_kg, capacity_kg=5000, max_km=1200):
    pts = np.vstack([depot_xy, cust_xy])
    d = dist_matrix(pts[:, 0], pts[:, 1], pts[:, 0], pts[:, 1])
    load = np.r_[0, load_kg]
    routes = [two_opt(r, d) for r in savings_vrp(d, load, capacity_kg, max_km)]
    optimised_km = sum(_route_len(r, d) for r in routes)
    direct_km = sum(2 * d[0, i] for i in range(1, len(load)))      # one dedicated trip per customer
    nn_km = sum(_route_len(r, d) for r in nearest_neighbour_vrp(d, load, capacity_kg, max_km))
    return routes, optimised_km, direct_km, nn_km, len(routes), len(load) - 1
