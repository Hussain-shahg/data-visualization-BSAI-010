# Week 7 submission — Roll No: BSAI-010

Run in this order, from this folder:

```bash
pip install -r requirements.txt
python3 partA_process.py > partA_audit.txt   # raw -> audit -> clean/, writes the decisions table
python3 partB_charts.py                      # 4 charts from clean/ -> charts/partB_1..4.png
python3 partC_interactive.py                 # interactive HTML + static default-state PNG
python3 partD_screen.py                      # the board's one screen -> charts/partD_screen.png
python3 partF_screen.py                      # bonus: same pipeline on real MTA data
```

`partA_process.py` reads the four raw files in `data/` (never edited by hand) and
`regions.geojson`, audits them, fixes 14 deliberate defects with a stated rule and row count
for each (printed and saved to `partA_decisions.md`), and writes clean copies to `clean/`.
Every later script reads only from `clean/`.

`partB_charts.py` answers four different kinds of question (trend, composition/hierarchy,
comparison, a normalized map) from the cleaned data. `partC_interactive.py` rebuilds the trend
chart in Plotly with hover, legend-click and a zoom slider — open `partC_interactive.html` in a
browser; the interaction contract is in `partC_contract.md`. `partD_screen.py` is the one screen
for the Board: the headline (network punctuality +1.73 pts) sits directly beside the reversal
(every mode's own punctuality fell), with the mix-shift explanation, the next-corridor map and
the farebox comparison alongside — documented in `partE_note.md`. `partF_screen.py` is the
optional bonus: the same audit/clean/figure pipeline run on real MTA daily ridership data,
cited and dated.
