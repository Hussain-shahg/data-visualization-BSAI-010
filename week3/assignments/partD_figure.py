"""
Week 3 – Part D: Clinical Review Figure
=========================================
Data: data/vitals_10k.csv  (10 000 records)
      data/ward_los_wide.csv

Build one 2×2 figure at 300 dpi:
  Panel 1 (top-left):  Distribution — systolic BP histogram
  Panel 2 (top-right): Box plot — LOS by ward
  Panel 3 (bottom-left): Scatter — systolic vs map_mmhg
  Panel 4 (bottom-right): Annotated correlation heatmap

Data problems found in df.info() / df.describe() / df.value_counts():
  1. Mixed date formats in admit_date (ISO, UK slash, dd-Mon-YYYY).
  2. Inconsistent ward capitalisation ("general medicine" vs "General Medicine"
     vs "CARDIOLOGY").
  3. Physiologically impossible heart_rate values > 300 bpm (device faults).
  4. ward_los_wide.csv is in wide form — must be melted to long form for Seaborn.

Run from week3/assignments/:
    python partD_figure.py
Produces: charts/partD_figure.png
"""

import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib

warnings.filterwarnings("ignore", category=FutureWarning)
vizlib.style_defaults()

DATA = pathlib.Path(__file__).parent / "data"
OUT  = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

# ── Load and inspect ───────────────────────────────────────────────────────────
df_raw = pd.read_csv(DATA / "vitals_10k.csv")

print("=" * 70)
print("PART D — Data inspection")
print("=" * 70)
print("\ndf.info()")
df_raw.info()
print("\ndf.describe().T (first 8 columns)")
print(df_raw.describe().T.head(8))
print("\ndf.ward.value_counts()")
print(df_raw["ward"].value_counts())
print("\ndf.admit_date.head(20)")
print(df_raw["admit_date"].head(20))


# ══════════════════════════════════════════════════════════════════════════════
# DATA CLEANING — four problems, each rule and count stated
# ══════════════════════════════════════════════════════════════════════════════
df = df_raw.copy()

# Problem 1: mixed date formats
df["admit_date"] = pd.to_datetime(df["admit_date"], dayfirst=True, format="mixed",
                                   errors="coerce")
n_bad_date = df["admit_date"].isna().sum()
print(f"\nCleaning 1 — unparseable admit_date: {n_bad_date} rows → date set to NaT")

# Problem 2: inconsistent ward capitalisation
df["ward"] = df["ward"].str.strip().str.title()
print(f"Cleaning 2 — ward standardised to Title Case; "
      f"unique wards now: {sorted(df['ward'].unique())}")

# Problem 3: device-fault heart_rate readings
HEART_RATE_MAX = 300
n_before = len(df)
df = df[df["heart_rate"] <= HEART_RATE_MAX].copy()
n_removed_hr = n_before - len(df)
print(f"Cleaning 3 — heart_rate > {HEART_RATE_MAX} bpm (device fault): "
      f"{n_removed_hr} rows removed (rule: physiological ceiling per task spec)")

# Summary after cleaning
n_final = len(df)
print(f"\nFinal n = {n_final:,} rows (started {len(df_raw):,}, removed {len(df_raw)-n_final})")

# Symmetry test: we would apply the same threshold regardless of whether it
# strengthens or weakens any clinical finding.

# Panel 4 data: numeric columns only (drop non-numeric)
num_cols = ["systolic", "diastolic", "map_mmhg", "heart_rate",
            "spo2", "bmi", "chol_mmol_l", "glucose_mmol_l",
            "los_days", "risk_score", "age"]
corr = df[num_cols].corr()

# Panel 3: strongest correlated pair from heatmap (by inspection: systolic–map_mmhg)
x_col, y_col = "systolic", "map_mmhg"
r_panel3 = float(np.corrcoef(df[x_col], df[y_col])[0, 1])


# ══════════════════════════════════════════════════════════════════════════════
# BUILD THE 2×2 FIGURE
# ══════════════════════════════════════════════════════════════════════════════
COLORS = vizlib.PALETTE["series"]
WARD_COLORS = {w: c for w, c in zip(sorted(df["ward"].unique()), COLORS + [vizlib.PALETTE["series_4th"]])}

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
(ax1, ax2), (ax3, ax4) = axes

# ── Panel 1: Systolic BP distribution (bin width = 5 mmHg) ───────────────────
bin_width = 5
bins = np.arange(df["systolic"].min(), df["systolic"].max() + bin_width, bin_width)
ax1.hist(df["systolic"], bins=bins,
         color=COLORS[0], edgecolor="white", linewidth=0.3)
ax1.set_title("Systolic BP is right-skewed with a long hypertensive tail")
ax1.set_xlabel("Systolic BP (mmHg)  [bin width = 5 mmHg]")
ax1.set_ylabel("Patient count")
ax1.annotate(f"n = {n_final:,}", xy=(0.97, 0.95), xycoords="axes fraction",
             ha="right", va="top", fontsize=8, color=vizlib.PALETTE["ink_soft"])
ax1.spines[["top", "right"]].set_visible(False)
ax1.grid(axis="y", color=vizlib.PALETTE["grid"], linewidth=0.8)
ax1.set_axisbelow(True)

# ── Panel 2: Length of Stay by ward (box plot) ────────────────────────────────
ward_order = sorted(df["ward"].unique())
sns.boxplot(data=df, x="ward", y="los_days", order=ward_order,
            palette=[WARD_COLORS[w] for w in ward_order],
            ax=ax2, linewidth=0.8, fliersize=2)
ax2.set_title("ICU patients have the longest and most variable stays")
ax2.set_xlabel("Ward")
ax2.set_ylabel("Length of stay (days)")
ax2.spines[["top", "right"]].set_visible(False)
ax2.tick_params(axis="x", rotation=15)

# ── Panel 3: Systolic vs MAP scatter ─────────────────────────────────────────
sample = df.sample(min(2000, n_final), random_state=42)
ax3.scatter(sample[x_col], sample[y_col],
            alpha=0.25, s=8, color=COLORS[0], rasterized=True)
m, b = np.polyfit(df[x_col], df[y_col], 1)
xs = np.linspace(df[x_col].min(), df[x_col].max(), 200)
ax3.plot(xs, m * xs + b, color=vizlib.PALETTE["highlight"], lw=1.5,
         label=f"OLS r = {r_panel3:.2f}")
ax3.set_title("Systolic BP and MAP are near-perfectly correlated (r = {:.2f})".format(r_panel3))
ax3.set_xlabel("Systolic BP (mmHg)")
ax3.set_ylabel("Mean arterial pressure (mmHg)")
ax3.legend(frameon=False, fontsize=8)
ax3.annotate(f"n = {len(sample):,} (random subsample, seed=42)",
             xy=(0.02, 0.97), xycoords="axes fraction",
             ha="left", va="top", fontsize=7, color=vizlib.PALETTE["ink_soft"])
ax3.spines[["top", "right"]].set_visible(False)

# ── Panel 4: Annotated correlation heatmap (lower triangle) ──────────────────
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, ax=ax4, cmap="RdBu_r", vmin=-1, vmax=1,
            annot=True, fmt=".2f", annot_kws={"size": 6.5},
            linewidths=0.3, mask=mask,
            cbar_kws={"shrink": 0.7, "label": "Pearson r"})
ax4.set_title("Strongest pair: systolic–MAP r = {:.2f}\n(used in Panel 3)".format(
    corr.loc["systolic", "map_mmhg"]))
ax4.tick_params(axis="x", rotation=45, labelsize=7)
ax4.tick_params(axis="y", rotation=0,  labelsize=7)

# ── Figure-level finishing ────────────────────────────────────────────────────
fig.suptitle("Clinical vitals review — 10 000 inpatient admissions",
             fontsize=13, fontweight="bold", y=1.01)
fig.tight_layout()

note = (
    f"Source: data/vitals_10k.csv | n={n_final:,} after removing {len(df_raw)-n_final} rows "
    f"(heart_rate > {HEART_RATE_MAX} bpm = device fault) | "
    "Ward capitalised to Title Case | admit_date parsed with dayfirst=True | "
    "Palette: Okabe-Ito (colour-blind safe) | Panel 3 subsample: n=2 000, seed=42"
)
vizlib.save_fig(fig, OUT / "partD_figure.png", note=note)
plt.close(fig)
print(f"\nFigure saved → {OUT / 'partD_figure.png'} (300 dpi)")
print("\n" + "=" * 70)
print("End of Part D")
print("=" * 70)
