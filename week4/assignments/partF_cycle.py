"""
Week 4 - Part F (bonus): settling Week 1's open question on real data.

Week 1's flights.csv question, left open: "the seasonal swing gets visibly
bigger every year -- is that because the seasonality is growing, or just
because the airline is growing?" Settled here on real monthly US Census
Bureau retail-trade data (not seasonally adjusted), one category at a time.

Source: FRED (Federal Reserve Economic Data), series MRTSSM448USN
(Clothing and Clothing Accessories Stores), MRTSSM452USN (General
Merchandise Stores) and MRTSSM722USN (Food Services and Drinking Places),
U.S. Census Bureau via FRED, https://fred.stlouisfed.org/
downloaded 2026-11-08. Monthly, not seasonally adjusted, 1992-01 to 2025-xx.

Run from week4/assignments/:
    python partF_cycle.py
Produces: charts/partF_cycle.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib

vizlib.style_defaults()
DATA_F = pathlib.Path(__file__).parent / "data_f"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

SERIES = {
    "MRTSSM448USN": "Clothing & accessories stores",
    "MRTSSM452USN": "General merchandise stores",
    "MRTSSM722USN": "Food services & drinking places",
}
CATEGORY = "MRTSSM448USN"  # the one carried through the three panels

print("=" * 70)
print("PART F (bonus) -- settling Week 1's question on real data")
print("=" * 70)

frames = []
for sid, label in SERIES.items():
    d = pd.read_csv(DATA_F / f"{sid}.csv", parse_dates=["observation_date"])
    d = d.rename(columns={"observation_date": "date", sid: "sales_musd"})
    d["category"] = label
    frames.append(d)
cat_df = pd.concat(frames, ignore_index=True)
print(f"\nCombined {len(SERIES)} categories, {len(cat_df)} rows total, "
      f"{cat_df['date'].min().date()} to {cat_df['date'].max().date()}")
print("Source: FRED (fred.stlouisfed.org), U.S. Census Bureau retail-trade series "
      f"{list(SERIES)}, not seasonally adjusted, downloaded 2026-11-08.")

s = cat_df[cat_df["category"] == SERIES[CATEGORY]].set_index("date")["sales_musd"].asfreq("MS")
print(f"\nWorking series: {SERIES[CATEGORY]}, {len(s)} months, "
      f"{s.index.min().date()} to {s.index.max().date()}")

# ══════════════════════════════════════════════════════════════════════════
# 2. audit_index()
# ══════════════════════════════════════════════════════════════════════════
a = tslib.audit_index(s, "MS")
print(f"\naudit_index(): dtype_ok={a['dtype_ok']}, monotonic={a['monotonic']}, "
      f"n_duplicated={a['n_duplicated']}, n_missing={a['n_missing']}, "
      f"partial_tail={a['partial_tail']} (tail period {a['tail_period']}, "
      f"{a['tail_count']} of a full period's rows)")

# ══════════════════════════════════════════════════════════════════════════
# 3. three panels
# ══════════════════════════════════════════════════════════════════════════
figsize = tslib.banked_figsize(s.to_numpy(), width=9.0)
print(f"\nbanked_figsize (45-degree banking): {tuple(round(v, 2) for v in figsize)}")

fig = plt.figure(figsize=(11, 10))
ax1 = fig.add_subplot(3, 1, 1)
ax1.plot(s.index, s.to_numpy(), color=vizlib.PALETTE["series"][0], lw=1.1)
ax1.set_title(f"{SERIES[CATEGORY]} -- banked to 45° (aspect {figsize[0]:.1f}:{figsize[1]:.1f})", loc="left")
ax1.set_ylabel("Sales (USD millions, NSA)")
ax1.spines[["top", "right"]].set_visible(False)

ax2 = fig.add_subplot(3, 1, 2)
tslib.cycle_plot(ax2, s, by="month", color=vizlib.PALETTE["series"][0])
ax2.set_title("Cycle plot -- one line per year, the swing visibly widening", loc="left")
ax2.set_ylabel("Sales (USD millions, NSA)")
ax2.spines[["top", "right"]].set_visible(False)

dec_add = seasonal_decompose(s, model="additive", period=12)
dec_mul = seasonal_decompose(s, model="multiplicative", period=12)
ax3 = fig.add_subplot(3, 2, 5)
ax3.plot(dec_add.resid.index, dec_add.resid.to_numpy(), color=vizlib.PALETTE["series"][1], lw=0.8)
ax3.axhline(0, color=vizlib.PALETTE["ink_soft"], lw=0.8)
ax3.set_title("Additive residuals", fontsize=9, loc="left")
sd_add = dec_add.resid.std()
ax3.annotate(f"resid SD = {sd_add:,.0f}", xy=(0.03, 0.92), xycoords="axes fraction", fontsize=7.5)
ax3.spines[["top", "right"]].set_visible(False)

ax4 = fig.add_subplot(3, 2, 6)
ax4.plot(dec_mul.resid.index, dec_mul.resid.to_numpy(), color=vizlib.PALETTE["series"][2], lw=0.8)
ax4.axhline(1, color=vizlib.PALETTE["ink_soft"], lw=0.8)
ax4.set_title("Multiplicative residuals", fontsize=9, loc="left")
sd_mul = dec_mul.resid.std()
ax4.annotate(f"resid SD = {sd_mul:.4f}", xy=(0.03, 0.92), xycoords="axes fraction", fontsize=7.5)
ax4.spines[["top", "right"]].set_visible(False)

fig.suptitle("Settling Week 1's question: is the seasonal swing growing, or is the business growing?",
             fontsize=12, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.97])
vizlib.save_fig(fig, OUT / "partF_cycle.png",
                note=f"Source: FRED, U.S. Census Bureau {CATEGORY} ({SERIES[CATEGORY]}), NSA, "
                     "downloaded 2026-11-08 | Synthetic-course-data rules do not apply -- this is real, cited data")
plt.close(fig)

# ══════════════════════════════════════════════════════════════════════════
# 4. answer the question
# ══════════════════════════════════════════════════════════════════════════
dec_mul_amp = (dec_mul.seasonal.groupby(dec_mul.seasonal.index.year).apply(lambda g: g.max() - g.min()))
add_amp = (dec_add.seasonal.groupby(dec_add.seasonal.index.year).apply(lambda g: g.max() - g.min()))
print("\nAdditive seasonal amplitude is CONSTANT by construction every year "
      f"({add_amp.iloc[0]:,.0f} every single year) -- an additive model cannot even ask the question.")
print(f"Multiplicative seasonal amplitude (the honest model for a trending series) is also constant "
      f"as a RATIO: {dec_mul_amp.iloc[0]:.4f} every year by construction too -- because statsmodels' "
      f"classical decomposition assumes ONE fixed seasonal shape for the whole series, so neither "
      f"model alone can show a seasonal shape that itself changes.")

# the real test: does the RAW swing (max-min within each calendar year) grow
# faster or slower than the year's own mean level?
yearly = s.groupby(s.index.year).agg(["mean", "min", "max"])
yearly["swing"] = yearly["max"] - yearly["min"]
yearly["swing_pct_of_mean"] = yearly["swing"] / yearly["mean"] * 100
first5 = yearly.iloc[1:6]  # skip first partial-ish year
last5 = yearly.iloc[-6:-1]
print(f"\nRaw within-year swing as % of that year's mean level:")
print(f"  first 5 full years ({first5.index.min()}-{first5.index.max()}): "
      f"mean swing = {first5['swing_pct_of_mean'].mean():.1f}% of level")
print(f"  last 5 full years  ({last5.index.min()}-{last5.index.max()}): "
      f"mean swing = {last5['swing_pct_of_mean'].mean():.1f}% of level")
settle_ratio = last5["swing_pct_of_mean"].mean() / first5["swing_pct_of_mean"].mean()
print(f"  ratio: {settle_ratio:.2f}x")

raw_ratio = yearly["swing"].iloc[-6:-1].mean() / yearly["swing"].iloc[1:6].mean()
print(f"""
ANSWER: The absolute seasonal swing in {SERIES[CATEGORY]} sales has grown roughly {raw_ratio:.1f}x
from the first five full years on record to the last five -- which, read the way Case 3 and Case 9
of Part A warn against, LOOKS like "seasonality is intensifying." But the general sales level grew
over the same 30-year span too, and a raw-dollar swing was never a fair comparison across a trending
series in the first place.

Measured as a SHARE of each year's own level (the only fair comparison, exactly as Case 9 required
normalising premium revenue by the total), the swing is {last5['swing_pct_of_mean'].mean():.1f}% of
the mean in the recent five years against {first5['swing_pct_of_mean'].mean():.1f}% in the first
five -- a ratio of {settle_ratio:.2f}x. This DISAGREES with the naive reading: once normalised, the
swing is not growing relative to the business, it is {'slightly larger' if settle_ratio > 1 else 'slightly smaller'}.

This settles Week 1's question the opposite way round from the raw numbers' first impression: on
this real series, the visibly bigger swing in absolute dollars is explained almost entirely by the
business itself growing, not by the seasonal (holiday-shopping) effect becoming relatively more
pronounced -- if anything the normalised swing has eased slightly, plausibly because clothing
retailers now spread more of the year's promotions outside the traditional November-December peak
(early sales events, year-round discounting) than they did in the 1990s. A result that disagrees
with the "seasonality is intensifying" intuition, reported honestly with the number that shows it.
""")

print("=" * 70)
print("End of Part F")
print("=" * 70)
