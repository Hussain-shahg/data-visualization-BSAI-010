"""
Week 3 – Part B: Lie Factor Audit
==================================
Using data/case07_lie_factor.csv (five graphics, A–E) plus the Part A
Case 7 dual-axis chart (Chart F).

Lie Factor = (graphic effect) / (data effect)
    data effect    = (value_end - value_start) / value_start
    graphic effect = (ink_end / ink_start)^ink_dimension - 1

Honest: LF ≈ 1.0  (Tufte accepts 0.95 – 1.05)

Run from week3/assignments/:
    python partB_lie_factor.py
"""

import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib

DATA = pathlib.Path(__file__).parent / "data"


# ── Load the audit table ───────────────────────────────────────────────────────
df = pd.read_csv(DATA / "case07_lie_factor.csv")
print("=" * 70)
print("PART B — Lie Factor Audit")
print("=" * 70)
print()

# ── Q1: Tabulate data effect, graphic effect, Lie Factor, verdict ─────────────
print("Q1 — Audit table\n")
rows = []
for _, row in df.iterrows():
    lf, data_eff, graphic_eff = vizlib.lie_factor(
        row["value_start"], row["value_end"],
        row["ink_start"],   row["ink_end"],
        ink_dimension=int(row["ink_dimension"]),
    )
    verdict = vizlib.lie_verdict(lf)
    rows.append({
        "chart_id":      row["chart_id"],
        "subject":       row["subject"],
        "data_effect":   data_eff,
        "graphic_effect": graphic_eff,
        "lie_factor":    lf,
        "verdict":       verdict,
        "encoding":      row["how_the_graphic_encodes_it"],
    })

audit = pd.DataFrame(rows)
pd.options.display.float_format = "{:,.3f}".format
print(audit[["chart_id", "subject", "data_effect", "graphic_effect",
             "lie_factor", "verdict"]].to_string(index=False))

print()

# ── Q2: Identify the one honest graphic ──────────────────────────────────────
print("Q2 — Honest graphic and what the others encode wrongly\n")
honest = audit[audit["lie_factor"].between(0.95, 1.05)]
print(f"Honest graphic(s): {list(honest['chart_id'])}")
for _, row in honest.iterrows():
    print(f"  Chart {row['chart_id']} ({row['subject']}): LF = {row['lie_factor']:.3f} — "
          f"{row['encoding']}")

print()
print("What the others encode wrongly:")
for _, row in audit[~audit["chart_id"].isin(honest["chart_id"])].iterrows():
    print(f"  Chart {row['chart_id']} ({row['subject']}): LF = {row['lie_factor']:.2f} — "
          f"{row['encoding']}")

print()

# ── Q3: Which graphics need ink_dimension=2 ──────────────────────────────────
print("Q3 — Charts that need ink_dimension=2\n")
raw = pd.read_csv(DATA / "case07_lie_factor.csv")
area_charts = raw[raw["ink_dimension"] == 2]
print("Charts with ink_dimension = 2:")
for _, row in area_charts.iterrows():
    lf_1, *_ = vizlib.lie_factor(row["value_start"], row["value_end"],
                                  row["ink_start"], row["ink_end"],
                                  ink_dimension=1)
    lf_2, *_ = vizlib.lie_factor(row["value_start"], row["value_end"],
                                  row["ink_start"], row["ink_end"],
                                  ink_dimension=2)
    print(f"  Chart {row['chart_id']}: ink_dimension=1 gives LF={lf_1:.2f}, "
          f"ink_dimension=2 gives LF={lf_2:.2f}")
    print(f"    Encoding: {row['how_the_graphic_encodes_it']}")
    print(f"    What goes wrong at dimension=1: the formula treats the icon as a LENGTH "
          f"change, missing that area scales as the SQUARE of the linear scale factor. "
          f"A 1.5× scaling reads as 1.5× with dim=1 but the area actually grew "
          f"1.5² = {1.5**2:.2f}×, so dim=1 understates the distortion.")

print()

# ── Q4: Why LF < 1 is still a distortion ─────────────────────────────────────
print("Q4 — Why Lie Factor < 1 is still a distortion\n")
under = audit[audit["lie_factor"] < 0.95]
if len(under):
    for _, row in under.iterrows():
        print(f"  Chart {row['chart_id']} LF = {row['lie_factor']:.2f}: "
              f"graphic understates the data effect.")
print("""
A Lie Factor below 1 means the graphic compresses the real change:
the visual signal is smaller than the data warrants. This is a distortion
in the opposite direction — it minimises a real effect rather than amplifying
a small one.

Who benefits from understating?
  - A company hiding a large cost rise: compressing the ink makes the jump look
    minor even if the data shows, say, a 40% increase.
  - A regulator softening the appearance of a pollution spike.
  - Anyone who wants to report a number without alarming the audience.

Tufte's honest range (0.95 – 1.05) is symmetric precisely because both
exaggeration AND understatement are manipulations — they differ only in which
direction they mislead the reader.
""")

# ── Q5: Lie Factor for Chart F (dual-axis, Case 7) ───────────────────────────
print("Q5 — Lie Factor for Chart F (Part A Case 7 — ShaheenGo dual-axis)\n")
print("""The dual-axis chart does not have a single quantifiable Lie Factor because:

  1. Two independent y-axes mean there is no common 'ink unit' for both series.
     The visual comparison is between a revenue line and a cost line plotted on
     different scales — the crossing point encodes a relationship (cost > revenue)
     that does not exist in the data (revenue 50–80 always > cost 40–56).

  2. Tufte's formula requires one start value and one end value mapped to
     ink positions. A dual-axis chart lets the designer choose FOUR anchors
     (two per axis) and any apparent crossing can be engineered by adjusting
     one axis independently.  The 'ink effect' is not a function of the data;
     it is a function of the designer's axis choice.

What the data actually shows:
  - Revenue ranges from 52 to 80 PKR million over 12 months.
  - Cost   ranges from 44 to 56 PKR million over the same period.
  - Revenue exceeds cost every month by at least 8 PKR million (month 1: 52 − 44 = 8).
  - The profit margin widens over the year as revenue grows faster than cost.

The dual-axis chart is therefore a category error, not just a large Lie Factor:
no single number describes the distortion because the distortion is structural.
The honest fix is a shared axis with a zero baseline (see Case 7 honest chart).
""")

print("=" * 70)
print("End of Part B audit")
print("=" * 70)
