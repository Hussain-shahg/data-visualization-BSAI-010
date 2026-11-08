# Part C — Interaction contract
**Week 7 Data Visualisation Assignment | Roll No: BSAI-010**

**The interactive view runs from `partC_interactive.py`**, reads only `clean/ridership_daily.csv`, and writes `partC_interactive.html` (open in any browser) plus a static default-state export `charts/partC_default.png`, from a clean checkout.

**The default state.** All four modes' monthly punctuality (sum of on-time departures over sum of operated departures, per month — never a mean of daily percentages) across the full reporting window, nothing isolated and nothing zoomed. Most readers never touch a control, so this is the view that has to stand on its own — and it already shows the one fact Task D's headline will build on: every mode's own line drifts slightly down over the period.

**The controls:**

| Control | What it changes | What it does NOT change | Way back |
|---|---|---|---|
| Hover | Reveals the exact punctuality percentage for one mode, one month | The plotted data | Always available |
| Legend click | Isolates (or restores) one mode's line | How punctuality is computed for the remaining visible line(s) — still `sum(on_time)/sum(operated)` over the full period, not recalculated against a smaller base | Click the same legend entry again, or any hidden entry, to bring it back |
| Date-range slider | Zooms the x-axis to any window | The monthly punctuality values themselves — each point is computed once, over its own month, before any zooming; dragging cannot manufacture a different number for a month already on screen | Drag the slider back out, or double-click the plot |

**The thing the control must not invite.** Isolating **Bus** with a legend click and then zooming the date-range slider to its three worst months makes it trivial to build a "the network is collapsing" screenshot — technically honest about Bus, but silent about two facts the default view carries and an isolated, zoomed view does not: Metro (the mode carrying the plurality of journeys, Task B Chart 2) stays above 94% for the entire period, and Bus's own ridership share has been *falling* over the same window (Task B Chart 2 / Part D), so a reader weighting modes equally is already over-weighting the one that matters least to the network total. The chart's caption states the computation rule (`sum(on_time)/sum(operated)`, never a mean of means) explicitly enough that it survives being carried along in a screenshot, and Task D's screen puts the mix-adjusted reversal next to the headline specifically so a reader cannot stop at one isolated mode's line.
