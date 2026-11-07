"""
Week 5 - Part F (bonus): a normalized map on real data.

COVID-19 cumulative deaths by US state (The New York Times, github.com/
nytimes/covid-19-data, series ended 2023-03-23, downloaded 2026-11-08),
normalized by 2023 state population (U.S. Census Bureau, Vintage 2023
population estimates, NST-EST2023-ALLDATA.csv, downloaded 2026-11-08).
Boundaries: US state polygons bundled with the `folium` Python package
(github.com/python-visualization/folium, examples/data/us-states.json,
downloaded 2026-11-08) -- a Natural-Earth-derived simplified state outline
set, in use unmodified since early folium releases.

Run from week5/assignments/:
    python partF_map.py
Produces: charts/partF_map.png
"""
import json
import pathlib
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import geolib

vizlib.style_defaults()


def _read_geojson_multipolygon_safe(path):
    """geolib.read_geojson() only handles Polygon features (every course
    dataset is one), but real-world US state boundaries include MultiPolygon
    states (Hawaii's islands, Michigan's two peninsulas, etc). geolib.py is
    kept unchanged on disk; for this real external file only, each
    MultiPolygon is reduced to its single largest ring by vertex count (a
    standard simplification for a small-scale national map, where discarding
    a state's minor offshore islands does not change which class it falls
    into). Documented here and in Part E."""
    with open(path) as fh:
        gj = json.load(fh)
    out = []
    for feat in gj["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            ring = geom["coordinates"][0]
        elif geom["type"] == "MultiPolygon":
            ring = max((part[0] for part in geom["coordinates"]), key=len)
        else:
            raise ValueError(f"expected Polygon/MultiPolygon, got {geom['type']}")
        ring = [tuple(p) for p in ring]
        if ring[0] == ring[-1]:
            ring = ring[:-1]
        rec = dict(feat.get("properties", {}))
        rec["ring"] = ring
        out.append(rec)
    return out
DATA_F = pathlib.Path(__file__).parent / "data_f"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART F (bonus) -- a normalized map on real data")
print("=" * 70)

feats = _read_geojson_multipolygon_safe(DATA_F / "us-states.geojson")
print(f"\n{len(feats)} state polygons loaded (folium/Natural Earth derived outlines).")

covid = pd.read_csv(DATA_F / "nyt_covid_states.csv", parse_dates=["date"])
last_date = covid["date"].max()
final = covid[covid["date"] == last_date][["state", "cases", "deaths"]]
print(f"NYT COVID series: final date in the file = {last_date.date()}, {len(final)} states/territories.")

pop = pd.read_csv(DATA_F / "census_pop.csv")
pop = pop[(pop["SUMLEV"] == 40)][["NAME", "POPESTIMATE2023"]].rename(
    columns={"NAME": "state", "POPESTIMATE2023": "population"})
print(f"Census Vintage-2023 state population estimates: {len(pop)} states.")

m = final.merge(pop, on="state", how="inner")
feat_names = {f["name"] for f in feats}
m = m[m["state"].isin(feat_names)]
unmatched = sorted(feat_names - set(m["state"]))
print(f"Joined on state name: {len(m)} of {len(feats)} polygons matched. "
      f"{len(unmatched)} polygons unmatched (territories not in the boundary set or the case data): {unmatched}")

m["deaths_per_100k"] = m["deaths"] / m["population"] * 1e5
pooled = m["deaths"].sum() / m["population"].sum() * 1e5
print(f"\nPooled rate: {pooled:.1f} deaths per 100,000, from {m['deaths'].sum():,.0f} deaths, "
      f"population {m['population'].sum():,.0f}.")

scheme = "natural"
edges = geolib.breaks(m["deaths_per_100k"].to_numpy(), scheme, 5)
gvf_score = geolib.gvf(m["deaths_per_100k"].to_numpy(), edges)
print(f"Classification: 5 classes, {scheme} (Jenks) breaks, GVF={gvf_score:.3f}: "
      + ", ".join(f"{e:.0f}" for e in edges))

top5 = m.sort_values("deaths_per_100k", ascending=False).head(5)
print("\nTop 5 states by deaths per 100,000:")
print(top5[["state", "deaths", "population", "deaths_per_100k"]].round(1).to_string(index=False))

rate_by_name = dict(zip(m["state"], m["deaths_per_100k"]))
feats_matched = [f for f in feats if f["name"] in rate_by_name]
values = [rate_by_name[f["name"]] for f in feats_matched]

fig, ax = plt.subplots(figsize=(10, 6))
geolib.choropleth(ax, feats_matched, values, scheme=scheme, k=5, projection="equal_area",
                  legend_title="COVID-19 deaths per\n100,000 residents")
ax.set_title(f"COVID-19 cumulative mortality by U.S. state, through {last_date.date()}", loc="left")
note = (
    f"Deaths: NYT COVID-19 data (github.com/nytimes/covid-19-data), cumulative through "
    f"{last_date.date()}, downloaded 2026-11-08 | Population: U.S. Census Bureau Vintage 2023 "
    f"state estimates, downloaded 2026-11-08 | Boundaries: folium/Natural-Earth-derived state "
    f"outlines, downloaded 2026-11-08 | {len(m)} of {len(feats)} states matched | "
    f"Projection: equal-area | Scheme: Jenks natural breaks, k=5, GVF={gvf_score:.2f}"
)
vizlib.save_fig(fig, OUT / "partF_map.png", note=note)
plt.close(fig)
print(f"\nFigure saved -> {OUT / 'partF_map.png'} (300 dpi)")

# raw-count counterfactual, for the one-sentence comparison
m["rank_rate"] = m["deaths_per_100k"].rank(ascending=False)
m["rank_count"] = m["deaths"].rank(ascending=False)
top3_count = m.sort_values("deaths", ascending=False).head(3)["state"].tolist()
top3_rate = m.sort_values("deaths_per_100k", ascending=False).head(3)["state"].tolist()
print(f"\nCounterfactual -- top 3 by RAW COUNT: {top3_count}  (mostly the largest states by "
      f"population); top 3 by RATE: {top3_rate}. Overlap: "
      f"{len(set(top3_count) & set(top3_rate))} of 3 -- a raw-count map would have pointed "
      f"the response at the biggest states almost regardless of their actual per-capita toll.")

print("\n" + "=" * 70)
print("End of Part F")
print("=" * 70)
