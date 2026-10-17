"""Stage 4b - Inventory policy simulation (links forecasting to the fill-rate KPI).

Order-up-to policy with daily review and a fixed replenishment lead time.
  baseline : static rule-of-thumb  S = 1.15 * avg_demand(last 90 d) * (L+1)
  proposed : forecast-driven       S = sum(forecast over L+1 days) + z*sigma*sqrt(L+1)
"""
import numpy as np
import pandas as pd


def simulate(actual: pd.Series, order_up_to, lead_time=2):
    """actual: demand per day. order_up_to: callable(t)->S. Returns (fill_rate, avg_on_hand)."""
    n = len(actual)
    on_hand = order_up_to(0)
    pipeline = np.zeros(n + lead_time + 1)
    served = lost = 0.0
    stock_trace = []
    for t in range(n):
        on_hand += pipeline[t]
        d = actual.iloc[t]
        sold = min(on_hand, d)
        served, lost, on_hand = served + sold, lost + (d - sold), on_hand - sold
        position = on_hand + pipeline[t + 1: t + lead_time + 1].sum()
        order = max(order_up_to(t) - position, 0)
        pipeline[t + lead_time] += order
        stock_trace.append(on_hand)
    return served / (served + lost), float(np.mean(stock_trace))


def compare(actual, pred, history_mean, resid_std, lead_time=2, z=1.65):
    L1 = lead_time + 1
    base_S = 1.15 * history_mean * L1
    base = simulate(actual, lambda t: base_S, lead_time)
    pv = pred.values

    def prop_S(t):
        window = pv[t + 1: t + 1 + L1]
        window = window if len(window) == L1 else np.r_[window, np.repeat(pv[-1], L1 - len(window))]
        return window.sum() + z * resid_std * np.sqrt(L1)

    prop = simulate(actual, prop_S, lead_time)
    return {"baseline_fill_rate": base[0], "baseline_avg_stock": base[1],
            "forecast_fill_rate": prop[0], "forecast_avg_stock": prop[1]}
