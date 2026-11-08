"""
Week 7 - Task C: make it interactive, and write the contract.

Rebuilds partB_1.png (monthly punctuality by mode) in Plotly: hover for
exact values, legend-click to isolate one mode, a date-range slider to
zoom -- all declared in the interaction contract (partC_contract.md).

Run from week7/assignments/:
    python partC_interactive.py
Produces: partC_interactive.html + charts/partC_default.png
"""
import pathlib
import sys

import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib

CLEAN = pathlib.Path(__file__).parent / "clean"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)
HERE = pathlib.Path(__file__).parent

print("=" * 70)
print("TASK C -- make it interactive, and write the contract")
print("=" * 70)

rd = pd.read_csv(CLEAN / "ridership_daily.csv", parse_dates=["date"])
monthly = rd.groupby([rd["date"].dt.to_period("M"), "mode"]).agg(
    on_time=("trips_on_time", "sum"), operated=("trips_operated", "sum")).reset_index()
monthly["punctuality"] = monthly["on_time"] / monthly["operated"] * 100
piv = monthly.pivot(index="date", columns="mode", values="punctuality")
piv.index = piv.index.to_timestamp()

colors = dict(zip(["Metro", "BRT", "Bus", "Ferry"],
                  vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]]))

fig = go.Figure()
for mode in ["Metro", "BRT", "Bus", "Ferry"]:
    s = piv[mode].dropna()
    fig.add_scatter(x=s.index, y=s.to_numpy(), mode="lines+markers", name=mode,
                    line=dict(color=colors[mode], width=2.5), marker=dict(size=5),
                    hovertemplate=f"{mode}<br>%{{x|%Y-%m}}: %{{y:.1f}}%<extra></extra>")
fig.add_shape(type="line", x0="2026-09-22", x1="2026-09-22", y0=0, y1=100,
             line=dict(color="#5B6573", dash="dot", width=1))
fig.add_annotation(x="2026-09-22", y=70, text="Bus & Ferry<br>stop reporting",
                   showarrow=False, xanchor="left", font=dict(size=10, color="#5B6573"))
fig.update_layout(
    title="Monthly punctuality by mode (click a legend entry to isolate it; drag to zoom)",
    xaxis_title="Month", yaxis_title="Punctuality (%)",
    yaxis=dict(range=[0, 100]),
    xaxis=dict(rangeslider=dict(visible=True)),
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="DejaVu Sans, Arial", size=12),
    legend=dict(orientation="h", y=1.1),
    margin=dict(t=90, b=40),
)
fig.add_annotation(text="Source: clean/ridership_daily.csv | punctuality = sum(on_time)/sum(operated) per month, "
                        "never a mean of daily percentages",
                   xref="paper", yref="paper", x=0, y=-0.2, showarrow=False,
                   font=dict(size=10, color=vizlib.PALETTE["ink_soft"]))

out_html = HERE / "partC_interactive.html"
fig.write_html(out_html)
print(f"Wrote {out_html}")

# Static default-state export (matplotlib fallback -- see Week 6's Task D1
# for why: kaleido needs a local Chrome install this environment could not
# complete)
out_png = OUT / "partC_default.png"
try:
    fig.write_image(str(out_png), width=1400, height=700, scale=2)
    print(f"Wrote {out_png} (via kaleido)")
except Exception as exc:
    print(f"kaleido unavailable ({type(exc).__name__}); matplotlib fallback for the default state")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig2, ax = plt.subplots(figsize=(9, 4.5))
    for mode in ["Metro", "BRT", "Bus", "Ferry"]:
        s = piv[mode].dropna()
        ax.plot(s.index, s.to_numpy(), color=colors[mode], marker="o", ms=3, lw=1.5, label=mode)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Month")
    ax.set_ylabel("Punctuality (%)")
    ax.set_title("Interactive chart, default state (legend-click and zoom not shown in a static export)",
                loc="left")
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="lower center")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig2, out_png,
                    note="Default state of partC_interactive.html -- identical to Task B Chart 1 | "
                         "static render (Chrome/kaleido unavailable in this environment)")
    plt.close(fig2)
    print(f"Wrote {out_png} (matplotlib fallback)")

print("""
Interaction contract (see partC_contract.md for the written version):
  Default state: all 4 modes' monthly punctuality, full date range, nothing isolated or zoomed
    -- the same information as Task B's static Chart 1.
  Controls: hover (exact values, no filter), legend-click (isolate/restore one mode's line,
    always has a click-back), date-range slider (zoom, does not change how monthly punctuality
    itself is computed -- still sum(on_time)/sum(operated) over whichever months are in view,
    never a mean of means).
  What it makes too easy: a reader could click Bus alone, zoom to its worst 3 months, and
  conclude the network is failing -- missing that Bus also carries the fewest riders of the
  surface modes and that Metro (the mode carrying the plurality of journeys) stays >94%
  throughout. The caption states the computation rule so a screenshot still carries it.
""")

print("=" * 70)
print("End of Task C")
print("=" * 70)
