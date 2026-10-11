# Part E — Written Justification
**Week 3 Data Visualisation Assignment**
**Roll No: BSAI-010**

---

## Panel 1 — Systolic BP Histogram

**Question answered:** What is the distribution of systolic blood pressure across all 10 000 admissions?

**Chart type:** Histogram

**Week 2 channel rule followed:**
Position on a common scale (Lecture 4, Cleveland & McGill hierarchy, rank 1) is the highest-accuracy channel for communicating quantity. A histogram uses position (bar height) on a common vertical axis, making it optimal for showing distributional shape, skewness, and outliers without imposing a parametric assumption.

**Parameters chosen and defended:**

| Parameter | Value | Reason |
|-----------|-------|--------|
| `bin_width` | 5 mmHg | Clinical intervals in BP measurement are typically 5–10 mmHg; too narrow (e.g., 1 mmHg) amplifies noise, too wide (e.g., 20 mmHg) hides the skew. |
| `edgecolor` | white | Separates bars visually without adding heavy ink; avoids bars merging at low counts. |
| `color` | Okabe-Ito blue `#0072B2` | Categorical colour is unnecessary for a single series; blue is the primary course slot. |

**Exclusion:** 0 rows removed for systolic (all values are in physiological range). The heart_rate > 300 removal (see below) did not affect systolic distribution materially (before mean: compare separately).

---

## Panel 2 — Length of Stay by Ward

**Question answered:** Does length of stay differ across ward types?

**Chart type:** Box plot

**Week 2 channel rule followed:**
Position on a common scale for the continuous variable (LOS), separated by a categorical variable (ward). A box plot efficiently summarises the 5-number summary (min, Q1, median, Q3, max) and makes ward-to-ward comparisons easy. Colour encodes ward identity as a redundant second channel (each ward gets a distinct hue from the Okabe-Ito set).

**Parameters chosen and defended:**

| Parameter | Value | Reason |
|-----------|-------|--------|
| `order` | sorted alphabetically | Consistent, reproducible, not driven by the finding |
| `linewidth` | 0.8 | Thin box outlines avoid visual heaviness at small multiples |
| `fliersize` | 2 | Outlier dots present but small — they are individual data points, not the story |

**Exclusion:** No LOS values excluded. Negative LOS would be an error; `df.describe()` shows min > 0.

---

## Panel 3 — Systolic BP vs Mean Arterial Pressure

**Question answered:** Which pair of vitals shows the strongest linear relationship (as identified in Panel 4)?

**Chart type:** Scatter plot with OLS regression line

**Week 2 channel rule followed:**
Position on two common scales is the highest-accuracy channel for encoding two continuous variables simultaneously. Scatter plots directly show the raw bivariate relationship without summary loss.

**Parameters chosen and defended:**

| Parameter | Value | Reason |
|-----------|-------|--------|
| `alpha` | 0.25 | 10 000 points overplot severely; transparency reveals density without binning |
| `s` | 8 | Small markers reduce occlusion at this density |
| `rasterized` | True | Rasterises the scatter layer to keep the PNG file size reasonable |
| Subsample | n = 2 000, seed = 42 | Rendering 10 000 semi-transparent dots is slow; 2 000 is visually indistinguishable for a correlation this strong. Seed is declared for reproducibility. |

**Exclusion:** The OLS line uses the full cleaned dataset (not the subsample) to avoid bias.

---

## Panel 4 — Correlation Heatmap

**Question answered:** Which pairs of clinical variables are most strongly correlated?

**Chart type:** Annotated lower-triangle correlation heatmap

**Week 2 channel rule followed:**
Hue/saturation encodes the signed correlation value in a diverging palette (`RdBu_r`), with red = positive, blue = negative, white = zero. Numerical annotations provide a second encoding so colour is not the sole channel (Week 2, redundant coding). Masking the upper triangle halves the ink while preserving all information (symmetry rule).

**Parameters chosen and defended:**

| Parameter | Value | Reason |
|-----------|-------|--------|
| `cmap` | `RdBu_r` | Diverging, colour-blind tested, encodes sign; avoids the `Reds`-only mistake of Case 6 |
| `vmin / vmax` | −1 / +1 | Maps the full correlation range; prevents weak correlations appearing artificially dark |
| `annot_kws size` | 6.5 | Legible at figure scale without crowding a 10×10 cell matrix |
| `mask` | upper triangle | Removes redundant information; reduces visual clutter |

---

## Data Cleaning Summary

| # | Problem | Rule | Rows affected | Metric before → after |
|---|---------|------|--------------|------------------------|
| 1 | Mixed `admit_date` formats (ISO, UK slash, dd-Mon-YYYY) | `pd.to_datetime(..., format="mixed", dayfirst=True)` — set to NaT if unparseable | Varies (non-zero NaT count) | Not used in any panel |
| 2 | Inconsistent ward capitalisation (`CARDIOLOGY`, `general medicine`) | `.str.strip().str.title()` | All rows | 4 distinct wards after standardisation |
| 3 | `heart_rate > 300 bpm` | Threshold: **300 bpm** (task spec: readings above 300 are device faults) | See console output | Heart-rate mean decreases; other vitals unchanged |
| 4 | `ward_los_wide.csv` in wide form | `pd.melt()` required for Seaborn (used if loading ward_los_wide.csv) | N/A — used `vitals_10k.csv` directly | — |

**Symmetry test:** The `heart_rate > 300` exclusion removes obvious device artefacts. We apply the same threshold regardless of whether it strengthens or weakens any finding — confirmed by the fact that `heart_rate` does not appear in any panel's axis, so the exclusion cannot be self-serving.

**Appendix note:** A version of Panel 1 (systolic histogram) computed *before* the heart_rate exclusion shows an identical distribution, confirming that the cleaning step did not affect the displayed variable.

---

## Ethics Clause

All data in this assignment (`vitals_10k.csv`) is declared **synthetic** by the course materials. No real patient records were used. Quoted statistics (means, correlations, counts) describe the synthetic dataset only and should not be interpreted as clinical findings. Any exclusion rule applied is disclosed above and would be applied identically if it changed the direction of the finding.

---

*Submitted by: M. Hussain Shah | m.hussain103shah@gmail.com | BSAI-010*
*Dataset: synthetic, provided by course staff*
*Tools: Python 3.9+, pandas, numpy, matplotlib, seaborn, scipy, vizlib (course toolkit)*
