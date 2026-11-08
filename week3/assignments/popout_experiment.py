"""
Week 3 bonus - Week 1's pop-out activity, rebuilt in code.  (Optional, 5 marks.)

Panels 1-2 are the course starter (starter/popout.py). Panels 3 (size only)
and 4 (colour AND shape, redundant coding) are completed below.

The timing experiment itself (TODO 3 in the starter -- show each panel to
five classmates, time them, chart mean seconds with a strip plot of the raw
times) is NOT run here: inventing five people's reaction times would be
exactly the kind of fabricated result this course's briefs repeatedly say
scores zero. The four-panel stimulus is built and ready to show; running
the actual timing on five real people and completing the results chart is
the one piece of this bonus still outstanding.

Run from week3/assignments/:
    python popout_experiment.py
Produces: popout_panels.png
"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vizlib import PALETTE, save_fig, style_defaults  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
style_defaults()

ROWS, COLS = 12, 18
TARGET = "3"
N_TARGETS = 9
SEED = 1947


def make_grid(seed=SEED):
    """A grid of digits with exactly N_TARGETS threes, in fixed positions."""
    rng = np.random.default_rng(seed)
    others = [d for d in "0123456789" if d != TARGET]
    grid = np.array([[rng.choice(others) for _ in range(COLS)]
                     for _ in range(ROWS)], dtype=object)
    flat = rng.choice(ROWS * COLS, size=N_TARGETS, replace=False)
    for k in flat:
        grid[k // COLS, k % COLS] = TARGET
    return grid


def draw(ax, grid, title, colour=False, size=False, shape=False):
    """
    colour -> targets get the highlight hue   (a preattentive channel)
    size   -> targets are drawn larger        (another one)
    shape  -> targets get a ring behind them  (a third, and it survives
              greyscale printing and colour blindness)
    """
    ax.set_xlim(-0.5, COLS - 0.5)
    ax.set_ylim(-0.5, ROWS - 0.5)
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title(title, fontsize=10.5, loc="left")
    for r in range(ROWS):
        for c in range(COLS):
            d = grid[r, c]
            hit = d == TARGET
            if shape and hit:
                ax.add_patch(plt.Circle((c, r), 0.40, fill=False,
                                        edgecolor=PALETTE["ink"], lw=1.6))
            ax.text(c, r, d, ha="center", va="center",
                    fontsize=15 if (size and hit) else 11,
                    fontweight="bold" if (size and hit) else "normal",
                    color=PALETTE["highlight"] if (colour and hit)
                    else PALETTE["ink"])


def main():
    grid = make_grid()
    fig, ax = plt.subplots(2, 2, figsize=(13.0, 8.0))

    # Panel 1: no channel -- serial search, you read every cell.
    draw(ax[0, 0], grid, "1. No channel -- you have to read every cell")

    # Panel 2: colour. One preattentive channel; the 3s appear at once.
    draw(ax[0, 1], grid, "2. Colour -- the targets appear before you look",
        colour=True)

    # Panel 3: SIZE ONLY, no colour. Wilke ch. 20: size is preattentive but
    # measurably slower than colour/hue for a search task like this one --
    # the reader still has to compare each candidate's size against its
    # neighbours, which colour (a categorical pop) does not require.
    draw(ax[1, 0], grid, "3. Size only -- preattentive, but slower than colour",
        size=True)

    # Panel 4: redundant coding -- colour AND shape together. The Week 2
    # accessibility rule in its original perceptual form: a reader with
    # deuteranopia loses panel 2 entirely (the highlight hue collapses
    # toward the ink colour) and keeps panel 4's ring cue intact.
    draw(ax[1, 1], grid, "4. Colour AND shape -- redundant coding, accessible under CVD",
        colour=True, shape=True)

    fig.suptitle(f"Count the {TARGET}s. Same {N_TARGETS} targets in all four "
                 f"panels, same positions.",
                 x=0.006, ha="left", fontsize=13.5, fontweight="bold",
                 color=PALETTE["ink"])
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = save_fig(fig, os.path.join(ROOT, "popout_panels.png"),
                   f"{ROWS}x{COLS} grid, {N_TARGETS} targets, seed {SEED}. "
                   f"Week 1 activity, rebuilt in Matplotlib.")
    plt.close(fig)
    print("wrote", out)

    print("""
NOT RUN: showing each panel to five real classmates, timing them with a
stopwatch (one at a time, a different random panel order per person), and
charting mean seconds (zero baseline, raw times as a strip plot over a
faded bar, n=5 and the randomisation method stated in the source note).
The brief is explicit that invented results score zero, so no timings are
fabricated here. The stimulus above is built and ready to show; running
the timing on five people and completing that chart plus the three-sentence
write-up is the one piece of this bonus still outstanding.
""")


if __name__ == "__main__":
    main()
