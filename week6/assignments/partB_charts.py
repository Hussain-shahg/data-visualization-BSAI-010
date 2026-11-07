"""
Week 6 - Task B: three charts, three different questions.

Uses the CLEANED files from clean/ (written by partA_process.py), never the
raw data directly.

Run from week6/assignments/:
    python partB_charts.py
Produces: charts/partB_1.png (trend), partB_2.png (composition/hierarchy),
          partB_3.png (comparison)
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib

vizlib.style_defaults()
CLEAN = pathlib.Path(__file__).parent / "clean"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("TASK B -- three charts, three questions")
print("=" * 70)

# ══════════════════════════════════════════════════════════════════════
# Chart 1 -- TREND: is the network's reliability improving? (grid_daily)
# Monthly outage rate (minutes per zone-day), 7-zone... err 6-zone network,
# with the partial final month marked.
# ══════════════════════════════════════════════════════════════════════
gd = pd.read_csv(CLEAN / "grid_daily.csv", parse_dates=["date"])
monthly = gd.set_index("date")["outage_minutes"].resample("MS").mean()
counts = gd.set_index("date")["outage_minutes"].resample("MS").size()
full_month_size = counts.iloc[1:-1].median()
partial = counts < 0.5 * full_month_size

fig, ax = plt.subplots(figsize=(8, 4.5))
colors = [vizlib.PALETTE["muted"] if p else vizlib.PALETTE["series"][0] for p in partial]
ax.bar(monthly.index, monthly.to_numpy(), width=20, color=colors)
roll = monthly.rolling(3, center=True, min_periods=2).mean()
ax.plot(roll.index, roll.to_numpy(), color=vizlib.PALETTE["highlight"], lw=1.8,
        label="3-month rolling mean")
ax.set_ylim(0)
ax.set_xlabel("Month")
ax.set_ylabel("Mean outage minutes per zone-day")
ax.set_title("Monthly mean outage length is flat, not improving -- no seasonal trend\n"
             "(grey bar = partial month, fewer than half the usual zone-day rows)", loc="left")
ax.legend(frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
vizlib.save_fig(fig, OUT / "partB_1.png",
                note=f"Decision supported: whether reliability is trending | "
                     f"Source: clean/grid_daily.csv | monthly mean of outage_minutes | "
                     f"aggregation: mean (not sum, outage_minutes is per-day) | "
                     f"partial final month ({monthly.index[-1].strftime('%Y-%m')}) shown in grey")
plt.close(fig)
print(f"Chart 1 (trend) saved: {len(monthly)} months, partial months: "
      f"{monthly.index[partial].strftime('%Y-%m').tolist()}")

# ══════════════════════════════════════════════════════════════════════
# Chart 2 -- COMPOSITION/HIERARCHY: is the shift to renewables real?
# (generation_mix) -- stacked area of source share over time.
# ══════════════════════════════════════════════════════════════════════
gm = pd.read_csv(CLEAN / "generation_mix.csv")
by_source = gm.groupby(["month", "source"])["mwh"].sum().unstack("source")
by_source = by_source.sort_index()
share = by_source.div(by_source.sum(axis=1), axis=0) * 100
order = ["Fossil", "Hydro", "Imported", "Renewable"]
share = share[order]

fig, ax = plt.subplots(figsize=(8.5, 4.5))
ax.stackplot(share.index, [share[c] for c in order], labels=order,
            colors=vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]])
ax.set_ylim(0, 100)
ax.set_xticks(range(0, len(share), 3))
ax.set_xticklabels(share.index[::3], rotation=45, ha="right", fontsize=7)
ax.set_ylabel("Share of monthly generation (%)")
ax.set_title("Renewable's share of the mix has grown -- but check the MWh, not just the share",
             loc="left")
ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(rect=[0, 0, 0.85, 1])
vizlib.save_fig(fig, OUT / "partB_2.png",
                note=f"Decision supported: whether the renewables shift is real, by share | "
                     f"Source: clean/generation_mix.csv | {share.index[0]} to {share.index[-1]}, "
                     f"'All sources' total row excluded from every sum")
plt.close(fig)

gen_start, gen_end = by_source.sum(axis=1).iloc[0], by_source.sum(axis=1).iloc[-1]
gen_pct = (gen_end - gen_start) / gen_start * 100
by_sub = gm.groupby(["month", "subsource"])["mwh"].sum().unstack("subsource").sort_index()
solar_start, solar_end = by_sub["Solar"].iloc[0], by_sub["Solar"].iloc[-1]
solar_pct = (solar_end - solar_start) / solar_start * 100
solar_share = by_sub["Solar"] / by_source.sum(axis=1) * 100
print(f"Chart 2 (composition) saved: total generation {gen_pct:+.1f}%, "
      f"solar MWh {solar_pct:+.1f}%, solar share of mix {solar_share.iloc[0]:.1f}% -> "
      f"{solar_share.iloc[-1]:.1f}%")

# ══════════════════════════════════════════════════════════════════════
# Chart 3 -- COMPARISON: which zones carry the network? (district_grid,
# aggregated to zone, sorted bars of solar capacity per 1,000 households)
# ══════════════════════════════════════════════════════════════════════
dg = pd.read_csv(CLEAN / "district_grid.csv")
by_zone = dg.groupby("zone").agg(solar_kw=("solar_kw_installed", "sum"),
                                 households=("households", "sum"),
                                 districts=("code", "count"))
by_zone["solar_per_1k_hh"] = by_zone["solar_kw"] / by_zone["households"] * 1000
by_zone = by_zone.sort_values("solar_per_1k_hh")

fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.barh(by_zone.index, by_zone["solar_per_1k_hh"], color=vizlib.PALETTE["series"][2])
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
ax.set_xlabel("Rooftop solar capacity per 1,000 households (kW)")
ax.set_title("Rooftop solar penetration varies 2-3x across the six supply zones", loc="left")
ax.spines[["top", "right"]].set_visible(False)
vizlib.save_fig(fig, OUT / "partB_3.png",
                note=f"Decision supported: where to prioritise rooftop-solar incentive spend | "
                     f"Source: clean/district_grid.csv | solar_kw_installed and households summed "
                     f"per zone, normalised per 1,000 households ({by_zone['districts'].sum()} districts, 6 zones)")
plt.close(fig)
print(f"Chart 3 (comparison) saved: solar per 1k households ranges "
      f"{by_zone['solar_per_1k_hh'].min():.0f} to {by_zone['solar_per_1k_hh'].max():.0f} kW across zones")

print("\n" + "=" * 70)
print("End of Task B")
print("=" * 70)
