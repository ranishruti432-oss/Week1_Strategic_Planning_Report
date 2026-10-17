# Strategic Planning and Data Exploration in Logistics

**Scenario:** *EastLink Distribution* - a regional FMCG/pharmacy distributor serving 40 towns in
West Bengal, Odisha, Jharkhand and North Bengal from three warehouses (Dankuni/Kolkata, Haldia, Durgapur).

**Prepared by:** Shruti Rani

This repository is the **Week 1 deliverable**: a strategic planning report (Word `.docx`) plus a working
Python prototype that shows how data science can improve delivery reliability, inventory and routing.

| Deliverable | Where |
|---|---|
| Strategic planning report (DOC) | [`docs/Strategic_Planning_Report.docx`](docs/Strategic_Planning_Report.docx) |
| Python scripts / snippets | [`src/`](src) |
| Results and figures | [`outputs/`](outputs) |

## Business problems

1. Late deliveries, especially in the monsoon, with no early warning.
2. Inventory that is too high or too low because static par levels ignore seasonality and festival peaks.
3. Warehouse allocation and multi-drop routes planned by hand.

## KPIs

| KPI | Definition | Prototype baseline |
|---|---|---|
| On-time delivery (OTD) | Deliveries within plan + 30 min / total | 82.8% (rain: 51.6%) |
| Cost per tonne-km | Trip cost (INR) / (tonnes x km) | INR 21.0 |
| Fill rate and average stock | Units served / demanded; mean on-hand stock | 100% fill; 2,180 units |
| Forecast accuracy (WAPE) | Sum abs error / sum actual, 60-day hold-out | 6.75% (seasonal naive) |
| Average km per unit | Demand-weighted distance from serving warehouse | 155.5 km |

## Data-science methods

| Technique | Use | Module |
|---|---|---|
| Linear and gradient-boosting regression, classification | Delay hours and late-risk prediction | `src/models.py` |
| K-Means clustering (silhouette, PCA) | Customer segmentation | `src/models.py` |
| Lag-feature time-series forecasting | 7-day warehouse demand forecast | `src/models.py` |
| Simulation | Order-up-to inventory policy vs static rule | `src/inventory.py` |
| Linear programming (`scipy.linprog`) | Capacitated warehouse allocation | `src/optimization.py` |
| Clarke-Wright savings + 2-opt | Multi-drop vehicle routing | `src/optimization.py` |

## Roadmap

`Collect -> Clean -> Explore -> Model -> Optimise -> Deploy` (details in Section 5 of the report).

## Project structure

```
.
├── README.md
├── requirements.txt
├── docs/
│   ├── Strategic_Planning_Report.docx   # main deliverable
│   └── build_report.js                  # regenerates the report from outputs/metrics.json
├── src/
│   ├── config.py                        # paths, seed, scenario constants
│   ├── generate_data.py                 # reproducible synthetic data
│   ├── data_cleaning.py                 # dedupe, impute, outliers, features
│   ├── models.py                        # regression, clustering, forecasting
│   ├── inventory.py                     # inventory policy simulation
│   ├── optimization.py                  # allocation LP + vehicle routing
│   ├── make_roadmap_figure.py           # roadmap diagram
│   └── run_pipeline.py                  # runs everything, writes outputs/
├── tests/test_pipeline.py               # smoke tests
├── data/raw/                            # generated CSVs (shipments, demand, customers, warehouses)
└── outputs/                             # metrics.json, customer_segments.csv, figures/
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.generate_data        # 1. create data/raw/*.csv
python -m src.run_pipeline         # 2. clean -> model -> optimise; writes outputs/
python -m src.make_roadmap_figure  # 3. (optional) roadmap diagram
python -m pytest -q tests          # 4. (optional) needs: pip install pytest

# optional: rebuild the Word report (needs Node.js and `npm install docx`)
node docs/build_report.js
```

## Prototype results (synthetic data)

| Area | Result |
|---|---|
| Delay model | GBM MAE 0.318 h, R2 0.545 (linear: 0.366 h, 0.371); late-risk AUC 0.81 |
| Forecast | Network WAPE 4.98% vs 6.75% seasonal naive |
| Inventory | About 11.6% lower average stock at the same 100% fill rate |
| Allocation | 9.0% fewer km per unit vs current dispatch mix |
| Routing | 32.7% fewer route km vs nearest-neighbour dispatch (64.8% vs one truck per customer) |

## Important notes

- **Data is synthetic.** Real logistics data is confidential, so `generate_data.py` simulates it using
  patterns from the literature (monsoon delays, festival peaks, weekly cycles). Results show that the
  approach works end-to-end; they are **not** claims about a real company. Replace `data/raw/*.csv`
  with real data in the same schema and the pipeline runs unchanged.
- Road distance is approximated as 1.3 x straight-line distance; use OSRM or Google distances for production.
- Candidate public data to validate on in Week 2: DataCo Smart Supply Chain, World Bank LPI, CVRPLIB, IMD rainfall.

## Research references

- NCAER (2025), *Assessment of Logistics Cost in India* (7.97% of GDP in 2023-24) - <https://ncaer.org/wp-content/uploads/2025/09/NCAER_Logistic_Study_Report_Sept2025.pdf>
- Clarke and Wright (1964), *Scheduling of vehicles from a central depot*, Operations Research 12(4)
- Hyndman and Athanasopoulos, *Forecasting: Principles and Practice*

Full reference list: Section 10 of the report.
