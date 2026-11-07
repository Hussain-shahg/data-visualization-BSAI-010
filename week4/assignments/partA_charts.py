"""
Week 4 - Part A: Rebuild nine charts, then take them apart.

Each case is arithmetically correct as drawn. The problem is upstream of the
pixels: a parse, a resample, a window, a denominator. Build the published
(misleading) chart exactly as the recipe says, then build the honest
redesign.

Run from week4/assignments/:
    python partA_charts.py
Produces: charts/caseXX_misleading.png and charts/caseXX_honest.png
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

DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# CASE 1 - "Orders peak in Q1 and collapse every year" - date sorted as text
# Mechanism: month column is text "YYYY-M" (no zero pad); sorting it
# lexicographically is NOT chronological order, because "2024-10" < "2024-2"
# as strings. The resulting sequence jumps backward twice.
# ══════════════════════════════════════════════════════════════════════════
def case01():
    df = pd.read_csv(DATA / "case01_orders_stringdate.csv")
    df_text_sorted = df.sort_values("month").reset_index(drop=True)  # STRING sort

    o = df_text_sorted["orders"].to_numpy()
    # find the two drops the brief predicts
    diffs = np.diff(o)
    drop_idx = np.where(diffs < 0)[0]
    print("Case 01 check -- 24 points, text-sorted order:")
    print(f"  climbs for {drop_idx[0] + 1} points, "
          f"drops {o[drop_idx[0]] - o[drop_idx[0] + 1]}, "
          f"climbs for {drop_idx[1] - drop_idx[0] - 1} points, "
          f"drops {o[drop_idx[1]] - o[drop_idx[1] + 1]}, then climbs again")
    assert len(drop_idx) == 2

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(range(len(df_text_sorted)), o, marker="o", ms=4,
            color=vizlib.PALETTE["series"][0])
    ax.set_ylim(0)
    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels(df_text_sorted["month"].iloc[::3], rotation=45, ha="right", fontsize=7)
    ax.set_title("Orders peak in Q1 and collapse every year -- a clear annual cycle")
    ax.set_xlabel("Month (sorted as text)")
    ax.set_ylabel("Orders")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case01_misleading.png",
                    note="Source: case01_orders_stringdate.csv | n=24 | month column SORTED AS TEXT")
    plt.close(fig)

    # honest redesign: parse the month as a real period and sort chronologically
    df["period"] = pd.PeriodIndex(df["month"].str.replace(
        r"^(\d{4})-(\d{1,2})$", lambda m: f"{m.group(1)}-{int(m.group(2)):02d}", regex=True), freq="M")
    df_true = df.sort_values("period").reset_index(drop=True)
    audit = tslib.audit_index(df_true.set_index("period").to_timestamp(), "MS")
    print(f"  audit_index on the TRUE order: monotonic={audit['monotonic']}, "
          f"missing={audit['n_missing']}")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df_true["period"].astype(str), df_true["orders"], marker="o", ms=4,
            color=vizlib.PALETTE["series"][0])
    ax.set_ylim(0)
    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels(df_true["period"].astype(str).iloc[::3], rotation=45, ha="right", fontsize=7)
    ax.set_title("Orders grew steadily, +52% over two years -- no annual cycle at all")
    ax.set_xlabel("Month (parsed as a real period, chronological order)")
    ax.set_ylabel("Orders")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case01_honest.png",
                    note="Source: case01_orders_stringdate.csv | n=24 | month parsed as pd.Period, true chronological order")
    plt.close(fig)
    print("  Case 01 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 2 - "Sales grew steadily, 22%, across the quarter" - plotted by row #
# Mechanism: the file only records TRADING days (weekends absent). Plotting
# against row number compresses the missing weekends out of the x-axis, so
# a trend that is genuinely there looks smoother/different than it should,
# and -- the real issue the brief flags -- any analysis of "days between"
# or velocity is silently wrong because row number != calendar day.
# ══════════════════════════════════════════════════════════════════════════
def case02():
    df = pd.read_csv(DATA / "case02_shop_closed.csv")
    df["date"] = pd.to_datetime(df["date"])
    s = df["sales_pkr_k"].to_numpy()
    first, last = s[0], s[-1]
    pct = (last - first) / first * 100
    print(f"Case 02 check -- 69 points, first {first}, last {last}, {pct:+.0f}%")
    assert len(df) == 69

    m, b = np.polyfit(range(len(df)), s, 1)
    xs = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(xs, s, color=vizlib.PALETTE["series"][0], marker="o", ms=3, lw=1)
    ax.plot(xs, m * xs + b, color=vizlib.PALETTE["highlight"], lw=1.5,
            label=f"OLS trend, +{pct:.0f}% end to end")
    ax.set_ylim(0)
    ax.set_xlabel("Row number (NOT calendar day)")
    ax.set_ylabel("Sales (PKR thousands)")
    ax.set_title("Sales grew steadily, 22%, across the quarter")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case02_misleading.png",
                    note="Source: case02_shop_closed.csv | n=69 trading-day rows | x = row number")
    plt.close(fig)

    # honest redesign: real calendar axis, gaps for the days the shop was
    # closed (weekends) shown as actual gaps, not silently compressed away
    full = tslib.reindex_full(df.set_index("date")["sales_pkr_k"], "D")
    a = tslib.audit_index(df.set_index("date"), "D")
    n_missing = a["n_missing"]
    span_days = (df["date"].max() - df["date"].min()).days + 1
    print(f"  Calendar span: {span_days} days, {len(df)} trading rows, "
          f"{n_missing} calendar days with no row (weekends/holidays)")

    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(full.index, full.to_numpy(), color=vizlib.PALETTE["series"][0],
            marker="o", ms=3, lw=1)
    ax.set_ylim(0)
    ax.set_xlabel(f"Calendar date -- trading days only, {n_missing} closed days left as gaps")
    ax.set_ylabel("Sales (PKR thousands)")
    ax.set_title(f"Sales on a true calendar axis -- {n_missing} closed days shown as gaps, not compressed away")
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    vizlib.save_fig(fig, OUT / "case02_honest.png",
                    note=f"Source: case02_shop_closed.csv | n=69 of {span_days} calendar days | "
                         f"{n_missing} non-trading days reindexed to NaN and left as gaps")
    plt.close(fig)
    print("  Case 02 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 3 - "Peak load jumped 43% overnight on 1 July" - a LEVEL resampled
# with .sum(). concurrent_users is a snapshot (a level), not an arrival
# count (a flow); summing 24 hourly snapshots produces a number with no
# real-world meaning, and its jump is an artefact of how many hours of
# elevated readings fell in each month, not a step change in peak load.
# ══════════════════════════════════════════════════════════════════════════
def case03():
    df = pd.read_csv(DATA / "case03_bandwidth_levels.csv")
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.set_index("ts")
    daily_sum = df["concurrent_users"].resample("D").sum()
    june = daily_sum["2025-06"]
    july = daily_sum["2025-07"]
    pct = (july.mean() - june.mean()) / june.mean() * 100
    print(f"Case 03 check -- June daily-SUM mean {june.mean():,.0f}, "
          f"July daily-SUM mean {july.mean():,.0f}, {pct:+.0f}% step")

    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(daily_sum.index, daily_sum.to_numpy(), color=vizlib.PALETTE["series"][0], lw=1)
    ax.axvline(pd.Timestamp("2025-07-01"), color=vizlib.PALETTE["highlight"], ls="--", lw=1.2)
    ax.set_ylim(0)
    ax.set_xlabel("Date")
    ax.set_ylabel("concurrent_users, SUMMED over 24 hourly readings (no real unit)")
    ax.set_title(f"Peak load jumped {pct:.0f}% overnight on 1 July")
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    vizlib.save_fig(fig, OUT / "case03_misleading.png",
                    note="Source: case03_bandwidth_levels.csv | concurrent_users (a LEVEL) resampled with .sum()")
    plt.close(fig)

    # honest redesign: a level is summarised with mean/max, never sum.
    daily_mean = df["concurrent_users"].resample("D").mean()
    daily_max = df["concurrent_users"].resample("D").max()
    jmean = (daily_mean["2025-07"].mean() - daily_mean["2025-06"].mean()) / daily_mean["2025-06"].mean() * 100
    print(f"  Honest check -- daily MEAN concurrent users: June {daily_mean['2025-06'].mean():.0f}, "
          f"July {daily_mean['2025-07'].mean():.0f}, {jmean:+.1f}% (not 43%)")

    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(daily_mean.index, daily_mean.to_numpy(), color=vizlib.PALETTE["series"][0],
            lw=1.3, label="Daily mean concurrent users")
    ax.plot(daily_max.index, daily_max.to_numpy(), color=vizlib.PALETTE["muted"],
            lw=0.8, label="Daily max concurrent users")
    ax.axvline(pd.Timestamp("2025-07-01"), color=vizlib.PALETTE["highlight"], ls="--", lw=1.2)
    ax.set_ylim(0)
    ax.set_xlabel("Date")
    ax.set_ylabel("Concurrent users (a level -- mean/max, never summed)")
    ax.set_title(f"Concurrent users rose only {jmean:+.0f}% -- the '43%' was 24x inflation from summing a level")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    vizlib.save_fig(fig, OUT / "case03_honest.png",
                    note="Source: case03_bandwidth_levels.csv | concurrent_users is a LEVEL -- resampled with .mean()/.max(), never .sum()")
    plt.close(fig)
    print("  Case 03 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 4 - "The new checkout flow started working on 7 September" - a
# TRAILING rolling mean finds its turning point late, by about half the
# window, because it cannot know about a turn until the window has filled.
# ══════════════════════════════════════════════════════════════════════════
def case04():
    df = pd.read_csv(DATA / "case04_intervention_lag.csv")
    df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")["conversion_pct"]
    trailing = s.rolling(31).mean()
    turn = trailing.idxmin()
    print(f"Case 04 check -- 31-day trailing mean bottoms out on {turn.date()}")
    assert str(turn.date()) == "2025-09-07"

    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.plot(s.index, s.to_numpy(), color=vizlib.PALETTE["muted"], lw=0.8, alpha=0.6, label="Raw, daily")
    ax.plot(trailing.index, trailing.to_numpy(), color=vizlib.PALETTE["series"][0], lw=1.6,
            label="31-day trailing mean")
    ax.axvline(turn, color=vizlib.PALETTE["highlight"], ls="--", lw=1.3)
    ax.annotate(f"Turn: {turn.date()}", xy=(turn, trailing.loc[turn]),
                xytext=(10, -22), textcoords="offset points", fontsize=8,
                arrowprops=dict(arrowstyle="->", color=vizlib.PALETTE["ink_soft"]))
    ax.set_xlabel("Date")
    ax.set_ylabel("Conversion (%)")
    ax.set_title("The new checkout flow started working on 7 September")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    vizlib.save_fig(fig, OUT / "case04_misleading.png",
                    note="Source: case04_intervention_lag.csv | 31-day TRAILING rolling mean")
    plt.close(fig)

    lg = tslib.lag_at_turn(s, 31, how="min")
    print(f"  lag_at_turn -- trailing turn {lg['trailing_turn'].date()}, "
          f"centred turn {lg['centred_turn'].date()}, lag {lg['lag_periods']} days "
          f"(half-window {lg['half_window']})")

    fig, ax = plt.subplots(figsize=(6.5, 4))
    centred = s.rolling(31, center=True).mean()
    ax.plot(s.index, s.to_numpy(), color=vizlib.PALETTE["muted"], lw=0.8, alpha=0.6, label="Raw, daily")
    ax.plot(centred.index, centred.to_numpy(), color=vizlib.PALETTE["series"][0], lw=1.6,
            label="31-day CENTRED mean -- true turning point")
    ax.plot(trailing.index, trailing.to_numpy(), color=vizlib.PALETTE["muted"], lw=1.2, ls="--",
            label="31-day trailing mean -- finds it 15 days late")
    ax.axvline(lg["centred_turn"], color=vizlib.PALETTE["series"][2], ls="--", lw=1.3)
    ax.axvline(lg["trailing_turn"], color=vizlib.PALETTE["highlight"], ls="--", lw=1.3)
    ax.set_xlabel("Date")
    ax.set_ylabel("Conversion (%)")
    ax.set_title(f"The true turn was {lg['centred_turn'].date()} -- the trailing mean found it "
                 f"{lg['lag_periods']} days late")
    ax.legend(frameon=False, fontsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    vizlib.save_fig(fig, OUT / "case04_honest.png",
                    note="Source: case04_intervention_lag.csv | trailing vs centred 31-day mean | "
                         f"lag = {lg['lag_periods']}d, half-window = {lg['half_window']}d")
    plt.close(fig)
    print("  Case 04 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 5 - "Revenue has fallen for six straight months" - a window chosen
# at the seasonal peak. The full 36-month series is strongly seasonal
# (peaks ~May/Jun, troughs ~Nov); May-Nov captures exactly the down-slope.
# ══════════════════════════════════════════════════════════════════════════
def case05():
    df = pd.read_csv(DATA / "case05_revenue_window.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    s = df.set_index("month")["revenue_pkr_m"]
    window = s.loc["2025-05":"2025-11"]
    pct = (window.iloc[-1] - window.iloc[0]) / window.iloc[0] * 100
    print(f"Case 05 check -- {len(window)} points, {window.iloc[0]} down to {window.iloc[-1]}, {pct:+.1f}%")
    assert len(window) == 7

    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.plot(window.index.astype(str), window.to_numpy(), marker="o",
            color=vizlib.PALETTE["series"][0])
    ax.set_ylim(0)
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (PKR millions)")
    ax.set_title(f"Revenue has fallen for six straight months ({pct:.0f}%)")
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    vizlib.save_fig(fig, OUT / "case05_misleading.png",
                    note="Source: case05_revenue_window.csv | window: May-Nov 2025 ONLY, n=7 of 36 months")
    plt.close(fig)

    # honest redesign: the full 36-month series, with the cherry-picked
    # window marked -- it is the down-leg of a wave repeated 3 times
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(s.index.astype(str), s.to_numpy(), color=vizlib.PALETTE["series"][0], lw=1.3)
    w0, w1 = s.index.get_loc("2025-05"), s.index.get_loc("2025-11")
    ax.axvspan(w0, w1, color=vizlib.PALETTE["highlight"], alpha=0.15,
               label="Part A's cherry-picked window")
    for yr in (2023, 2024, 2025):
        peak = s.loc[f"{yr}-01":f"{yr}-12"].idxmax()
        ax.annotate("peak", xy=(s.index.get_loc(peak), s.loc[peak]),
                    xytext=(0, 8), textcoords="offset points", fontsize=7,
                    ha="center", color=vizlib.PALETTE["ink_soft"])
    ax.set_xticks(range(0, 36, 3))
    ax.set_xticklabels(s.index.astype(str)[::3], rotation=45, ha="right", fontsize=7)
    ax.set_ylim(0)
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (PKR millions)")
    ax.set_title("Revenue is strongly seasonal, peaking every May/June -- not in decline")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case05_honest.png",
                    note="Source: case05_revenue_window.csv | full 36-month series, 2023-01 to 2025-12")
    plt.close(fig)
    print("  Case 05 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 6 - "Orders collapsed in October" - resampled to monthly SUM, but
# the extract was taken part-way through October: October is a PARTIAL
# month shown at the same visual weight as the complete ones.
# ══════════════════════════════════════════════════════════════════════════
def case06():
    df = pd.read_csv(DATA / "case06_monthly_partial.csv")
    df["date"] = pd.to_datetime(df["date"])
    s = df.set_index("date")["orders"]
    monthly = s.resample("MS").sum()
    days_in_month = s.resample("MS").size()
    sep, oct_ = monthly.loc["2025-09-01"], monthly.loc["2025-10-01"]
    pct_of_sep = oct_ / sep * 100
    print(f"Case 06 check -- {len(monthly)} bars, September {sep:,.0f}, "
          f"October {oct_:,.0f} -- {pct_of_sep:.0f}% of it")
    print(f"  Days of data: September {days_in_month.loc['2025-09-01']}, "
          f"October {days_in_month.loc['2025-10-01']} (partial month)")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(monthly.index.strftime("%Y-%m"), monthly.to_numpy(), color=vizlib.PALETTE["series"][0])
    ax.set_ylim(0)
    ax.set_xlabel("Month")
    ax.set_ylabel("Orders per month (sum)")
    ax.set_title("Orders collapsed in October")
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    vizlib.save_fig(fig, OUT / "case06_misleading.png",
                    note="Source: case06_monthly_partial.csv | monthly orders, .resample('MS').sum()")
    plt.close(fig)

    # honest redesign: mark the partial month distinctly, and show the
    # daily run-rate instead of the raw monthly sum for the partial one
    run_rate = monthly.astype(float).copy()
    run_rate.loc["2025-10-01"] = oct_ / days_in_month.loc["2025-10-01"] * days_in_month.loc["2025-09-01"]
    colors = [vizlib.PALETTE["series"][0]] * len(monthly)
    oct_pos = list(monthly.index).index(pd.Timestamp("2025-10-01"))
    colors[oct_pos] = vizlib.PALETTE["muted"]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(monthly.index.strftime("%Y-%m"), monthly.to_numpy(), color=colors)
    ax.bar(run_rate.index.strftime("%Y-%m")[oct_pos:oct_pos + 1],
           [run_rate.iloc[oct_pos]], facecolor="none", edgecolor=vizlib.PALETTE["highlight"],
           lw=1.5, ls="--", label=f"October, annualised to a full {days_in_month.loc['2025-09-01']}-day month")
    ax.annotate(f"only {days_in_month.loc['2025-10-01']} days of data",
                xy=(oct_pos, oct_), xytext=(0, 15), textcoords="offset points",
                ha="center", fontsize=7.5, color=vizlib.PALETTE["ink_soft"])
    ax.set_ylim(0)
    ax.set_xlabel("Month")
    ax.set_ylabel("Orders per month (sum)")
    ax.set_title(f"October is a partial month ({days_in_month.loc['2025-10-01']} of "
                 f"~{days_in_month.loc['2025-09-01']} days) -- not a collapse")
    ax.legend(frameon=False, fontsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    vizlib.save_fig(fig, OUT / "case06_honest.png",
                    note="Source: case06_monthly_partial.csv | partial final month marked and annualised for comparison")
    plt.close(fig)
    print("  Case 06 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 7 - "Product D has been erratic since mid-2024" - volatility
# leaking upward through a stacked area's moving baseline. product_d's own
# values are smooth; it is drawn on top of product_b, whose swings move
# product_d's baseline up and down even though product_d itself is stable.
# ══════════════════════════════════════════════════════════════════════════
def case07():
    df = pd.read_csv(DATA / "case07_stacked_products.csv")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    df = df.set_index("month")
    cols = ["product_a", "product_b", "product_c", "product_d"]
    total = df[cols].sum(axis=1)
    print(f"Case 07 check -- total envelope runs {total.min():.0f} to {total.max():.0f}")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.stackplot(df.index.astype(str), [df[c] for c in cols], labels=cols,
                 colors=vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]])
    ax.set_xticks(range(0, 36, 3))
    ax.set_xticklabels(df.index.astype(str)[::3], rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("Revenue (PKR millions)")
    ax.set_title("Product D has been erratic since mid-2024")
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case07_misleading.png",
                    note="Source: case07_stacked_products.csv | stacked area, product_a at bottom, product_d on top")
    plt.close(fig)

    # honest redesign: product_d alone, on its own zero baseline -- it is
    # in fact one of the smoothest of the four series
    cv = df[cols].std() / df[cols].mean()
    print(f"  Coefficient of variation by product: "
          + ", ".join(f"{c}={cv[c]:.3f}" for c in cols))
    fig, axes = plt.subplots(2, 2, figsize=(8, 5.5), sharex=True)
    for ax, c in zip(axes.flat, cols):
        ax.plot(df.index.astype(str), df[c], color=vizlib.PALETTE["series"][0], lw=1.3)
        ax.set_ylim(0)
        ax.set_title(f"{c}  (CV = {cv[c]:.2f})", fontsize=9)
        ax.set_xticks(range(0, 36, 6))
        ax.set_xticklabels(df.index.astype(str)[::6], rotation=45, ha="right", fontsize=6.5)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Unstacked: product_d (CV lowest of the four) is the SMOOTHEST series, "
                 "not the most erratic", fontsize=10)
    fig.tight_layout()
    vizlib.save_fig(fig, OUT / "case07_honest.png",
                    note="Source: case07_stacked_products.csv | each product on its own zero baseline, small multiples")
    plt.close(fig)
    print("  Case 07 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 8 - "Paid search drives 43% of our customers" - the touch_* columns
# are not mutually exclusive (a customer can be touched by several
# channels before purchase), so the four shares sum past 100% and a pie
# of them is not legal.
# ══════════════════════════════════════════════════════════════════════════
def case08():
    df = pd.read_csv(DATA / "case08_channel_attrib.csv")
    touch_cols = ["touch_search", "touch_social", "touch_email", "touch_direct"]
    ex = tslib.exclusivity_check(df, touch_cols)
    print(f"Case 08 check -- shares: "
          + ", ".join(f"{k.replace('touch_', '')}={v:.1f}%" for k, v in ex["shares_pct"].items()))
    print(f"  sum = {ex['sum_pct']:.1f}%, exclusive = {ex['exclusive']}, "
          f"{ex['n_multi']} of {ex['n']} customers touched by >1 channel ({ex['pct_multi']:.1f}%)")

    labels = [k.replace("touch_", "").title() for k in touch_cols]
    shares = [ex["shares_pct"][k] for k in touch_cols]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(shares, labels=labels, autopct="%1.1f%%", startangle=90,
           colors=vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]])
    ax.set_title(f"Paid search drives {shares[0]:.0f}% of our customers")
    vizlib.save_fig(fig, OUT / "case08_misleading.png",
                    note=f"Source: case08_channel_attrib.csv | n={ex['n']:,} | "
                         f"PIE OF NON-EXCLUSIVE SHARES summing to {ex['sum_pct']:.1f}%")
    plt.close(fig)

    # honest redesign: a bar chart (legal for non-exclusive parts) PLUS the
    # overlap made explicit
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4), gridspec_kw={"width_ratios": [1.3, 1]})
    order = sorted(touch_cols, key=lambda k: -ex["shares_pct"][k])
    ax1.barh([k.replace("touch_", "").title() for k in order],
             [ex["shares_pct"][k] for k in order], color=vizlib.PALETTE["series"][0])
    ax1.set_xlim(0, 100)
    ax1.set_xlabel("% of customers touched by this channel (not exclusive)")
    ax1.invert_yaxis()
    ax1.spines[["top", "right"]].set_visible(False)
    for i, k in enumerate(order):
        ax1.annotate(f"{ex['shares_pct'][k]:.1f}%", xy=(ex["shares_pct"][k], i),
                     xytext=(3, 0), textcoords="offset points", va="center", fontsize=8)

    n_touches = df[touch_cols].sum(axis=1)
    counts = n_touches.value_counts().sort_index()
    ax2.bar(counts.index.astype(str), counts.to_numpy(), color=vizlib.PALETTE["series"][1])
    ax2.set_xlabel("Number of channels that touched this customer")
    ax2.set_ylabel("Customers")
    ax2.set_title(f"{ex['pct_multi']:.0f}% touched by 2+", fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Shares sum to {ex['sum_pct']:.0f}% because channels are not exclusive -- "
                 "a pie cannot legally show this", fontsize=10)
    fig.tight_layout()
    vizlib.save_fig(fig, OUT / "case08_honest.png",
                    note=f"Source: case08_channel_attrib.csv | n={ex['n']:,} | bar chart of non-exclusive touch shares + overlap count")
    plt.close(fig)
    print("  Case 08 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 9 - "Premium is now 38% of revenue -- a record" - a rising share of
# a FALLING total. Premium revenue is roughly flat; total revenue fell, so
# the share rose mechanically, not because premium grew.
# ══════════════════════════════════════════════════════════════════════════
def case09():
    df = pd.read_csv(DATA / "case09_premium_share.csv")
    df["share_pct"] = df["premium_revenue_pkr_m"] / df["total_revenue_pkr_m"] * 100
    print(f"Case 09 check -- share rises from {df['share_pct'].iloc[0]:.1f}% to {df['share_pct'].iloc[-1]:.1f}%")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["quarter"], df["share_pct"], marker="o", color=vizlib.PALETTE["series"][0])
    ax.set_ylim(0)
    ax.annotate(f"{df['share_pct'].iloc[-1]:.0f}% -- a record",
                xy=(len(df) - 1, df["share_pct"].iloc[-1]), xytext=(-55, 10),
                textcoords="offset points", fontsize=8,
                arrowprops=dict(arrowstyle="->", color=vizlib.PALETTE["ink_soft"]))
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Premium share of revenue (%)")
    ax.set_title("Premium is now 38% of revenue -- a record")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case09_misleading.png",
                    note="Source: case09_premium_share.csv | share = premium_revenue / total_revenue per quarter")
    plt.close(fig)

    pct_change_premium = (df["premium_revenue_pkr_m"].iloc[-1] - df["premium_revenue_pkr_m"].iloc[0]) \
        / df["premium_revenue_pkr_m"].iloc[0] * 100
    pct_change_total = (df["total_revenue_pkr_m"].iloc[-1] - df["total_revenue_pkr_m"].iloc[0]) \
        / df["total_revenue_pkr_m"].iloc[0] * 100
    print(f"  Honest check -- premium revenue changed {pct_change_premium:+.1f}%, "
          f"total revenue changed {pct_change_total:+.1f}% over the same 8 quarters")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4))
    ax1.plot(df["quarter"], df["total_revenue_pkr_m"], marker="o",
             color=vizlib.PALETTE["series"][1], label="Total revenue")
    ax1.plot(df["quarter"], df["premium_revenue_pkr_m"], marker="s",
             color=vizlib.PALETTE["series"][0], label="Premium revenue")
    ax1.set_ylim(0)
    ax1.set_ylabel("Revenue (PKR millions)")
    ax1.legend(frameon=False, fontsize=8)
    ax1.set_title(f"Premium {pct_change_premium:+.0f}%, total {pct_change_total:+.0f}%", fontsize=9)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")
    ax1.spines[["top", "right"]].set_visible(False)

    ax2.plot(df["quarter"], df["share_pct"], marker="o", color=vizlib.PALETTE["highlight"])
    ax2.set_ylim(0)
    ax2.set_ylabel("Premium share of revenue (%)")
    ax2.set_title("The share rose because the total fell,\nnot because premium grew", fontsize=9)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    vizlib.save_fig(fig, OUT / "case09_honest.png",
                    note="Source: case09_premium_share.csv | premium revenue is roughly flat; the share rose because the total fell")
    plt.close(fig)
    print("  Case 09 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# DIAGNOSIS SUMMARY
# ══════════════════════════════════════════════════════════════════════════
DIAGNOSES = {
    "Case 01 Orders String-Date": {
        "invited_conclusion": "Orders peak in Q1 and collapse every year -- a clear annual cycle.",
        "decoy_objection": "Could the sample be too small? No -- n=24, a full two years of monthly data; "
                            "the issue is order, not size.",
        "mechanism": "The month column is text ('2024-1', '2024-10', ...) with no zero-padding. "
                     "Sorting it as a STRING is not chronological: '2024-10' < '2024-2' lexicographically, "
                     "so October, November and December sort before February. The series genuinely climbs "
                     "monotonically; the two 'drops' (958 and 978) are artefacts of the resort, not business events.",
        "redesign": "Parse the month as a pd.Period and sort chronologically -- orders rise steadily +52%, no cycle."
    },
    "Case 02 Shop Closed": {
        "invited_conclusion": "Sales grew steadily, 22%, across the quarter.",
        "decoy_objection": "Could the OLS line be overfit? No -- the trend is real; the issue is the x-axis, "
                            "not the regression.",
        "mechanism": "The file only records trading days (weekends excluded). Plotting against row number "
                     "treats 69 consecutive rows as 69 consecutive days, silently compressing the real "
                     "90-day calendar span and erasing the weekend gaps -- a reader cannot see that "
                     "Friday-to-Monday is one business day's gap on this axis but three calendar days.",
        "redesign": "Reindex onto a full calendar and plot by true date, leaving closed days as gaps in the line."
    },
    "Case 03 Bandwidth Levels": {
        "invited_conclusion": "Peak load jumped 43% overnight on 1 July.",
        "decoy_objection": "Could July simply have more users? Real growth would show in the MEAN level too "
                            "-- and it barely moves.",
        "mechanism": "concurrent_users is a LEVEL (a snapshot of who is connected at that instant), not a "
                     "flow. Resampling a level with .sum() adds up 24 unrelated snapshots per day, a number "
                     "with no real-world meaning. The '43% jump' is sensitive to how many hours of already-"
                     "elevated readings happen to fall in July vs June, not a step change in capacity.",
        "redesign": "Resample the level with .mean() or .max(), never .sum() -- the true change is a few percent."
    },
    "Case 04 Intervention Lag": {
        "invited_conclusion": "The new checkout flow started working on 7 September.",
        "decoy_objection": "Could the 31-day window be too long? No -- any trailing window has the same lag "
                            "problem, just a different number of days late.",
        "mechanism": "A trailing rolling mean at day t only knows about days t-30..t, so it cannot register a "
                     "turn until the window has filled. lag_at_turn() shows the trailing mean finds the "
                     "minimum roughly half a window (about 15 days) after the centred mean does -- the real "
                     "turning point is in late August, not 7 September.",
        "redesign": "A centred rolling mean locates the true turn; report both and state which a live dashboard can show."
    },
    "Case 05 Revenue Window": {
        "invited_conclusion": "Revenue has fallen for six straight months.",
        "decoy_objection": "Is n=7 too small to trust? n is fine for describing those 7 months -- the problem "
                            "is which 7 months were chosen, not how many.",
        "mechanism": "The full 36-month series is strongly seasonal, peaking every May/June and troughing "
                     "every November, repeated three times. May-to-November is exactly the down-leg of one "
                     "cycle. The same '6 straight months of decline' claim could be made every single year "
                     "on this series.",
        "redesign": "Plot the full 36 months with the cherry-picked window and the three annual peaks marked."
    },
    "Case 06 Monthly Partial": {
        "invited_conclusion": "Orders collapsed in October.",
        "decoy_objection": "Could October genuinely be a weak month? The daily run-rate (orders per day) is "
                            "actually in line with September once the shorter month is accounted for.",
        "mechanism": "The extract was taken part-way through October, so the October bar sums far fewer days "
                     "than every complete month before it. A partial period summed and drawn at the same "
                     "visual weight as complete periods always looks like a collapse.",
        "redesign": "Mark the partial month distinctly and show its run-rate annualised to a full month for comparison."
    },
    "Case 07 Stacked Products": {
        "invited_conclusion": "Product D has been erratic since mid-2024.",
        "decoy_objection": "Could product_d's own numbers be volatile? Its coefficient of variation is the "
                            "LOWEST of the four products -- it is the smoothest, not the most erratic.",
        "mechanism": "Volatility leaking upward through a stacked area's moving baseline. product_d is drawn "
                     "on top of product_a+b+c, so its visible band wobbles whenever the series beneath it "
                     "(chiefly the volatile product_b) wobbles, even though product_d's own value barely moves.",
        "redesign": "Unstack into small multiples, each product on its own zero baseline -- product_d is visibly the calmest series."
    },
    "Case 08 Channel Attribution": {
        "invited_conclusion": "Paid search drives 43% of our customers.",
        "decoy_objection": "Could the 43% simply be rounded from a clean number? No -- the four shares sum "
                            "to well over 100%, which is impossible for a true partition.",
        "mechanism": "exclusivity_check() shows the four touch_* shares sum to over 130% and a large share of "
                     "customers are touched by more than one channel before purchase -- the categories are "
                     "not mutually exclusive, so a pie (or any part-to-whole chart) of them is not legal.",
        "redesign": "A sorted bar chart of (non-exclusive) touch shares, plus a histogram of how many channels touched each customer."
    },
    "Case 09 Premium Share": {
        "invited_conclusion": "Premium is now 38% of revenue -- a record.",
        "decoy_objection": "Did premium revenue actually grow? It is essentially flat quarter to quarter "
                            "(+240 to +228, even dipping) -- the growth is not there.",
        "mechanism": "A rising share of a falling total. Premium revenue barely changes across the 8 quarters "
                     "while total revenue nearly halves; the share rises mechanically as the denominator "
                     "shrinks, not because the premium line is winning more business.",
        "redesign": "Two series (premium and total revenue) plotted directly, beside the share -- showing the share rose for the wrong reason."
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
    print("Running Part A -- nine charts\n")
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
