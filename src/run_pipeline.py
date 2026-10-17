"""End-to-end pipeline:  python -m src.generate_data && python -m src.run_pipeline"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import FIG_DIR, OUT_DIR, SEED
from . import data_cleaning, models, inventory, optimization as opt

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 9})
BLUE, ORANGE, GREEN, GREY = "#1F4E79", "#E07B39", "#2E8B57", "#888888"


def main():
    res = {}
    # ---------------- Stage 2: cleaning
    clean, demand, cust, wh, audit = data_cleaning.run()
    res["cleaning_audit"] = audit

    # ---------------- Stage 3: KPIs / EDA
    clean["year_month"] = clean["date"].dt.to_period("M").astype(str)
    res["kpi_baseline"] = {
        "on_time_delivery_pct": round(100 * (1 - clean.late.mean()), 1),
        "avg_delay_hours": round(clean.delay_hours.mean(), 2),
        "cost_per_km_inr": round(clean.cost_inr.sum() / clean.distance_km.sum(), 1),
        "cost_per_tonne_km_inr": round(clean.cost_inr.sum() / (clean.weight_kg / 1000 * clean.distance_km).sum(), 1),
        "otd_dry_pct": round(100 * (1 - clean[clean.rain_flag == 0].late.mean()), 1),
        "otd_rain_pct": round(100 * (1 - clean[clean.rain_flag == 1].late.mean()), 1),
    }
    m = clean.groupby("year_month").agg(otd=("late", lambda x: 100 * (1 - x.mean())), rain=("rain_flag", "mean"))
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(m.index, m.otd, color=BLUE, marker="o", ms=3, label="On-time delivery %")
    ax.set_ylabel("OTD (%)"); ax.set_xticks(range(0, len(m), 2)); ax.set_xticklabels(m.index[::2], rotation=45, ha="right")
    ax2 = ax.twinx(); ax2.bar(m.index, 100 * m.rain, alpha=.2, color=ORANGE, label="Rain share %")
    ax2.set_ylabel("Shipments in rain (%)"); ax2.spines["top"].set_visible(False)
    ax.set_title("Monthly on-time delivery vs rain exposure"); fig.tight_layout()
    fig.savefig(FIG_DIR / "01_otd_vs_rain.png"); plt.close(fig)

    # ---------------- Stage 4a: delay models
    dm, imp, _ = models.delay_models(clean)
    res["delay_models"] = {k: round(float(v), 3) for k, v in dm.items()}
    fig, ax = plt.subplots(figsize=(6, 3.2))
    imp.head(6)[::-1].plot.barh(ax=ax, color=BLUE)
    ax.set_title("Permutation importance - delay model (gradient boosting)"); ax.set_xlabel("Mean drop in R²")
    fig.tight_layout(); fig.savefig(FIG_DIR / "02_delay_feature_importance.png"); plt.close(fig)

    # ---------------- Stage 4b: customer clustering
    seg, scores, k, Z = models.customer_segments(clean, demand, cust)
    prof = seg.groupby("cluster").agg(customers=("town", "size"), mean_demand=("mean_demand", "mean"),
                                      avg_distance_km=("avg_distance_km", "mean"),
                                      late_rate=("late_rate", "mean")).round(2)
    res["clustering"] = {"best_k": int(k), "silhouette": {int(a): round(b, 3) for a, b in scores.items()},
                         "profiles": prof.reset_index().to_dict("records")}
    from sklearn.decomposition import PCA
    P = PCA(2, random_state=SEED).fit_transform(Z)
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    for c_, col in zip(range(k), [BLUE, ORANGE, GREEN, GREY, "#8E44AD", "#C0392B"]):
        mk = seg["cluster"].values == c_
        ax.scatter(P[mk, 0], P[mk, 1], s=35, color=col, label=f"Cluster {c_}")
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2"); ax.legend(frameon=False); ax.set_title(f"Customer segments (K-Means, k={k})")
    fig.tight_layout(); fig.savefig(FIG_DIR / "03_customer_clusters.png"); plt.close(fig)
    seg.to_csv(OUT_DIR / "customer_segments.csv")

    # ---------------- Stage 4c: demand forecast + inventory simulation
    D = opt.dist_matrix(cust.lat, cust.lon, wh.lat, wh.lon)
    nearest = pd.Series(D.argmin(1), index=cust.customer_id).map(dict(enumerate(wh.warehouse_id)))
    demand["wh"] = demand.customer_id.map(nearest)
    fc_res, inv_res = {}, {}
    for wid, g in demand.groupby("wh"):
        s = g.groupby("date")["demand_units"].sum()
        r = models.forecast_series(s)
        fc_res[wid] = {"WAPE_model_%": round(100 * r["wape_model"], 2), "WAPE_seasonal_naive_%": round(100 * r["wape_naive"], 2)}
        train_mean = s.iloc[:-60].mean()
        inv_res[wid] = {k_: round(float(v), 3) for k_, v in
                        inventory.compare(r["actual"], r["pred"], train_mean, r["resid_std"]).items()}
    tot = demand.groupby("date")["demand_units"].sum()
    rt = models.forecast_series(tot)
    res["forecast"] = {"per_warehouse": fc_res, "network_WAPE_model_%": round(100 * rt["wape_model"], 2),
                       "network_WAPE_naive_%": round(100 * rt["wape_naive"], 2)}
    res["inventory_sim"] = inv_res
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot(rt["actual"].index, rt["actual"], color=BLUE, label="Actual")
    ax.plot(rt["pred"].index, rt["pred"], color=ORANGE, label="Model forecast")
    ax.plot(rt["naive"].index, rt["naive"], color=GREY, ls="--", lw=1, label="Seasonal naive (t-7)")
    ax.set_title("Network daily demand: 60-day hold-out forecast"); ax.set_ylabel("Units"); ax.legend(frameon=False)
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(FIG_DIR / "04_demand_forecast.png"); plt.close(fig)

    # ---------------- Stage 4d: optimisation
    dem_avg = (demand[demand.date >= "2024-01-01"].groupby("customer_id")["demand_units"].mean()
               .reindex(cust.customer_id))
    mix = clean.groupby(["customer_id", "warehouse_id"]).size().unstack(fill_value=0)
    mix = mix.div(mix.sum(axis=1), axis=0)
    al = opt.allocate(cust, wh, dem_avg, mix)
    res["allocation"] = {"current_avg_km_per_unit": round(al["current_avg_km_per_unit"], 1),
                         "optimised_avg_km_per_unit": round(al["optimised_avg_km_per_unit"], 1),
                         "km_reduction_pct": round(100 * (1 - al["optimised_avg_km_per_unit"] / al["current_avg_km_per_unit"]), 1),
                         "warehouse_load_units": {k_: float(v) for k_, v in al["warehouse_load_units"].items()},
                         "capacity": dict(zip(wh.warehouse_id, map(int, wh.daily_capacity)))}

    # routing for the busiest warehouse under the LP plan (customers with >50% share)
    A = al["assignment"]
    routing, route_store = {}, {}
    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    colors = plt.cm.tab20(np.linspace(0, 1, 20))
    ci = 0
    for j, w in enumerate(wh.itertuples()):
        ids = A.index[A[w.warehouse_id] > 1e-6]
        sub = cust.set_index("customer_id").loc[ids]
        load_kg = (A.loc[ids, w.warehouse_id].values * 15).round(0)  # 15 kg / unit
        routes, o_km, d_km, nn_km, nv, nc = opt.plan_routes((w.lat, w.lon), sub[["lat", "lon"]].values, load_kg)
        routing[w.warehouse_id] = {"customers": nc, "vehicles_needed": nv,
                                   "direct_km": round(d_km), "nearest_neighbour_km": round(nn_km),
                                   "optimised_km": round(o_km),
                                   "km_saved_vs_direct_pct": round(100 * (1 - o_km / d_km), 1),
                                   "km_saved_vs_nn_pct": round(100 * (1 - o_km / nn_km), 1)}
        for r in routes:
            pts = [(w.lat, w.lon)] + [tuple(sub.iloc[i - 1][["lat", "lon"]]) for i in r] + [(w.lat, w.lon)]
            ax.plot([p[1] for p in pts], [p[0] for p in pts], color=colors[ci % 20], lw=1.4, alpha=.9)
            ci += 1
        ax.scatter(w.lon, w.lat, marker="s", s=90, color="black", zorder=5)
        ax.annotate(w.name.split(" ")[0], (w.lon, w.lat), xytext=(4, 4), textcoords="offset points", fontsize=8, weight="bold")
    ax.scatter(cust.lon, cust.lat, s=10, color=GREY, zorder=4)
    ax.set_title("Optimised delivery routes (Clarke-Wright + 2-opt)"); ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    fig.tight_layout(); fig.savefig(FIG_DIR / "05_optimised_routes.png"); plt.close(fig)
    res["routing"] = routing
    tot_direct = sum(v["direct_km"] for v in routing.values())
    tot_nn = sum(v["nearest_neighbour_km"] for v in routing.values())
    tot_opt = sum(v["optimised_km"] for v in routing.values())
    res["routing_total"] = {"direct_km": tot_direct, "nearest_neighbour_km": tot_nn, "optimised_km": tot_opt,
                            "km_saved_vs_direct_pct": round(100 * (1 - tot_opt / tot_direct), 1),
                            "km_saved_vs_nn_pct": round(100 * (1 - tot_opt / tot_nn), 1),
                            "daily_saving_vs_nn_inr": round((tot_nn - tot_opt) * 28)}  # ~INR 28/km, 5-t truck

    with open(OUT_DIR / "metrics.json", "w") as f:
        json.dump(res, f, indent=2, default=float)
    print(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    main()
