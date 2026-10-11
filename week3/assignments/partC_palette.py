"""
Week 3 – Part C: Palette Proof
================================
Prove colour-blind safety using vizlib.simulate_cvd() and vizlib.worst_pair().

Tasks:
  C1. Simulate tab10 under deuteranopia, protanopia, and tritanopia.
      Show before/after swatches.
  C2. Repeat for vizlib.PALETTE["series"] + 4th slot.
  C3. Use worst_pair() on each palette; report ΔE and explain the problem colour.
  C4. State the rule for charts needing more than 3 categories.

Run from week3/assignments/:
    python partC_palette.py
Produces: charts/partC_swatches.png
"""

import pathlib
import sys

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib

vizlib.style_defaults()
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

# ── tab10: first 6 colours (a typical use-case) ──────────────────────────────
import matplotlib.cm as cm
tab10_hex = [
    "#{:02X}{:02X}{:02X}".format(*[int(c * 255) for c in cm.tab10(i)[:3]])
    for i in range(10)
]
# We test the first 6 (a typical multi-series chart)
TAB10_6 = tab10_hex[:6]

COURSE_3  = vizlib.PALETTE["series"]
COURSE_4  = vizlib.PALETTE["series"] + [vizlib.PALETTE["series_4th"]]

PALETTES = {
    "tab10 (first 6)": TAB10_6,
    "course palette (3 slots)": COURSE_3,
    "course palette + 4th slot": COURSE_4,
}

CVD_TYPES = ["deutan", "protan", "tritan"]

# ══════════════════════════════════════════════════════════════════════════════
# Helper: draw a row of colour swatches
# ══════════════════════════════════════════════════════════════════════════════
def swatch_row(ax, colours, label, y=0.5, swatch_w=0.12, gap=0.01):
    x = 0.0
    for c in colours:
        rect = mpatches.FancyBboxPatch(
            (x, y - 0.35), swatch_w, 0.7,
            boxstyle="round,pad=0.01",
            linewidth=0,
            facecolor=c,
        )
        ax.add_patch(rect)
        ax.text(x + swatch_w / 2, y - 0.45, c, ha="center", va="top",
                fontsize=5.5, color=vizlib.PALETTE["ink_soft"])
        x += swatch_w + gap
    ax.text(-0.01, y, label, ha="right", va="center", fontsize=7,
            color=vizlib.PALETTE["ink"])
    return x  # total width used


# ══════════════════════════════════════════════════════════════════════════════
# C1 & C2: Before / after swatch figure
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("PART C — Palette Proof")
print("=" * 70)

fig, axes = plt.subplots(
    len(PALETTES) * (1 + len(CVD_TYPES)), 1,
    figsize=(10, 0.9 * len(PALETTES) * (1 + len(CVD_TYPES))),
    gridspec_kw={"hspace": 0.05},
)
axes = list(axes)

row_idx = 0
for pal_name, pal in PALETTES.items():
    ax = axes[row_idx]
    ax.set_xlim(-0.3, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    swatch_row(ax, pal, f"{pal_name}\n[original]")
    row_idx += 1

    for cvd in CVD_TYPES:
        sim = vizlib.simulate_cvd(pal, kind=cvd)
        ax2 = axes[row_idx]
        ax2.set_xlim(-0.3, 1)
        ax2.set_ylim(0, 1)
        ax2.axis("off")
        swatch_row(ax2, sim, f"  → {cvd}")
        row_idx += 1

fig.suptitle("Palette colour-vision deficiency simulation\n"
             "(Machado et al. 2009, severity 1.0, applied in linear RGB)",
             fontsize=10, y=1.01)
vizlib.save_fig(fig, OUT / "partC_swatches.png",
                note="Source: vizlib.simulate_cvd() | tab10 first 6 colours vs course palette")
plt.close(fig)
print(f"\nSwatch figure saved → {OUT / 'partC_swatches.png'}\n")


# ══════════════════════════════════════════════════════════════════════════════
# C3: worst_pair() analysis
# ══════════════════════════════════════════════════════════════════════════════
print("C3 — worst_pair() analysis\n")
for pal_name, pal in PALETTES.items():
    print(f"Palette: {pal_name}")
    for cvd in [None] + CVD_TYPES:
        label = "normal vision" if cvd is None else cvd
        i, j, a, b, de = vizlib.worst_pair(pal, kind=cvd)
        v = vizlib.verdict(de)
        print(f"  {label:18s}: worst pair S{i}/S{j}  ({a} vs {b})  ΔE = {de:5.1f}  [{v}]")
    print()

print("""
Explanation of what ΔE means (OKLab, ×100):
  ≥ 15  : clearly distinct for normal and CVD vision
  ≥  8  : acceptable for CVD viewers
  6–8   : needs a SECOND encoding channel (marker shape, direct label, texture)
  < 6   : the two series are the same colour — fix the palette

The course 4th slot (#CC79A7 — mauve/pink) is the problem colour because under
deuteranopia it collapses towards the blue slot (#0072B2), dropping the worst-pair
ΔE below 8. Any chart that uses all four slots must add marker shapes, direct
labels, or a data table so CVD viewers can distinguish S1 (blue) from S4 (mauve).
""")


# ══════════════════════════════════════════════════════════════════════════════
# C4: Rule for > 3 categories
# ══════════════════════════════════════════════════════════════════════════════
print("C4 — Rule for charts needing more than three categories\n")
print("""Rule: When a chart needs more than three categorical series, add a second
redundant encoding channel so that colour is not the sole discriminator.

Specifically:
  1. Assign each series a DISTINCT MARKER SHAPE (circle, square, triangle, diamond)
     in addition to its colour.
  2. If the chart type allows it, use DIRECT LABELS on the line/bar ends instead
     of a colour legend.
  3. If neither is possible (e.g., a dense scatter), use a LOOK-UP TABLE or
     small-multiple layout so no two series need to be distinguished by colour alone.

Do NOT answer "use a bigger palette": adding more hues beyond four almost always
produces CVD failures, and the course toolkit provides only three safe slots plus
one conditional fourth slot.

Cite: Wilke, Fundamentals of Data Visualisation, Ch. 20 (redundant coding).
""")

print("=" * 70)
print("End of Part C")
print("=" * 70)
