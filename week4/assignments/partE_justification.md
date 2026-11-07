# Part E — Written Justification
**Week 4 Data Visualisation Assignment | Roll No: BSAI-010**

## 1. Per panel: question, chart type, Week 2 channel rule

**Panel 1 — daily sessions, raw + 7-day rolling mean.** Question: *is traffic actually trending, underneath the weekly rhythm?* Position on a common vertical scale (Cleveland & McGill rank 1) carries both the raw line and the smoothed line; the raw series stays in light grey so the smoothing is a layer, not an erasure (Week 4 rule: keep the raw series).

**Panel 2 — day-of-week × hour-of-day heatmap.** Question: *when, within a week, does traffic actually happen?* Hue/lightness on a sequential colormap (one hue, dark = more) is the right channel for a quantity spread over two categorical axes where no single pair of bars could show the interaction; this is Week 3's rule (sequential colormap, never rainbow) applied to two dimensions at once.

**Panel 3 — treemap of category → sub-category net revenue.** Question: *where does the mass of the catalogue sit?* Area is the channel (Cleveland & McGill's weakest, acknowledged explicitly — which is why every block also carries its value as text, Week 4's rule for hierarchies).

**Panel 4 — sorted horizontal bars of the same sub-categories.** Question: *by how much does one sub-category beat another?* Position along a common axis (rank 1) answers the question area cannot: precise pairwise comparison. Panels 3 and 4 are Lecture 8's argument side by side — containment vs magnitude — not two views of the same idea.

## 2. Every time decision, named and defended

- **Parse:** `sessions_hourly.csv` mixes ISO (`%Y-%m-%d %H:%M:%S`, 9,019 rows) and slash (`%d/%m/%Y %H:%M`, 3,651 rows) timestamps. Each format was parsed **separately** with `dayfirst=True` on the slash subset. Checked against the trap: `format="mixed"` would have silently relocated 1,382 of those 3,651 rows to the wrong calendar date (e.g. `05/10/2024` → 10 May instead of 5 Oct) — caught by comparing `format="mixed"` output against the explicit per-format parse, not by trusting row counts.
- **Aggregation:** `sessions` is a flow (visits *beginning in* that hour), so the daily series is `.resample("D").sum(min_count=1)` — never `.last()`, and `min_count=1` so a day with zero contributing hourly rows reports `NaN`, not a misleading `0`.
- **Window:** 7 days, fixed *before* plotting (see the ethics clause below and Part B.1) — the smallest window that fully cancels the weekly cycle, which is the one rhythm a Monday review already expects and should not have to re-discover every week.
- **Centred, not trailing, in the submitted figure:** Part D's Panel 1 is a retrospective weekly review, not a live feed, so it uses a **centred** 7-day mean — it does not need to guess at a turning point the way a live dashboard does (Part B.4). If this chart were rebuilt as a live, daily-refreshed dashboard, it would have to switch to a trailing window and say so in the caption.

## 3. Every row removed, rule, count

| # | What | Rule | Rows affected | Moved from → to |
|---|---|---|---|---|
| 1 | `sessions < 0` | Physically impossible for a count of visits; treated as a device-fault sentinel (290 of the 290 bad rows were exactly `-1`) | 290 of 12,670 | Set to `NaN` (not dropped — `orders`/`revenue_pkr` for those hours are still usable) |
| 2 | Duplicate timestamps (after parsing, including cross-format duplicates the raw string missed) | Two loggers wrote overlapping hours; first occurrence kept | 286 of 12,670 | Removed from the hourly table entirely |
| 3 | Catalogue: duplicate SKU `SKU-0127` ("AUDI-04") filed under both *Audio* and *Wearables* | Kept the copy whose category matches the SKU name's own prefix (Audio); the Wearables copy was a mis-filing | 1 of 345 | Removed from `Lifestyle → Wearables`, kept in `Audio & Imaging → Audio` |
| 4 | Catalogue: `net_revenue_pkr_m < 0` (returns exceeded that SKU's revenue) | Kept — these are genuine small SKUs where returns legitimately outran sales that period, and no sub-category *total* goes negative once summed (checked explicitly before drawing any area) | 7 of 344 | Stayed in their sub-category sums |

**Missing-period handling (not a drop):** 312 of 12,696 hours on the complete calendar were never logged at all. These were **reindexed in as real `NaN` rows**, not dropped and not filled with 0 — the daily resample's `min_count=1` then correctly turns any day built entirely from such hours into a gap in the line rather than a false zero.

## 4. Every level rolled up

Panel 3's hierarchy is `category → sub-category`, 4 categories and 8 sub-categories, no further SKU-level drill. `tslib.rollup_other()` was run at the standard 1% threshold and found **nothing to roll up**: the smallest sub-category (Drones) is still 2.4% of net revenue, so every one of the 8 blocks is independently meaningful and none were folded into an `Other` bucket. Eight panels is above the 4±1 rule of thumb, but each is individually labelled with its own value printed on the block (Week 4's hierarchy rule) and on the companion bar chart, so no block is competing for attention it cannot earn — the rule is satisfied by declaring that the check was made and nothing qualified, not by forcing a rollup the data does not support.

## The ethics clause

The window was fixed at **7 days before plotting**, because the cycle being removed is weekly (Part B.1) — the chart is reviewed every Monday, and a 7-day window is the smallest one that fully cancels that specific rhythm without also flattening real month-level movement (as 28- or 91-day windows would).

The series is shown from its first recorded day (2024-04-01); no start date was selected to flatter or flatten any particular trend.

Part B.5's sweep is the evidence this was not an after-the-fact choice: of 60 start-month × window-length combinations on this same unchanged series, 32 produce a rising trend and 28 a falling one — a start date or window length picked *after* looking at the result could have argued either direction. The 7-day centred window used here was chosen for the cycle it cancels, stated above, not for the direction it shows.

Applying Week 2's symmetry test to this page itself: yes — the 7-day choice would have been made identically whether the underlying trend turned out to be rising or falling, because the justification (cancel the weekly cycle) never refers to the direction of the series at all.

---

*Submitted by: M. Hussain Shah | m.hussain103shah@gmail.com | BSAI-010*
*Dataset: synthetic, generated for CDB601220, Superior University Lahore*
*Tools: Python 3.12, pandas, numpy, matplotlib, statsmodels, squarify, vizlib + tslib (course toolkits)*
