"""Draws the end-to-end analysis roadmap used in the report."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from .config import FIG_DIR

steps = [("1. Collect", "ERP/WMS, GPS-TMS,\nweather, public data"),
         ("2. Clean", "dedupe, impute,\noutliers, validate"),
         ("3. Explore", "KPIs, seasonality,\ncorrelations"),
         ("4. Model", "regression, clustering,\nforecasting"),
         ("5. Optimise", "allocation LP,\nVRP routing"),
         ("6. Deploy", "dashboard, alerts,\nmonitor & retrain")]
fig, ax = plt.subplots(figsize=(10, 2.2)); ax.axis("off"); ax.set_xlim(0, 12.6); ax.set_ylim(0, 2)
for i, (t, s) in enumerate(steps):
    x = 0.1 + i * 2.1
    ax.add_patch(FancyBboxPatch((x, 0.25), 1.8, 1.5, boxstyle="round,pad=0.03", fc="#1F4E79" if i % 2 == 0 else "#2E75B6", ec="none"))
    ax.text(x + 0.9, 1.3, t, ha="center", va="center", color="white", weight="bold", fontsize=10)
    ax.text(x + 0.9, 0.7, s, ha="center", va="center", color="white", fontsize=7.5)
    if i < len(steps) - 1:
        ax.annotate("", xy=(x + 2.08, 1.0), xytext=(x + 1.84, 1.0), arrowprops=dict(arrowstyle="-|>", color="#444"))
fig.savefig(FIG_DIR / "00_roadmap.png", bbox_inches="tight", dpi=150)
