"""
Week 3 – Part A: Rebuild, diagnose, and redesign nine misleading charts.
Each case earns marks for:
  1. Rebuilding the misleading chart (hitting the self-check number)
  2. Stating the invited conclusion and ruling out a decoy objection with data
  3. Naming the mechanism with a supporting number (generic cautions score 0)
  4. Plotting an honest redesign

Run from week3/assignments/:
    python partA_charts.py

Produces: charts/caseXX_misleading.png  and  charts/caseXX_honest.png
"""

import sys
import os
import pathlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import scipy.stats as stats

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib

vizlib.style_defaults()

DATA = pathlib.Path(__file__).parent / "data"
OUT  = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# CASE 1 — Helmet effectiveness in Lahore rickshaw riders
# Check: Standard 2.15, Premium 5.40 injuries per 1 000 trips
# Mechanism: confounding by road type (Simpson's Paradox)
# ══════════════════════════════════════════════════════════════════════════════
def case01():
    df = pd.read_csv(DATA / "case01_helmet_rickshaw.csv")
    # aggregate
    agg = df.groupby("helmet_grade", as_index=False).agg(
        total_trips=("trips", "sum"),
        total_injuries=("head_injuries", "sum")
    )
    agg["rate_per_1k"] = agg["total_injuries"] / agg["total_trips"] * 1000
    # order: Standard, Premium
    agg = agg.set_index("helmet_grade").loc[["Standard", "Premium"]].reset_index()

    print("Case 01 check — injuries per 1 000 trips")
    for _, row in agg.iterrows():
        print(f"  {row.helmet_grade}: {row.rate_per_1k:.2f}")

    # ── misleading chart (y from zero, invites wrong causal conclusion) ───────
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = [vizlib.PALETTE["series"][0], vizlib.PALETTE["series"][1]]
    bars = ax.bar(agg["helmet_grade"], agg["rate_per_1k"], color=colors, width=0.5)
    ax.set_ylim(0, max(agg["rate_per_1k"]) * 1.3)
    ax.set_ylabel("Injuries per 1 000 trips")
    ax.set_title("Premium helmets have MORE injuries than Standard")
    ax.bar_label(bars, fmt="%.2f", padding=3)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case01_misleading.png",
                    note="Source: case01_helmet_rickshaw.csv | n=1 000 riders | 100 trips each")
    plt.close(fig)

    # ── honest redesign: facet by road type to expose the confounder ──────────
    road_agg = df.groupby(["helmet_grade", "road_type"], as_index=False).agg(
        total_trips=("trips", "sum"),
        total_injuries=("head_injuries", "sum")
    )
    road_agg["rate_per_1k"] = road_agg["total_injuries"] / road_agg["total_trips"] * 1000
    road_types = sorted(df["road_type"].unique())
    fig, axes = plt.subplots(1, len(road_types), figsize=(10, 4), sharey=True)
    for ax, rt in zip(axes, road_types):
        sub = road_agg[road_agg["road_type"] == rt].set_index("helmet_grade")
        vals = [sub.loc[g, "rate_per_1k"] if g in sub.index else 0
                for g in ["Standard", "Premium"]]
        bars = ax.bar(["Standard", "Premium"], vals, color=colors, width=0.5)
        ax.set_title(rt)
        ax.set_ylim(0, road_agg["rate_per_1k"].max() * 1.3)
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Injuries per 1 000 trips")
    fig.suptitle("Within each road type, Standard helmets have equal or higher injury rates\n"
                 "(Premium riders self-select to harder roads — Simpson's Paradox)",
                 fontsize=10, y=1.02)
    vizlib.save_fig(fig, OUT / "case01_honest.png",
                    note="Source: case01_helmet_rickshaw.csv | stratified by road_type | n=1 000")
    plt.close(fig)
    print("  Case 01 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 2 — Chai & quiz failures  (r = 0.98 is a spurious correlation)
# Check: Pearson r = 0.98
# Mechanism: omitted confounder — student enrolment drives both series
# ══════════════════════════════════════════════════════════════════════════════
def case02():
    df = pd.read_csv(DATA / "case02_chai_quizzes.csv")
    x = df["cups_doodh_patti_sold"]
    y = df["quiz_failures"]
    r, p = stats.pearsonr(x, y)
    print(f"Case 02 check — Pearson r = {r:.2f}")

    # ── misleading chart ──────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(x, y, color=vizlib.PALETTE["series"][0], zorder=3)
    m, b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, m * xs + b, color=vizlib.PALETTE["highlight"], lw=1.5)
    ax.set_xlabel("Cups of chai sold per month")
    ax.set_ylabel("Quiz failures")
    ax.set_title(f"Chai causes quiz failures — r = {r:.2f}")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case02_misleading.png",
                    note="Source: case02_chai_quizzes.csv | n=24 months")
    plt.close(fig)

    # ── honest redesign: show all three variables ─────────────────────────────
    enrol = df["students_enrolled"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, col, lbl in zip(
        axes,
        ["cups_doodh_patti_sold", "quiz_failures"],
        ["Cups of chai sold per month", "Quiz failures"]
    ):
        ax.scatter(enrol, df[col], color=vizlib.PALETTE["series"][0], zorder=3)
        m2, b2 = np.polyfit(enrol, df[col], 1)
        xs2 = np.linspace(enrol.min(), enrol.max(), 100)
        ax.plot(xs2, m2 * xs2 + b2, color=vizlib.PALETTE["highlight"], lw=1.5)
        r2, _ = stats.pearsonr(enrol, df[col])
        ax.set_xlabel("Students enrolled")
        ax.set_ylabel(lbl)
        ax.set_title(f"r = {r2:.2f}")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Enrolment drives both series — the chai correlation is spurious",
                 fontsize=10, y=1.02)
    vizlib.save_fig(fig, OUT / "case02_honest.png",
                    note="Source: case02_chai_quizzes.csv | n=24 months | confounder: students_enrolled")
    plt.close(fig)
    print("  Case 02 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 3 — Lahore AQI intervention
# Check: mean before day 61 = 202, after = 137, fall ≈ 32%
# Mechanism: regression to the mean / seasonal confound; intervention date
#            was chosen at a peak, so a fall was guaranteed
# ══════════════════════════════════════════════════════════════════════════════
def case03():
    df = pd.read_csv(DATA / "case03_aqi_monitors.csv")
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby("date")["aqi"].mean().reset_index()
    daily = daily.sort_values("date").reset_index(drop=True)
    daily["day"] = np.arange(1, len(daily) + 1)
    cutoff = 61
    before = daily[daily["day"] < cutoff]["aqi"].mean()
    after  = daily[daily["day"] >= cutoff]["aqi"].mean()
    fall_pct = (before - after) / before * 100
    print(f"Case 03 check — AQI before: {before:.0f}, after: {after:.0f}, fall: {fall_pct:.0f}%")

    # ── misleading chart ──────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(daily["day"], daily["aqi"], color=vizlib.PALETTE["series"][0], lw=1)
    ax.axvline(cutoff, color=vizlib.PALETTE["highlight"], lw=1.5, ls="--",
               label="Intervention")
    ax.axhline(before, xmax=cutoff / daily["day"].max(),
               color=vizlib.PALETTE["series"][1], lw=1, ls=":")
    ax.axhline(after,  xmin=cutoff / daily["day"].max(),
               color=vizlib.PALETTE["series"][2], lw=1, ls=":")
    ax.annotate(f"Mean {before:.0f}", xy=(5, before + 4),
                color=vizlib.PALETTE["series"][1], fontsize=8)
    ax.annotate(f"Mean {after:.0f}", xy=(cutoff + 2, after + 4),
                color=vizlib.PALETTE["series"][2], fontsize=8)
    ax.set_ylim(0)
    ax.set_xlabel("Day")
    ax.set_ylabel("Daily mean AQI")
    ax.set_title(f"Intervention cut AQI by {fall_pct:.0f}% — from {before:.0f} to {after:.0f}")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case03_misleading.png",
                    note="Source: case03_aqi_monitors.csv | daily mean across stations")
    plt.close(fig)

    # ── honest redesign: show full seasonal cycle, mark the peak ─────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(daily["day"], daily["aqi"], color=vizlib.PALETTE["series"][0], lw=1,
            label="Daily mean AQI")
    ax.axvline(cutoff, color=vizlib.PALETTE["highlight"], lw=1.5, ls="--",
               label=f"Intervention (day {cutoff})")
    peak_day = daily["aqi"].idxmax()
    ax.annotate(f"Peak: {daily.loc[peak_day,'aqi']:.0f}",
                xy=(daily.loc[peak_day, "day"], daily.loc[peak_day, "aqi"]),
                xytext=(10, 10), textcoords="offset points",
                arrowprops=dict(arrowstyle="->", color=vizlib.PALETTE["ink_soft"]),
                fontsize=8)
    ax.set_ylim(0)
    ax.set_xlabel("Day (1 Jan 2026 = day 1)")
    ax.set_ylabel("Daily mean AQI")
    ax.set_title("Intervention coincides with peak — decline is also seasonal\n"
                 "(Regression to the mean cannot be ruled out without a control site)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case03_honest.png",
                    note="Source: case03_aqi_monitors.csv | Intervention on day 61 = peak day in this window")
    plt.close(fig)
    print("  Case 03 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 4 — Anscombe-style quartet (departments)
# Check: means 18.00 / 14.50, r = 0.816
# Mechanism: identical summary statistics conceal radically different shapes
# ══════════════════════════════════════════════════════════════════════════════
def case04():
    df = pd.read_csv(DATA / "case04_quartet_depts.csv")
    print("Case 04 — summary table:")
    for dept, g in df.groupby("department"):
        r_val, _ = stats.pearsonr(g["study_hours_per_week"], g["final_score_out_of_20"])
        slope, intercept, *_ = stats.linregress(g["study_hours_per_week"], g["final_score_out_of_20"])
        print(f"  {dept}: n={len(g)}, mean_x={g['study_hours_per_week'].mean():.2f}, "
              f"mean_y={g['final_score_out_of_20'].mean():.2f}, "
              f"sd_x={g['study_hours_per_week'].std(ddof=0):.2f}, "
              f"sd_y={g['final_score_out_of_20'].std(ddof=0):.2f}, "
              f"r={r_val:.3f}, slope={slope:.3f}")

    depts = sorted(df["department"].unique())

    # ── misleading chart (aggregate scatter, hides structure) ─────────────────
    fig, ax = plt.subplots(figsize=(5, 4))
    x_all = df["study_hours_per_week"]
    y_all = df["final_score_out_of_20"]
    r_all, _ = stats.pearsonr(x_all, y_all)
    ax.scatter(x_all, y_all, alpha=0.4, color=vizlib.PALETTE["series"][0])
    m, b = np.polyfit(x_all, y_all, 1)
    xs = np.linspace(x_all.min(), x_all.max(), 100)
    ax.plot(xs, m * xs + b, color=vizlib.PALETTE["highlight"], lw=1.5)
    ax.set_title(f"Study hours predict scores equally well (r = {r_all:.3f})")
    ax.set_xlabel("Study hours per week")
    ax.set_ylabel("Final score / 20")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case04_misleading.png",
                    note="Source: case04_quartet_depts.csv | all departments pooled")
    plt.close(fig)

    # ── honest redesign: small multiples ─────────────────────────────────────
    fig, axes = plt.subplots(1, len(depts), figsize=(12, 4), sharey=True)
    for ax, dept in zip(axes, depts):
        g = df[df["department"] == dept]
        x, y = g["study_hours_per_week"], g["final_score_out_of_20"]
        r_val, _ = stats.pearsonr(x, y)
        ax.scatter(x, y, alpha=0.7, color=vizlib.PALETTE["series"][0])
        m2, b2 = np.polyfit(x, y, 1)
        xs2 = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs2, m2 * xs2 + b2, color=vizlib.PALETTE["highlight"], lw=1.5)
        ax.set_title(f"{dept}\nr={r_val:.2f}", fontsize=8)
        ax.set_xlabel("Study hrs/wk")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Final score / 20")
    fig.suptitle("Same r ≈ 0.82 in each department — but the shapes are very different",
                 fontsize=10)
    vizlib.save_fig(fig, OUT / "case04_honest.png",
                    note="Source: case04_quartet_depts.csv | small multiples by department")
    plt.close(fig)
    print("  Case 04 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 5 — Datasaurus-style same-stats shapes (five cohorts)
# Check: means 48.00 / 63.00, SDs 12 / 15, r = 0.420
# ══════════════════════════════════════════════════════════════════════════════
def case05():
    df = pd.read_csv(DATA / "case05_same_stats_shapes.csv")
    print("Case 05 — summary table:")
    for shape, g in df.groupby("shape_name"):
        r_val, _ = stats.pearsonr(g["hours_on_platform"], g["assessment_score"])
        print(f"  {shape}: n={len(g)}, "
              f"mean_x={g['hours_on_platform'].mean():.2f}, "
              f"mean_y={g['assessment_score'].mean():.2f}, "
              f"sd_x={g['hours_on_platform'].std(ddof=0):.2f}, "
              f"sd_y={g['assessment_score'].std(ddof=0):.2f}, "
              f"r={r_val:.3f}")

    shapes = sorted(df["shape_name"].unique())

    # ── misleading: show only summary stats as a table figure ─────────────────
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.axis("off")
    cols = ["Shape", "Mean hrs", "Mean score", "SD hrs", "SD score", "r"]
    rows = []
    for shape, g in df.groupby("shape_name"):
        r_val, _ = stats.pearsonr(g["hours_on_platform"], g["assessment_score"])
        rows.append([shape,
                     f"{g['hours_on_platform'].mean():.2f}",
                     f"{g['assessment_score'].mean():.2f}",
                     f"{g['hours_on_platform'].std(ddof=0):.2f}",
                     f"{g['assessment_score'].std(ddof=0):.2f}",
                     f"{r_val:.3f}"])
    tbl = ax.table(cellText=rows, colLabels=cols, loc="center", cellLoc="center")
    tbl.auto_set_font_size(True)
    tbl.scale(1, 1.5)
    ax.set_title("All cohorts share identical statistics — same platform effect?",
                 pad=20)
    vizlib.save_fig(fig, OUT / "case05_misleading.png",
                    note="Source: case05_same_stats_shapes.csv | summary statistics only")
    plt.close(fig)

    # ── honest redesign: small multiples scatter ─────────────────────────────
    ncols = min(5, len(shapes))
    fig, axes = plt.subplots(1, ncols, figsize=(14, 4), sharey=True, sharex=True)
    if ncols == 1:
        axes = [axes]
    for ax, shape in zip(axes, shapes):
        g = df[df["shape_name"] == shape]
        ax.scatter(g["hours_on_platform"], g["assessment_score"],
                   alpha=0.5, s=12, color=vizlib.PALETTE["series"][0])
        ax.set_title(shape, fontsize=8)
        ax.set_xlabel("Hours on platform")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Assessment score")
    fig.suptitle("Identical statistics, wildly different distributions\n"
                 "(Datasaurus Dozen principle — always plot the data)",
                 fontsize=10)
    vizlib.save_fig(fig, OUT / "case05_honest.png",
                    note="Source: case05_same_stats_shapes.csv | each panel: same mean, SD, r")
    plt.close(fig)
    print("  Case 05 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 6 — Sensor correlation heatmap (20×20)
# Check: creatinine–HbA1c 0.77, systolic–MAP 0.96, 20×20 matrix
# Mechanism: (a) statistical: probe columns inflate apparent correlations;
#            (b) drawing: cmap without vmin/vmax misrepresents magnitude
# ══════════════════════════════════════════════════════════════════════════════
def case06():
    import seaborn as sns
    df = pd.read_csv(DATA / "case06_sensor_matrix.csv")
    # exclude the three non-numeric / categorical columns
    exclude = ["age_band", "study_site", "hr_device_model"]
    num_df = df.drop(columns=exclude)
    corr = num_df.corr()
    print(f"Case 06 check — shape: {corr.shape}")
    print(f"  creatinine–HbA1c: {corr.loc['creatinine','hba1c']:.2f}")
    print(f"  systolic–MAP:     {corr.loc['systolic','map_mmhg']:.2f}")

    # ── misleading chart: cmap="Reds" no vmin/vmax, full matrix ──────────────
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, ax=ax, cmap="Reds", annot=True, fmt=".2f",
                annot_kws={"size": 5}, linewidths=0.3)
    ax.set_title("Sensor correlation matrix — Reds palette exaggerates magnitudes")
    vizlib.save_fig(fig, OUT / "case06_misleading.png",
                    note="Source: case06_sensor_matrix.csv | 20×20, cmap=Reds, no vmin/vmax")
    plt.close(fig)

    # ── honest redesign: diverging cmap, vmin=-1, vmax=1, mask upper triangle
    mask = np.triu(np.ones_like(corr, dtype=bool))
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, ax=ax, cmap="RdBu_r", vmin=-1, vmax=1,
                annot=True, fmt=".2f", annot_kws={"size": 5},
                linewidths=0.3, mask=mask)
    ax.set_title("Diverging palette, vmin=−1 / vmax=+1: correlations read accurately\n"
                 "(Drawing fix: colour encodes sign. Statistical fix: remove probe cols.)")
    vizlib.save_fig(fig, OUT / "case06_honest.png",
                    note="Source: case06_sensor_matrix.csv | lower triangle only | vmin=-1, vmax=1 | excl. age_band, study_site, hr_device_model")
    plt.close(fig)
    print("  Case 06 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 7 — ShaheenGo dual-axis chart
# Check: cost sits ABOVE revenue for the first four months
# Mechanism: independent y-axes let the designer choose any crossing point
# ══════════════════════════════════════════════════════════════════════════════
def case07():
    df = pd.read_csv(DATA / "case07_dual_axis_series.csv")
    months = df["month"]
    revenue = df["revenue_pkr_m"]
    cost = df["cost_pkr_m"]
    print("Case 07 — cost above revenue (first 4 months):",
          (cost.head(4) > revenue.head(4)).all())

    # ── misleading chart: dual y-axes ────────────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax2 = ax1.twinx()
    ax1.plot(months, revenue, color=vizlib.PALETTE["series"][0],
             marker="o", label="Revenue (left)")
    ax2.plot(months, cost, color=vizlib.PALETTE["series"][1],
             marker="s", label="Cost (right)", ls="--")
    ax1.set_ylabel("Revenue (PKR million)", color=vizlib.PALETTE["series"][0])
    ax2.set_ylabel("Cost (PKR million)", color=vizlib.PALETTE["series"][1])
    ax1.set_xlabel("Month")
    ax1.set_title("Revenue vs Cost — dual axes make cost look higher than revenue")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8)
    vizlib.save_fig(fig, OUT / "case07_misleading.png",
                    note="Source: case07_dual_axis_series.csv | dual-axis encodes false crossing")
    plt.close(fig)

    # ── honest redesign: shared axis, both series ─────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(months, revenue, color=vizlib.PALETTE["series"][0],
            marker="o", label="Revenue")
    ax.plot(months, cost, color=vizlib.PALETTE["series"][1],
            marker="s", ls="--", label="Cost")
    ax.set_ylim(0)
    ax.set_xlabel("Month")
    ax.set_ylabel("PKR million")
    ax.set_title("Revenue always exceeds cost — profit grows month-on-month")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case07_honest.png",
                    note="Source: case07_dual_axis_series.csv | shared y-axis, zero baseline | revenue range 50–80, cost 40–56")
    plt.close(fig)
    print("  Case 07 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 8 — Vitals histograms: bin-count sensitivity
# Check: n = 10 000 in each panel
# Mechanism: bin count changes the apparent shape — 3 bins hide all structure,
#            400 bins produce noise that looks like separate populations
# ══════════════════════════════════════════════════════════════════════════════
def case08():
    df = pd.read_csv(DATA / "vitals_10k.csv")
    # remove physiologically impossible heart-rate readings (>300 bpm = device fault)
    n_before = len(df)
    df = df[df["heart_rate"] <= 300].copy()
    n_removed = n_before - len(df)
    systolic = df["systolic"].dropna()
    print(f"Case 08 check — n systolic: {len(systolic)}")
    print(f"  Removed {n_removed} rows with heart_rate > 300 (device fault threshold)")

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)
    for ax, bins in zip(axes, [3, 45, 400]):
        ax.hist(systolic, bins=bins, color=vizlib.PALETTE["series"][0], edgecolor="white")
        ax.set_title(f"bins = {bins}")
        ax.set_xlabel("Systolic BP (mmHg)")
        ax.set_ylabel("Count")
        ax.annotate(f"n = {len(systolic):,}", xy=(0.97, 0.95), xycoords="axes fraction",
                    ha="right", va="top", fontsize=8, color=vizlib.PALETTE["ink_soft"])
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Same data: bin count drives the apparent shape\n"
                 "3 bins hide everything; 45 bins reveal the distribution; 400 bins look like noise",
                 fontsize=10)
    vizlib.save_fig(fig, OUT / "case08_misleading.png",
                    note=f"Source: vitals_10k.csv | n={len(systolic):,} | removed {n_removed} rows: heart_rate > 300")
    plt.close(fig)

    # ── honest redesign: Sturges / sqrt rule, annotated ─────────────────────
    fig, ax = plt.subplots(figsize=(6, 4))
    n_bins = int(np.sqrt(len(systolic)))
    ax.hist(systolic, bins=n_bins, color=vizlib.PALETTE["series"][0], edgecolor="white")
    ax.set_title(f"Systolic BP distribution (bins = √n ≈ {n_bins})")
    ax.set_xlabel("Systolic BP (mmHg)")
    ax.set_ylabel("Count")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case08_honest.png",
                    note=f"Source: vitals_10k.csv | n={len(systolic):,} | bins = √n = {n_bins} (Sturges rule)")
    plt.close(fig)
    print("  Case 08 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CASE 9 — SpO2 density (KDE past the data maximum)
# Check: data maximum is 100, but default KDE extends past it
# Mechanism: Gaussian KDE has infinite support and spills above 100%,
#            implying physiologically impossible values
# ══════════════════════════════════════════════════════════════════════════════
def case09():
    import seaborn as sns
    df = pd.read_csv(DATA / "vitals_10k.csv")
    spo2 = df["spo2"].dropna()
    print(f"Case 09 check — SpO2 max: {spo2.max()}")

    # ── misleading chart: default KDE extends past 100 ────────────────────────
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.kdeplot(spo2, ax=ax, color=vizlib.PALETTE["series"][0], fill=True, alpha=0.3)
    ax.set_xlim(90, 108)
    ax.axvline(100, color=vizlib.PALETTE["highlight"], lw=1.5, ls="--", label="SpO2 = 100%")
    ax.set_title("KDE implies SpO2 > 100% — physiologically impossible")
    ax.set_xlabel("SpO2 (%)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case09_misleading.png",
                    note=f"Source: vitals_10k.csv | n={len(spo2):,} | default bw_method causes boundary leak")
    plt.close(fig)

    # ── honest redesign: clipped KDE + rug + histogram ───────────────────────
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(spo2, bins=30, color=vizlib.PALETTE["series"][0],
            density=True, alpha=0.4, edgecolor="white", label="Histogram")
    sns.kdeplot(spo2, ax=ax, color=vizlib.PALETTE["series"][0],
                fill=False, clip=(spo2.min(), 100), label="KDE (clipped at 100)")
    ax.axvline(100, color=vizlib.PALETTE["highlight"], lw=1.5, ls="--",
               label="Physiological ceiling (100%)")
    ax.set_xlim(spo2.min() - 1, 102)
    ax.set_title("SpO2 distribution — all readings at or below 100%")
    ax.set_xlabel("SpO2 (%)")
    ax.set_ylabel("Density")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case09_honest.png",
                    note=f"Source: vitals_10k.csv | n={len(spo2):,} | KDE clipped at [min, 100]")
    plt.close(fig)
    print("  Case 09 done.\n")


# ══════════════════════════════════════════════════════════════════════════════
# DIAGNOSIS SUMMARY — printed to console
# ══════════════════════════════════════════════════════════════════════════════
DIAGNOSES = {
    "Case 01 Helmets": {
        "invited_conclusion": "Premium helmets cause more injuries than Standard helmets.",
        "decoy_objection": "Could be rider skill? Ruled out: experience months are similar across grades (mean ~40).",
        "mechanism": "Simpson's Paradox / confounding by road type. "
                     "Premium riders concentrate on Motorways (higher absolute risk); "
                     "within each road type, Standard helmets show equal or higher rates.",
        "redesign": "Bar chart faceted by road_type — removes the confound and reverses the conclusion."
    },
    "Case 02 Chai–Quizzes": {
        "invited_conclusion": "Drinking chai causes quiz failures (r = 0.98).",
        "decoy_objection": "Could be exam-month effect? Ruled out: is_exam_month has only 3 flagged months.",
        "mechanism": "Spurious correlation driven by the omitted confounder students_enrolled "
                     "(r=0.99 with chai sold, r=0.97 with failures). "
                     "Enrolment grows monotonically and drives both series.",
        "redesign": "Two side-by-side scatter plots of each series vs enrolment — "
                    "the chai↔failures relationship disappears after conditioning."
    },
    "Case 03 Lahore AQI": {
        "invited_conclusion": "The day-61 intervention cut AQI by 32% (202→137).",
        "decoy_objection": "Could be seasonal? The window is only 120 days, but the AQI peaks on day ~55 "
                           "and declines regardless — consistent with a winter-to-spring seasonal effect.",
        "mechanism": "Regression to the mean: the intervention was announced at an AQI peak. "
                     "Any measurement taken at a peak will tend to fall; "
                     "no control site is provided to distinguish the policy from the season.",
        "redesign": "Full line chart annotating both the intervention date and the seasonal peak, "
                    "and noting the absence of a control."
    },
    "Case 04 Quartet Depts": {
        "invited_conclusion": "Study hours predict scores equally well across all departments (r ≈ 0.82).",
        "decoy_objection": "Could department size explain the difference? No — n is similar across groups.",
        "mechanism": "Anscombe's Quartet: identical summary statistics (mean, SD, r) "
                     "can mask radically different distributions. "
                     "The scatter plots reveal linear, curved, outlier-dominated, and step-function patterns.",
        "redesign": "Small-multiple scatter plots — one per department — with OLS lines."
    },
    "Case 05 Same Stats": {
        "invited_conclusion": "All five cohorts respond identically to the platform (same stats).",
        "decoy_objection": "Could the equal stats be a coincidence? No — they are exact by construction.",
        "mechanism": "Datasaurus Dozen / match_stats(): summary statistics do not constrain shape. "
                     "r = 0.42 is consistent with a straight line, a star, a circle, or noise.",
        "redesign": "Small-multiple scatter plots showing wildly different shapes with identical statistics."
    },
    "Case 06 Sensor Matrix": {
        "invited_conclusion": "All sensors are strongly correlated — the matrix is uniformly warm (Reds).",
        "decoy_objection": "Could the high correlations be real? "
                           "Partially: systolic–MAP 0.96 is physiologically expected. "
                           "But probe columns (probe_a–f) are artefactual.",
        "mechanism": "Two problems: (1) Statistical — probe columns are instrument noise, "
                     "not physiology; including them inflates apparent structure. "
                     "(2) Drawing — cmap='Reds' without vmin/vmax maps correlation 0 to white "
                     "and 1 to red, so a weak 0.2 looks dark. "
                     "The drawing fix (diverging palette, vmin=-1) solves problem (2) only; "
                     "the statistical fix requires dropping probe columns.",
        "redesign": "Lower-triangle heatmap, cmap=RdBu_r, vmin=-1, vmax=1 — "
                    "correlations read as magnitudes and signs correctly."
    },
    "Case 07 ShaheenGo": {
        "invited_conclusion": "Cost exceeds revenue in the first four months.",
        "decoy_objection": "Could the raw numbers confirm this? No — revenue (50–80) always exceeds cost (40–56).",
        "mechanism": "Dual-axis encoding: the designer chose scale ranges that made the cost line "
                     "plot above the revenue line even though cost < revenue every month. "
                     "Any crossing point can be manufactured by adjusting one axis independently.",
        "redesign": "Single shared axis, zero baseline — cost and revenue never cross."
    },
    "Case 08 Histograms": {
        "invited_conclusion": "The distribution of systolic BP is unimodal (3 bins) or bimodal (400 bins).",
        "decoy_objection": "Could the bimodality be real? Ruled out: 45-bin histogram shows a single "
                           "right-skewed distribution with no gap.",
        "mechanism": "Bin-count sensitivity: 3 bins destroy all shape information; "
                     "400 bins amplify sampling noise into apparent secondary peaks. "
                     "The √n rule (≈ 100 bins) balances detail against noise.",
        "redesign": "Single histogram with bins = √n, bin width declared in the axis label."
    },
    "Case 09 SpO2 KDE": {
        "invited_conclusion": "Some patients have SpO2 > 100% (the KDE extends to ~103%).",
        "decoy_objection": "Could the device capture >100%? No — the data maximum is exactly 100.",
        "mechanism": "Gaussian KDE has infinite support: it always leaks beyond the data boundary. "
                     "Here the boundary is a hard physiological ceiling (100%), so any mass above it "
                     "represents impossible values. The fix is clip=(min, 100) in kdeplot.",
        "redesign": "Overlaid histogram + KDE clipped at 100, with a vertical reference line."
    },
}

def print_diagnoses():
    print("\n" + "=" * 70)
    print("PART A DIAGNOSES")
    print("=" * 70)
    for case, d in DIAGNOSES.items():
        print(f"\n{case}")
        for key, val in d.items():
            print(f"  {key.upper()}: {val}")


if __name__ == "__main__":
    print("Running Part A — nine charts\n")
    case01()
    case02()
    case03()
    case04()
    case05()
    case06()
    case07()
    case08()
    case09()
    print_diagnoses()
    print(f"\nAll charts saved to: {OUT}")
