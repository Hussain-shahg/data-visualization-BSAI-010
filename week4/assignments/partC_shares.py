"""
Week 4 - Part C: part-to-whole legality, and the ranking.

Questions 1 and 4 (legality tests, and the rule) are answered here, computed.
Questions 2 and 3 require timing a REAL reader with a stopwatch on a printed
stimulus -- that cannot be fabricated (invented results score zero, per the
brief), so it is not simulated here. See the note at the bottom.

Run from week4/assignments/:
    python partC_shares.py
"""
import pathlib
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import vizlib
import tslib

vizlib.style_defaults()
DATA = pathlib.Path(__file__).parent / "data"
OUT = pathlib.Path(__file__).parent / "charts"
OUT.mkdir(exist_ok=True)

print("=" * 70)
print("PART C -- part-to-whole legality, and the ranking")
print("=" * 70)

# ══════════════════════════════════════════════════════════════════════════
# C1 -- the three conditions, tested in code, for all three tables
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("C1 -- the three conditions (exclusive parts / meaningful whole / share is the question)")
print("-" * 70)

print("\n(a) The four touch_* columns of case08_channel_attrib.csv")
df8 = pd.read_csv(DATA / "case08_channel_attrib.csv")
ex8 = tslib.exclusivity_check(df8, ["touch_search", "touch_social", "touch_email", "touch_direct"])
print(f"  exclusivity_check: sum={ex8['sum_pct']:.1f}%, exclusive={ex8['exclusive']}, "
      f"{ex8['n_multi']} of {ex8['n']} customers touched by >1 channel")
print("  Test 1 (exclusive parts): FAILS -- shares sum to 131%, a customer can be in several.")
print("  Test 2 (meaningful whole): the 4,000 customers are a real, fixed population -- OK.")
print("  Test 3 (share is the question): the real question is 'which channels drive customers', "
      "not 'what share of one whole' -- a part-to-whole chart is the wrong question entirely.")
print("  VERDICT: neither a pie nor a (stacked, 100%) bar -- NEITHER. A plain (non-stacked) bar "
      "of each channel's reach is legal; a part-to-whole chart of these four is not.")

print("\n(b) The eight rows of shares_eight.csv")
df_sh = pd.read_csv(DATA / "shares_eight.csv")
total_sh = df_sh["share_pct"].sum()
print(f"  sum of share_pct = {total_sh:.2f}%")
print("  Test 1 (exclusive parts): PASSES -- one sub-category per slice, by construction.")
print("  Test 2 (meaningful whole): PASSES -- the whole is 'this catalogue's 8 biggest "
      "sub-categories', a real, named total.")
print("  Test 3 (share is the question): PASSES -- the deck's own question is about share of "
      "catalogue revenue.")
print("  VERDICT: legal as a pie AND as a bar chart. (Part A/Week 2's channel ranking is the "
      "argument for drawing the bar chart anyway: position beats angle.)")

print("\n(c) premium vs other revenue, case09_premium_share.csv, 2025Q4")
df9 = pd.read_csv(DATA / "case09_premium_share.csv")
q4 = df9[df9["quarter"] == "2025Q4"].iloc[0]
other = q4["total_revenue_pkr_m"] - q4["premium_revenue_pkr_m"]
print(f"  premium={q4['premium_revenue_pkr_m']:.1f}, other={other:.1f}, "
      f"total={q4['total_revenue_pkr_m']:.1f} -- sums exactly by construction.")
print("  Test 1 (exclusive parts): PASSES -- premium and 'everything else' partition total "
      "revenue exactly, by definition.")
print("  Test 2 (meaningful whole): PASSES -- total quarterly revenue is a real, single number.")
print("  Test 3 (share is the question): FAILS as Case 9 used it -- the deck's real question was "
      "'is premium revenue growing', and the share alone cannot answer that (Case 9's diagnosis: "
      "the share rose because the TOTAL fell, not because premium grew).")
print("  VERDICT: a 2-slice pie or bar for THIS quarter is arithmetically legal, but answers the "
      "wrong question on its own -- it must be shown beside the two raw series, not instead of them.")

# ══════════════════════════════════════════════════════════════════════════
# C4 -- state the rule
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("C4 -- the rule")
print("-" * 70)
print("""  I will draw a pie only when all three slide-32 conditions hold AT ONCE: the parts are
  verifiably exclusive (tested in code, not assumed), the whole is a single named, fixed
  quantity a reader would recognise, and "what share of that whole" is actually the question
  being asked -- not a proxy for a trend or a rate question that a pie cannot answer. In every
  other case: a sorted bar chart.""")

# ══════════════════════════════════════════════════════════════════════════
# C2/C3 -- the reader experiment: stimuli built, experiment NOT fabricated
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 70)
print("C2/C3 -- the pie-ranking experiment on a real reader")
print("-" * 70)
order = df_sh["slice"].tolist()
shares = df_sh["share_pct"].tolist()

fig, ax = plt.subplots(figsize=(5, 5))
ax.pie(shares, labels=order, startangle=90, counterclock=False,
       colors=(vizlib.PALETTE["series"] * 3)[:8])
ax.set_title("Eight shares -- rank them A to H, largest first")
vizlib.save_fig(fig, OUT / "partC_pie_stimulus.png",
                note="Source: shares_eight.csv | no numbers shown | startangle=90, counterclock=False")
plt.close(fig)

sorted_df = df_sh.sort_values("share_pct", ascending=True)
fig, ax = plt.subplots(figsize=(6, 4))
ax.barh(sorted_df["slice"], sorted_df["share_pct"], color=vizlib.PALETTE["series"][0])
ax.set_xlabel("")
ax.set_title("Eight shares -- rank them A to H, largest first")
ax.spines[["top", "right"]].set_visible(False)
vizlib.save_fig(fig, OUT / "partC_bar_stimulus.png",
                note="Source: shares_eight.csv | sorted horizontal bars, no numbers shown")
plt.close(fig)
print("  Both stimuli generated: charts/partC_pie_stimulus.png, charts/partC_bar_stimulus.png")
print(f"  True rank order (largest first): "
      f"{' > '.join(df_sh.sort_values('share_pct', ascending=False)['slice'])}")

print("""
  NOT RUN: this part asks for a real reader, timed with time.perf_counter() on each
  stimulus above, with their answers and times saved to pie_ranking_results.csv. The brief
  is explicit that invented results score zero and are obvious, so no numbers are fabricated
  here. The stimuli are generated and ready; running the experiment and completing
  pie_ranking_results.csv, the scoring (C3) and the two-line write-up is the one piece of this
  part still outstanding, and needs an actual person in front of the two PNGs above with a
  stopwatch.
""")

print("=" * 70)
print("End of Part C")
print("=" * 70)
