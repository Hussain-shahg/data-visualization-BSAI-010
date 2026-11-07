"""
Week 5 - Part B: the five spatial and channel decisions, computed.

Run from week5/assignments/:
    python partB_decisions.py
Produces: charts/partB_overplotting.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import geolib

vizlib.style_defaults()
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART B -- the five decisions, computed")
print("=" * 70)

# ══════════════════════════════════════════════════════════════════════════
# B1 -- the size range
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("B1 -- the size range for health_indicators.csv (Part D1)")
print("-" * 70)
hi = pd.read_csv(DATA / "health_indicators.csv")
pop = hi["pop_m"]
LO_PT, HI_PT = 20, 1200
diam_lo, diam_hi = np.sqrt(LO_PT / np.pi) * 2, np.sqrt(HI_PT / np.pi) * 2
print(f"  sizes=({LO_PT}, {HI_PT}) points^2 (AREA, not radius -- s= is passed the area value "
      f"directly, as matplotlib defines it).")
print(f"  Smallest mark ({LO_PT}pt^2, diameter {diam_lo:.1f}pt): the smallest value matplotlib "
      f"still renders as a filled, visually distinct dot rather than a speck -- below ~15pt^2 "
      f"markers start disappearing against the grid at this figure's dpi.")
print(f"  Largest mark ({HI_PT}pt^2, diameter {diam_hi:.1f}pt): at a 7x5 inch figure this is "
      f"about 15% of the panel's shorter dimension -- large enough to read clearly without "
      f"one mark swallowing its neighbours within 1-2 'country widths' on the x axis.")
print(f"  Diameter ratio implied: {diam_hi / diam_lo:.2f}:1 (AREA ratio: {HI_PT / LO_PT:.1f}:1) "
      f"for a population ratio of {pop.max() / pop.min():.0f}:1 -- deliberately far gentler than "
      f"linear, because area already reads as more-than-linear to the eye (Case 1's lesson).")

# ══════════════════════════════════════════════════════════════════════════
# B2 -- overplotting
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("B2 -- overplotting, scatter_dense.csv (n=9,000)")
print("-" * 70)
sd = pd.read_csv(DATA / "scatter_dense.csv")
cluster = sd[(sd["x"].between(2.6, 3.6)) & (sd["y"].between(2.5, 3.5))]
print(f"  n={len(sd)}. The 800-point cluster near (3.1, 3.0): {len(cluster)} points found in a "
      f"1.0x1.0 window around it.")

ALPHA, GRIDSIZE = 0.05, 40
fig, axes = plt.subplots(1, 4, figsize=(15, 4))
axes[0].scatter(sd["x"], sd["y"], s=6, color=vizlib.PALETTE["series"][0])
axes[0].set_title("Opaque (alpha=1.0)", fontsize=9)
axes[1].scatter(sd["x"], sd["y"], s=6, color=vizlib.PALETTE["series"][0], alpha=ALPHA)
axes[1].set_title(f"Transparent (alpha={ALPHA})", fontsize=9)
axes[2].hexbin(sd["x"], sd["y"], gridsize=GRIDSIZE, cmap=vizlib.PALETTE["sequential"])
axes[2].set_title(f"Hexbin (gridsize={GRIDSIZE})", fontsize=9)
import scipy.stats as stats
xx, yy = np.mgrid[sd["x"].min():sd["x"].max():100j, sd["y"].min():sd["y"].max():100j]
positions = np.vstack([xx.ravel(), yy.ravel()])
kernel = stats.gaussian_kde(np.vstack([sd["x"], sd["y"]]))
zz = np.reshape(kernel(positions).T, xx.shape)
axes[3].contourf(xx, yy, zz, levels=15, cmap=vizlib.PALETTE["sequential"])
axes[3].set_title("2-D KDE", fontsize=9)
for ax in axes:
    ax.set_xlabel("x")
    ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("y")
fig.suptitle("The 800-point cluster near (3.1, 3.0) -- visible only once overplotting is handled", fontsize=11)
fig.tight_layout()
vizlib.save_fig(fig, OUT / "partB_overplotting.png",
                note=f"Source: scatter_dense.csv | n=9,000 | alpha={ALPHA}, hexbin gridsize={GRIDSIZE}")
plt.close(fig)
print(f"""
  Opaque:      the cluster is INVISIBLE -- a 9,000-point opaque scatter saturates to one solid
               blob everywhere there is more than a handful of points; the cluster has no
               distinguishing visual weight at all.
  Transparent (alpha={ALPHA}): the cluster becomes faintly VISIBLE as a slightly denser patch,
               but is easy to miss and depends entirely on the alpha chosen.
  Hexbin:      the cluster is CLEARLY VISIBLE as a distinct bright cell, the most legible of
               the four.
  2-D KDE:     the cluster is VISIBLE as a distinct local mode, smooth and legible, but can
               soften or merge a cluster that is genuinely small/sharp (bandwidth-dependent).

  Publish: hexbin. It is the only one of the four with no continuous tuning parameter fighting
  the reader's perception (alpha and KDE bandwidth both have to be hand-tuned per dataset to
  avoid hiding or exaggerating structure); a hexbin's gridsize is coarser-grained and the colour
  directly encodes a count, which is also auditable (you can read off a cell's count).
""")

# ══════════════════════════════════════════════════════════════════════════
# B3 -- scaling and dimension reduction
# ══════════════════════════════════════════════════════════════════════════
print("-" * 70)
print("B3 -- scaling and PCA, health_indicators.csv")
print("-" * 70)
COLS = ["gdp_pc", "healthcare_access", "urban_pct", "median_age", "cases_per_100k"]
for how in ("minmax", "zscore", "rank"):
    s = geolib.scale_frame(hi, COLS, how)["gdp_pc"]
    print(f"  {how:8s} gdp_pc axis: min={s.min():.3f}, median={s.median():.3f}, "
          f"max={s.max():.3f}, 90th pct value sits at rank "
          f"{(s <= s.quantile(0.9)).sum()}/{len(s)}")
print("""
  min-max is dominated by the single $120,219 outlier (median lands near 0.02 -- Case 3).
  z-score keeps the outlier's relative distance (it is several SD out) but at least every
  other country's z-score reflects its OWN distance from the mean, not a crushed 0-0.1 band.
  rank is immune to the outlier's magnitude entirely -- the top country is simply rank 60/60,
  the same position a $20,000 country would hold if it happened to be the richest in the sample.
""")

X = geolib.scale_frame(hi, COLS, "zscore").to_numpy()
pca = PCA().fit(X)
evr = pca.explained_variance_ratio_
print(f"  PCA explained variance ratio: PC1={evr[0]:.3f}, PC2={evr[1]:.3f}, "
      f"PC1+PC2={evr[0] + evr[1]:.3f}")
print(f"  A two-axis picture (e.g. a scatter of PC1 vs PC2) of this 5-variable dataset is "
      f"MISSING {1 - evr[0] - evr[1]:.1%} of the total variance -- a substantial amount, "
      f"which is the argument for a parallel coordinates plot (D2) over a 2-D projection here.")

# ══════════════════════════════════════════════════════════════════════════
# B4 -- project before you measure
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("B4 -- project before you measure, districts.geojson")
print("-" * 70)
feats = geolib.read_geojson(DATA / "districts.geojson")
dh = pd.read_csv(DATA / "district_health.csv")


def shoelace_degrees(ring):
    ring = list(ring)
    if ring[0] == ring[-1]:
        ring = ring[:-1]
    x = np.array([p[0] for p in ring])
    y = np.array([p[1] for p in ring])
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


spherical = {f["code"]: geolib.polygon_area_km2(f["ring"]) for f in feats}
raw_deg = {f["code"]: shoelace_degrees(f["ring"]) for f in feats}

lat_by_code = dict(zip(dh["code"], dh["lat"]))
north4 = dh.nlargest(4, "lat")["code"].tolist()
sph_total = sum(spherical.values())
deg_total = sum(raw_deg.values())
sph_share = sum(spherical[c] for c in north4) / sph_total * 100
deg_share = sum(raw_deg[c] for c in north4) / deg_total * 100
print(f"  4 northernmost districts: {north4}")
print(f"  Share of total area -- spherical (correct): {sph_share:.2f}%  |  "
      f"raw-degree shoelace (wrong): {deg_share:.2f}%")

ratios = {c: (raw_deg[c] / deg_total) / (spherical[c] / sph_total) for c in spherical}
worst = max(ratios, key=lambda c: abs(ratios[c] - 1))
print(f"  Most distorted district: {worst}, its degree-based share is "
      f"{ratios[worst]:.2f}x its true spherical share")

lats = [lat_by_code[c] for c in spherical]
mercator_inflation = 1 / np.cos(np.radians(lats))
print(f"  Mercator area inflation across the federation (sec(latitude)): "
      f"{min(mercator_inflation):.3f}x (south) to {max(mercator_inflation):.3f}x (north)")
print("""
  This is exactly why slide 34 requires an equal-area projection for a choropleth: Mercator's
  inflation factor changes WITH latitude, so two districts of identical true area would be
  drawn at visibly different sizes purely because of where they sit on the map -- and a
  choropleth's colour-by-area-covered reading (as in Case 8) would be distorted by this before
  any data-driven unevenness even enters the picture.
""")

# ══════════════════════════════════════════════════════════════════════════
# B5 -- small-area stability
# ══════════════════════════════════════════════════════════════════════════
print("-" * 70)
print("B5 -- small-area stability, smallarea_cases.csv")
print("-" * 70)
sa = pd.read_csv(DATA / "smallarea_cases.csv")
pooled = sa["cases"].sum() / sa["population"].sum() * 1e5
z = 1.96
lam = pooled / 1e5 * sa["population"]
lo = np.maximum(lam - z * np.sqrt(lam), 0) / sa["population"] * 1e5
hi_ = (lam + z * np.sqrt(lam)) / sa["population"] * 1e5
rate = sa["cases"] / sa["population"] * 1e5
outside = int(((rate < lo) | (rate > hi_)).sum())
print(f"  {outside} of {len(sa)} units fall outside their own 95% Poisson limits.")
print(f"  This is exactly what Case 6's diagnosis argues: with {len(sa)} units tested "
      f"simultaneously at 95% confidence, ~{len(sa) * 0.05:.1f} false positives are expected by "
      f"chance alone even under one shared true rate -- {outside} outlier(s) found is consistent "
      f"with pure noise, not proof of a real hotspot on the Case 6 map.")


def min_pop_to_distinguish(r1, r2, per=100_000, z=1.96):
    """Smallest population at which two Poisson rates' 95% CIs stop overlapping."""
    for pop in np.arange(100, 2_000_000, 100):
        lam1, lam2 = r1 / per * pop, r2 / per * pop
        hi1 = lam1 + z * np.sqrt(lam1)
        lo2 = lam2 - z * np.sqrt(lam2)
        if hi1 < lo2:
            return pop
    return None


min_pop = min_pop_to_distinguish(9, 18)
print(f"  Minimum population at which a rate of 9/100k could be distinguished from 18/100k "
      f"(95% CIs stop overlapping): {min_pop:,} people.")

print("\n" + "=" * 70)
print("End of Part B")
print("=" * 70)
