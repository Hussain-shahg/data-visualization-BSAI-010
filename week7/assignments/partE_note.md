# Part E — The note
**Week 7 Data Visualisation Assignment | Roll No: BSAI-010**

## 1. The message, the reader, the parameters

**Message, one sentence:** Network punctuality rose +1.73 points (78.87% → 80.60%, 2025 Q2 vs 2026 Q2), but every single mode's own on-time rate fell (Metro −1.31, BRT −0.85, Bus −1.10, Ferry −1.19) — the network figure improved only because the mix shifted toward punctual Metro (10.9% → 21.8% of departures) and away from Bus (71.6% → 57.6%), which `dashlib.rate_decomposition()` splits exactly into within = −1.10 pts and mix = +2.82 pts.

**Reader:** the Authority's board, choosing how to read their own published headline before next month's budget meeting — specifically the Secretary (reads the KPI tile and nothing else) and the finance director (will filter to one mode).

**Parameters, each with a reason:**

| Parameter | Value | Reason |
|---|---|---|
| Window | 2025 Q2 vs 2026 Q2 (full calendar quarters) | Matches how the Authority itself reports; Part D's own text notes the finding holds under two other windows too (first-3-months-vs-last-3 gives +2.02 pts, first-6-vs-last-6 gives +1.52 pts), so the quarter choice is not load-bearing |
| Unit | Boardings for Task B/D's map and the counterfactual; on-time departures / operated departures (never a mean of daily percentages) for punctuality | A boarding is not a journey (the file-wide ratio is 1.305); punctuality is a ratio of two counts, so it is summed then divided, never averaged daily |
| Denominator (map) | Population, boardings per 1,000 residents | The board is siting infrastructure by where people already ride relative to how many live there, not by raw traffic |
| Classification | Natural (Jenks) breaks, k=5 | Scored by GVF, not asserted |
| Projection | Equal-area | Colour over an area makes area the channel; Mercator would distort it by 1.11×–1.22× across this federation (Week 5, Part B.4) |
| Scaling / axis order | N/A this week (no parallel-coordinates panel) | — |

## 2. The counterfactual

A raw-count map of boardings would be, almost exactly, a population map: r(boardings, population) = **+0.945** across the 24 districts, against only **+0.249** for the per-capita rate. Ranked by raw count, the top three districts are **D17, D09, D13**; ranked by the rate the board should actually care about, they are **D12, D21, D09** — only **D09** appears on both lists. A raw-count version of Task B/D's map would have pointed the next-corridor conversation at D17 and D13 chiefly because they are large, taking it away from **D12** and **D21**, where transit use per resident is genuinely highest. This is the same pattern Weeks 5 and 6 showed on different data: the five most populous districts hold **59.9%** of the federation's residents on just **12.6%** of its land, so any raw-count view gives those five districts most of the ink by construction, independent of whether the underlying thing being mapped is disease, outages, or — here — transit ridership.

No district was suppressed or merged for this submission; all 24 districts' boardings counts are large enough to publish individually.
