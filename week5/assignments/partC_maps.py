"""
Week 5 - Part C: the two-map activity, on real readers.

Builds both maps (3 marks) and verifies the self-check numbers. The reader
activity (5+ real people, each asked the same question on Map A then Map B,
4 marks) is NOT fabricated here -- see the note at the bottom; it needs
actual people in front of the two maps, which this session cannot supply.

Run from week5/assignments/:
    python partC_maps.py
Produces: charts/partC_mapA_count.png, charts/partC_mapB_rate.png
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
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART C -- the two-map activity, on real readers")
print("=" * 70)

# ══════════════════════════════════════════════════════════════════════════
# 1. Build both maps
# ══════════════════════════════════════════════════════════════════════════
cc = pd.read_csv(DATA / "county_crime.csv")
feats = geolib.read_geojson(DATA / "districts.geojson")
feat_codes = {f["code"] for f in feats}
county_codes = set(cc["code"])
unmatched_counties = sorted(county_codes - feat_codes)   # county rows with no polygon
unmatched_polygons = sorted(feat_codes - county_codes)   # polygons with no county row
matched = cc[~cc["code"].isin(unmatched_counties)].copy()
print(f"\n{len(cc)} counties, joined to districts.geojson's 24 features on `code`. "
      f"{len(unmatched_counties)} county rows have no matching polygon. "
      f"{len(unmatched_polygons)} polygons ({unmatched_polygons}) have no county row and are "
      f"left blank on both maps, as the brief specifies -- the dataset covers D01-D20 of the "
      f"federation's 24 districts.")

r_pop = stats.pearsonr(matched["crimes_reported"], matched["population"])[0]
print(f"r(crimes_reported, population) = {r_pop:.3f}")

top3_count = matched.sort_values("crimes_reported", ascending=False).head(3)["county"].tolist()
matched["rate"] = matched["crimes_reported"] / matched["population"] * 1e5
top3_rate = matched.sort_values("rate", ascending=False).head(3)["county"].tolist()
overlap = len(set(top3_count) & set(top3_rate))
print(f"Top 3 by count: {top3_count}")
print(f"Top 3 by rate:  {top3_rate}")
print(f"Overlap: {overlap}")

matched["rank_count"] = matched["crimes_reported"].rank(ascending=False)
matched["rank_rate"] = matched["rate"].rank(ascending=False)
n_moved3 = int(((matched["rank_count"] - matched["rank_rate"]).abs() >= 3).sum())
print(f"Counties moving 3+ places between the two rankings: {n_moved3} of {len(matched)}")

bottom_examples = matched[matched["county"].isin(["Elmsworth", "Hollowfield"])]
if len(bottom_examples):
    print(bottom_examples[["county", "crimes_reported", "population", "rate",
                           "rank_count", "rank_rate"]].to_string(index=False))

fig, ax = plt.subplots(figsize=(6, 6.5))
geolib.choropleth(ax, [f for f in feats if f["code"] in matched["code"].values],
                  dict(zip(matched["code"], matched["crimes_reported"])),
                  scheme="natural", k=5, legend_title="Crimes reported (count)")
ax.set_title("Map A -- crimes reported (count)", loc="left")
vizlib.save_fig(fig, OUT / "partC_mapA_count.png",
                note=f"Source: county_crime.csv + districts.geojson | n={len(matched)} of 24 districts "
                     f"({unmatched_polygons} have no county row, left off the map)")
plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 6.5))
geolib.choropleth(ax, [f for f in feats if f["code"] in matched["code"].values],
                  dict(zip(matched["code"], matched["rate"])),
                  scheme="natural", k=5, legend_title="Crimes per 100,000 residents")
ax.set_title("Map B -- crimes per 100,000 residents", loc="left")
vizlib.save_fig(fig, OUT / "partC_mapB_rate.png",
                note=f"Source: county_crime.csv + districts.geojson | n={len(matched)} of 24 districts "
                     f"({unmatched_polygons} have no county row, left off the map)")
plt.close(fig)
print(f"\nBoth maps saved: charts/partC_mapA_count.png, charts/partC_mapB_rate.png")

print("""
NOT RUN: the activity asks for at least 5 real readers, shown Map A first ("which three
counties would you send extra police to?"), then Map B with the same question, their answers
and the overlap recorded to partC_reader_results.csv. The brief is explicit that fabricated or
implausible reader results score zero for the whole part, so no responses are invented here.
Both maps above are built, correct, and ready to show; running the activity with 5 real people
and completing partC_reader_results.csv plus the mean-overlap write-up is the one piece of this
part still outstanding.
""")

print("=" * 70)
print("End of Part C")
print("=" * 70)
