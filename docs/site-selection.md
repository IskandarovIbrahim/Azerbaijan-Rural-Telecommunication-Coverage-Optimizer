# Selecting tower sites

For each mast-height and grid-spacing scenario, we asked how few sites could serve every settlement with a usable terrain-aware link. All sites have one modeled cost unit. The candidate locations and radio parameters come from the [height and spacing experiment](mast-height-and-spacing.md).

| Mast height | Grid spacing | Candidate sites | Settlements reached | Greedy towers | Minimum towers |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 m | 6 km | 19 | 5 of 14 | 2 | 2 |
| 40 m | 6 km | 19 | 6 of 14 | 3 | 3 |
| 20 m | 3 km | 84 | 8 of 14 | 5 | 5 |
| 40 m | 3 km | 84 | 9 of 14 | 5 | 5 |

Greedy matched the minimum tower count in all four scenarios. The exact solver certified each minimum, and independent enumeration of reachable coverage patterns confirmed it. In the 40 m, 3 km scenario, the methods shared three sites and chose different locations for the other two. Both covered the same nine settlements. [SciPy mixed-integer solver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

On the 3 km grid, 40 m masts reach one more settlement than 20 m masts with the same minimum tower count. On the 6 km grid, reaching the additional settlement increases the minimum from two towers to three. The model uses equal site costs and does not price the extra mast height.

Full coverage is infeasible in all four scenarios. No evaluated candidate reaches Laza, Adur, Qrızdəhnə, Aladaş or Kuzun even in the 40 m, 3 km case.

## Reproduce

From the project root in PowerShell, install the optimization extra and generate the [height and spacing cases](mast-height-and-spacing.md) if they are missing, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[geodata,optimization]'
.\.venv\Scripts\python.exe scripts/compare_tower_selections.py
```

Open `outputs/quba-selection/comparison.json` for the shared summary. Each scenario subfolder contains its own `selection.json`, with selected site IDs, the settlements each can reach, the full-cover status and the input matrix checksum. Greedy breaks ties by site ID. The exact solver can return another equally good selection when several are optimal.
