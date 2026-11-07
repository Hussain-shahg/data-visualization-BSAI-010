"""
Week 4 - Part B: smoothing, windows and panel shape, computed.

Works on the cleaned daily session series (the same cleaning as Part D --
duplicated here so this script is standalone; see partD_figure.py for the
fault-by-fault commentary).

Run from week4/assignments/:
    python partB_windows.py
"""
import pathlib
import sys

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose, STL

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib

DATA = pathlib.Path(__file__).parent / "data"


def cleaned_daily_sessions():
    """Part D's cleaning, condensed to the series Part B needs."""
    df = pd.read_csv(DATA / "sessions_hourly.csv")
    iso_mask = df["ts"].str.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
    ts = pd.Series(index=df.index, dtype="datetime64[ns]")
    ts[iso_mask] = pd.to_datetime(df.loc[iso_mask, "ts"], format="%Y-%m-%d %H:%M:%S")
    ts[~iso_mask] = pd.to_datetime(df.loc[~iso_mask, "ts"], format="%d/%m/%Y %H:%M", dayfirst=True)
    df["ts"] = ts
    df.loc[df["sessions"] < 0, "sessions"] = np.nan
    df = df.sort_values("ts").drop_duplicates(subset="ts", keep="first").set_index("ts").sort_index()
    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="h"))
    daily = df["sessions"].resample("D").sum(min_count=1)
    return daily


print("=" * 70)
print("PART B -- smoothing, windows and panel shape, computed")
print("=" * 70)

daily = cleaned_daily_sessions()
print(f"\nCleaned daily series: {len(daily)} days, {daily.notna().sum()} with data, "
      f"{daily.index.min().date()} to {daily.index.max().date()}")

# ══════════════════════════════════════════════════════════════════════════
# B1 -- the window is a hypothesis
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("B1 -- window_report() for windows 7, 28, 91")
print("-" * 70)
wr = tslib.window_report(daily.dropna(), windows=(7, 28, 91))
print(wr.to_string(index=False))
print("""
  window=7   removes the WEEKLY cycle (weekday/weekend rhythm). Periods lost
             at each end: 3.
  window=28  removes the weekly cycle AND most of the day-to-day noise, but
             also flattens short monthly promo spikes (e.g. Black Friday).
             Periods lost at each end: 14.
  window=91  removes everything up to roughly a quarter -- including real
             month-to-month growth, which is exactly what the Monday review
             wants to SEE. Periods lost at each end: 45.

  Chosen window for Part D: 7 days. The chart is reviewed every Monday and
  its job is to separate the weekly rhythm (the thing that is NOT news) from
  the underlying trend (the thing that IS). A 7-day window is the smallest
  window that fully cancels the 7-day cycle; 28 and 91 throw away real
  month-level movement the board needs to see, not just noise.
""")

# ══════════════════════════════════════════════════════════════════════════
# B2 -- three smoothers against one spike (Black Friday)
# ══════════════════════════════════════════════════════════════════════════
print("-" * 70)
print("B2 -- three smoothers against the Black Friday spike (2024-11-29)")
print("-" * 70)
bf = pd.Timestamp("2024-11-29")
raw_val = daily.loc[bf]
med14 = daily.rolling(14, center=True, min_periods=7).median()
mean14 = daily.rolling(14, center=True, min_periods=7).mean()
ewma14 = daily.ewm(span=14, adjust=False).mean()
fortnight = daily.loc[bf - pd.Timedelta(days=7): bf + pd.Timedelta(days=7)]
print(f"  Raw value on {bf.date()}: {raw_val:,.0f} sessions "
      f"(fortnight median {fortnight.median():,.0f})")
print(f"  14-day centred MEAN   at that date: {mean14.loc[bf]:,.0f}")
print(f"  14-day centred MEDIAN at that date: {med14.loc[bf]:,.0f}")
print(f"  14-day EWMA           at that date: {ewma14.loc[bf]:,.0f}")
print("""
  The median is almost untouched by the spike (robust to one extreme value)
  -- use it on a MONITORING DASHBOARD, where you want "is today normal?"
  and a single freak day should not move the reference line.
  The mean and EWMA both absorb the spike into the trend -- use the mean
  (declared, and symmetric) in a QUARTERLY REPORT, where Black Friday's
  revenue is a real part of the quarter's story and should not be smoothed
  away as if it never happened.
""")

# ══════════════════════════════════════════════════════════════════════════
# B3 -- decompose it
# ══════════════════════════════════════════════════════════════════════════
print("-" * 70)
print("B3 -- seasonal_decompose, period=7 and period=365")
print("-" * 70)
s_full = daily.interpolate(limit_direction="both")  # decompose needs no NaN
dec7 = seasonal_decompose(s_full, model="additive", period=7)
amp7 = dec7.seasonal.max() - dec7.seasonal.min()
worst_resid_date = dec7.resid.abs().idxmax()
print(f"  period=7:  weekly seasonal peak-to-trough amplitude = {amp7:,.0f} sessions")
print(f"             largest residual on {worst_resid_date.date()} "
      f"(|resid| = {dec7.resid.abs().max():,.0f}) -- "
      f"{'matches Black Friday' if worst_resid_date == bf else 'NOT Black Friday -- worth investigating'}")

try:
    dec365 = seasonal_decompose(s_full, model="additive", period=365)
    amp365 = dec365.seasonal.max() - dec365.seasonal.min()
    print(f"  period=365: seasonal peak-to-trough amplitude = {amp365:,.0f} sessions")
except ValueError as e:
    print(f"  period=365: seasonal_decompose REFUSES to run -- {e}")
    print(f"  This file spans {len(s_full)} days (~{len(s_full) / 365.25:.1f} years); the classical "
          f"method needs 2 full annual cycles (730+ days) and this is a real limitation of the data, "
          f"not a bug. STL (loess-based) has no such hard minimum, so it is used here INSTEAD, declared "
          f"as a substitution, to still show what an annual decomposition would look like:")
    stl365 = STL(s_full, period=365, robust=True).fit()
    amp365 = stl365.seasonal.max() - stl365.seasonal.min()
    print(f"  STL, period=365: seasonal peak-to-trough amplitude = {amp365:,.0f} sessions "
          f"(indicative only -- under 2 full cycles of data)")
print("""
  Moving from period=7 to period=365: the slow year-level drift (the
  gradual month-on-month growth trend, and any single-year seasonal
  pattern like a holiday season) moves OUT of `resid` and INTO `seasonal`,
  because period=365 now has room to absorb it as a repeating annual shape
  instead of leaving it as unexplained noise.
""")

# ══════════════════════════════════════════════════════════════════════════
# B4 -- trailing or centred
# ══════════════════════════════════════════════════════════════════════════
print("-" * 70)
print("B4 -- lag_at_turn(), 31-day window")
print("-" * 70)
s_clean = daily.dropna()
lg = tslib.lag_at_turn(s_clean, 31, how="max")
print(f"  trailing turn (max): {lg['trailing_turn'].date()}")
print(f"  centred turn  (max): {lg['centred_turn'].date()}")
print(f"  lag: {lg['lag_periods']} days (half-window = {lg['half_window']})")
print("""
  A live dashboard that refreshes every morning MUST show the TRAILING
  mean -- the centred mean needs future data that does not exist yet on a
  live feed. The caption must say so explicitly: "31-day trailing mean --
  typically lags a true turning point by about two weeks", so a reader
  does not mistake "the line just turned" for "the turn just happened".
""")

# ══════════════════════════════════════════════════════════════════════════
# B5 -- the window is a claim (Lie Factor moved from ink to framing)
# ══════════════════════════════════════════════════════════════════════════
print("-" * 70)
print("B5 -- 12 start months x 5 window lengths: how many directions can one series argue?")
print("-" * 70)
starts = pd.date_range(daily.index.min(), periods=12, freq="MS")
lengths = (7, 14, 28, 56, 91)
n_rising, n_falling = 0, 0
results = []
for start in starts:
    for L in lengths:
        window = daily.loc[start: start + pd.Timedelta(days=L - 1)].dropna()
        if len(window) < max(3, L // 2):
            continue
        x = np.arange(len(window))
        slope, intercept = np.polyfit(x, window.to_numpy(), 1)
        results.append((start, L, slope))
        if slope > 0:
            n_rising += 1
        elif slope < 0:
            n_falling += 1
print(f"  {len(results)} combinations fitted. Rising trend: {n_rising}. Falling trend: {n_falling}.")
print("""
  Tufte's Lie Factor = (effect shown) / (effect in the data) ASSUMES there
  is one well-defined "effect in the data" to compare against -- a single
  start and end value the chart is representing. A cherry-picked window has
  no such anchor: the "effect in the data" changes depending on which
  window you pick, so the denominator of the formula is not a fixed
  number, it is a free parameter the analyst chose. You cannot divide by a
  choice.

  The honest substitute is exactly what this question does: report the
  FULL distribution of trends every window produces (both counts above),
  and say which single window you are using in the submitted figure and
  why -- fixed BEFORE looking at the result, in terms of which cycle it
  cancels (Part B.1), not which direction it shows.
""")

print("=" * 70)
print("End of Part B")
print("=" * 70)
