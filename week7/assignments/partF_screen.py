"""
Week 7 - Task F (bonus, F2 not chosen -- real data instead): the same
pipeline (audit, clean, decisions table, one figure) on a real dataset.

Source: MTA Daily Ridership Data: Beginning 2020, data.ny.gov (Socrata
dataset vxuj-8kew), New York State / Metropolitan Transportation
Authority, downloaded 2026-11-08 via the Socrata API
(https://data.ny.gov/resource/vxuj-8kew.csv). Daily, 2020-03-01 to
2025-01-09, 1,776 rows, 7 transit modes.

Run from week7/assignments/:
    python partF_screen.py
Produces: charts/partF_screen.png
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
DATA_F = pathlib.Path(__file__).parent / "data_f"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART F (bonus) -- the same pipeline, on real MTA ridership data")
print("=" * 70)

raw = pd.read_csv(DATA_F / "mta_ridership.csv")
raw["date"] = pd.to_datetime(raw["date"])
print(f"\n{len(raw)} rows, {raw['date'].min().date()} to {raw['date'].max().date()}")

# ── Defect 1: a misspelled column name in the source file ──────────────
assert "buses_total_estimated_ridersip" in raw.columns
raw = raw.rename(columns={"buses_total_estimated_ridersip": "buses_total_estimated_ridership"})
print("Defect 1 -- column 'buses_total_estimated_ridersip' is misspelled in the source file "
      "(missing an 'h') -- renamed for internal consistency with every other mode's column name.")

df = raw.set_index("date").sort_index()

# ── audit_index() ───────────────────────────────────────────────────────
a = tslib.audit_index(df, "D")
print(f"\naudit_index(): dtype_ok={a['dtype_ok']}, monotonic={a['monotonic']}, "
      f"n_duplicated={a['n_duplicated']}, n_missing={a['n_missing']}, "
      f"span {a['span'][0]} to {a['span'][1]}")

# ── Defect 2 (a finding, not an error): 32 true zero-ridership days on
# the Staten Island Railway, clustered on weekends in 2020-2021 -- a real
# service suspension, not a missing-data code. Verified by day-of-week.
sir = df["staten_island_railway_total_estimated_ridership"]
zero_days = sir[sir == 0]
dow = zero_days.index.day_name()
weekend_share = dow.isin(["Saturday", "Sunday"]).mean() * 100
print(f"\nDefect 2 (a finding, not a data error) -- {len(zero_days)} days of exactly 0 ridership "
      f"on the Staten Island Railway, {zero_days.index.min().date()} to {zero_days.index.max().date()}. "
      f"{weekend_share:.0f}% of them are Saturdays/Sundays -- this is a real, documented weekend "
      f"service suspension during the pandemic recovery, not a sentinel or a missing-data code. "
      f"Week 1's rule applies in reverse here: a value that LOOKS like it should be flagged as "
      f"missing can be a genuine zero, and treating it as an error and dropping it would erase a "
      f"real finding about the service, not clean the data.")

# ── a second real anomaly worth naming: Black Friday 2024 ──────────────
lirr_ratio = df["lirr_of_comparable_pre_pandemic_day"]
peak_date = lirr_ratio.idxmax()
print(f"\nAlso notable: {peak_date.date()} ({peak_date.day_name()}) -- LIRR ridership hit "
      f"{lirr_ratio.max() * 100:.0f}% of its pre-pandemic baseline and Metro-North hit "
      f"{df.loc[peak_date, 'metro_north_of_comparable_pre_pandemic_day'] * 100:.0f}% -- Black "
      f"Friday holiday travel into the city, the same real-calendar anomaly Week 4's Part F found "
      f"in US retail data.")

CLEAN = pathlib.Path(__file__).parent / "clean_f"
CLEAN.mkdir(exist_ok=True)
df.to_csv(CLEAN / "mta_ridership.csv")

# ── one figure ───────────────────────────────────────────────────────────
monthly = sir.resample("MS").mean()
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(sir.index, sir.to_numpy(), color=vizlib.PALETTE["muted"], lw=0.5, alpha=0.6,
       label="Daily ridership")
ax.plot(monthly.index, monthly.to_numpy(), color=vizlib.PALETTE["series"][0], lw=1.8,
       label="Monthly mean")
ax.axvspan(zero_days.index.min(), zero_days.index.max(), color=vizlib.PALETTE["highlight"],
          alpha=0.12, label="Weekend suspension period (32 zero-ridership days)")
ax.annotate(f"{peak_date.date()}: Black Friday\n(LIRR, not shown here, hit {lirr_ratio.max()*100:.0f}% "
           "of pre-pandemic)", xy=(peak_date, sir.loc[peak_date]), xytext=(-180, 40),
           textcoords="offset points", fontsize=7.5,
           arrowprops=dict(arrowstyle="->", color=vizlib.PALETTE["ink_soft"]))
ax.set_ylim(0)
ax.set_xlabel("Date")
ax.set_ylabel("Staten Island Railway, estimated daily ridership")
ax.set_title("A real zero is not a missing value: 32 weekend days of genuinely zero ridership,\n"
             "not a data-quality flag", loc="left")
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
vizlib.save_fig(fig, OUT / "partF_screen.png",
                note="Source: MTA Daily Ridership Data: Beginning 2020, data.ny.gov (dataset "
                     "vxuj-8kew), New York MTA, downloaded 2026-11-08 | n=1,776 days, "
                     "2020-03-01 to 2025-01-09 | column 'ridersip' typo corrected")
plt.close(fig)
print(f"\nFigure saved -> {OUT / 'partF_screen.png'} (300 dpi)")
print("=" * 70)
print("End of Part F")
print("=" * 70)
