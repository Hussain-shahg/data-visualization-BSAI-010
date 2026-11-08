"""
Week 7 - Task D: the one screen.

One figure, 3-6 panels, for the three readers in the case: the Secretary
(30 seconds, top-left), the finance director (filters to one mode), and a
journalist (sent the link). Answers the board's three questions and puts
the reversal directly beside the headline that needs it.

Run from week7/assignments/:
    python partD_screen.py
Produces: charts/partD_screen.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import dashlib
import geolib

vizlib.style_defaults()
CLEAN = pathlib.Path(__file__).parent / "clean"
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("TASK D -- the one screen")
print("=" * 70)

rd = pd.read_csv(CLEAN / "ridership_daily.csv", parse_dates=["date"])
q2_2025 = rd[(rd["date"] >= "2025-04-01") & (rd["date"] <= "2025-06-30")]
q2_2026 = rd[(rd["date"] >= "2026-04-01") & (rd["date"] <= "2026-06-30")]
dec = dashlib.rate_decomposition(q2_2025, q2_2026, "mode", "trips_on_time", "trips_operated")
print(f"Network on-time: {dec['rate_before']:.2f}% -> {dec['rate_after']:.2f}% "
      f"({dec['change']:+.2f} pts)")
print(f"within {dec['within']:+.2f} pts, mix {dec['mix']:+.2f} pts, reversal={dec['reversal']}")
print(dec["groups"][["rate_before", "rate_after", "delta", "share_before", "share_after"]].round(2))

# ══════════════════════════════════════════════════════════════════════
# Channel plan -- checked BEFORE drawing, per the brief
# ══════════════════════════════════════════════════════════════════════
panels_spec = [
    {"panel": "kpi", "y": "on_time_pct"},
    {"panel": "modes", "x": "quarter", "y": "on_time_pct", "hue": "mode"},
    {"panel": "mix", "x": "mode", "y": "share", "hue": "mode"},
    {"panel": "map", "lightness": "boardings_per_1k"},
    {"panel": "fare", "x": "month", "y": "pct_change", "shape": "series"},
]
cc = dashlib.channel_conflicts(panels_spec)
print(f"\nchannel_conflicts(): ok={cc['ok']}, conflicts={cc['conflicts']}")
print(f"redundant (deliberate): {cc['redundant']}")
assert cc["ok"], "fix the channel plan before drawing"

PALETTE_USED = vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]]
vizlib.cvd_report(PALETTE_USED, "deutan")

# ══════════════════════════════════════════════════════════════════════
# Data for the other panels
# ══════════════════════════════════════════════════════════════════════
dt = pd.read_csv(CLEAN / "district_transit.csv")
feats = geolib.read_geojson(DATA / "regions.geojson")
boardings_rate = dt["boardings_annual"] / dt["population"] * 1000

fr = pd.read_csv(CLEAN / "fare_revenue.csv")
by_month = fr.groupby("month")[["trips", "revenue_pkr"]].sum().sort_index()
by_month = by_month[(by_month.index >= "2025-04") & (by_month.index <= "2026-08")]
j_idx = by_month["trips"] / by_month["trips"].iloc[0] * 100
r_idx = by_month["revenue_pkr"] / by_month["revenue_pkr"].iloc[0] * 100

colors = dict(zip(["Metro", "BRT", "Bus", "Ferry"], PALETTE_USED))

# ══════════════════════════════════════════════════════════════════════
# Build the screen
# ══════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(14, 9))
axd = dashlib.dashboard_grid(
    fig,
    [["kpi", "modes", "modes"],
     ["mix", "map", "fare"]],
    headline="Punctuality improved +1.73 pts network-wide -- but every single mode got worse",
    standfirst="For the Board | 2025 Q2 vs 2026 Q2 | unit: on-time departures / operated departures, "
              "never a mean of daily percentages | the rise is a mix shift (more Metro, less Bus), not a real gain",
    height_ratios=[1.0, 1.25],
)

dashlib.kpi_tile(axd["kpi"], "network on-time", dec["rate_after"], delta=dec["change"],
                 note="vs 2025 Q2, same quarter last year", fmt="{:.2f}%", good="up")

for mode in ["Metro", "BRT", "Bus", "Ferry"]:
    row = dec["groups"].loc[mode]
    axd["modes"].plot([0, 1], [row["rate_before"], row["rate_after"]], marker="o",
                      color=colors[mode], lw=2.2, label=f"{mode} ({row['delta']:+.2f})")
axd["modes"].set_xlim(-0.15, 1.3)
axd["modes"].set_xticks([0, 1])
axd["modes"].set_xticklabels(["2025 Q2", "2026 Q2"])
axd["modes"].set_ylabel("On-time (%)")
axd["modes"].set_title("THE REVERSAL: every mode's own punctuality fell", loc="left", fontsize=11)
axd["modes"].legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.01, 0.5))
axd["modes"].spines[["top", "right"]].set_visible(False)

share_df = dec["groups"][["share_before", "share_after"]]
x = np.arange(4)
w = 0.35
axd["mix"].bar(x - w / 2, share_df["share_before"], width=w, color=vizlib.PALETTE["muted"],
               label="2025 Q2")
axd["mix"].bar(x + w / 2, share_df["share_after"], width=w, color=vizlib.PALETTE["highlight"],
               label="2026 Q2")
axd["mix"].set_xticks(x)
axd["mix"].set_xticklabels(share_df.index)
axd["mix"].set_ylabel("Share of departures (%)")
axd["mix"].set_title(f"WHY: Metro's share {share_df.loc['Metro','share_before']:.0f}%->"
                     f"{share_df.loc['Metro','share_after']:.0f}%, Bus's "
                     f"{share_df.loc['Bus','share_before']:.0f}%->{share_df.loc['Bus','share_after']:.0f}%",
                     loc="left", fontsize=10)
axd["mix"].legend(frameon=False, fontsize=7.5)
axd["mix"].spines[["top", "right"]].set_visible(False)

geolib.choropleth(axd["map"], feats, dict(zip(dt["code"], boardings_rate)), scheme="natural", k=5,
                  legend_title="Boardings per\n1,000 residents", legend_loc="lower left",
                  legend_anchor=(0.0, 0.0))
axd["map"].set_title("Next corridor: per-capita", fontsize=10, loc="left")

# Journeys/Revenue distinguished by LINE STYLE + direct end-labels, not by
# hue -- hue already carries "mode" on three other panels of this screen,
# and reusing it here for a different meaning is exactly what
# channel_conflicts() is for catching.
axd["fare"].plot(range(len(j_idx)), j_idx.to_numpy(), color=vizlib.PALETTE["ink"],
                 lw=2, ls="-")
axd["fare"].plot(range(len(r_idx)), r_idx.to_numpy(), color=vizlib.PALETTE["ink"],
                 lw=2, ls="--")
axd["fare"].annotate(f"Journeys +{j_idx.iloc[-1]-100:.0f}%", xy=(len(j_idx) - 1, j_idx.iloc[-1]),
                     xytext=(4, 0), textcoords="offset points", fontsize=8, va="center")
axd["fare"].annotate(f"Revenue +{r_idx.iloc[-1]-100:.0f}%", xy=(len(r_idx) - 1, r_idx.iloc[-1]),
                     xytext=(4, 0), textcoords="offset points", fontsize=8, va="center")
axd["fare"].set_xlim(0, len(j_idx) + 2.2)
axd["fare"].set_xticks([0, len(j_idx) - 1])
axd["fare"].set_xticklabels([by_month.index[0], by_month.index[-1]])
axd["fare"].set_ylabel("Index (2025-04 = 100)")
axd["fare"].set_title("Farebox: revenue 2x journeys", fontsize=10, loc="left")
axd["fare"].spines[["top", "right"]].set_visible(False)

note = (
    f"Source: clean/ridership_daily.csv, clean/district_transit.csv + regions.geojson, "
    f"clean/fare_revenue.csv | within={dec['within']:+.2f}pts, mix={dec['mix']:+.2f}pts "
    f"(dashlib.rate_decomposition) | map: boardings per 1,000 residents, natural breaks k=5, "
    f"equal-area projection | fare index: 2025-04=100 | channel_conflicts() ok, "
    f"cvd_report() checked on the palette used"
)
vizlib.save_fig(fig, OUT / "partD_screen.png", note=note)
plt.close(fig)
print(f"\nFigure saved -> {OUT / 'partD_screen.png'} (300 dpi)")
print("=" * 70)
print("End of Task D")
print("=" * 70)
