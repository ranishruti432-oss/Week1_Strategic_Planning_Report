// Builds docs/Strategic_Planning_Report.docx from outputs/metrics.json + figures
const fs = require("fs");
const path = require("path");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel, AlignmentType,
  WidthType, ShadingType, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber, TableOfContents } = D;

const ROOT = path.resolve(__dirname, "..");
const M = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs/metrics.json"), "utf8"));
const fig = (n) => fs.readFileSync(path.join(ROOT, "outputs/figures", n));
const FONT = "Calibri", NAVY = "1F4E79";
const W = 9638; // content width (A4, 2 cm margins)

const p = (text, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, alignment: o.align, children: runs(text, o) });
function runs(text, o = {}) {
  // **bold** inline support
  return String(text).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(t =>
    t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, size: o.size || 22 })
      : new TextRun({ text: t, font: FONT, size: o.size || 22, italics: o.italics, color: o.color }));
}
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 140 }, children: [new TextRun({ text: t, font: FONT })] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 }, children: [new TextRun({ text: t, font: FONT })] });
const bullet = (t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 264 }, children: runs(t) });
const num = (t) => new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 60, line: 264 }, children: runs(t) });
const cap = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555", font: FONT })] });
const img = (name, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 60 },
  children: [new ImageRun({ type: "png", data: fig(name), transformation: { width: w, height: h }, altText: { title: name, description: name, name } })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(headers, rows, widths) {
  const cell = (t, w, head) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: head ? { fill: NAVY, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: String(t), bold: head, color: head ? "FFFFFF" : undefined, size: 19, font: FONT })] })],
  });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths, rows: [
    new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true)) }),
    ...rows.map(r => new TableRow({ children: r.map((c, i) => cell(c, widths[i], false)) })),
  ] });
}
function code(src) {
  return src.trim().split("\n").map((line, i, arr) => new Paragraph({
    spacing: { after: 0, line: 240 },
    shading: { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" },
    border: i === 0 ? { top: { style: BorderStyle.SINGLE, size: 4, color: "D9D9D9", space: 4 } } : (i === arr.length - 1 ? { bottom: { style: BorderStyle.SINGLE, size: 4, color: "D9D9D9", space: 4 } } : undefined),
    indent: { left: 120, right: 120 },
    children: [new TextRun({ text: line || " ", font: "Consolas", size: 16 })],
  })).concat([new Paragraph({ spacing: { after: 120 }, children: [] })]);
}

// ---- numbers pulled from the prototype run
const k = M.kpi_baseline, dm = M.delay_models, fc = M.forecast, al = M.allocation, rt = M.routing_total, cl = M.clustering;
const inv = M.inventory_sim;
const baseStock = Object.values(inv).reduce((s, v) => s + v.baseline_avg_stock, 0);
const propStock = Object.values(inv).reduce((s, v) => s + v.forecast_avg_stock, 0);
const stockCut = (100 * (1 - propStock / baseStock)).toFixed(1);

const body = [];
// ---------------- Title page
body.push(new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "STRATEGIC PLANNING REPORT", bold: true, size: 24, color: "7F7F7F", font: FONT })] }));
body.push(new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Data-Driven Distribution Planning for EastLink Distribution", bold: true, size: 52, color: NAVY, font: FONT })] }));
body.push(new Paragraph({ spacing: { after: 400 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 8 } },
  children: [new TextRun({ text: "Inventory forecasting, delay prediction and route optimisation for an Eastern India FMCG network using Python", size: 26, color: "404040", font: FONT })] }));
body.push(p("**Week 1 Deliverable:** Strategic Planning and Data Exploration in Logistics"));
body.push(p("**Scope:** project definition, KPIs, background research, methodology, roadmap and a working Python prototype"));
body.push(p("**Prepared by:** Shruti Rani"));
body.push(p("**Date:** 17 October 2026"));
body.push(p("**Code repository:** logistics-strategic-planning/ (README, src/, data/, outputs/)"));
body.push(new Paragraph({ children: [new PageBreak()] }));
body.push(new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Contents", bold: true, size: 32, color: NAVY, font: FONT })] }));
["1. Executive Summary","2. Project Definition","3. Key Performance Indicators","4. Background Research","5. Strategic Roadmap","6. Python Code Illustration","7. Prototype Results and Insights","8. Feasibility, Risks and Assumptions","9. Expected Outcomes and Decision Impact","10. References"].forEach(t => body.push(new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: t, size: 24, font: FONT })] })));
body.push(new Paragraph({ children: [new PageBreak()] }));

// ---------------- 1 Executive summary
body.push(h1("1. Executive Summary"));
body.push(p("EastLink Distribution is a hypothetical regional distributor of FMCG and pharmacy products that supplies 40 towns in West Bengal, Odisha, Jharkhand and North Bengal from three warehouses (Dankuni/Kolkata, Haldia and Durgapur). Management faces three connected problems: late deliveries (especially in the monsoon), inventory that is either too high or too low during festival peaks, and delivery routes planned by hand."));
body.push(p("This report defines the scenario, selects five KPIs, summarises public research that frames the problem, and sets out an end-to-end Python roadmap covering data collection, cleaning, exploratory analysis, predictive modelling and optimisation. To prove feasibility, a working prototype was built on a reproducible synthetic dataset (22,060 shipment records and 29,240 daily demand records). Results are illustrative and must be re-validated on real company data."));
body.push(p("**Prototype headline results (synthetic data):**"));
body.push(bullet(`Baseline on-time delivery is ${k.on_time_delivery_pct}%; it falls to ${k.otd_rain_pct}% on rainy days versus ${k.otd_dry_pct}% on dry days, so weather is the dominant delay driver.`));
body.push(bullet(`A gradient-boosting model predicts delay with MAE ${dm.gbm_MAE_h} h (R² ${dm.gbm_R2}) and flags late shipments with ROC-AUC ${dm.late_risk_AUC}.`));
body.push(bullet(`Demand forecasting reduces network WAPE from ${fc["network_WAPE_naive_%"]}% (seasonal naive) to ${fc["network_WAPE_model_%"]}%; in a stock simulation this allows about ${stockCut}% lower average inventory at the same 100% fill rate.`));
body.push(bullet(`Capacitated allocation cuts average distance per unit by ${al.km_reduction_pct}%, and savings-based routing cuts route kilometres by ${rt.km_saved_vs_nn_pct}% against a nearest-neighbour dispatcher baseline.`));

// ---------------- 2 Project definition
body.push(h1("2. Project Definition"));
body.push(h2("2.1 Logistics scenario"));
body.push(p("**Company profile.** EastLink Distribution moves roughly 1,900 units of product per day (2024 average) from three warehouses to 40 delivery towns. Customers fall into four segments: grocery, pharmacy, modern trade and e-commerce. Three vehicle classes are used: Tata Ace (up to 750 kg), Eicher Pro (up to 3 tonnes) and 10-tonne trucks. Road transport carries all volume."));
body.push(table(["Warehouse", "Location", "Daily capacity (units)"],
  Object.entries(al.capacity).map(([id, c]) => [id, { WH_KOL: "Dankuni, Kolkata", WH_HAL: "Haldia", WH_DGP: "Durgapur" }[id], c]), [2400, 4000, 3238]));
body.push(p(""));
body.push(h2("2.2 Business problems"));
body.push(bullet("**Service reliability:** deliveries are frequently late, with strong monsoon and congestion effects, and dispatchers have no early-warning signal."));
body.push(bullet("**Inventory imbalance:** static par levels ignore weekly seasonality, the Durga Puja and Diwali demand peak (about +35%) and the underlying growth trend."));
body.push(bullet("**Allocation and routing inefficiency:** about 20% of shipments leave a non-nearest warehouse, and multi-drop routes are built by experience rather than by optimisation."));
body.push(h2("2.3 Project objectives"));
body.push(num("Quantify current performance with a baseline KPI dashboard built from cleaned shipment and demand data."));
body.push(num("Predict shipment delay and late-delivery risk before dispatch so planners can act."));
body.push(num("Forecast warehouse-level demand 7 days ahead and convert forecasts into safety-stock and order-up-to levels."));
body.push(num("Optimise warehouse-to-customer allocation and multi-drop vehicle routes to cut distance and cost."));
body.push(num("Translate model outputs into decision rules and a monitoring plan for operations managers."));

// ---------------- 3 KPIs
body.push(h1("3. Key Performance Indicators"));
body.push(p("Five KPIs were chosen so that each project objective can be measured. Baselines come from the prototype dataset; targets are proposed planning values that will be agreed with stakeholders after real baselines are computed."));
body.push(table(["KPI", "Definition / formula", "Baseline (prototype)", "Proposed target"], [
  ["On-time delivery (OTD)", "Deliveries with actual time ≤ planned + 30 min ÷ total deliveries", `${k.on_time_delivery_pct}% (rain: ${k.otd_rain_pct}%)`, "≥ 90% overall"],
  ["Transport cost per tonne-km", "Σ trip cost (INR) ÷ Σ (tonnes × km)", `INR ${k.cost_per_tonne_km_inr}`, "−8% to −10%"],
  ["Fill rate and average stock", "Units served ÷ units demanded; mean on-hand stock (units)", `100% fill rate; ${Math.round(baseStock)} units on hand`, `Hold ≥ 98% fill; stock −${stockCut}%`],
  ["Forecast accuracy (WAPE)", "Σ|actual − forecast| ÷ Σ actual on 60-day hold-out", `${fc["network_WAPE_naive_%"]}% (seasonal naive)`, `≤ ${fc["network_WAPE_model_%"]}% (achieved in prototype)`],
  ["Average km per unit delivered", "Demand-weighted road distance from serving warehouse", `${al.current_avg_km_per_unit} km`, `≤ ${al.optimised_avg_km_per_unit} km`],
], [2100, 3300, 2300, 1938]));
body.push(p(""));

// ---------------- 4 Research
body.push(h1("4. Background Research"));
body.push(h2("4.1 Industry context"));
body.push(p("Logistics cost is a policy priority in India. The NCAER study for DPIIT, released in 2025, estimated India's logistics cost at 7.97% of GDP for 2023–24. This replaced the widely quoted 13–14% figure, which came from external or partial data. Road transport carries the largest share of freight in India, and the National Logistics Policy (2022) aims to bring cost down to global benchmarks through multimodal shifts, digitisation and initiatives such as PM Gati Shakti and the Unified Logistics Interface Platform."));
body.push(p("For a distributor like EastLink the lesson is that cost per tonne-km, delivery reliability and inventory carrying cost are the controllable levers. These are data problems: demand uncertainty, travel-time variability and network design can all be modelled."));
body.push(h2("4.2 Public data and resources"));
body.push(table(["Source", "Use in this project"], [
  ["NCAER / DPIIT logistics cost reports (ncaer.org, pib.gov.in)", "Benchmarks for cost structure, freight cost per tonne-km and target setting"],
  ["World Bank Logistics Performance Index", "Country-level benchmarking of timeliness, tracking and infrastructure"],
  ["DataCo Smart Supply Chain dataset (public on Kaggle/Mendeley Data)", "Real-world order, shipping and late-delivery fields to validate the delay-classification pipeline"],
  ["CVRPLIB benchmark instances", "Verify the routing heuristic against published best-known solutions"],
  ["OpenStreetMap / OSRM road network", "Replace the 1.3 × straight-line distance with actual road distance and drive time"],
  ["IMD rainfall records", "Replace the simulated rain flag with observed weather by district and date"],
], [4400, 5238]));
body.push(p("Note: the datasets above are candidates; availability, licences and schema will be confirmed in Week 2. The prototype uses synthetic data generated by src/generate_data.py, calibrated to patterns reported in the literature (monsoon slowdowns, festival peaks, weekly cycles).", { italics: true, size: 20 }));
body.push(h2("4.3 Data science concepts and how they apply"));
body.push(table(["Technique", "Logistics question", "Python implementation"], [
  ["Regression (linear, gradient boosting)", "How many hours late will this shipment be? Which factors drive delay?", "scikit-learn LinearRegression, HistGradientBoostingRegressor, permutation importance"],
  ["Classification", "Is this shipment at high risk of being late?", "HistGradientBoostingClassifier, ROC-AUC"],
  ["Clustering (K-Means)", "Which customers share demand and service profiles and need different policies?", "KMeans, silhouette score, PCA for visualisation"],
  ["Time-series forecasting", "How much will each warehouse need in the next 7 days?", "Lag/rolling features + gradient boosting; seasonal-naive benchmark"],
  ["Linear programming", "Which warehouse should serve each customer within capacity?", "scipy.optimize.linprog (HiGHS)"],
  ["Heuristic optimisation (VRP)", "In what order should a truck visit its customers?", "Clarke–Wright savings + 2-opt in NumPy"],
  ["Simulation", "What fill rate and stock result from a given inventory policy?", "Order-up-to policy simulation in src/inventory.py"],
], [2300, 3700, 3638]));
body.push(p(""));

// ---------------- 5 Roadmap
body.push(h1("5. Strategic Roadmap"));
body.push(img("00_roadmap.png", 620, 148));
body.push(cap("Figure 1: End-to-end analysis process flow"));
body.push(table(["Phase", "Activities", "Python tools", "Output"], [
  ["1. Data collection", "Extract shipments from TMS/ERP, daily demand from WMS, customer and warehouse masters; add weather and road-distance data", "pandas, requests, SQLAlchemy", "Raw CSV / database tables with data dictionary"],
  ["2. Cleaning", "Remove duplicates, standardise labels, impute missing values, flag impossible durations, engineer delay and cost features", "pandas, numpy", "shipments_clean.csv plus audit log"],
  ["3. Exploration", "Compute KPIs, monthly trends, rain/traffic effects, demand seasonality, customer profiles", "pandas, matplotlib, seaborn", "Baseline KPI report and charts"],
  ["4. Modelling", "Delay regression and late-risk classifier, K-Means segmentation, demand forecasting, inventory simulation", "scikit-learn", "Validated models and metrics.json"],
  ["5. Optimisation", "Capacitated allocation LP, savings-based vehicle routing", "scipy, numpy", "Allocation matrix and route plans"],
  ["6. Deployment", "Weekly refresh, dashboard, alerting, drift monitoring and retraining", "Streamlit or Power BI, cron/Airflow", "Planner-facing dashboard and monitoring report"],
], [1500, 3800, 2100, 2238]));
body.push(p(""));
body.push(h2("5.1 Timeline"));
body.push(bullet("**Week 1:** scenario, KPIs, research, roadmap and prototype (this report)."));
body.push(bullet("**Week 2:** acquire and profile real or public datasets; finalise schema and data-quality rules."));
body.push(bullet("**Weeks 3–4:** cleaning pipeline, EDA and baseline KPI dashboard."));
body.push(bullet("**Weeks 5–6:** predictive models with time-based validation."));
body.push(bullet("**Weeks 7–8:** optimisation, what-if scenarios and stakeholder review."));
body.push(h2("5.2 Validation strategy"));
body.push(p("Forecasts are validated on the last 60 days using a time split rather than a random split, and are always compared with a seasonal-naive benchmark. Delay models use a held-out test set and are compared with a predict-the-mean baseline. Optimisation results are benchmarked against what dispatchers do today, not against a theoretical worst case."));

// ---------------- 6 Code
body.push(h1("6. Python Code Illustration"));
body.push(p("The snippets below are taken from the working prototype in the src/ folder. Run python -m src.generate_data followed by python -m src.run_pipeline to reproduce every number and figure in this report."));
body.push(h2("6.1 Cleaning and feature engineering"));
body.push(...code(`
def clean_shipments(ship):
    df = ship.drop_duplicates(subset="shipment_id").copy()
    vmap = {"tata_ace": "Tata_Ace", "eicher_pro": "Eicher_Pro", "truck_10t": "Truck_10T"}
    v = df["vehicle_type"].str.strip().str.lower().str.replace(" ", "_")
    df["vehicle_type"] = v.map(vmap)
    # impute with group medians
    g = df.groupby("vehicle_type")["weight_kg"].transform("median")
    df["weight_kg"] = df["weight_kg"].fillna(g)
    g = df.groupby("warehouse_id")["traffic_index"].transform("median")
    df["traffic_index"] = df["traffic_index"].fillna(g)
    # actual duration > 4x plan is treated as a recording error
    df = df[(df["actual_hours"] / df["planned_hours"]) <= 4]
    df["delay_hours"] = df["actual_hours"] - df["planned_hours"]
    df["late"] = (df["delay_hours"] > 0.5).astype(int)
    return df
`));
body.push(h2("6.2 Delay prediction (regression and classification)"));
body.push(...code(`
pre = ColumnTransformer([("num", StandardScaler(), NUM),
                         ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])
reg = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.06)
gbr = Pipeline([("pre", pre), ("m", reg)])
gbr.fit(X_train, y_delay_train)
print("MAE (h):", mean_absolute_error(y_test, gbr.predict(X_test)))
clf = Pipeline([("pre", pre), ("m", HistGradientBoostingClassifier(max_iter=250))])
clf.fit(X_train, late_train)
print("AUC:", roc_auc_score(late_test, clf.predict_proba(X_test)[:, 1]))
`));
body.push(h2("6.3 Customer clustering"));
body.push(...code(`
Z = StandardScaler().fit_transform(features)   # demand, variability, distance, late rate
scores = {k: silhouette_score(Z, KMeans(k, n_init=10).fit_predict(Z))
          for k in range(2, 8)}
best_k = max(scores, key=scores.get)
features["cluster"] = KMeans(best_k, n_init=10, random_state=42).fit_predict(Z)
`));
body.push(h2("6.4 Demand forecast with a naive benchmark"));
body.push(...code(`
f["lag_7"], f["lag_14"] = s.shift(7), s.shift(14)   # lags >= 7 d: valid for 7-day horizon
f["roll28"] = s.shift(7).rolling(28).mean()
f["dow"], f["month"] = s.index.dayofweek, s.index.month
model = HistGradientBoostingRegressor(max_iter=300).fit(train[cols], train["y"])
wape = lambda a, p: np.abs(a - p).sum() / a.sum()
print(wape(test["y"], model.predict(test[cols])))
print(wape(test["y"], test["lag_7"]))               # seasonal-naive benchmark
`));
body.push(h2("6.5 Warehouse allocation (linear programming)"));
body.push(...code(`
# minimise sum(distance[i, j] * x[i, j])
# s.t. sum_j x[i, j] = demand[i]          (every customer fully served)
#      sum_i x[i, j] <= capacity[j]       (warehouse capacity)
res = linprog(c=D.flatten(), A_ub=A_ub, b_ub=capacity, A_eq=A_eq, b_eq=demand,
              bounds=(0, None), method="highs")
x = res.x.reshape(n_customers, n_warehouses)
`));
body.push(h2("6.6 Vehicle routing (savings heuristic)"));
body.push(...code(`
savings = sorted(((d[0, i] + d[0, j] - d[i, j], i, j)
                  for i in customers for j in customers if i < j), reverse=True)
for s, i, j in savings:          # merge routes while capacity and max-km allow
    if route_of[i] != route_of[j] and fits_capacity(i, j) and are_endpoints(i, j):
        merge_routes(i, j)
routes = [two_opt(r, d) for r in routes]   # local improvement per route
`));

// ---------------- 7 Prototype results
body.push(h1("7. Prototype Results and Insights"));
body.push(p("All results below come from synthetic data and demonstrate that the approach is technically feasible; they are not claims about a real company."));
body.push(h2("7.1 Data quality"));
const ca = M.cleaning_audit;
body.push(p(`The raw shipment table held ${ca.rows_raw.toLocaleString()} rows. Cleaning removed ${ca.duplicates_removed} duplicate records and ${ca.outliers_removed} impossible durations, and imputed ${ca.missing_before.traffic_index} missing traffic values and ${ca.missing_before.weight_kg} missing weights, leaving ${ca.rows_clean.toLocaleString()} rows with no missing values.`));
body.push(h2("7.2 Delivery performance"));
body.push(img("01_otd_vs_rain.png", 560, 256));
body.push(cap("Figure 2: Monthly on-time delivery follows rain exposure"));
body.push(p(`OTD is ${k.otd_dry_pct}% on dry days and ${k.otd_rain_pct}% in rain. Permutation importance confirms rain as the strongest delay driver, followed by planned duration, distance, driver experience and traffic.`));
body.push(img("02_delay_feature_importance.png", 470, 251));
body.push(cap("Figure 3: Drivers of delivery delay"));
body.push(table(["Model", "MAE (hours)", "R²"], [
  ["Predict the mean (baseline)", dm["baseline_MAE_h(predict mean)"], "0.00"],
  ["Linear regression", dm.linear_MAE_h, dm.linear_R2],
  ["Gradient boosting", dm.gbm_MAE_h, dm.gbm_R2],
], [4638, 2500, 2500]));
body.push(p(""));
body.push(p(`The late-risk classifier reaches ROC-AUC ${dm.late_risk_AUC}. Operationally, shipments with high predicted risk can be re-planned, given a more experienced driver, or communicated early to the customer.`));
body.push(h2("7.3 Customer segments"));
body.push(img("03_customer_clusters.png", 400, 262));
body.push(cap("Figure 4: K-Means segments (k chosen by silhouette score)"));
body.push(table(["Cluster", "Customers", "Avg daily demand", "Avg distance (km)", "Late rate"],
  cl.profiles.map(r => [r.cluster, r.customers, r.mean_demand, r.avg_distance_km, (100 * r.late_rate).toFixed(0) + "%"]), [1500, 1800, 2200, 2238, 1900]));
body.push(p(""));
body.push(p("Cluster 1 holds the distant North Bengal, Jharkhand and Odisha towns, which have the highest late rate and should receive buffer time, consolidated schedules or a regional cross-dock. Cluster 2 contains the two towns that sit next to a warehouse (Durgapur and Haldia): trips are very short, so cost per km is high, and small vehicles or combined milk-run deliveries are a better fit."));
body.push(h2("7.4 Demand forecasting and inventory"));
body.push(img("04_demand_forecast.png", 560, 256));
body.push(cap("Figure 5: 60-day hold-out forecast (network level)"));
body.push(table(["Warehouse", "WAPE model", "WAPE naive", "Avg stock baseline", "Avg stock forecast-driven"],
  Object.keys(fc.per_warehouse).map(id => [id, fc.per_warehouse[id]["WAPE_model_%"] + "%", fc.per_warehouse[id]["WAPE_seasonal_naive_%"] + "%", Math.round(inv[id].baseline_avg_stock), Math.round(inv[id].forecast_avg_stock)]),
  [1800, 1700, 1700, 2200, 2238]));
body.push(p(""));
body.push(p(`Both policies achieved a 100% fill rate in the simulation, so the benefit appears as lower stock: ${Math.round(baseStock)} to ${Math.round(propStock)} units on hand in total (${stockCut}% less). The baseline is a rule-of-thumb order-up-to level; the proposed policy uses forecast demand plus safety stock at z = 1.65.`));
body.push(h2("7.5 Allocation and routing"));
body.push(img("05_optimised_routes.png", 400, 359));
body.push(cap("Figure 6: Optimised multi-drop routes from the three warehouses"));
body.push(table(["Measure", "Current / baseline", "Optimised", "Change"], [
  ["Average km per unit (allocation)", al.current_avg_km_per_unit, al.optimised_avg_km_per_unit, `−${al.km_reduction_pct}%`],
  ["Daily route km vs nearest-neighbour dispatch", rt.nearest_neighbour_km.toLocaleString(), rt.optimised_km.toLocaleString(), `−${rt.km_saved_vs_nn_pct}%`],
  ["Daily route km vs one-truck-per-customer", rt.direct_km.toLocaleString(), rt.optimised_km.toLocaleString(), `−${rt.km_saved_vs_direct_pct}%`],
], [3800, 2000, 1800, 2038]));
body.push(p(""));
body.push(p(`The nearest-neighbour comparison is the realistic one: it represents a dispatcher choosing the closest next stop. The one-truck-per-customer figure is an upper bound. At an assumed INR 28 per km for a 5-tonne truck, the difference against nearest-neighbour is about INR ${rt.daily_saving_vs_nn_inr.toLocaleString("en-IN")} per day. Durgapur is fully loaded at its 700-unit capacity, so the LP also signals where extra capacity would be most valuable.`));

// ---------------- 8 Risks
body.push(h1("8. Feasibility, Risks and Assumptions"));
body.push(table(["Risk / assumption", "Impact", "Mitigation"], [
  ["Real data is incomplete or inconsistent", "Weaker models, delayed schedule", "Data-quality audit in Week 2; documented imputation rules; start with core fields"],
  ["Synthetic results overstate real gains", "Unrealistic expectations", "Report all prototype numbers as illustrative; re-baseline on real data before committing targets"],
  ["Straight-line distance × 1.3 is an approximation", "Route and cost errors", "Use OSRM or Google road distances and drive times"],
  ["Weather and demand shocks (floods, strikes, festival shifts)", "Forecast and delay error", "Event features, prediction intervals, safety stock, weekly retraining"],
  ["Planner adoption", "Models unused", "Explainable outputs, dashboard in planners' workflow, pilot on one warehouse first"],
], [3200, 2400, 4038]));
body.push(p(""));
body.push(p("All libraries used (pandas, NumPy, SciPy, scikit-learn, matplotlib) are open source, and the prototype runs in under a minute on a laptop, so the approach needs no specialised infrastructure. Larger route problems can move to OR-Tools or a commercial solver without changing the surrounding pipeline."));

// ---------------- 9 Conclusion
body.push(h1("9. Expected Outcomes and Decision Impact"));
body.push(p("If the prototype gains carry over to real data even partially, EastLink can expect:"));
body.push(bullet("**Higher service reliability:** earlier warnings for rain and long-haul shipments so that dispatchers can add buffer, re-plan or notify customers."));
body.push(bullet("**Lower inventory with stable service:** forecast-based order-up-to levels replace static par stocks, releasing working capital, particularly ahead of festival peaks."));
body.push(bullet("**Lower transport cost:** better warehouse allocation and consolidated routes reduce kilometres driven and cost per tonne-km."));
body.push(bullet("**Better strategic decisions:** segmentation and capacity-shadow-prices show where to add a cross-dock, upgrade vehicles or renegotiate customer delivery windows."));
body.push(p("The decision flow is: forecast → set stock levels → allocate orders to warehouses → plan routes → monitor OTD and cost KPIs → retrain. Each step produces numbers that a planner can act on, and each is measured by one of the five KPIs defined in Section 3."));
body.push(p("**Next step:** begin Week 2 by confirming real data access (or adopting a public dataset such as DataCo), freezing the data dictionary, and re-computing the baseline KPIs before any target is committed."));

// ---------------- References
body.push(h1("10. References"));
[
  "NCAER (2025). Assessment of Logistics Cost in India. Study for DPIIT, Ministry of Commerce and Industry. https://ncaer.org/wp-content/uploads/2025/09/NCAER_Logistic_Study_Report_Sept2025.pdf",
  "Press Information Bureau (2025). Supercharging India's Logistics (7.97% of GDP, 2023–24). https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251127708301.pdf",
  "NCAER. Logistics Cost in India: Assessment and Long-term Framework. NCAER. https://www.ncaer.org/?p=21265",
  "Business Standard (2025). Confidence in India's logistics cost: the story of economic transition. https://www.business-standard.com/amp/opinion/columns/confidence-in-india-s-logistics-cost-the-story-of-economic-transition-125112001452_1.html",
  "Government of India (2022). National Logistics Policy; PM Gati Shakti National Master Plan.",
  "Clarke, G. and Wright, J. W. (1964). Scheduling of vehicles from a central depot to a number of delivery points. Operations Research, 12(4).",
  "Dantzig, G. B. and Ramser, J. H. (1959). The truck dispatching problem. Management Science, 6(1).",
  "Hyndman, R. J. and Athanasopoulos, G. Forecasting: Principles and Practice (online textbook).",
  "Chopra, S. and Meindl, P. Supply Chain Management: Strategy, Planning, and Operation. Pearson.",
  "Pedregosa, F. et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12.",
].forEach(r => body.push(new Paragraph({ numbering: { reference: "num2", level: 0 }, spacing: { after: 80 }, children: [new TextRun({ text: r, size: 19, font: FONT })] })));

const doc = new Document({
  creator: "Shruti Rani", title: "Strategic Planning Report - EastLink Distribution",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: NAVY, font: FONT }, paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, color: "2E75B6", font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
    { reference: "num2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 540 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "EastLink Distribution - Strategic Planning Report  |  Page ", size: 17, color: "7F7F7F", font: FONT }),
      new TextRun({ children: [PageNumber.CURRENT], size: 17, color: "7F7F7F", font: FONT })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(path.join(__dirname, "Strategic_Planning_Report.docx"), buf); console.log("written"); });
