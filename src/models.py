"""Stage 4 - Predictive & descriptive models.

1. Delay regression + late-risk classifier  (shipment level)
2. K-Means customer segmentation             (customer level)
3. Demand forecasting vs seasonal-naive      (warehouse level, 7-day horizon)
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (mean_absolute_error, r2_score, roc_auc_score, silhouette_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .config import SEED, FORECAST_HOLDOUT_DAYS

NUM = ["distance_km", "weight_kg", "rain_flag", "traffic_index", "driver_experience_yrs",
       "planned_hours", "month", "dow"]
CAT = ["vehicle_type", "warehouse_id"]


# ----------------------------------------------------------------- 1. delay
def delay_models(df):
    X, y_reg, y_clf = df[NUM + CAT], df["delay_hours"], df["late"]
    Xtr, Xte, ytr, yte, ctr, cte = train_test_split(X, y_reg, y_clf, test_size=0.2, random_state=SEED)

    pre = ColumnTransformer([("num", StandardScaler(), NUM),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
    lin = Pipeline([("pre", pre), ("m", LinearRegression())]).fit(Xtr, ytr)
    gbr = Pipeline([("pre", pre), ("m", HistGradientBoostingRegressor(max_iter=250, learning_rate=0.06,
                                                                       random_state=SEED))]).fit(Xtr, ytr)
    clf = Pipeline([("pre", pre), ("m", HistGradientBoostingClassifier(max_iter=250, learning_rate=0.06,
                                                                        random_state=SEED))]).fit(Xtr, ctr)
    metrics = {
        "linear_MAE_h": mean_absolute_error(yte, lin.predict(Xte)),
        "linear_R2": r2_score(yte, lin.predict(Xte)),
        "gbm_MAE_h": mean_absolute_error(yte, gbr.predict(Xte)),
        "gbm_R2": r2_score(yte, gbr.predict(Xte)),
        "baseline_MAE_h(predict mean)": mean_absolute_error(yte, np.full(len(yte), ytr.mean())),
        "late_risk_AUC": roc_auc_score(cte, clf.predict_proba(Xte)[:, 1]),
        "late_rate_test": float(cte.mean()),
    }
    sample = Xte.sample(2000, random_state=SEED)
    imp = permutation_importance(gbr, sample, yte.loc[sample.index], n_repeats=5, random_state=SEED)
    importance = pd.Series(imp.importances_mean, index=NUM + CAT).sort_values(ascending=False)
    return metrics, importance, clf


# ------------------------------------------------------------- 2. clustering
def customer_segments(df, demand, cust, k_range=range(2, 8)):
    d = demand.groupby("customer_id")["demand_units"].agg(mean_demand="mean", std="std")
    d["demand_cv"] = d["std"] / d["mean_demand"]
    s = df.groupby("customer_id").agg(avg_distance_km=("distance_km", "mean"),
                                      late_rate=("late", "mean"),
                                      avg_cost_per_km=("cost_per_km", "mean"))
    feat = d[["mean_demand", "demand_cv"]].join(s).dropna()
    Z = StandardScaler().fit_transform(feat)
    scores = {k: silhouette_score(Z, KMeans(k, n_init=10, random_state=SEED).fit_predict(Z)) for k in k_range}
    best_k = max(scores, key=scores.get)
    km = KMeans(best_k, n_init=10, random_state=SEED).fit(Z)
    feat["cluster"] = km.labels_
    feat = feat.join(cust.set_index("customer_id")[["town", "lat", "lon", "segment"]])
    return feat, scores, best_k, Z


# --------------------------------------------------------------- 3. forecast
def _features(s: pd.Series) -> pd.DataFrame:
    """Lags >= 7 so that a forecast up to 7 days ahead never uses unseen data."""
    f = pd.DataFrame({"y": s})
    for lag in (7, 14, 21, 28):
        f[f"lag_{lag}"] = s.shift(lag)
    f["roll7"] = s.shift(7).rolling(7).mean()
    f["roll28"] = s.shift(7).rolling(28).mean()
    idx = s.index
    f["dow"], f["month"], f["doy"] = idx.dayofweek, idx.month, idx.dayofyear
    f["festival"] = (((idx.month == 10) | ((idx.month == 11) & (idx.day <= 15)))).astype(int)
    return f.dropna()


def forecast_series(s: pd.Series):
    f = _features(s)
    train, test = f.iloc[:-FORECAST_HOLDOUT_DAYS], f.iloc[-FORECAST_HOLDOUT_DAYS:]
    cols = [c for c in f.columns if c != "y"]
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=SEED)
    m.fit(train[cols], train["y"])
    pred = pd.Series(m.predict(test[cols]), index=test.index)
    naive = test["lag_7"]
    resid = train["y"] - m.predict(train[cols])
    wape = lambda a, p: float(np.abs(a - p).sum() / a.sum())
    return {"actual": test["y"], "pred": pred, "naive": naive,
            "wape_model": wape(test["y"], pred), "wape_naive": wape(test["y"], naive),
            "resid_std": float(resid.std())}
