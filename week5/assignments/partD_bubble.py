"""
Week 5 - Part D1: the four-variable bubble chart.

Run from week5/assignments/:
    python partD_bubble.py
Produces: charts/partD_bubble.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import geolib

vizlib.style_defaults()
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART D1 -- the four-variable bubble chart")
print("=" * 70)

df = pd.read_csv(DATA / "health_indicators.csv")

# Size: AREA proportional to pop_m, range chosen in Part B.1
LO_PT, HI_PT = 20, 1200
rng = df["pop_m"].max() - df["pop_m"].min()
s = LO_PT + (df["pop_m"] - df["pop_m"].min()) / rng * (HI_PT - LO_PT)

regions = sorted(df["region"].unique())
# 6 regions, but the course palette only guarantees 4 CVD-safe hues (Week 3's
# worst_pair() rule) -- a 5th/6th hue would silently collide for some viewers
# (and literally does: Andara/Dravira, Borealis/Esperia and Caldera/Fenwick
# would otherwise share identical colours). Redundant-code the repeat instead
# of adding hues (Week 3 Part C4's rule): 4 hues x marker shape.
hues4 = vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]]
colour_map = {r: hues4[i % 4] for i, r in enumerate(regions)}
marker_map = {r: vizlib.MARKERS[i // 4] for i, r in enumerate(regions)}
print(f"Region -> (hue, marker), 6 categories on 4 CVD-safe hues + shape as the second channel:")
for r in regions:
    print(f"  {r:10s} {colour_map[r]}  marker={marker_map[r]!r}")

# The gdp_pc outlier
outlier = df.loc[df["gdp_pc"].idxmax()]
print(f"gdp_pc outlier: {outlier['country']} at ${outlier['gdp_pc']:,} "
      f"({outlier['gdp_pc'] / df['gdp_pc'].nlargest(2).iloc[1]:.1f}x the next-highest) -- "
      f"KEPT on a log-x axis, which is exactly the axis choice that makes one extreme value "
      f"tolerable rather than crushing everything else (Case 3's lesson, applied here instead "
      f"of ignored).")

fig, ax = plt.subplots(figsize=(9.5, 6.5))
for region in regions:
    g = df[df["region"] == region]
    ax.scatter(g["gdp_pc"], g["healthcare_access"], s=s[g.index], color=colour_map[region],
              marker=marker_map[region], alpha=0.65, edgecolor="white", lw=0.5, label=region)
ax.set_xscale("log")
ax.set_xlabel("GDP per capita (USD, log scale)")
ax.set_ylabel("Healthcare access (0-100)")
ax.set_ylim(0, 100)
ax.set_title("Richer countries have better healthcare access, but population size and region\n"
             "cut across the trend", loc="left")

# Direct-label 4 countries worth talking about
talk_about = [outlier["country"],
             df.loc[df["pop_m"].idxmax(), "country"],
             df.loc[df["healthcare_access"].idxmin(), "country"],
             df.loc[(df["gdp_pc"] < 2000) & (df["healthcare_access"] > 60), "country"].iloc[0]
             if len(df[(df["gdp_pc"] < 2000) & (df["healthcare_access"] > 60)]) else df.loc[df["healthcare_access"].idxmax(), "country"]]
for name in talk_about:
    row = df[df["country"] == name].iloc[0]
    ax.annotate(name, xy=(row["gdp_pc"], row["healthcare_access"]), xytext=(6, 6),
               textcoords="offset points", fontsize=8, fontweight="bold")

leg1 = ax.legend(title="Region", loc="upper left", bbox_to_anchor=(1.02, 1.0),
                 frameon=False, fontsize=8)
ax.add_artist(leg1)
geolib.size_legend(ax, df["pop_m"].to_numpy(), max_pt=HI_PT, title="Population (M)",
                   loc="upper left", bbox_to_anchor=(1.02, 0.45), fmt="{:.0f}M")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(rect=[0, 0, 0.82, 1])

vizlib.save_fig(fig, OUT / "partD_bubble.png",
                note=f"Source: health_indicators.csv | n={len(df)} | area (not radius) proportional "
                     f"to pop_m, sizes=({LO_PT},{HI_PT})pt2 | gdp_pc outlier ({outlier['country']}) "
                     f"kept, log-x axis absorbs it | 6 regions on 4 CVD-safe hues, marker shape as the "
                     f"redundant second channel for the repeated pair in each hue")
plt.close(fig)
print(f"\nFigure saved -> {OUT / 'partD_bubble.png'} (300 dpi)")
print("=" * 70)
print("End of Part D1")
print("=" * 70)
