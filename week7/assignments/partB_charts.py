"""
Week 7 - Task B: the static spine -- four charts, four kinds of question.

Uses only the cleaned files from clean/.

Run from week7/assignments/:
    python partB_charts.py
Produces: charts/partB_1.png (trend), partB_2.png (composition/hierarchy),
          partB_3.png (comparison), partB_4.png (map, normalized)
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib
import geolib

vizlib.style_defaults()
CLEAN = pathlib.Path(__file__).parent / "clean"
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("TASK B -- the static spine")
print("=" * 70)

# ══════════════════════════════════════════════════════════════════════
# Chart 1 -- TREND: network punctuality, monthly, by mode
# (ridership_daily -- the time-axis requirement)
# ══════════════════════════════════════════════════════════════════════
rd = pd.read_csv(CLEAN / "ridership_daily.csv", parse_dates=["date"])
monthly = rd.groupby([rd["date"].dt.to_period("M"), "mode"]).agg(
    on_time=("trips_on_time", "sum"), operated=("trips_operated", "sum")).reset_index()
monthly["punctuality"] = monthly["on_time"] / monthly["operated"] * 100
piv = monthly.pivot(index="date", columns="mode", values="punctuality")
piv.index = piv.index.to_timestamp()

fig, ax = plt.subplots(figsize=(9, 4.5))
colors = dict(zip(["Metro", "BRT", "Bus", "Ferry"],
                  vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]]))
for mode in ["Metro", "BRT", "Bus", "Ferry"]:
    s = piv[mode].dropna()
    ax.plot(s.index, s.to_numpy(), color=colors[mode], marker="o", ms=3, lw=1.5, label=mode)
ax.axvline(pd.Timestamp("2026-09-22"), color=vizlib.PALETTE["ink_soft"], ls=":", lw=1)
ax.annotate("Bus & Ferry\nstop reporting", xy=(pd.Timestamp("2026-09-22"), 70),
            fontsize=7.5, color=vizlib.PALETTE["ink_soft"])
ax.set_ylim(0, 100)
ax.set_xlabel("Month")
ax.set_ylabel("Punctuality (trips on time / trips operated, %)")
ax.set_title("Metro is reliably punctual; Bus lags every mode, every month", loc="left")
ax.legend(frameon=False, fontsize=8, ncol=4, loc="lower center")
ax.spines[["top", "right"]].set_visible(False)
vizlib.save_fig(fig, OUT / "partB_1.png",
                note="Decision supported: which mode's punctuality needs attention first | "
                     "Source: clean/ridership_daily.csv | monthly punctuality = sum(on_time)/sum(operated), "
                     "never a mean of daily percentages | Bus & Ferry stop reporting after 2026-09-22")
plt.close(fig)
print("Chart 1 (trend) saved")

# ══════════════════════════════════════════════════════════════════════
# Chart 2 -- COMPOSITION/HIERARCHY: journeys by mode and fare product
# (fare_revenue -- the part-to-whole requirement)
# ══════════════════════════════════════════════════════════════════════
fr = pd.read_csv(CLEAN / "fare_revenue.csv")
latest_month = fr["month"].max()
latest = fr[fr["month"] == latest_month]
by_mode_product = latest.groupby(["mode", "ticket_type"])["trips"].sum()
mode_order = latest.groupby("mode")["trips"].sum().sort_values(ascending=False).index.tolist()

fig, ax = plt.subplots(figsize=(8, 4.5))
bottom = np.zeros(len(mode_order))
for product, color in zip(["Single", "Daily", "Monthly"],
                          vizlib.PALETTE["series"]):
    vals = [by_mode_product.get((m, product), 0) for m in mode_order]
    ax.bar(mode_order, vals, bottom=bottom, label=product, color=color)
    bottom += np.array(vals)
ax.set_ylabel("Journeys")
ax.set_title(f"Metro's journeys are mostly single tickets -- {latest_month}", loc="left")
ax.legend(title="Fare product", frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
vizlib.save_fig(fig, OUT / "partB_2.png",
                note=f"Decision supported: which fare product to promote per mode | "
                     f"Source: clean/fare_revenue.csv | month={latest_month} | "
                     f"'All tickets' subtotal excluded from every sum")
plt.close(fig)
print("Chart 2 (composition/hierarchy) saved")

# ══════════════════════════════════════════════════════════════════════
# Chart 3 -- COMPARISON: crowding vs cost recovery by route (routes.csv)
# ══════════════════════════════════════════════════════════════════════
rt = pd.read_csv(CLEAN / "routes.csv")
by_mode = rt.groupby("mode").agg(crowding=("crowding_index", "mean"),
                                 cost_recovery=("cost_recovery_pct", "mean")).sort_values("crowding")

fig, ax1 = plt.subplots(figsize=(7, 4.5))
x = np.arange(len(by_mode))
bars = ax1.bar(x, by_mode["crowding"], color=vizlib.PALETTE["series"][0])
ax1.axhline(1.0, color=vizlib.PALETTE["highlight"], ls="--", lw=1.2, label="capacity (1.0)")
ax1.bar_label(bars, fmt="%.2f", padding=3, fontsize=8)
ax1.set_xticks(x)
ax1.set_xticklabels(by_mode.index)
ax1.set_ylabel("Mean crowding index (peak-hour pax / capacity)")
ax1.set_title("BRT runs over capacity at peak; Ferry has the most spare room", loc="left")
ax1.legend(frameon=False, fontsize=8)
ax1.spines[["top", "right"]].set_visible(False)
vizlib.save_fig(fig, OUT / "partB_3.png",
                note="Decision supported: which mode needs more peak-hour fleet | "
                     "Source: clean/routes.csv | mean crowding_index per mode, 36 routes")
plt.close(fig)
print("Chart 3 (comparison) saved")

# ══════════════════════════════════════════════════════════════════════
# Chart 4 -- MAP, normalized: boardings per 1,000 residents by district
# ══════════════════════════════════════════════════════════════════════
dt = pd.read_csv(CLEAN / "district_transit.csv")
feats = geolib.read_geojson(DATA / "regions.geojson")
rate = dt["boardings_annual"] / dt["population"] * 1000

fig, ax = plt.subplots(figsize=(6, 6.5))
edges = geolib.choropleth(ax, feats, dict(zip(dt["code"], rate)), scheme="natural", k=5,
                          legend_title="Boardings per\n1,000 residents")
ax.set_title("Transit use per resident is highest in the smaller western districts", loc="left")
vizlib.save_fig(fig, OUT / "partB_4.png",
                note=f"Decision supported: where the network already has the highest per-capita use | "
                     f"Source: clean/district_transit.csv + regions.geojson | normalized: boardings "
                     f"per 1,000 residents (not raw boardings) | natural breaks k=5")
plt.close(fig)
print("Chart 4 (map, normalized) saved")

print("\n" + "=" * 70)
print("End of Task B")
print("=" * 70)
