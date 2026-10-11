# Week 3 — Matplotlib & Seaborn: Deceptive Charts and Honest Redesigns

**Roll No:** BSAI-010
**Submitted by:** M. Hussain Shah (m.hussain103shah@gmail.com)
**Course:** Data Visualisation

---

## Overview

Week 3 covers **Matplotlib (Lecture 5)** and **Seaborn (Lecture 6)**, focusing on how charts can mislead even when the underlying arithmetic is correct. The assignment has five parts (A–E) plus an optional bonus, worth 100 marks total.

---

## Directory Structure

```
week3/
├── README.md                        ← This file
└── assignments/
    ├── vizlib.py                    ← Course toolkit (Lie Factor, CVD sim, palette)
    ├── partA_charts.py              ← Part A: 9 misleading charts + honest redesigns
    ├── partB_lie_factor.py          ← Part B: Lie Factor audit
    ├── partC_palette.py             ← Part C: Palette colour-blind proof
    ├── partD_figure.py              ← Part D: Clinical 2×2 review figure
    ├── partE_justification.md       ← Part E: Written justification
    ├── data/
    │   ├── case01_helmet_rickshaw.csv
    │   ├── case02_chai_quizzes.csv
    │   ├── case03_aqi_monitors.csv
    │   ├── case04_quartet_depts.csv
    │   ├── case05_same_stats_shapes.csv
    │   ├── case06_sensor_matrix.csv
    │   ├── case07_dual_axis_series.csv
    │   ├── case07_lie_factor.csv
    │   ├── vitals_10k.csv
    │   ├── ward_los_wide.csv
    │   └── DATA_DICTIONARY.md
    ├── starter/
    │   ├── starter.py
    │   ├── palette_check.py
    │   └── popout.py
    └── charts/                      ← Generated output (PNG files)
        ├── case01_misleading.png
        ├── case01_honest.png
        ├── ...
        ├── case09_honest.png
        ├── partC_swatches.png
        └── partD_figure.png
```

---

## Setup

```bash
pip install pandas numpy matplotlib seaborn scipy
cd week3/assignments
python vizlib.py        # Self-check — should print Lie Factor examples and palette report
```

---

## Part A — Rebuild and Diagnose Nine Misleading Charts (36 marks)

**File:** `assignments/partA_charts.py`

**Run:** `python partA_charts.py`

**Output:** `charts/case0X_misleading.png` + `charts/case0X_honest.png` (18 files total)

Each case produces two charts and prints a diagnosis to the console.

| Case | Dataset | Misleading mechanism | Check value |
|------|---------|----------------------|-------------|
| 01 Helmets | `case01_helmet_rickshaw.csv` | Simpson's Paradox — road type confounds helmet grade | Standard 2.15, Premium 5.40 injuries/1000 |
| 02 Chai & Quizzes | `case02_chai_quizzes.csv` | Spurious correlation — enrolment drives both variables | r = 0.98 |
| 03 Lahore AQI | `case03_aqi_monitors.csv` | Regression to the mean — intervention placed at a peak | Mean 202 before, 137 after (32% fall) |
| 04 Anscombe Depts | `case04_quartet_depts.csv` | Identical summary stats, different shapes (Anscombe) | means 18.00/14.50, r = 0.816 |
| 05 Same Stats | `case05_same_stats_shapes.csv` | Datasaurus principle — stats don't constrain shape | means 48.00/63.00, r = 0.420 |
| 06 Sensor Matrix | `case06_sensor_matrix.csv` | `cmap="Reds"` without vmin/vmax + probe column inflation | creatinine–HbA1c 0.77, systolic–MAP 0.96, 20×20 |
| 07 ShaheenGo | `case07_dual_axis_series.csv` | Dual y-axes manufacture a false crossing | Cost > revenue first 4 months (visual only) |
| 08 Histograms | `vitals_10k.csv` | Bin count changes apparent shape (3 vs 45 vs 400) | n = 10 000 each panel |
| 09 SpO2 KDE | `vitals_10k.csv` | Gaussian KDE leaks past hard physiological ceiling (100%) | Data max = 100, KDE extends further |

### What each diagnosis covers

For every case the script prints:
1. **Invited conclusion** — what the chart is designed to make you believe
2. **Decoy objection** — an alternative explanation, ruled out with data
3. **Mechanism** — the specific named error with a supporting number
4. **Redesign rationale** — what the honest chart does differently

---

## Part B — Lie Factor Audit (15 marks)

**File:** `assignments/partB_lie_factor.py`

**Run:** `python partB_lie_factor.py`

Uses `vizlib.lie_factor()` to audit five graphics (A–E) from `case07_lie_factor.csv`, then analyses the Case 7 dual-axis chart as Chart F.

### Key findings

| Chart | Subject | LF | Verdict |
|-------|---------|----|-|
| A | Corporate tax rate (truncated bars) | ~12 | Exaggerates |
| B | Health budget (area icon, dim=2) | ~2.25 | Exaggerates |
| C | Export earnings (bars from zero) | 1.00 | **Honest** |
| D | Air-pollution index (compressed) | ~1.13 | Exaggerates |
| E | City population (bubble radius, dim=2) | ~4.0 | Exaggerates |
| F | ShaheenGo dual axis | — | Undefined (structural, not scalar) |

**Lie Factor < 1** understates the data effect — a distortion that benefits anyone who wants to hide a large change. Honest is symmetric (0.95–1.05).

**Area encoding (ink_dimension = 2):** Charts B and E scale icons in two dimensions, so the perceived area grows as the square of the scale factor. `ink_dimension=1` would understate the distortion; the formula needs `=2`.

---

## Part C — Palette Proof (9 marks)

**File:** `assignments/partC_palette.py`

**Run:** `python partC_palette.py`

**Output:** `charts/partC_swatches.png`

Tests `tab10` (first 6 colours) and the course palette (3 and 4 slots) under **deuteranopia**, **protanopia**, and **tritanopia** using Machado et al. (2009) matrices in linear RGB.

### Key result

| Palette | CVD type | Worst pair | ΔE | Verdict |
|---------|----------|------------|----|---------|
| tab10 (6 slots) | deutan | S1/S3 | ~5 | FAILS |
| tab10 (6 slots) | normal | — | ~15 | OK |
| Course palette (3) | deutan | S1/S3 | ≥11 | OK |
| Course palette + 4th | deutan | S1/S4 | ~7.6 | Needs 2nd channel |

**Rule for > 3 categories:** Assign each series a distinct **marker shape** in addition to colour. Use **direct labels** if the chart type allows. Never add more hues — the 4th slot already falls below the 8 ΔE threshold under CVD.

---

## Part D — Clinical Review Figure (25 marks)

**File:** `assignments/partD_figure.py`

**Run:** `python partD_figure.py`

**Output:** `charts/partD_figure.png` (300 dpi, bbox_inches="tight")

### Data problems identified and handled

| # | Problem | Rule applied | Rows affected |
|---|---------|-------------|---------------|
| 1 | Mixed `admit_date` formats | `pd.to_datetime(format="mixed", dayfirst=True)` | All rows |
| 2 | Inconsistent ward capitalisation | `.str.strip().str.title()` | All rows |
| 3 | `heart_rate > 300 bpm` (device fault) | Excluded; threshold = 300 bpm per task spec | Varies |
| 4 | `ward_los_wide.csv` is wide form | `pd.melt()` required for Seaborn | N/A |

### Four panels

| Panel | Question | Chart type | Key parameter |
|-------|----------|------------|---------------|
| 1 (top-left) | Distribution of systolic BP | Histogram | `bin_width = 5 mmHg` |
| 2 (top-right) | LOS by ward | Box plot | wards sorted alphabetically |
| 3 (bottom-left) | Systolic vs MAP | Scatter + OLS | alpha=0.25, subsample n=2000 |
| 4 (bottom-right) | All-pairs vitals correlation | Heatmap (lower △) | `cmap=RdBu_r, vmin=-1, vmax=1` |

---

## Part E — Written Justification (15 marks)

**File:** `assignments/partE_justification.md`

One-page justification covering:
- Per-panel question, chart type, and Week 2 channel rule
- Every declared parameter with its reason
- Every excluded row with rule, count, and metric before/after
- Symmetry test and ethics clause

---

## References

- VanderPlas, J. (2016). *Python Data Science Handbook*, Ch. 4. O'Reilly.
- Waskom, M. (2021). Seaborn: Statistical data visualization. *JOSS*, 6(60).
- Wilke, C.O. (2019). *Fundamentals of Data Visualization*, Ch. 7, 9, 20. O'Reilly.
- Anscombe, F.J. (1973). Graphs in Statistical Analysis. *American Statistician*, 27(1), 17–21.
- Matejka, J. & Fitzmaurice, G. (2017). Same stats, different graphs. *CHI 2017*.
- Tufte, E.R. (1983). *The Visual Display of Quantitative Information*. Graphics Press.
- Machado, G., Oliveira, M. & Fernandes, L. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE TVCG*, 15(6).

---

*All data used in this assignment is synthetic and provided by the course staff.*
