"""
Week 6 - Task C: the figure the board will actually see.

One figure, one message, for the National Grid Authority's board: where is
supply least reliable? A normalized choropleth (interruptions per 1,000
households) beside the raw-count map it replaces.

Run from week6/assignments/:
    python partC_figure.py
Produces: charts/partC_figure.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import geolib

vizlib.style_defaults()
CLEAN = pathlib.Path(__file__).parent / "clean"
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("TASK C -- the figure the board will actually see")
print("=" * 70)

dg = pd.read_csv(CLEAN / "district_grid.csv")
feats = geolib.read_geojson(DATA / "regions.geojson")

dg["rate_per_1k_hh"] = dg["outages"] / dg["households"] * 1000
pooled = dg["outages"].sum() / dg["households"].sum() * 1000
print(f"National pooled rate: {pooled:.1f} interruptions per 1,000 households")

r_count = stats.pearsonr(dg["outages"], dg["households"])[0]
r_rate = stats.pearsonr(dg["rate_per_1k_hh"], dg["households"])[0]
print(f"r(interruptions, households) = {r_count:.3f}")
print(f"r(interruptions per 1,000 households, households) = {r_rate:.3f}")

top3_count = dg.sort_values("outages", ascending=False).head(3)["code"].tolist()
top3_rate = dg.sort_values("rate_per_1k_hh", ascending=False).head(3)["code"].tolist()
overlap = sorted(set(top3_count) & set(top3_rate))
print(f"Top 3 by count: {top3_count}")
print(f"Top 3 by rate:  {top3_rate}")
print(f"On both lists: {overlap}")

areas = {f["code"]: geolib.polygon_area_km2(f["ring"]) for f in feats}
dg["area_km2_geo"] = dg["code"].map(areas)
top5pop = dg.sort_values("population", ascending=False).head(5)
land_share = top5pop["area_km2_geo"].sum() / dg["area_km2_geo"].sum() * 100
pop_share = top5pop["population"].sum() / dg["population"].sum() * 100
print(f"5 most populous districts: {land_share:.1f}% of land, {pop_share:.1f}% of population")

edges = geolib.breaks(dg["rate_per_1k_hh"].to_numpy(), "natural", 5)
gvf_score = geolib.gvf(dg["rate_per_1k_hh"].to_numpy(), edges)
print(f"Classification: natural breaks k=5, GVF={gvf_score:.3f}")

fig, (ax_rate, ax_count) = plt.subplots(1, 2, figsize=(10.5, 5.6), gridspec_kw={"width_ratios": [1, 1]})
geolib.choropleth(ax_rate, feats, dict(zip(dg["code"], dg["rate_per_1k_hh"])), scheme="natural", k=5,
                  legend_title="Interruptions per\n1,000 households", legend_loc="lower left",
                  legend_anchor=(0.0, 0.0))
ax_rate.set_title(f"RATE: {', '.join(top3_rate)} least reliable", fontsize=10, loc="left")

geolib.choropleth(ax_count, feats, dict(zip(dg["code"], dg["outages"])), scheme="natural", k=5,
                  legend_title="Interruptions\n(raw count)", legend_loc="lower left",
                  legend_anchor=(0.0, 0.0))
ax_count.set_title(f"COUNT (default view): {', '.join(top3_count)} -- only "
                   f"{overlap[0] if overlap else 'no district'} shared with the rate map",
                   fontsize=10, loc="left")

fig.suptitle("Where is supply least reliable? By rate, not by headcount",
             fontsize=14, fontweight="bold", y=0.99)
fig.text(0.01, 0.905,
         "For the Board | reliability-budget review, trailing 12 months | "
         "unit: interruptions per 1,000 households, not raw count",
         fontsize=9, color=vizlib.PALETTE["ink_soft"])
fig.tight_layout(rect=[0, 0.02, 1, 0.86])

note = (
    f"Normalized by households (not population): interruptions per 1,000 households | "
    f"Classification: natural (Jenks) breaks, k=5, GVF={gvf_score:.2f} | Projection: equal-area | "
    f"r(count, households)={r_count:.2f}, r(rate, households)={r_rate:.2f} | "
    f"5 most populous districts hold {pop_share:.1f}% of people on {land_share:.1f}% of the land | "
    f"Source: clean/district_grid.csv + regions.geojson, synthetic, CDB601220"
)
vizlib.save_fig(fig, OUT / "partC_figure.png", note=note)
plt.close(fig)
print(f"\nFigure saved -> {OUT / 'partC_figure.png'} (300 dpi)")
print("=" * 70)
print("End of Task C")
print("=" * 70)
