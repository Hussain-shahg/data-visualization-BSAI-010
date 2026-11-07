# Part D1 (bonus) — Interaction contract

**What:** An interactive rebuild of Task B's Chart 1 (monthly mean outage length) in Plotly.
Open `partD_interactive.html` in any browser; `charts/partD_interactive.png` is the static
default-state export for a reader with no mouse.

**Default state:** identical information to the static chart — 18 monthly bars, the partial
final month shaded grey, a 3-month rolling mean line, nothing pre-filtered or pre-zoomed.

**The controls:**

| Control | What it changes | What it does NOT change | Way back |
|---|---|---|---|
| Hover | Reveals the exact mean outage minutes for the month under the cursor, and flags partial months explicitly | The plotted data | Always available — no state to reset |
| Range-slider zoom | Restricts the visible x-range to any window the reader drags | The rolling mean's calculation — it is computed over the **full** 18-month series first, then clipped to whatever is in view, so zooming cannot manufacture a trend the full series does not support | Double-click the plot area to reset to the full range |

**One sentence on what the interaction lets a reader do that the static version cannot:** a
reader can isolate and read exact values for any sub-period they personally care about (a
specific quarter, a specific incident window) without the chart-maker having had to anticipate it.

**One sentence on what it lets them do that I would rather they did not:** zoom to a short,
conveniently-sloping 3–4 month window and screenshot it as "the trend" — exactly Week 4 Part
B.5's cherry-picked-window problem, now reachable with a mouse drag instead of a pandas slice;
the caption states the full 18-month range precisely so a screenshot of a zoomed view still
carries the honest full-series context next to it.
