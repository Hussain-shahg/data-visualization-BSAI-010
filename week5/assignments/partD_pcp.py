"""
Week 5 - Part D2: the parallel coordinates plot.

Run from week5/assignments/:
    python partD_pcp.py
Produces: charts/partD_pcp.png
"""
import pathlib
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import geolib


def _corr_chain_patched(df, cols):
    """See partA_charts.py for why this is needed: pandas >= 3.0 makes
    Copy-on-Write permanent, so geolib.corr_chain()'s np.fill_diagonal on a
    freshly-computed .corr().abs() array raises. geolib.py stays unchanged
    on disk; this is a runtime-only monkeypatch, documented in Part E."""
    import numpy as np
    cols = list(cols)
    r = df[cols].corr().abs()
    vals = r.to_numpy(copy=True)
    np.fill_diagonal(vals, 0.0)
    r = pd.DataFrame(vals, index=r.index, columns=r.columns)
    i, j = np.unravel_index(np.argmax(r.to_numpy()), r.shape)
    order = [cols[i], cols[j]]
    while len(order) < len(cols):
        rest = [c for c in cols if c not in order]
        order.append(max(rest, key=lambda c: r.loc[order[-1], c]))
    return order


geolib.corr_chain = _corr_chain_patched

vizlib.style_defaults()
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART D2 -- the parallel coordinates plot")
print("=" * 70)

df = pd.read_csv(DATA / "health_indicators.csv")
COLS = ["gdp_pc", "healthcare_access", "urban_pct", "median_age", "cases_per_100k"]

# 1. Scaling: percentile rank (Part B.3 -- immune to the $120k outlier that
# crushes min-max, and Case 3's own lesson)
HOW = "rank"
print(f"Scaling: '{HOW}' (percentile rank) -- min-max would crush 58/60 countries into the "
      f"bottom 10% of the gdp_pc axis around the single $120,219 outlier (Case 3 / Part B.3).")

# 2. Axis order: computed by corr_chain, not eyeballed
chain = geolib.corr_chain(df, COLS)
print(f"Axis order (geolib.corr_chain, greedy by |r|): {' -> '.join(chain)}")

# 3. Clutter control: grey everything, brush one region
brush_region = "Andara"
highlight = (df["region"] == brush_region).to_numpy()
print(f"Brushed region: {brush_region} ({highlight.sum()} of {len(df)} countries)")

fig, ax = plt.subplots(figsize=(10, 5.5))
geolib.pcp(ax, df, chain, how=HOW, highlight=highlight,
          hl_color=vizlib.PALETTE["highlight"])
ax.set_title(f"Axes ordered by correlation strength (corr_chain) -- healthcare access and\n"
             f"case rate cross sharply; {brush_region} (bold) sits at low GDP but mid-range access",
             loc="left")
vizlib.save_fig(fig, OUT / "partD_pcp.png",
                note=f"Source: health_indicators.csv | n={len(df)} | axes percentile-rank scaled | "
                     f"order computed by corr_chain(): {' -> '.join(chain)} | "
                     f"{brush_region} brushed, rest in grey")
plt.close(fig)

r1 = df[chain[0]].corr(df[chain[1]])
r2 = df[chain[-2]].corr(df[chain[-1]])
print(f"""
Two relationships actually visible in the chart:
  1. {chain[0]} <-> {chain[1]}: r={r1:.2f} -- the first and second axes, adjacent by
     construction (the strongest pair in the whole table).
  2. {chain[-2]} <-> {chain[-1]}: r={r2:.2f} -- the last two axes, the weakest link in the
     chain but still the best available once the stronger pairs are used up.
""")

print(f"Figure saved -> {OUT / 'partD_pcp.png'} (300 dpi)")
print("=" * 70)
print("End of Part D2")
print("=" * 70)
