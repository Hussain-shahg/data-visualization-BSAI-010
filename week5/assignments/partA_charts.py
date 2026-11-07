"""
Week 5 - Part A: Rebuild nine charts, then take them apart.

Every chart here is arithmetically correct, properly labelled and often
colour-blind safe -- the trap this week is a chart that is beautiful and
wrong: the lying channel or the lying boundary, not a drawing mistake.

Run from week5/assignments/:
    python partA_charts.py
Produces: charts/caseXX_misleading.png and charts/caseXX_honest.png
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import geolib

vizlib.style_defaults()


def _corr_chain_patched(df, cols):
    """geolib.corr_chain(), with one line changed: pandas >= 3.0 makes CoW
    permanent (the 'mode.copy_on_write' option is removed), so .corr().abs()
    now returns a read-only array and the original's np.fill_diagonal(r.values, ...)
    raises. geolib.py is kept byte-identical on disk (it is this week's
    toolkit, unchanged); this wrapper is monkey-patched in at runtime only,
    and documented here and in Part E."""
    cols = list(cols)
    r = df[cols].corr().abs()
    vals = r.to_numpy(copy=True)
    np.fill_diagonal(vals, 0.0)
    r = pd.DataFrame(vals, index=r.index, columns=r.columns)
    i, j = np.unravel_index(np.argmax(r.to_numpy()), r.shape)
    order = [cols[i], cols[j]]
    while len(order) < len(cols):
        rest = [c for c in cols if c not in order]
        order.append(max(rest, key=lambda c: r.loc[order[-1], c]))
    return order


geolib.corr_chain = _corr_chain_patched

DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
# CASE 1 - "Population and healthcare access are unrelated" - size driven
# by pop_m**2 passed straight to s=, so the mark's AREA scales as pop_m^4,
# not pop_m. Small countries become literally invisible.
# ══════════════════════════════════════════════════════════════════════════
def case01():
    df = pd.read_csv(DATA / "health_indicators.csv")
    s_wrong = df["pop_m"] ** 2
    pop_ratio = df["pop_m"].max() / df["pop_m"].min()
    area_ratio = s_wrong.max() / s_wrong.min()
    print(f"Case 01 check -- {len(df)} marks. Population ratio max/min = {pop_ratio:.0f}x; "
          f"since s=pop_m**2, the drawn AREA ratio is {pop_ratio:.0f}^2 = {area_ratio:,.0f}x. "
          f"Countries with pop<2.0M smaller than a single point (s<2): {(df['pop_m'] < 2.0).sum()}")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(df["gdp_pc"], df["healthcare_access"], s=s_wrong,
               color=vizlib.PALETTE["series"][0], alpha=0.55, edgecolor="white", lw=0.4)
    ax.set_xscale("log")
    ax.set_xlabel("GDP per capita (USD, log scale)")
    ax.set_ylabel("Healthcare access (0-100)")
    ax.set_title("Population and healthcare access are unrelated -- the large countries\n"
                 "are spread right across the range")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case01_misleading.png",
                    note=f"Source: health_indicators.csv | n={len(df)} | s=pop_m**2 (AREA scales as pop_m^4)")
    plt.close(fig)

    # honest redesign: area legally proportional to pop_m (s is area in pt^2,
    # so pass the value directly and scale via sizes=)
    lo_pt, hi_pt = 20, 1200
    rng = df["pop_m"].max() - df["pop_m"].min()
    s_right = lo_pt + (df["pop_m"] - df["pop_m"].min()) / rng * (hi_pt - lo_pt)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sc = ax.scatter(df["gdp_pc"], df["healthcare_access"], s=s_right,
                    color=vizlib.PALETTE["series"][0], alpha=0.55, edgecolor="white", lw=0.4)
    ax.set_xscale("log")
    ax.set_xlabel("GDP per capita (USD, log scale)")
    ax.set_ylabel("Healthcare access (0-100)")
    ax.set_title("Legally area-scaled: the largest 9 countries by population cluster at\n"
                 "mid-to-high access -- the earlier chart hid them entirely")
    for v, lbl in [(df["pop_m"].min(), f"{df['pop_m'].min():.1f}M"),
                   (df["pop_m"].median(), f"{df['pop_m'].median():.0f}M"),
                   (df["pop_m"].max(), f"{df['pop_m'].max():.0f}M")]:
        pt = lo_pt + (v - df["pop_m"].min()) / rng * (hi_pt - lo_pt)
        ax.scatter([], [], s=pt, color=vizlib.PALETTE["muted"], alpha=0.6, label=lbl)
    ax.legend(title="Population", frameon=False, fontsize=8, labelspacing=1.4, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case01_honest.png",
                    note=f"Source: health_indicators.csv | n={len(df)} | area legally proportional to pop_m, sizes=({lo_pt},{hi_pt})pt2")
    plt.close(fig)
    print("  Case 01 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 2 - "Outbreak concentrated in the three districts around the capital"
# - a RAW COUNT choropleth. The top-3 districts by count are simply the
# most populous; the map is a population map wearing a disease map's title.
# ══════════════════════════════════════════════════════════════════════════
def case02():
    df = pd.read_csv(DATA / "district_health.csv")
    feats = geolib.read_geojson(DATA / "districts.geojson")
    total_cases = df["cases"].sum()
    total_pop = df["population"].sum()
    top3 = df.sort_values("cases", ascending=False).head(3)["code"].tolist()
    print(f"Case 02 check -- {len(df)} districts, {total_cases:,} cases, population {total_pop:,}. "
          f"Top 3 by count: {top3}")
    r_pop = stats.pearsonr(df["cases"], df["population"])[0]
    print(f"  r(cases, population) = {r_pop:.3f} -- the count map IS a population map")

    fig, ax = plt.subplots(figsize=(6, 6.5))
    geolib.choropleth(ax, feats, dict(zip(df["code"], df["cases"])), scheme="natural", k=5,
                      legend_title="Cases (count)")
    ax.set_title("Outbreak concentrated in the three districts around the capital", loc="left")
    vizlib.save_fig(fig, OUT / "case02_misleading.png",
                    note="Source: district_health.csv + districts.geojson | RAW COUNT choropleth, natural breaks k=5")
    plt.close(fig)

    rate = (df["cases"] / df["population"] * 1e5)
    top3_rate = df.assign(rate=rate).sort_values("rate", ascending=False).head(3)["code"].tolist()
    fig, ax = plt.subplots(figsize=(6, 6.5))
    geolib.choropleth(ax, feats, dict(zip(df["code"], rate)), scheme="natural", k=5,
                      legend_title="Cases per 100,000 residents")
    ax.set_title(f"Normalised: the top-3 by rate ({', '.join(top3_rate)}) are NOT the top-3 by\n"
                 f"count (r(cases,pop)={r_pop:.2f}) -- the raw map just shows where people live", loc="left")
    vizlib.save_fig(fig, OUT / "case02_honest.png",
                    note="Source: district_health.csv + districts.geojson | cases per 100,000 residents, natural breaks k=5")
    plt.close(fig)
    print("  Case 02 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 3 - "GDP per capita barely varies" - min-max scaling crushed by one
# extreme outlier (a single $120k country vs a $283-6k rest).
# ══════════════════════════════════════════════════════════════════════════
def case03():
    df = pd.read_csv(DATA / "health_indicators.csv")
    cols = ["gdp_pc", "healthcare_access", "urban_pct", "median_age", "cases_per_100k"]
    scaled = geolib.scale_frame(df, cols, "minmax")
    below = (scaled["gdp_pc"] < 0.10).sum()
    print(f"Case 03 check -- after min-max scaling, {below} of {len(df)} countries sit below "
          f"0.10 on gdp_pc, median {scaled['gdp_pc'].median():.3f}")
    outlier = df.loc[df["gdp_pc"].idxmax()]
    second = df["gdp_pc"].nlargest(2).iloc[1]
    print(f"  Outlier: {outlier['country']} at ${outlier['gdp_pc']:,}, "
          f"{outlier['gdp_pc'] / second:.1f}x the second-largest (${second:,.0f})")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    geolib.pcp(ax, df, cols, how="minmax")
    ax.set_title("GDP per capita barely varies across the sample -- the axis is almost flat", loc="left")
    vizlib.save_fig(fig, OUT / "case03_misleading.png",
                    note="Source: health_indicators.csv | min-max scaled, 5 axes")
    plt.close(fig)

    scaled_rank = geolib.scale_frame(df, cols, "rank")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    geolib.pcp(ax1, df, cols, how="minmax")
    ax1.set_title(f"min-max: 1 outlier ({outlier['country']}) crushes 58/60 countries\n"
                 "below 0.10 -- the axis LOOKS flat only because of one point", fontsize=9)
    geolib.pcp(ax2, df, cols, how="rank")
    ax2.set_title("percentile RANK: the same 60 countries, same axis -- real spread\n"
                 "across the full 0-1 range, immune to the one outlier", fontsize=9)
    vizlib.save_fig(fig, OUT / "case03_honest.png",
                    note="Source: health_indicators.csv | min-max (left, same as misleading) vs percentile rank (right)")
    plt.close(fig)
    print("  Case 03 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 4 - "Healthcare access and case rate are unrelated -- no crossing
# pattern" - columns left in FILE order, so the two axes that are actually
# strongly correlated sit three apart, far too far to see the crossing.
# ══════════════════════════════════════════════════════════════════════════
def case04():
    df = pd.read_csv(DATA / "health_indicators.csv")
    file_order = ["gdp_pc", "healthcare_access", "urban_pct", "median_age", "cases_per_100k"]
    gap = abs(file_order.index("healthcare_access") - file_order.index("cases_per_100k"))
    r_direct = stats.pearsonr(df["healthcare_access"], df["cases_per_100k"])[0]
    print(f"Case 04 check -- 5 axes in file order, healthcare_access/cases_per_100k are "
          f"{gap} apart. r(healthcare_access, cases_per_100k) = {r_direct:.3f}")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    geolib.pcp(ax, df, file_order, how="minmax")
    ax.set_title("Healthcare access and case rate are unrelated -- no crossing pattern\n"
                 "between them (axes in file order)", loc="left")
    vizlib.save_fig(fig, OUT / "case04_misleading.png",
                    note="Source: health_indicators.csv | axis order = FILE ORDER (not computed)")
    plt.close(fig)

    chain = geolib.corr_chain(df, file_order)
    gap_chain = abs(chain.index("healthcare_access") - chain.index("cases_per_100k"))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    geolib.pcp(ax, df, chain, how="minmax")
    ax.set_title(f"Reordered by corr_chain(): healthcare_access and case rate are now "
                 f"adjacent (r={r_direct:.2f}) -- a clear X-shaped waist is visible", loc="left")
    vizlib.save_fig(fig, OUT / "case04_honest.png",
                    note=f"Source: health_indicators.csv | axis order computed by geolib.corr_chain(): {' -> '.join(chain)}")
    plt.close(fig)
    print(f"  corr_chain order: {' -> '.join(chain)}, gap now {gap_chain}")
    print("  Case 04 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 5 - "Clear five-level gradient across the federation" - quantile
# classification invents 5 visually distinct classes out of a rate that
# only spans 7.2% of its own mean -- noise, not a gradient.
# ══════════════════════════════════════════════════════════════════════════
def case05():
    df = pd.read_csv(DATA / "case05_flat_rates.csv")
    feats = geolib.read_geojson(DATA / "districts.geojson")
    rate = df["cases"] / df["population"] * 1e5
    spread_pct = (rate.max() - rate.min()) / rate.mean() * 100
    print(f"Case 05 check -- {len(df)} districts, rate runs {rate.min():.2f} to {rate.max():.2f} "
          f"per 100,000 -- a spread of {spread_pct:.1f}% of the mean")

    fig, ax = plt.subplots(figsize=(6, 6.5))
    edges = geolib.choropleth(ax, feats, dict(zip(df["code"], rate)), scheme="quantile", k=5,
                              legend_title="Cases per 100,000")
    ax.set_title("A clear five-level gradient in incidence across the federation", loc="left")
    vizlib.save_fig(fig, OUT / "case05_misleading.png",
                    note=f"Source: case05_flat_rates.csv | quantile k=5 | range {rate.min():.2f}-{rate.max():.2f} "
                         f"({spread_pct:.1f}% of mean)")
    plt.close(fig)

    gvf_q = geolib.gvf(rate.to_numpy(), geolib.breaks(rate.to_numpy(), "quantile", 5))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 5))
    ax1.hist(rate, bins=12, color=vizlib.PALETTE["series"][0], edgecolor="white")
    ax1.axvline(rate.mean(), color=vizlib.PALETTE["highlight"], ls="--", lw=1.3,
               label=f"mean {rate.mean():.1f}")
    ax1.set_xlabel("Cases per 100,000")
    ax1.set_ylabel("Districts")
    ax1.set_title(f"The rate is noise around one value -- spread is only {spread_pct:.1f}% of the mean\n"
                 f"(quantile scheme GVF = {gvf_q:.3f}, barely above 'no structure')", fontsize=9)
    ax1.legend(frameon=False, fontsize=8)
    ax1.spines[["top", "right"]].set_visible(False)
    geolib.choropleth(ax2, feats, dict(zip(df["code"], rate)), scheme="quantile", k=5,
                      legend_title="Cases per 100,000", fmt="{:.2f}")
    ax2.set_title("Same map, breaks printed to 2dp -- the 'gradient' is 31.1 to 33.4", fontsize=9)
    vizlib.save_fig(fig, OUT / "case05_honest.png",
                    note=f"Source: case05_flat_rates.csv | distribution + same map with precise breaks | GVF={gvf_q:.3f}")
    plt.close(fig)
    print("  Case 05 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 6 - "Unit U32 is a hotspot, nearly 5x the national rate" - a
# small-area rate from 9 cases in 22,000 people, well within Poisson noise.
# ══════════════════════════════════════════════════════════════════════════
def case06():
    df = pd.read_csv(DATA / "smallarea_cases.csv")
    rate = df["cases"] / df["population"] * 1e5
    pooled = df["cases"].sum() / df["population"].sum() * 1e5
    u32 = df[df["unit"] == "U32"].iloc[0]
    u32_rate = u32["cases"] / u32["population"] * 1e5
    big = df[df["population"] > 100_000]
    big_rate = big["cases"] / big["population"] * 1e5
    print(f"Case 06 check -- {len(df)} units. Pooled rate {pooled:.2f} per 100k. "
          f"U32: {u32_rate:.1f} ({u32_rate / pooled:.1f}x) from {u32['cases']} cases in "
          f"{u32['population']:,} people. {len(big)} units with pop>100k: "
          f"{big_rate.min():.1f} to {big_rate.max():.1f}")

    order = df.assign(rate=rate).sort_values("rate")
    fig, ax = plt.subplots(figsize=(6.5, 9))
    colors = [vizlib.PALETTE["highlight"] if u == "U32" else vizlib.PALETTE["series"][0]
             for u in order["unit"]]
    ax.barh(order["unit"], order["rate"], color=colors)
    ax.axvline(pooled, color=vizlib.PALETTE["ink_soft"], ls="--", lw=1)
    ax.set_xlabel("Cases per 100,000")
    ax.set_title(f"Unit U32 is a hotspot -- running at nearly {u32_rate / pooled:.0f}x the "
                 "national rate", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case06_misleading.png",
                    note=f"Source: smallarea_cases.csv | n=40 units | U32 highlighted, rate ranked")
    plt.close(fig)

    # Compute each unit's OWN 95% Poisson limits directly (row-aligned) --
    # do not join back to geolib.funnel_limits()'s output by population
    # VALUE, which is unsafe: 3 pairs of units in this file share an
    # identical population (e.g. U04/U40 both 5,000), so a value-based
    # join silently picks an arbitrary row's cases for its partner.
    z = 1.96
    lam = pooled / 1e5 * df["population"]
    lo = np.maximum(lam - z * np.sqrt(lam), 0) / df["population"] * 1e5
    hi = (lam + z * np.sqrt(lam)) / df["population"] * 1e5
    outside_mask = (rate < lo) | (rate > hi)
    outside = int(outside_mask.sum())
    expected_false_pos = len(df) * 0.05
    print(f"  {outside} of 40 units fall outside their own 95% Poisson limits "
          f"(expect ~{expected_false_pos:.1f} by chance alone, testing 40 units at 95% each)")

    pop_sorted = df["population"].sort_values()
    lam_s = pooled / 1e5 * pop_sorted
    lo_s = np.maximum(lam_s - z * np.sqrt(lam_s), 0) / pop_sorted * 1e5
    hi_s = (lam_s + z * np.sqrt(lam_s)) / pop_sorted * 1e5

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.fill_between(pop_sorted, lo_s, hi_s, color=vizlib.PALETTE["muted"], alpha=0.3,
                    label="95% Poisson limits")
    ax.plot(pop_sorted, [pooled] * len(pop_sorted), color=vizlib.PALETTE["ink_soft"],
           lw=1, ls="--", label=f"pooled rate {pooled:.1f}")
    ax.scatter(df.loc[~outside_mask, "population"], rate[~outside_mask], s=22,
              color=vizlib.PALETTE["series"][0], zorder=5, label="inside limits")
    ax.scatter(df.loc[outside_mask, "population"], rate[outside_mask], s=60,
              color=vizlib.PALETTE["highlight"], zorder=6,
              label=f"outside limits (n={outside}, incl. U32)")
    ax.set_xscale("log")
    ax.set_xlabel("Population (log scale)")
    ax.set_ylabel("Cases per 100,000")
    ax.set_title(f"U32 falls outside ITS OWN 95% limit -- but testing 40 units at 95% each\n"
                 f"expects ~{expected_false_pos:.0f} such 'outliers' by chance alone, even if every "
                 "unit shares one true rate", loc="left")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case06_honest.png",
                    note=f"Source: smallarea_cases.csv | funnel plot, 95% Poisson control limits (row-aligned, "
                         f"not joined by population value) vs population | {outside}/40 outside, "
                         f"~{expected_false_pos:.1f} expected by chance at this confidence level")
    plt.close(fig)
    print("  Case 06 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 7 - "District income and case rate are only weakly related" -
# r=-0.31 reported flatly, no honest redesign needed beyond showing the
# scatter itself and naming what -0.31 actually means (not "unrelated").
# ══════════════════════════════════════════════════════════════════════════
def case07():
    df = pd.read_csv(DATA / "district_health.csv")
    rate = df["cases"] / df["population"] * 1e5
    r, p = stats.pearsonr(df["income_pc_usd"], rate)
    print(f"Case 07 check -- r = {r:.3f} across {len(df)} districts (p={p:.3f})")

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(df["income_pc_usd"], rate, color=vizlib.PALETTE["series"][0], s=35)
    m, b = np.polyfit(df["income_pc_usd"], rate, 1)
    xs = np.linspace(df["income_pc_usd"].min(), df["income_pc_usd"].max(), 100)
    ax.plot(xs, m * xs + b, color=vizlib.PALETTE["highlight"], lw=1.3)
    ax.set_xlabel("Income per capita (USD/year)")
    ax.set_ylabel("Cases per 100,000")
    ax.set_title(f"District income and case rate are only weakly related -- r is about {r:.2f}", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case07_misleading.png",
                    note=f"Source: district_health.csv | n=24 | r={r:.3f}, Pearson")
    plt.close(fig)

    r2 = r ** 2
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(df["income_pc_usd"], rate, color=vizlib.PALETTE["series"][0], s=35)
    ax.plot(xs, m * xs + b, color=vizlib.PALETTE["highlight"], lw=1.3)
    ax.set_xlabel("Income per capita (USD/year)")
    ax.set_ylabel("Cases per 100,000")
    ax.set_title(f"r={r:.2f} means income explains r²={r2:.0%} of the variance in rate -- a real\n"
                 "but modest relationship, not 'unrelated', and not strong enough to act on alone", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    vizlib.save_fig(fig, OUT / "case07_honest.png",
                    note=f"Source: district_health.csv | n=24 | same scatter, r²={r2:.3f} stated explicitly")
    plt.close(fig)
    print("  Case 07 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 8 - "Rural outbreak -- look how much of the map is dark" - judging
# a choropleth by AREA covered ignores that the most populous districts are
# small on the map and carry most of the actual people.
# ══════════════════════════════════════════════════════════════════════════
def case08():
    df = pd.read_csv(DATA / "district_health.csv")
    feats = geolib.read_geojson(DATA / "districts.geojson")
    rate = df["cases"] / df["population"] * 1e5
    areas = {f["code"]: geolib.polygon_area_km2(f["ring"]) for f in feats}
    df["area_km2_computed"] = df["code"].map(areas)
    top5_pop = df.sort_values("population", ascending=False).head(5)
    land_share = top5_pop["area_km2_computed"].sum() / df["area_km2_computed"].sum() * 100
    pop_share = top5_pop["population"].sum() / df["population"].sum() * 100
    print(f"Case 08 check -- 5 most populous districts: {land_share:.1f}% of land area, "
          f"{pop_share:.1f}% of population")
    edges = geolib.breaks(rate.to_numpy(), "natural", 5)
    top2_class = (geolib.class_of(rate.to_numpy(), edges) >= 3)
    print(f"  Districts in the top-2 classes: {int(top2_class.sum())} of {len(df)}")

    fig, ax = plt.subplots(figsize=(6, 6.5))
    geolib.choropleth(ax, feats, dict(zip(df["code"], rate)), scheme="natural", k=5,
                      legend_title="Cases per 100,000")
    ax.set_title("This is a rural outbreak -- look how much of the map is dark", loc="left")
    vizlib.save_fig(fig, OUT / "case08_misleading.png",
                    note="Source: district_health.csv + districts.geojson | judged by map AREA covered")
    plt.close(fig)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 6))
    geolib.choropleth(ax1, feats, dict(zip(df["code"], rate)), scheme="natural", k=5,
                      legend_title="Cases per 100,000")
    ax1.set_title("Same map", fontsize=9)
    geolib.prop_symbols(ax2, feats, dict(zip(df["code"], df["population"])), max_pt=1400,
                        color=vizlib.PALETTE["series"][1])
    geolib.outlines(ax2, feats)
    geolib.size_legend(ax2, df["population"].to_numpy(), max_pt=1400, title="Population")
    ax2.set_title(f"Population by district -- the 5 largest districts hold {pop_share:.0f}% of\n"
                 f"all residents on just {land_share:.0f}% of the land. 'Dark area' is not\n"
                 "'where the people are'.", fontsize=9)
    vizlib.save_fig(fig, OUT / "case08_honest.png",
                    note=f"Source: district_health.csv + districts.geojson | choropleth beside population "
                         f"proportional symbols | top-5-by-pop: {land_share:.1f}% land, {pop_share:.1f}% people")
    plt.close(fig)
    print("  Case 08 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# CASE 9 - "Region A is the stronger profile -- encloses visibly more
# area" - a radar chart's enclosed area depends on AXIS ORDER, which is
# arbitrary; the two regions' means are almost identical.
# ══════════════════════════════════════════════════════════════════════════
def _radar_area(values, n):
    """Shoelace area of a radar polygon with n equally-spaced spokes."""
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = values * np.cos(theta)
    y = values * np.sin(theta)
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def case09():
    df = pd.read_csv(DATA / "region_profiles.csv")
    n = len(df)
    mean_a, mean_b = df["region_a"].mean(), df["region_b"].mean()
    area_a = _radar_area(df["region_a"].to_numpy(), n)
    area_b = _radar_area(df["region_b"].to_numpy(), n)
    print(f"Case 09 check -- means {mean_a:.1f} / {mean_b:.1f} (diff {abs(mean_a - mean_b):.2f}). "
          f"File-order enclosed areas: A={area_a:,.0f}, B={area_b:,.0f}")

    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    theta_closed = np.append(theta, theta[0])
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    for col, label, color in [("region_a", "Region A", vizlib.PALETTE["series"][0]),
                              ("region_b", "Region B", vizlib.PALETTE["series"][1])]:
        vals = np.append(df[col].to_numpy(), df[col].iloc[0])
        ax.plot(theta_closed, vals, color=color, lw=1.6, label=label)
        ax.fill(theta_closed, vals, color=color, alpha=0.15)
    ax.set_xticks(theta)
    ax.set_xticklabels(df["indicator"])
    ax.set_title("Region A is the stronger of the two -- its profile encloses\n"
                 "visibly more area", y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), frameon=False, fontsize=8)
    vizlib.save_fig(fig, OUT / "case09_misleading.png",
                    note="Source: region_profiles.csv | radar, 6 axes in file order, both profiles filled")
    plt.close(fig)

    order_sorted = df.sort_values("indicator")["indicator"].tolist()
    df_s = df.set_index("indicator").loc[order_sorted].reset_index()
    area_a2 = _radar_area(df_s["region_a"].to_numpy(), n)
    area_b2 = _radar_area(df_s["region_b"].to_numpy(), n)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    ax1.bar(df["indicator"], df["region_a"] - df["region_b"],
           color=[vizlib.PALETTE["series"][0] if v > 0 else vizlib.PALETTE["series"][1]
                  for v in (df["region_a"] - df["region_b"])])
    ax1.axhline(0, color=vizlib.PALETTE["ink_soft"], lw=0.8)
    ax1.set_ylabel("Region A minus Region B")
    ax1.set_title(f"Per-indicator difference -- A leads on 3, B leads on 3.\n"
                 f"Overall means: A={mean_a:.1f}, B={mean_b:.1f} (diff {abs(mean_a - mean_b):.2f}, "
                 "not a real gap)", fontsize=9)
    plt.setp(ax1.get_xticklabels(), rotation=30, ha="right")
    ax1.spines[["top", "right"]].set_visible(False)
    ax2.axis("off")
    ax2.text(0.02, 0.9, "Enclosed radar area depends on AXIS ORDER\n(not a property of the data):",
            fontsize=9, fontweight="bold", transform=ax2.transAxes)
    ax2.text(0.02, 0.65, f"File order:    A={area_a:,.0f}   B={area_b:,.0f}   "
                        f"(A looks {area_a / area_b:.2f}x B)", fontsize=9, transform=ax2.transAxes)
    ax2.text(0.02, 0.50, f"Sorted order:  A={area_a2:,.0f}   B={area_b2:,.0f}   "
                        f"(A looks {area_a2 / area_b2:.2f}x B)", fontsize=9, transform=ax2.transAxes)
    ax2.text(0.02, 0.25, "Relabelling the SAME data changes which region looks bigger.\n"
                        "Area is not a valid encoding for a profile comparison.",
            fontsize=9, transform=ax2.transAxes, color=vizlib.PALETTE["ink_soft"])
    fig.suptitle("Radar area is an artefact of axis order, not a measure of 'strength'", fontsize=11)
    vizlib.save_fig(fig, OUT / "case09_honest.png",
                    note=f"Source: region_profiles.csv | per-indicator bar difference + axis-order area comparison")
    plt.close(fig)
    print("  Case 09 done.\n")


# ══════════════════════════════════════════════════════════════════════════
# DIAGNOSIS SUMMARY
# ══════════════════════════════════════════════════════════════════════════
DIAGNOSES = {
    "Case 01 Health Indicators (size)": {
        "invited_conclusion": "Population and healthcare access are unrelated -- the large countries "
                               "are spread right across the range.",
        "decoy_objection": "Could the scatter just be noisy? No -- the real issue is that most large "
                            "countries are not visible on the chart at all.",
        "mechanism": "s=pop_m**2 is passed directly to matplotlib's `s`, which is already an AREA "
                     "in points^2 -- so the mark's area scales as pop_m to the FOURTH power, not "
                     "pop_m. The largest mark is 589x the area of the smallest, and 9 countries "
                     "under 2.0M population are smaller than a single rendered point.",
        "redesign": "Scale `s` so area is linearly proportional to pop_m, with a stated size range and a 3-value legend."
    },
    "Case 02 District Health (raw count map)": {
        "invited_conclusion": "The outbreak is concentrated in the three districts around the capital.",
        "decoy_objection": "Could the capital genuinely have worse health outcomes? The per-capita "
                            "rate map shows a completely different top three.",
        "mechanism": "A choropleth of the RAW CASE COUNT, with no denominator. r(cases, population) "
                     "is very strong, so the map is really showing where people live, not disease risk.",
        "redesign": "Normalise to cases per 100,000 residents before classifying or colouring."
    },
    "Case 03 Health Indicators (PCP min-max)": {
        "invited_conclusion": "GDP per capita barely varies across the sample.",
        "decoy_objection": "Could GDP genuinely be uniform here? No -- it ranges from $283 to over "
                            "$120,000, a huge real spread.",
        "mechanism": "Min-max scaling maps the single $120,219 outlier to 1.0 and crushes every "
                     "other country into the bottom 10% of the axis -- one extreme value flattens "
                     "the whole picture.",
        "redesign": "Percentile-rank scaling (immune to the outlier) shows the same 60 countries spread across the full axis."
    },
    "Case 04 Health Indicators (PCP axis order)": {
        "invited_conclusion": "Healthcare access and case rate are unrelated -- no crossing pattern "
                               "between them.",
        "decoy_objection": "Could the relationship genuinely be weak? No -- directly correlated, "
                            "r is strongly negative once the two axes are placed next to each other.",
        "mechanism": "The axes are left in FILE order, which happens to put two other columns "
                     "between the two that are actually related -- a crossing pattern three axes "
                     "apart is invisible by construction.",
        "redesign": "geolib.corr_chain() places the two strongly-correlated axes adjacent, revealing the X-shaped waist."
    },
    "Case 05 Flat Rates (quantile classes)": {
        "invited_conclusion": "There is a clear five-level gradient in incidence across the federation.",
        "decoy_objection": "Could 5 classes be a reasonable choice regardless? Quantile classing "
                            "ALWAYS produces 5 full classes, even from pure noise -- that is not evidence of structure.",
        "mechanism": "The underlying rate spans only 7.2% of its own mean (31.07 to 33.40 per 100k) "
                     "-- noise-level variation. Quantile classification forces this flat distribution "
                     "into 5 equal-count bins regardless, manufacturing a gradient that is not there.",
        "redesign": "A histogram showing the rate's true (flat) spread, plus the same map with breaks printed to 2dp."
    },
    "Case 06 Small-Area Hotspot": {
        "invited_conclusion": "Unit U32 is a hotspot -- running at nearly five times the national rate.",
        "decoy_objection": "Could U32 genuinely be exceptional? Every unit with a large, stable "
                            "population (>100k) falls in a narrow 5.5-12.0 band -- only tiny units swing wildly, "
                            "and U32's own 9-case count is exactly the kind of small count a single bad month "
                            "can produce.",
        "mechanism": "U32's rate comes from just 9 cases in 22,000 people -- small-area Poisson noise. "
                     "It does fall just outside ITS OWN 95% control limit, but the map ranks 40 such units "
                     "at once: testing 40 independent units at 95% confidence EXPECTS about 2 false "
                     "positives by chance alone, even if every unit shares one true underlying rate "
                     "(which the generating process here does, by construction). One flagged unit out "
                     "of 40 is within that expectation, not a confirmed hotspot.",
        "redesign": "A funnel plot: rate against population with 95% Poisson limits, instead of a flat ranked bar chart -- showing the single flag in the context of 40 simultaneous tests."
    },
    "Case 07 Income vs Rate": {
        "invited_conclusion": "District income and case rate are only weakly related -- r is about -0.31.",
        "decoy_objection": "Is 'weakly related' actually the right reading of r=-0.31? It depends on "
                            "what the number is used FOR -- r^2=0.09 means income alone is a poor predictor.",
        "mechanism": "No drawing mechanism here -- the number is reported correctly. The chart simply "
                     "never states what r=-0.31 (r^2=9%) actually means in plain terms, leaving 'weakly "
                     "related' to carry more or less weight than the number supports depending on the reader.",
        "redesign": "The same scatter, with r^2 stated explicitly so 'weak' has a number behind it."
    },
    "Case 08 Rural Outbreak (map area)": {
        "invited_conclusion": "This is a rural outbreak -- look how much of the map is dark.",
        "decoy_objection": "Could the dark area genuinely represent most of the affected population? "
                            "The 5 most populous districts are only 12.6% of the land but 59.9% of the people.",
        "mechanism": "Judging a choropleth by the AREA it covers silently weights every square "
                     "kilometre equally, but population (and therefore the true burden) is wildly "
                     "uneven across the map -- a few small, dense districts matter far more than their "
                     "map footprint suggests.",
        "redesign": "The choropleth beside a population proportional-symbol map, so area-read and people-read are both visible."
    },
    "Case 09 Region Profiles (radar area)": {
        "invited_conclusion": "Region A is the stronger of the two -- its profile encloses visibly more area.",
        "decoy_objection": "Could area be a fair way to compare two profiles? Re-ordering the SAME "
                            "six axes changes which region's polygon looks bigger -- area is not a property of the data at all.",
        "mechanism": "A radar chart's enclosed area is a function of axis ORDER as much as the "
                     "values themselves (the shoelace formula is order-dependent); the two regions' "
                     "overall means are almost identical (62.3 vs 62.0), each leading on 3 of 6 indicators.",
        "redesign": "A per-indicator difference bar chart -- the only fair, order-independent comparison of the two profiles."
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
