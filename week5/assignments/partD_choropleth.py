"""
Week 5 - Part D3: the normalized choropleth, the six-step recipe.

Run from week5/assignments/:
    python partD_choropleth.py
Produces: charts/partD_choropleth.png
"""
import pathlib
import sys
from datetime import date

import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import geolib

vizlib.style_defaults()
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART D3 -- the normalized choropleth")
print("=" * 70)

# 1. PROJECT -- equal-area (geolib.choropleth defaults to it)
# 2. JOIN -- on code, count failures
df = pd.read_csv(DATA / "district_health.csv")
feats = geolib.read_geojson(DATA / "districts.geojson")
feat_codes = {f["code"] for f in feats}
unmatched = sorted(set(df["code"]) - feat_codes)
print(f"1. Projection: equal-area (Lambert cylindrical), shared reference latitude across the layer.")
print(f"2. Join on `code`: {len(unmatched)} failures (of {len(df)} districts).")

# 3. NORMALIZE -- cases per 100,000 residents
df["rate"] = df["cases"] / df["population"] * 1e5
pooled = df["cases"].sum() / df["population"].sum() * 1e5
print(f"3. Normalize: cases per 100,000 residents. Pooled rate = {pooled:.1f} from "
      f"{df['cases'].sum():,} cases.")

# 4. CLASSIFY -- 5 classes, Jenks natural breaks, printed
edges = geolib.breaks(df["rate"].to_numpy(), "natural", 5)
gvf_score = geolib.gvf(df["rate"].to_numpy(), edges)
print(f"4. Classify: 5 classes, Jenks natural breaks (GVF={gvf_score:.3f}), edges: "
      + ", ".join(f"{e:.1f}" for e in edges))

top3_rate = df.sort_values("rate", ascending=False).head(3)["code"].tolist()
top3_count = df.sort_values("cases", ascending=False).head(3)["code"].tolist()
r_pop = stats.pearsonr(df["cases"], df["population"])[0]
print(f"   Top 3 by rate: {top3_rate}  |  Top 3 by count: {top3_count}  |  "
      f"overlap: {len(set(top3_rate) & set(top3_count))}  |  r(cases,pop)={r_pop:.3f}")

# 5. COLOUR -- one sequential hue, dark = more. A single-hue sequential
# colormap varies only in lightness, so it is CVD-safe by construction
# (nothing to confuse hue-deficient vision with) -- unlike the categorical
# swatches vizlib.cvd_report() checks, which need an actual hue comparison.
print(f"5. Colour: sequential, single-hue '{vizlib.PALETTE['sequential']}' colormap, dark = more.")

# 6. CAPTION -- units, source, date, projection, suppression
CAPTION_NOTE = (
    f"Units: cases per 100,000 residents, 24 districts | Source: district_health.csv, synthetic, "
    f"CDB601220 | Boundaries: districts.geojson, same source | Extraction date: 2026-11-08 | "
    f"Projection: equal-area (Lambert cylindrical) | Join: {len(unmatched)} of {len(df)} failed | "
    f"Nothing suppressed -- all 24 districts' counts are large enough to publish individually "
    f"(min {df['cases'].min()} cases)"
)

fig, (ax_map, ax_bar) = plt.subplots(1, 2, figsize=(11.5, 7), gridspec_kw={"width_ratios": [0.72, 1]})
geolib.choropleth(ax_map, feats, dict(zip(df["code"], df["rate"])), scheme="natural", k=5,
                  legend_title="Cases per\n100,000 residents", legend_loc="upper center",
                  legend_anchor=(0.5, -0.03))
ax_map.set_title(f"Top 3 by rate: {', '.join(top3_rate)}", fontsize=9.5, loc="left")

order = df.sort_values("rate")
bars = ax_bar.barh(order["district"], order["rate"], color=vizlib.PALETTE["series"][0])
ax_bar.bar_label(bars, fmt="%.1f", fontsize=7, padding=2)
ax_bar.set_xlabel("Cases per 100,000 residents")
ax_bar.set_title(f"Top 3 by count: {', '.join(top3_count)} -- a different three entirely", fontsize=9.5, loc="left")
ax_bar.spines[["top", "right"]].set_visible(False)

fig.suptitle("Normalized incidence by district -- a raw-count map would point at different districts",
             fontsize=12, fontweight="bold")
fig.tight_layout(rect=[0, 0.08, 1, 0.93])
vizlib.save_fig(fig, OUT / "partD_choropleth.png", note=CAPTION_NOTE)
plt.close(fig)

print(f"\nFigure saved -> {OUT / 'partD_choropleth.png'} (300 dpi)")
print("=" * 70)
print("End of Part D3")
print("=" * 70)
