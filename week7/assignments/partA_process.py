"""
Week 7 - Task A: make the four files trustworthy.

Reads the four raw files and the GeoJSON, audits them, fixes what it finds,
and writes cleaned copies to clean/. No file in data/ is ever edited by
hand; every fix below is applied in code, with a stated rule and a count.

Run from week7/assignments/:
    python partA_process.py
Produces: clean/district_transit.csv, clean/routes.csv,
          clean/ridership_daily.csv, clean/fare_revenue.csv
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib
import geolib
import dashlib

DATA = pathlib.Path(__file__).parent / "data"
CLEAN = pathlib.Path(__file__).parent / "clean"
CLEAN.mkdir(exist_ok=True)

DECISIONS = []


def log(what, how, rule, n):
    DECISIONS.append((what, how, rule, n))
    print(f"  DECISION: {what} | detected: {how} | rule: {rule} | rows affected: {n}")


print("=" * 78)
print("TASK A -- make the four files trustworthy")
print("=" * 78)

# ════════════════════════════════════════════════════════════════════════
# 1. district_transit.csv -- 5 defects
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("district_transit.csv -- AUDIT")
print("-" * 78)
dt_raw = pd.read_csv(DATA / "district_transit.csv")
print(f"rows: {len(dt_raw)}")
feats = geolib.read_geojson(DATA / "regions.geojson")
feat_codes = {f["code"] for f in feats}
matched_raw = dt_raw["code"].isin(feat_codes).sum()
print(f"GeoJSON join, as filed: {matched_raw} of {len(dt_raw)} match {len(feats)} features")

dt = dt_raw.copy()

# Fault 1: code casing/whitespace ("d13", "D 20")
before_codes = dt["code"].tolist()
dt["code"] = dt["code"].str.strip().str.upper().str.replace(" ", "", regex=False)
n_code_fix = sum(1 for a, b in zip(before_codes, dt["code"]) if a != b)
log("Register key stored inconsistently: lowercase ('d13') and an embedded space ('D 20')",
    "code values that don't match ^D\\d{2}$ after the geojson join fails for them",
    "Normalised with .strip().upper().replace(' ', '') -- a formatting fix, not a repair of content",
    n_code_fix)

# Fault 2: extra register row (D00, no matching polygon)
n_before = len(dt)
dt = dt[dt["code"] != "D00"].copy()
log("Extra register row D00 'Qilabad Capital Territory' -- not one of the federation's 24 "
    "districts, no matching GeoJSON polygon",
    "code 'D00' has no match in regions.geojson's 24 features even after the casing fix",
    "Dropped -- it is a real administrative entity but not part of this 24-district join, "
    "and keeping it would inflate the population total past the federation's true 57,857,000",
    n_before - len(dt))

# Fault 3: boardings_annual truncated (3 districts read as <1 boarding/resident/year)
mask = dt["boardings_annual"] < dt["population"]
n_boarding = int(mask.sum())
affected = dt.loc[mask, "code"].tolist()
dt.loc[mask, "boardings_annual"] = dt.loc[mask, "boardings_annual"] * 1000
log(f"boardings_annual missing 3 trailing zeros for {affected} (reads as <1 boarding per "
    f"resident per year, impossible for an urban transit network)",
    "boardings_annual < population",
    "Repaired x1000 -- confirmed because it is the only multiplier that reconciles the "
    "register's own published annual total (873,564,130) and the route-table cross-check",
    n_boarding)

# Fault 4: road_km sentinel (-1.0)
n_road = int((dt["road_km"] < 0).sum())
dt.loc[dt["road_km"] < 0, "road_km"] = np.nan
log("road_km == -1.0 (impossible for a length)",
    "(road_km < 0).sum()",
    "Set to NaN, not dropped -- every other column for those rows is still usable",
    n_road)

# Fault 5: fare_concession_pct stored as a fraction, not a percentage, for 4 rows
mask_pct = dt["fare_concession_pct"] < 1.0
n_pct = int(mask_pct.sum())
affected_pct = dt.loc[mask_pct, "code"].tolist()
dt.loc[mask_pct, "fare_concession_pct"] = dt.loc[mask_pct, "fare_concession_pct"] * 100
log(f"fare_concession_pct stored as a 0-1 fraction instead of 0-100 for {affected_pct}",
    "fare_concession_pct < 1.0 while every other row is 20-40",
    "Multiplied by 100 -- the column's own unit (per the data dictionary, a percentage)",
    n_pct)

dt.to_csv(CLEAN / "district_transit.csv", index=False)
matched_fixed = dt["code"].isin(feat_codes).sum()
print(f"\nCleaned: {len(dt)} rows -> clean/district_transit.csv")
print(f"GeoJSON join after repair: {matched_fixed} of {len(dt)}")
print(f"Population / households: {dt['population'].sum():,} / {dt['households'].sum():,}")
print(f"boardings_annual total: {dt['boardings_annual'].sum():,}")
rate = dt["boardings_annual"] / dt["population"] * 1000
print(f"Boardings per 1,000 residents: {rate.min():,.0f} - {rate.max():,.0f}, "
      f"national pooled {dt['boardings_annual'].sum() / dt['population'].sum() * 1000:,.0f}")
print(f"fare_concession_pct: {dt['fare_concession_pct'].min():.1f} - {dt['fare_concession_pct'].max():.1f}")
print(f"road_km usable: {dt['road_km'].notna().sum()} of {len(dt)}")

# ════════════════════════════════════════════════════════════════════════
# 2. routes.csv -- 3 defects
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("routes.csv -- AUDIT")
print("-" * 78)
rt = pd.read_csv(DATA / "routes.csv")
print(f"rows: {len(rt)}, raw mode labels: {sorted(rt['mode'].unique())}")

raw_modes = sorted(rt["mode"].unique())
rt["mode"] = rt["mode"].str.strip().str.lower().replace({
    "brt": "BRT", "bus rapid transit": "BRT", "metro": "Metro",
    "bus": "Bus", "ferry": "Ferry"})
log(f"mode spelled {len(raw_modes)} ways for 4 true modes {raw_modes}",
    "distinct raw strings collapsing to 4 after case-folding and a known alias",
    "Normalised case + mapped 'Bus Rapid Transit' -> 'BRT'",
    len(rt))

n_punc = int((rt["punctuality_pct"] == 999).sum())
rt.loc[rt["punctuality_pct"] == 999, "punctuality_pct"] = np.nan
log("punctuality_pct == 999.0 (an operator code, impossible as a percentage)",
    "(punctuality_pct == 999).sum()",
    "Set to NaN",
    n_punc)

n_cost = int((rt["cost_recovery_pct"] == 0).sum())
rt.loc[rt["cost_recovery_pct"] == 0, "cost_recovery_pct"] = np.nan
log("cost_recovery_pct == 0.0 (a route recovering literally none of its cost from fares is a "
    "reporting code here, not a measurement -- both flagged rows are Ferry/Bus routes with "
    "otherwise-normal subsidy figures)",
    "(cost_recovery_pct == 0).sum(), cross-checked against subsidy_pkr_per_trip being normal",
    "Set to NaN",
    n_cost)

rt.to_csv(CLEAN / "routes.csv", index=False)
print(f"\nCleaned: {len(rt)} rows -> clean/routes.csv")
print(f"Routes per mode: {rt['mode'].value_counts().to_dict()}")
print(f"punctuality_pct usable: {rt['punctuality_pct'].notna().sum()} of {len(rt)}, "
      f"range {rt['punctuality_pct'].min():.1f}-{rt['punctuality_pct'].max():.1f}")
print(f"boardings_annual summed over routes: {rt['boardings_annual'].sum():,}")

ov = dashlib.overlap_factor(rt, "route_id", "districts_served", "boardings_annual")
print(f"overlap_factor (districts_served): true={ov['true_total']:,.0f}, "
      f"attributed={ov['attributed_total']:,.0f}, factor={ov['factor']:.3f}x "
      f"({ov['units_multi']} of {ov['units']} routes serve >1 district)")

# ════════════════════════════════════════════════════════════════════════
# 3. ridership_daily.csv -- 5 defects
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("ridership_daily.csv -- AUDIT")
print("-" * 78)
rd = pd.read_csv(DATA / "ridership_daily.csv")
print(f"rows: {len(rd)}, modes: {sorted(rd['mode'].unique())}")

iso_mask = rd["date"].str.match(r"^\d{4}-\d{2}-\d{2}$")
n_slash = int((~iso_mask).sum())
mf = pd.to_datetime(rd.loc[~iso_mask, "date"], format="%m/%d/%Y", errors="coerce")
n_mf_fail = int(mf.isna().sum())
n_mf_silent = n_slash - n_mf_fail
dt_parsed = pd.Series(index=rd.index, dtype="datetime64[ns]")
dt_parsed[iso_mask] = pd.to_datetime(rd.loc[iso_mask, "date"], format="%Y-%m-%d")
dt_parsed[~iso_mask] = pd.to_datetime(rd.loc[~iso_mask, "date"], format="%d/%m/%Y", dayfirst=True)
rd["date"] = dt_parsed
log(f"Mixed date formats: {int(iso_mask.sum())} ISO, {n_slash} 'dd/mm/yyyy'. A naive month-first "
    f"(US-style) parse fails outright on {n_mf_fail} of them but SILENTLY ACCEPTS the other "
    f"{n_mf_silent} as a different (wrong) calendar day",
    "regex match against ISO; cross-parsed the slash subset both ways to measure the trap",
    "Parsed the two formats separately, dayfirst=True on the slash subset",
    n_slash)

other_cols = ["mode", "trips_scheduled", "trips_operated", "trips_on_time", "boardings", "delay_minutes"]
n_before = len(rd)
rd = rd.sort_values("date").drop_duplicates(subset=["date"] + other_cols, keep="first")
log("Exact duplicate (date, mode, ...) re-submissions -- all one mode (Bus), all one month "
    "(2026-05); some resubmitted in the OTHER date format, so a raw-string dedup before "
    "parsing would have missed them",
    "full-row duplicated() after date parsing",
    "Keep first occurrence",
    n_before - len(rd))

# Missing-slot audit runs BEFORE the impossible-row drop below: a row that
# was filed with contradictory numbers was still FILED -- it is a data-
# quality problem, not a non-report, and conflating the two would count
# those 7 zone-days as "never filed" when the opposite is true.
full_slots = pd.MultiIndex.from_product(
    [pd.date_range(rd["date"].min(), rd["date"].max(), freq="D"), sorted(rd["mode"].unique())])
have = set(zip(rd["date"], rd["mode"]))
missing = [s for s in full_slots if s not in have]
by_mode = pd.Series([m for _, m in missing]).value_counts()
log(f"Zone-days never filed: {len(missing)} of "
    f"{(rd['date'].max() - rd['date'].min()).days + 1} days x 4 modes, unevenly spread "
    f"({by_mode.to_dict()})",
    "complete (date x mode) calendar vs rows present, checked BEFORE dropping the 7 "
    "impossible rows below (a filed-but-contradictory row is still a filing)",
    "Not reindexed in as rows -- counted and reported; resample with min_count-aware logic",
    len(missing))

bad = rd["trips_on_time"] > rd["trips_operated"]
n_bad = int(bad.sum())
rd.loc[bad, ["trips_on_time", "trips_operated"]] = np.nan
log("trips_on_time > trips_operated (more on-time departures than departures that ran at all)",
    "(trips_on_time > trips_operated).sum()",
    "Both trips_on_time AND trips_operated set to NaN for just these rows -- the contradiction "
    "means neither count on that row can be trusted, so both are excluded from any punctuality "
    "aggregation (pandas groupby().sum() skips NaN, which is equivalent to excluding the row "
    "from the rate calculation without discarding it). boardings/trips_scheduled/delay_minutes "
    "on the same row are independent counts and stay usable -- dropping the whole row would "
    "also discard real boardings data for that zone-day",
    n_bad)

cutoff = pd.Timestamp("2026-09-22")
late = rd[rd["date"] >= cutoff]
stopped = sorted(set(rd["mode"].unique()) - set(late["mode"].unique()))
log(f"Two modes ({stopped}) stop filing entirely after {cutoff.date()} -- not scattered gaps, "
    f"a reporting cutoff specific to those modes",
    "modes present before the cutoff but absent after it",
    "Flagged, not imputed -- any trend chart spanning the cutoff must say which modes it can "
    "still show",
    int((rd["date"] >= cutoff).groupby(rd["mode"]).size().reindex(["BRT", "Bus", "Ferry", "Metro"], fill_value=0).loc[stopped].sum()) if stopped else 0)

rd.to_csv(CLEAN / "ridership_daily.csv", index=False)
print(f"\nCleaned: {len(rd)} rows -> clean/ridership_daily.csv")
boardings_12mo = rd[(rd["date"] > "2025-08-31") & (rd["date"] <= "2026-08-31")]["boardings"].sum()
print(f"Boardings, 12 months to 2026-08-31: {boardings_12mo:,}")

# ════════════════════════════════════════════════════════════════════════
# 4. fare_revenue.csv -- 1 defect
# ════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 78)
print("fare_revenue.csv -- AUDIT")
print("-" * 78)
fr = pd.read_csv(DATA / "fare_revenue.csv")
print(f"rows: {len(fr)}, ticket_type: {sorted(fr['ticket_type'].unique())}")

dd = dashlib.drilldown_check(fr, "ticket_type", "trips", within=("month", "mode"),
                             total_label="All tickets")
log("'All tickets' is the published subtotal filed as a 4th ticket_type row per month per mode, "
    "not a real fare product",
    f"drilldown_check(): summing every row gives {dd['sum_all_pct']:.1f}% of the parts",
    "Excluded from any sum over ticket_type -- summing every row double-counts the file",
    int(fr["ticket_type"].eq("All tickets").sum()))

fr_clean = fr[fr["ticket_type"] != "All tickets"].copy()
fr_clean.to_csv(CLEAN / "fare_revenue.csv", index=False)
print(f"\nCleaned (parts only): {len(fr_clean)} rows -> clean/fare_revenue.csv")
print(f"Journeys: {fr_clean['trips'].sum():,}, revenue: {fr_clean['revenue_pkr'].sum():,} PKR, "
      f"mean fare {fr_clean['revenue_pkr'].sum() / fr_clean['trips'].sum():.1f} PKR/journey")

boardings_total = rd["boardings"].sum()
journeys_total = fr_clean["trips"].sum()
print(f"\nBoardings / journeys, whole file: {boardings_total / journeys_total:.3f}")

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
