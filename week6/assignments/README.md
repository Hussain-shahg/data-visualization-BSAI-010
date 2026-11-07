# Week 6 submission — Roll No: BSAI-010

Run in this order, from this folder:

```bash
pip install -r requirements.txt
python3 partA_process.py > partA_audit.txt   # raw -> audit -> clean/, writes the decisions table
python3 partB_charts.py                      # 3 charts from clean/ -> charts/partB_1..3.png
python3 partC_figure.py                      # the board figure -> charts/partC_figure.png
python3 partD_interactive.py                 # bonus: interactive HTML + static PNG
```

`partA_process.py` reads the three raw CSVs in `data/` (never edited by hand) and the
`regions.geojson` boundaries, audits them, fixes 11 deliberate defects with a stated rule and
row count for each (printed and saved to `partA_decisions.md`), and writes clean copies to
`clean/`. Every later script reads only from `clean/`, never from `data/`.

`partB_charts.py` answers three different kinds of question (trend, composition, comparison)
from the cleaned data. `partC_figure.py` is the one figure for the board: a normalized
choropleth of grid interruptions, with the raw-count map beside it so the denominator's effect
is visible, documented in `partC_note.md`. `partD_interactive.py` is the optional bonus —
a Plotly rebuild of the Task B trend chart with hover and a zoom slider; open
`partD_interactive.html` in a browser, the interaction contract is printed by the script and in
`partD_interactive.md`.
