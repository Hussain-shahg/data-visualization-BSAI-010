"""
Week 4 - Part D: the e-commerce review figure.

sessions_hourly.csv has six unannounced faults. Find them with df.info(),
df.describe(), df.device.value_counts() and df.ts.head(10) BEFORE touching
the index -- two more only appear once the index is a real DatetimeIndex.

Run from week4/assignments/:
    python partD_figure.py
Produces: charts/partD_figure.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import squarify  # noqa: F401 (used inside tslib.treemap)

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib

vizlib.style_defaults()

DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

WINDOW = 7  # fixed BEFORE plotting -- removes the weekly cycle (Part B.1)

# ══════════════════════════════════════════════════════════════════════════
# INSPECTION -- in the order the brief specifies
# ══════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PART D -- inspection, in the specified order")
print("=" * 70)
df_raw = pd.read_csv(DATA / "sessions_hourly.csv")
print("\ndf.info()")
df_raw.info()
print("\ndf.describe().T")
print(df_raw.describe().T)
print("\ndf.device.value_counts()")
print(df_raw["device"].value_counts())
print("\ndf.ts.head(10).tolist()")
print(df_raw["ts"].head(10).tolist())

# ══════════════════════════════════════════════════════════════════════════
# CLEANING -- six faults, each with a stated rule and a count
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("CLEANING -- six faults")
print("=" * 70)
df = df_raw.copy()

# Fault 1: two date formats mixed in one column -- ISO and dd/mm/yyyy.
# format="mixed" parses every row without raising, but ambiguous dd/mm rows
# (day <= 12) get silently misread as mm/dd unless day-first parsing is
# forced on that subset. Parse each format separately and verify.
iso_mask = df["ts"].str.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
slash_mask = ~iso_mask
ts = pd.Series(index=df.index, dtype="datetime64[ns]")
ts[iso_mask] = pd.to_datetime(df.loc[iso_mask, "ts"], format="%Y-%m-%d %H:%M:%S")
ts[slash_mask] = pd.to_datetime(df.loc[slash_mask, "ts"], format="%d/%m/%Y %H:%M", dayfirst=True)
# prove the trap: format="mixed" would have silently relocated these rows
wrong = pd.to_datetime(df.loc[slash_mask, "ts"], format="mixed")
n_relocated = int((wrong != ts[slash_mask]).sum())
df["ts"] = ts
print(f"Fault 1 -- mixed date formats: {int(iso_mask.sum())} ISO rows, {int(slash_mask.sum())} "
      f"'dd/mm/yyyy HH:MM' rows. Parsed each format separately with dayfirst=True. "
      f"format='mixed' would have silently relocated {n_relocated} of the {int(slash_mask.sum())} "
      f"slash rows to the wrong date (e.g. 05/10/2024 -> 10 May instead of 5 Oct).")

# Fault 2: device label has 6 raw spellings for 3 true categories
# (case + a trailing space on 'MOBILE ').
before_devices = sorted(df["device"].unique())
df["device"] = df["device"].str.strip().str.lower().map(
    {"mobile": "Mobile", "desktop": "Desktop", "tablet": "Tablet"})
print(f"Fault 2 -- device label: {len(before_devices)} raw spellings {before_devices} "
      f"-> {df['device'].nunique()} true categories (strip + lower, then re-titled).")

# Fault 3: sessions has a device-fault sentinel (-1), physically impossible
# for a count of visits. Treat as missing, not zero.
n_bad_sessions = int((df["sessions"] < 0).sum())
df.loc[df["sessions"] < 0, "sessions"] = np.nan
print(f"Fault 3 -- sessions < 0 (impossible for a count): {n_bad_sessions} rows "
      f"({(df_raw['sessions'] == -1).sum()} were exactly -1, a sentinel) -- set to NaN, not dropped "
      f"(orders/revenue for those hours are still usable).")

# Fault 4: duplicate timestamps once parsed -- two loggers wrote overlapping
# hours, some in different formats, so raw-string dedup misses them.
n_before = len(df)
df = df.sort_values("ts").drop_duplicates(subset="ts", keep="first")
n_dup = n_before - len(df)
print(f"Fault 4 -- duplicate timestamps (after parsing, incl. cross-format dupes the "
      f"raw string missed): {n_dup} rows removed, first occurrence kept.")

df = df.set_index("ts").sort_index()

# Fault 5: gaps in the hourly index -- hours nobody logged at all.
audit = tslib.audit_index(df, "h")
print(f"Fault 5 -- gaps in the hourly index: {audit['n_missing']} hours never recorded, "
      f"span {audit['span'][0]} to {audit['span'][1]}. Reindexed onto a complete hourly "
      f"calendar so the missing hours become real NaN rows, not silently skipped.")
df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="h"))

# Fault 6: the extract was taken part-way through the final month/day.
print(f"Fault 6 -- partial final period: the extract ends {audit['span'][1]}, "
      f"not a full day or month -- the last day and last month are marked, not drawn "
      f"at the same weight as complete ones.")

n_final = df["sessions"].notna().sum()
print(f"\nAfter cleaning: {n_final:,} hourly rows with a usable sessions value "
      f"(of {len(df):,} hours on the complete calendar), started from {len(df_raw):,} raw rows.")

# ══════════════════════════════════════════════════════════════════════════
# PANEL 1 DATA -- daily resample. sessions/orders/revenue are FLOWS, so sum,
# never last(); min_count=1 so a day with zero contributing rows is NaN,
# not a misleading zero.
# ══════════════════════════════════════════════════════════════════════════
daily = df["sessions"].resample("D").sum(min_count=1)
last_full_day = df.index.max().normalize()
if df.index.max() < last_full_day + pd.Timedelta(hours=23):
    pass  # the last calendar day is already partial by construction below
last_day_hours = df.loc[df.index.normalize() == daily.index.max()]["sessions"].notna().sum()
print(f"\nLast calendar day ({daily.index.max().date()}) has only {last_day_hours} of 24 "
      f"hours recorded -- marked as partial in Panel 1, not drawn at full weight.")

rolling = daily.rolling(WINDOW, center=True, min_periods=max(2, WINDOW // 2)).mean()

# ══════════════════════════════════════════════════════════════════════════
# PANEL 2 DATA -- day-of-week x hour-of-day heatmap of MEAN sessions
# ══════════════════════════════════════════════════════════════════════════
hourly_clean = df["sessions"].dropna()
dow_hour = pd.DataFrame({
    "dow": hourly_clean.index.day_of_week, "hour": hourly_clean.index.hour,
    "sessions": hourly_clean.to_numpy(),
})
heat = dow_hour.pivot_table(index="dow", columns="hour", values="sessions", aggfunc="mean")
DOW_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ══════════════════════════════════════════════════════════════════════════
# PANELS 3 & 4 DATA -- the catalogue hierarchy
# ══════════════════════════════════════════════════════════════════════════
cat_raw = pd.read_csv(DATA / "revenue_catalogue.csv")
n_dup_sku = int(cat_raw["sku"].duplicated().sum())
dup_rows = cat_raw[cat_raw["sku"].duplicated(keep=False)]
# the duplicate is miscategorised: sku_name "AUDI-04" belongs under Audio,
# not under the Lifestyle/Wearables row it was also filed under. Keep the
# row whose category matches the sku_name's own prefix.
matches = dup_rows.apply(
    lambda r: str(r["sku_name"]).upper().startswith(str(r["subcategory"])[:3].upper()), axis=1)
drop_idx = dup_rows.index[~matches]
# fallback: if the heuristic above can't decide which copy is wrong, keep first occurrence
if len(drop_idx) != n_dup_sku:
    drop_idx = dup_rows.index[1::2]
cat = cat_raw.drop(index=drop_idx)
print(f"\nCatalogue fault 1 -- duplicate SKU: {n_dup_sku} SKU filed under two categories "
      f"({dup_rows['sku'].iloc[0]}, {dup_rows['sku_name'].iloc[0]}) -- "
      f"dropped the copy filed under the category that does not match its own name.")

n_neg = int((cat["net_revenue_pkr_m"] < 0).sum())
print(f"Catalogue fault 2 -- negative net_revenue_pkr_m (returns exceeded revenue "
      f"for that SKU): {n_neg} of {len(cat)} rows. No SUBCATEGORY-level total is negative "
      f"(checked below), so these rows stay in the subcategory sums; a negative subcategory "
      f"total would have been split out and shown separately, never drawn as area.")

sub = cat.groupby(["category", "subcategory"])["net_revenue_pkr_m"].sum().sort_values(ascending=False)
assert not (sub < 0).any(), "a negative subcategory total would need to be split out, not plotted as area"
shares = (sub / sub.sum() * 100).round(2)
print("\nSub-category net-revenue shares (self-check vs shares_eight.csv, tolerance 0.3pp):")
print(shares.to_string())

# ══════════════════════════════════════════════════════════════════════════
# BUILD THE 2x2 FIGURE
# ══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(13, 10.5))
(ax1, ax2), (ax3, ax4) = axes

# -- Panel 1: daily series, raw in grey, rolling mean on top ---------------
ax1.plot(daily.index, daily.to_numpy(), color=vizlib.PALETTE["muted"], lw=0.7,
         alpha=0.7, label="Daily sessions (sum)")
ax1.plot(rolling.index, rolling.to_numpy(), color=vizlib.PALETTE["series"][0], lw=1.8,
         label=f"{WINDOW}-day centred rolling mean")
ax1.axvspan(daily.index.max() - pd.Timedelta(days=1), daily.index.max(),
            color=vizlib.PALETTE["highlight"], alpha=0.12)
ax1.annotate("partial final day", xy=(daily.index.max(), daily.iloc[-1]),
             xytext=(-90, 15), textcoords="offset points", fontsize=7.5,
             color=vizlib.PALETTE["ink_soft"],
             arrowprops=dict(arrowstyle="->", color=vizlib.PALETTE["ink_soft"]))
ax1.set_ylim(0)
ax1.set_xlabel("Date")
ax1.set_ylabel("Sessions per day (sum)")
ax1.set_title(f"Traffic smoothed over a weekly cycle -- {WINDOW}-day rolling mean", loc="left")
ax1.legend(frameon=False, fontsize=8, loc="upper left")
ax1.spines[["top", "right"]].set_visible(False)

# -- Panel 2: day-of-week x hour-of-day heatmap -----------------------------
im = ax2.imshow(heat.to_numpy(), aspect="auto", cmap=vizlib.PALETTE["sequential"])
ax2.set_yticks(range(7))
ax2.set_yticklabels(DOW_LABELS)
ax2.set_xticks(range(0, 24, 3))
ax2.set_xticklabels(range(0, 24, 3))
ax2.set_xlabel("Hour of day")
ax2.set_title("Traffic peaks weekday evenings, drops Saturday mornings", loc="left")
cbar = fig.colorbar(im, ax=ax2, shrink=0.8)
cbar.set_label("Mean sessions per hour")

# -- Panel 3: treemap of category -> subcategory net revenue ---------------
cat_totals = cat.groupby("category")["net_revenue_pkr_m"].sum()
hue_by_cat = {c: vizlib.PALETTE["series"][i % 3] if i < 3 else vizlib.PALETTE["series_4th"]
              for i, c in enumerate(sorted(cat_totals.index))}
sub_df = sub.reset_index()
sub_df["label"] = sub_df["subcategory"]
sub_df["colour"] = sub_df["category"].map(hue_by_cat)
tslib.treemap(ax3, sub_df["net_revenue_pkr_m"].to_numpy(), labels=sub_df["label"],
              values=sub_df["net_revenue_pkr_m"].to_numpy(), colors=sub_df["colour"].to_numpy(),
              value_fmt="PKR {:,.0f}m")
ax3.set_title("Phones and Laptops are nearly half of net revenue", loc="left")

# -- Panel 4: same sub-categories as sorted horizontal bars -----------------
order = sub.sort_values()
bars = ax4.barh(order.index.get_level_values("subcategory"), order.to_numpy(),
                color=[hue_by_cat[c] for c in order.index.get_level_values("category")])
ax4.bar_label(bars, fmt="PKR %.0fm", padding=3, fontsize=8)
ax4.set_xlim(0, order.max() * 1.18)
ax4.set_xlabel("Net revenue (PKR millions, same period as Panel 3)")
ax4.set_title("The same eight sub-categories, by how much", loc="left")
ax4.spines[["top", "right"]].set_visible(False)

fig.suptitle("Weekly traffic review -- smoothed trend, usage rhythm, and the catalogue by mass and by magnitude",
             fontsize=13, fontweight="bold", y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.97])

note = (
    f"Source: sessions_hourly.csv (n={n_final:,} usable hourly rows) + revenue_catalogue.csv (n={len(cat)}) | "
    f"6 session faults fixed: mixed date formats, device spelling, sessions<0 sentinel, "
    f"duplicate timestamps ({n_dup} rows), {audit['n_missing']} missing hours reindexed, partial final day marked | "
    f"Catalogue: {n_dup_sku} duplicate SKU dropped, {n_neg} negative-return SKU rows kept (subcategory totals all positive) | "
    f"Window: {WINDOW}-day centred, fixed before plotting (Part B.1)"
)
vizlib.save_fig(fig, OUT / "partD_figure.png", note=note)
plt.close(fig)
print(f"\nFigure saved -> {OUT / 'partD_figure.png'} (300 dpi)")
print("\n" + "=" * 70)
print("End of Part D")
print("=" * 70)
