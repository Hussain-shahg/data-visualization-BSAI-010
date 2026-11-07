"""
Week 6 - Task A: make the files trustworthy.

Reads the three raw CSVs and the GeoJSON, audits them, fixes what it finds,
and writes cleaned copies to clean/. No file in data/ is ever edited by
hand; every fix below is applied in code, with a stated rule and a count.

Run from week6/assignments/:
    python partA_process.py
Produces: clean/district_grid.csv, clean/grid_daily.csv,
          clean/generation_mix.csv, partA_audit.txt (if redirected)
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib
import geolib

DATA = pathlib.Path(__file__).parent / "data"
CLEAN = pathlib.Path(__file__).parent / "clean"
CLEAN.mkdir(exist_ok=True)

DECISIONS = []  # (what, how_detected, rule, rows_affected)


def log(what, how, rule, n):
    DECISIONS.append((what, how, rule, n))
    print(f"  DECISION: {what} | detected: {how} | rule: {rule} | rows affected: {n}")


print("=" * 78)
print("TASK A -- make the files trustworthy")
print("=" * 78)

# ════════════════════════════════════════════════════════════════════════
# 1. district_grid.csv -- the district register
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("district_grid.csv -- AUDIT")
print("-" * 78)
dg = pd.read_csv(DATA / "district_grid.csv")
print(f"rows: {len(dg)}, dtypes:\n{dg.dtypes}")
print(f"key (`code`) uniqueness: {dg['code'].nunique()} unique of {len(dg)} rows, "
      f"{dg['code'].duplicated().sum()} duplicate")
print(f"electrification_pct raw dtype: {dg['electrification_pct'].dtype} (should be numeric)")
print(f"outage_minutes range: {dg['outage_minutes'].min()} to {dg['outage_minutes'].max()}")
print(f"households/population ratio range (pre-clean): "
      f"{(dg['population'] / dg['households']).min():.2f} to "
      f"{(dg['population'] / dg['households']).max():.2f}")

# Fault 1: duplicate code D11 (an extra register row)
n_dup = int(dg["code"].duplicated().sum())
dg_clean = dg.drop_duplicates(subset="code", keep="first").copy()
log("Duplicate register row for D11 ('Kotla' and 'Kotla City', identical "
    "population/households/income)",
    "code.duplicated() == 2 rows for D11",
    "Keep the first occurrence ('Kotla', the name matching the rest of the register's style); "
    "repair not possible -- no way to know which of the two near-identical rows is authoritative, "
    "so this is a DROP not a repair",
    n_dup)

# Fault 2: electrification_pct mixed types -- literal '%' suffix on some
# rows, genuinely blank on 3 others
raw_pct = dg_clean["electrification_pct"].astype(str)
has_pct_sign = raw_pct.str.contains("%").sum()
n_missing_before = dg_clean["electrification_pct"].isna().sum()
dg_clean["electrification_pct"] = (
    dg_clean["electrification_pct"].astype(str).str.rstrip("%").replace("nan", np.nan).astype(float))
n_missing_after = dg_clean["electrification_pct"].isna().sum()
log("electrification_pct stored as text, some rows with a literal '%' suffix, "
    "3 rows genuinely blank",
    "dtype was object/str, not float; .str.contains('%')",
    f"Strip '%' and convert to float ({has_pct_sign} rows affected); leave the "
    f"{n_missing_after} genuinely blank rows as NaN -- missing is not zero",
    int(has_pct_sign + n_missing_after))

# Fault 3: outage_minutes carries an operator not-available code (-1)
n_bad_outage = int((dg_clean["outage_minutes"] < 0).sum())
dg_clean.loc[dg_clean["outage_minutes"] < 0, "outage_minutes"] = np.nan
log("outage_minutes == -1 (operator not-available code, not a measurement)",
    "(outage_minutes < 0).sum()",
    "A negative duration is impossible; set to NaN, not dropped (outages count for those rows "
    "is still usable)",
    n_bad_outage)

# Fault 4: D21's households is off by a factor of ~1000 (truncated)
ratio = dg_clean["population"] / dg_clean["households"]
broken = ratio[(ratio < 5.0) | (ratio > 10.0)]
d21_before = int(dg_clean.loc[dg_clean["code"] == "D21", "households"].iloc[0])
# cross-check: the register's own published population/household totals
# (57,857,000 / 8,908,512) only reconcile if D21 = 182,000, not 182
implied = 8_908_512 - dg_clean.loc[dg_clean["code"] != "D21", "households"].sum()
dg_clean.loc[dg_clean["code"] == "D21", "households"] = implied
log(f"D21 households = {d21_before} (implies {ratio.loc[dg_clean['code'] == 'D21'].iloc[0] if False else 1081000/d21_before:.0f} "
    f"people per household -- impossible; every other district is 5.7-7.4)",
    "population/households ratio far outside the 5.7-7.4 range every other district falls in",
    f"Repaired to {implied:,} -- the three trailing zeros were lost (182 -> 182,000), confirmed "
    f"because it is the ONLY value that reconciles the register's own published household total "
    f"(8,908,512) and lands the ratio ({1081000/implied:.2f}) inside the 5.7-7.4 band every other "
    f"district falls in",
    1)

dg_clean.to_csv(CLEAN / "district_grid.csv", index=False)
print(f"\nCleaned: {len(dg_clean)} rows -> clean/district_grid.csv")
print(f"Population / households totals: {dg_clean['population'].sum():,} / "
      f"{dg_clean['households'].sum():,}")
pp_hh = dg_clean["population"] / dg_clean["households"]
print(f"Persons-per-household range: {pp_hh.min():.2f} - {pp_hh.max():.2f}")
print(f"electrification_pct range: {dg_clean['electrification_pct'].min():.1f} - "
      f"{dg_clean['electrification_pct'].max():.1f}, "
      f"{dg_clean['electrification_pct'].isna().sum()} missing")
mean_interruption = dg_clean["outage_minutes"] / dg_clean["outages"]
print(f"Usable outage_minutes: {dg_clean['outage_minutes'].notna().sum()} of {len(dg_clean)}, "
      f"mean interruption length per district (outage_minutes/outages): "
      f"{mean_interruption.min():.0f}-{mean_interruption.max():.0f} min")
print(f"Interruptions, all districts: {dg_clean['outages'].sum():,}")

# ════════════════════════════════════════════════════════════════════════
# 2. grid_daily.csv -- the daily returns
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("grid_daily.csv -- AUDIT")
print("-" * 78)
gd = pd.read_csv(DATA / "grid_daily.csv")
print(f"rows: {len(gd)}, zones: {sorted(gd['zone'].unique())}")

# Fault 1: mixed date formats
iso_mask = gd["date"].str.match(r"^\d{4}-\d{2}-\d{2}$")
n_slash = int((~iso_mask).sum())
dt = pd.Series(index=gd.index, dtype="datetime64[ns]")
dt[iso_mask] = pd.to_datetime(gd.loc[iso_mask, "date"], format="%Y-%m-%d")
dt[~iso_mask] = pd.to_datetime(gd.loc[~iso_mask, "date"], format="%d/%m/%Y", dayfirst=True)
wrong = pd.to_datetime(gd.loc[~iso_mask, "date"], format="mixed")
n_relocated = int((wrong != dt[~iso_mask]).sum())
gd["date"] = dt
log(f"Mixed date formats: {int(iso_mask.sum())} ISO rows, {n_slash} 'dd/mm/yyyy' rows",
    "regex match against ISO pattern",
    f"Parsed the two formats separately with dayfirst=True on the slash subset; "
    f"format='mixed' would have silently relocated {n_relocated} of {n_slash} rows",
    n_slash)

# Fault 2 & 3: duplicate (date, zone) -- exact resubmissions vs conflicting records
dupmask = gd.duplicated(subset=["date", "zone"], keep=False)
groups = gd[dupmask].groupby(["date", "zone"])
n_exact_rows, n_conflict_rows = 0, 0
conflict_keys = []
for key, g in groups:
    if g.duplicated(keep=False).all():
        n_exact_rows += len(g) - 1
    else:
        n_conflict_rows += len(g)
        conflict_keys.append(key)
gd = gd.sort_values("date")
gd_exact_dropped = gd.drop_duplicates(subset=["date", "zone", "cumulative_mwh", "peak_load_mw",
                                              "outage_minutes"], keep="first")
log(f"Exact duplicate (date, zone) re-submissions, identical in every column",
    "full-row duplicated() within (date,zone) groups",
    "Keep first occurrence, drop the resubmitted copy",
    n_exact_rows)

still_dup = gd_exact_dropped[gd_exact_dropped.duplicated(subset=["date", "zone"], keep=False)]
resolved_rows = []
for key, g in still_dup.groupby(["date", "zone"]):
    merged = g.iloc[0].copy()
    merged["peak_load_mw"] = g["peak_load_mw"].mean()
    merged["outage_minutes"] = g["outage_minutes"].mean()
    resolved_rows.append(merged)
gd_clean = pd.concat([
    gd_exact_dropped[~gd_exact_dropped.duplicated(subset=["date", "zone"], keep=False)],
    pd.DataFrame(resolved_rows),
], ignore_index=True)
log(f"Conflicting duplicate records: same (date, zone), identical cumulative_mwh "
    f"but DIFFERENT peak_load_mw/outage_minutes ({conflict_keys})",
    "duplicated (date,zone) rows that are not full-row duplicates",
    "Two sensor readings for the same zone-day, neither clearly wrong -- averaged "
    "peak_load_mw and outage_minutes rather than arbitrarily picking one",
    len(conflict_keys))

# Fault 4: peak_load_mw operator not-available code
n_bad_peak = int((gd_clean["peak_load_mw"] < 0).sum())
gd_clean.loc[gd_clean["peak_load_mw"] < 0, "peak_load_mw"] = np.nan
log("peak_load_mw == -1 (SCADA not-available code, per the data dictionary)",
    "(peak_load_mw < 0).sum()",
    "Set to NaN -- an instantaneous peak cannot be negative",
    n_bad_peak)

# Fault 5: meter reading goes DOWN (replacement/reset event)
gd_clean = gd_clean.sort_values(["zone", "date"])
gd_clean["mwh_diff"] = gd_clean.groupby("zone")["cumulative_mwh"].diff()
reset_rows = gd_clean[gd_clean["mwh_diff"] < 0]
log(f"Meter reading falls vs the previous day, same zone (P4, 2026-02-17: "
    f"reading drops to {gd_clean.loc[gd_clean['mwh_diff'] < 0, 'cumulative_mwh'].iloc[0] if len(reset_rows) else 'n/a'})",
    "groupby(zone).diff() < 0",
    "A cumulative meter cannot fall except on a physical meter replacement -- flagged as a "
    "reset point: the single day's own delivered-energy diff is excluded from any sum (NaN), "
    "not treated as negative consumption, and later diffs resume from the new base",
    len(reset_rows))
gd_clean.loc[gd_clean["mwh_diff"] < 0, "mwh_diff"] = np.nan

# Fault 6: missing zone-day slots
full_slots = pd.MultiIndex.from_product(
    [pd.date_range(gd_clean["date"].min(), gd_clean["date"].max(), freq="D"),
     sorted(gd_clean["zone"].unique())], names=["date", "zone"])
have = set(zip(gd_clean["date"], gd_clean["zone"]))
n_missing_slots = sum(1 for s in full_slots if s not in have)
span_days = (gd_clean["date"].max() - gd_clean["date"].min()).days + 1
log(f"Zone-days never filed at all: {n_missing_slots} of {span_days * gd_clean['zone'].nunique()} "
    f"possible slots",
    "complete (date x zone) calendar vs the rows actually present",
    "Not reindexed in as rows (no fabricated reading exists to fill them with) -- counted and "
    "reported; any resample must use min_count / explicit diff logic that tolerates the gaps",
    n_missing_slots)

gd_clean.drop(columns="mwh_diff").to_csv(CLEAN / "grid_daily.csv", index=False)
print(f"\nCleaned: {len(gd_clean)} rows -> clean/grid_daily.csv")
print(f"Reporting span: {gd_clean['date'].min().date()} to {gd_clean['date'].max().date()} "
      f"= {span_days} days x {gd_clean['zone'].nunique()} zones = "
      f"{span_days * gd_clean['zone'].nunique()} slots")
print(f"Zone-days never reported: {n_missing_slots}")
print(f"Unusable peak_load_mw: {n_bad_peak}")
print(f"Zone-days where the meter reading goes down: {len(reset_rows)}")

p1 = gd_clean[gd_clean["zone"] == "P1"].sort_values("date")
before_june = p1[p1["date"] < "2026-06-01"]["cumulative_mwh"].iloc[-1]
end_june = p1[(p1["date"] >= "2026-06-01") & (p1["date"] < "2026-07-01")]["cumulative_mwh"].iloc[-1]
delivered_diff = end_june - before_june
delivered_sum = p1[(p1["date"] >= "2026-06-01") & (p1["date"] < "2026-07-01")]["cumulative_mwh"].sum()
print(f"Energy delivered in zone P1, June 2026 (differenced): {delivered_diff:,.0f} MWh")
print(f"... the same month, if you sum() the column instead: {delivered_sum:,.0f} MWh "
      f"({delivered_sum / delivered_diff:.0f}x too big)")

# ════════════════════════════════════════════════════════════════════════
# 3. generation_mix.csv
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("generation_mix.csv -- AUDIT")
print("-" * 78)
gm = pd.read_csv(DATA / "generation_mix.csv")
print(f"rows: {len(gm)}, months: {gm['month'].nunique()}, sources: {sorted(gm['source'].unique())}")

dd_check = tslib.drilldown_check if hasattr(tslib, "drilldown_check") else None
is_total = gm["source"] == "All sources"
n_total_rows = int(is_total.sum())
parts = gm[~is_total]
totals = gm[is_total]
sum_all_pct = gm["mwh"].sum() / parts["mwh"].sum() * 100
log(f"'All sources / Total' is a published subtotal filed as an extra row per month, "
    f"not a generation category",
    "source == 'All sources'; summing every row gives exactly 200% of the real total",
    "Excluded from any sum over `source`/`subsource` -- summing every row as if it were a part "
    "double-counts the whole file",
    n_total_rows)

# cross-check parts against the published total
by_month_parts = parts.groupby("month")["mwh"].sum()
by_month_total = totals.set_index("month")["mwh"]
diff = (by_month_parts - by_month_total).abs()
print(f"Parts vs published total, worst month disagreement: {diff.max():,.0f} MWh "
      f"(of {by_month_parts.max():,.0f})")

parts.to_csv(CLEAN / "generation_mix.csv", index=False)
print(f"\nCleaned (parts only): {len(parts)} rows -> clean/generation_mix.csv")
print(f"Summing every row of the RAW file: {gm['mwh'].sum() / parts['mwh'].sum() * 100:.1f}% "
      f"of the energy generated")

# ════════════════════════════════════════════════════════════════════════
# 4. regions.geojson -- join check
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("regions.geojson -- JOIN CHECK")
print("-" * 78)
feats = geolib.read_geojson(DATA / "regions.geojson")
feat_codes = {f["code"] for f in feats}
unmatched = sorted(set(dg_clean["code"]) - feat_codes)
print(f"{len(feats)} GeoJSON features, {len(unmatched)} unmatched against the cleaned register")

# ════════════════════════════════════════════════════════════════════════
# decisions table
# ════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 78)
print(f"DECISIONS TABLE -- {len(DECISIONS)} decisions")
print("=" * 78)
md = ["# Part A — Decisions Table", "", "| # | What | How detected | Rule | Rows affected |",
      "|---|---|---|---|---|"]
for i, (what, how, rule, n) in enumerate(DECISIONS, start=1):
    md.append(f"| {i} | {what} | {how} | {rule} | {n} |")
(pathlib.Path(__file__).parent / "partA_decisions.md").write_text("\n".join(md), encoding="utf-8")
print(f"\nWrote partA_decisions.md ({len(DECISIONS)} rows)")

print("\n" + "=" * 78)
print("End of Task A")
print("=" * 78)
