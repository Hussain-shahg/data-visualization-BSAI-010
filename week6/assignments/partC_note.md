# Part C — Note
**Week 6 Data Visualisation Assignment | Roll No: BSAI-010**

**The figure runs from `partC_figure.py`**, reads only `clean/district_grid.csv` and `data/regions.geojson`, and exports at 300 dpi with a source note naming the files, the classification scheme, the projection and both correlation checks.

**The quantity is normalized.** The left panel is interruptions **per 1,000 households** — named in words in the legend title, not just "interruptions". The denominator is households, not population, because an interruption is billed and felt per connection, not per head.

**The message, in one sentence, for the named reader:** for the National Grid Authority board splitting next month's reliability budget, the districts that are genuinely hardest to keep powered are **D12, D11 and D13** — not the three biggest districts the raw interruption count would point at (**D17, D13, D24**), which share only **D13** with the real answer.

**Parameters, each with a reason:**

| Parameter | Value | Reason |
|---|---|---|
| Denominator | Households | An interruption is a connection-level event; households is the unit the budget is actually spent per |
| Classification scheme | Natural breaks (Jenks), k=5, GVF=0.96 | Jenks maximises the variance explained by the class boundaries — not asserted, scored |
| Projection | Equal-area (Lambert cylindrical) | Colour over an area makes area the encoding channel; Mercator would inflate the northern districts relative to the south (Week 5, Part B.4: 1.11×–1.22× across this exact federation) |
| Period | Trailing 12 months | Matches the register's own `outages`/`outage_minutes` window, stated in the standfirst |

**The counterfactual.** r(interruptions, households) = **0.99** — a raw-count map is, to a very close approximation, a population-of-households map, and it would have sent the committee's attention to **D17, D13 and D24**, the three largest districts by connection count. r(rate, households) is much weaker at **0.18**, confirming the rate map is not simply re-deriving the same population pattern under a different name. Only **D13** appears on both lists; the raw-count version would have taken the reliability budget **away from D12 and D11**, the two districts whose residents actually experience the most interruptions per connection, and given it instead to D17 and D24 chiefly because more people happen to live there. The same pattern as Weeks 5 and 6's earlier maps: the five most populous districts hold **59.9%** of all residents on just **12.6%** of the land, so a count-based view gives those five districts most of the ink and most of the budget almost regardless of their actual service quality.

No district was suppressed or merged; all 24 districts' interruption counts (minimum 3,234) are large enough to publish individually without a small-area stability concern.
