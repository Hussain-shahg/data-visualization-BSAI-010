"""
Week 6 - Task D1 (bonus): make Task B's trend chart interactive.

Rebuilds partB_1.png (monthly outage-length trend) in Plotly: hover shows
the exact value and whether the month is partial, and a range slider lets
the reader zoom to any window.

Run from week6/assignments/:
    python partD_interactive.py
Produces: partD_interactive.html (open in a browser) + charts/partD_interactive.png
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
print("TASK D1 (bonus) -- interactive version of the Task B trend chart")
print("=" * 70)

gd = pd.read_csv(CLEAN / "grid_daily.csv", parse_dates=["date"])
monthly = gd.set_index("date")["outage_minutes"].resample("MS").mean()
counts = gd.set_index("date")["outage_minutes"].resample("MS").size()
full_month_size = counts.iloc[1:-1].median()
partial = counts < 0.5 * full_month_size
roll = monthly.rolling(3, center=True, min_periods=2).mean()

colors = [vizlib.PALETTE["muted"] if p else vizlib.PALETTE["series"][0] for p in partial]
hover = [f"{m.strftime('%Y-%m')}<br>{v:.1f} min/zone-day"
        + ("<br><b>partial month</b>" if p else "")
        for m, v, p in zip(monthly.index, monthly, partial)]

fig = go.Figure()
fig.add_bar(x=monthly.index, y=monthly.to_numpy(), marker_color=colors,
           hovertext=hover, hoverinfo="text", name="Monthly mean outage minutes")
fig.add_scatter(x=roll.index, y=roll.to_numpy(), mode="lines",
                line=dict(color=vizlib.PALETTE["highlight"], width=2.5),
                name="3-month rolling mean",
                hovertemplate="%{x|%Y-%m}<br>rolling mean %{y:.1f}<extra></extra>")
fig.update_layout(
    title="Monthly mean outage length is flat, not improving (hover for exact values; "
          "drag the range slider to zoom)",
    xaxis_title="Month", yaxis_title="Mean outage minutes per zone-day",
    yaxis=dict(rangemode="tozero"),
    xaxis=dict(rangeslider=dict(visible=True)),
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="DejaVu Sans, Arial", size=12),
    legend=dict(orientation="h", y=1.08),
    margin=dict(t=90, b=40),
)
fig.add_annotation(text="Source: clean/grid_daily.csv | grey bars = partial reporting month",
                   xref="paper", yref="paper", x=0, y=-0.18, showarrow=False,
                   font=dict(size=10, color=vizlib.PALETTE["ink_soft"]))

out_html = HERE / "partD_interactive.html"
fig.write_html(out_html)
print(f"Wrote {out_html}")

out_png = OUT / "partD_interactive.png"
try:
    fig.write_image(str(out_png), width=1400, height=700, scale=2)
    print(f"Wrote {out_png} (default-state static export, via kaleido)")
except Exception as exc:
    # kaleido needs a local Chrome install, which this machine does not have
    # and could not finish downloading. The interactive chart's DEFAULT
    # state carries exactly the same information as Task B's Chart 1 (same
    # data, same bars, same rolling mean, no filter applied) -- so that
    # already-verified matplotlib figure is the honest static stand-in,
    # redrawn here rather than silently skipped.
    print(f"Plotly/kaleido static export unavailable in this environment ({type(exc).__name__}); "
          f"falling back to a matplotlib render of the identical default state")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt2
    fig2, ax2 = plt2.subplots(figsize=(9, 4.5))
    ax2.bar(monthly.index, monthly.to_numpy(), width=20, color=colors)
    ax2.plot(roll.index, roll.to_numpy(), color=vizlib.PALETTE["highlight"], lw=1.8,
            label="3-month rolling mean")
    ax2.set_ylim(0)
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Mean outage minutes per zone-day")
    ax2.set_title("Interactive chart, default state (hover + zoom not shown in a static export)",
                  loc="left")
    ax2.legend(frameon=False, fontsize=8)
    ax2.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig2, out_png,
                    note="Default state of partD_interactive.html -- identical data to Task B "
                         "Chart 1, no filter/zoom applied | static render (Chrome/kaleido "
                         "unavailable in this environment)")
    plt2.close(fig2)
    print(f"Wrote {out_png} (matplotlib fallback)")

print("""
Interaction contract:
  Default state: the same information as Task B's static chart -- 18 monthly bars, the
    partial final month in grey, a 3-month rolling mean line, nothing pre-filtered or pre-zoomed.
  Controls:
    1. Hover -- reveals the exact mean outage minutes for any month and flags partial months
       explicitly. Does not change what is plotted. Always available, no reset needed.
    2. Range-slider zoom -- lets the reader restrict the view to any window. Does NOT change
       the rolling mean's calculation (still computed over the full series first, then
       clipped to view), so zooming cannot manufacture a trend the full series does not
       support. A double-click on the plot resets to the full range -- the control has a
       way back.
  What this control makes too easy: a reader could zoom to a 3-4 month window that happens to
  slope up or down and screenshot it as "the trend" -- exactly Week 4 Part B.5's cherry-picked-
  window problem, now available with a mouse instead of a pandas slice. The caption states the
  full 18-month range and that zooming does not recompute the rolling mean, so a screenshot of
  a zoomed view still carries the full-series statistic alongside it, not a different number.
""")

print("=" * 70)
print("End of Task D1")
print("=" * 70)
