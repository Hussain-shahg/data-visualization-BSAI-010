# Part E — Written Justification
**Week 5 Data Visualisation Assignment | Roll No: BSAI-010**

## 1. Channel assignment, ranked by precision required

**D1 bubble chart:** `gdp_pc` and `healthcare_access` get the two **position** channels (rank 1) — they are the two variables the chart is actually about, and position is read most precisely. `pop_m` gets **area** (rank 4, the weakest channel used here) — population is context, not the message, and Case 1 proved exactly what happens when area is mis-scaled. `region` gets **hue + marker shape** — identity only, never implying order, and shape is added because 6 regions exceed the course palette's 4 CVD-safe hues (Week 3 Part C4's rule: redundant-code a repeat, never add a 5th hue).

**D2 parallel-coordinates:** all five variables share the same channel — **position**, one axis each — which is exactly why axis order (computed by `corr_chain`, Part B.3/D2) matters as much as any colour choice: adjacency is the only thing that lets a reader see a relationship between two axes at all.

**D3 choropleth:** the rate gets **lightness** on a single sequential hue (rank 4, the weakest channel, used because geography forces area as the base layer) — never a rainbow, because hue has no inherent order and this is an ordered quantity.

## 2. The parallel-coordinates decisions

**Scaling:** percentile rank, chosen because min-max scaling is dominated by the single $120,219 GDP outlier (Aldonia, 9.2× the second-highest country) and crushes 58 of 60 countries into the bottom 10% of that axis (Case 3) — exactly the failure the chart must not repeat.

**Axis order:** computed by `geolib.corr_chain()`, not eyeballed: `healthcare_access → cases_per_100k → urban_pct → median_age → gdp_pc`, the greedy chain by absolute pairwise correlation. Case 4 is the proof this matters — the same two axes left in file order (three apart) show "no crossing pattern"; placed adjacent by the computed order, the r = −0.80 relationship is immediately visible as a clean X.

**One relationship a pairwise scatter matrix would not show as clearly:** the three-way interaction between `urban_pct`, `median_age` and `gdp_pc` in the middle of the chain — a scatter matrix would show each pair in isolation, but the parallel-coordinates view lets a reader trace one country's full path across all three at once and see, for example, that the brushed region (Andara) is simultaneously low-GDP *and* mid-range on both urbanisation and median age, a joint pattern no single 2-D panel states directly.

## 3. The spatial decisions

**Denominator:** cases per 100,000 residents, not raw count — Case 2 and Case 8 are the argument: r(cases, population) = 0.99, so an un-normalised map is a population map wearing a disease map's title, and judged by area-covered it also points at the wrong districts (the 5 most populous are 12.6% of the land but 59.9% of the people).

**Classification scheme:** Jenks natural breaks (GVF = 0.969 for D3's rate), chosen over quantile because quantile always manufactures 5 full classes even from near-flat data (Case 5's lesson — a 7.2%-of-mean spread quantiled into a "clear five-level gradient"); natural breaks only produces visually distinct classes when the data actually clusters that way, and the GVF score is reported so the choice is justified by a number, not an assertion.

**Projection:** equal-area (Lambert cylindrical, one shared reference latitude across the whole layer), because colouring an area with a quantity makes area the encoding channel, and Part B.4 measured what the alternative costs: Mercator inflates area by 1.11× in the south of the federation to 1.22× in the north — a latitude-dependent distortion that would sit underneath the data-driven pattern and make it unreadable as a true comparison.

## 4. The counterfactual

A raw-count version of the D3 map would have coloured every district by its absolute case count instead of its rate. Because r(cases, population) = 0.99 in this data, that map is, to a very close approximation, just a population map: it would point almost entirely at **D17, D13 and D09** — the most populous districts — regardless of their actual per-capita incidence. The normalised map instead points at **D19, D20 and D21**, a completely different set of three (zero overlap between the two top-3 lists), and these are the districts whose residents are genuinely most exposed. A reader shown only the raw-count version would be led to concentrate a response in the largest cities, which is where the raw numbers are always biggest regardless of risk — taking attention and resources away from the smaller, higher-incidence districts the normalised map actually identifies. This is the same pattern Case 2, Case 8 and Part C's crime-rate activity all demonstrate independently, which is why Part D3 normalises before classifying rather than after.

---

*Submitted by: M. Hussain Shah | m.hussain103shah@gmail.com | BSAI-010*
*Dataset: synthetic, generated for CDB601220, Superior University Lahore*
*Tools: Python 3.12, pandas, numpy, matplotlib, scikit-learn, vizlib + geolib (course toolkits)*
*Note: geolib.corr_chain() needed a one-line runtime patch (documented in partA_charts.py and partD_pcp.py) because pandas >= 3.0's permanent Copy-on-Write makes the unmodified function's `np.fill_diagonal(r.values, ...)` raise on a read-only array. geolib.py itself is committed byte-identical to the version shipped for this week.*
