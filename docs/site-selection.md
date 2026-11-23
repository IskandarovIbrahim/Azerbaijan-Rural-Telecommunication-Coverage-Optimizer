# Selecting tower sites

The 40 m mast and 3 km candidate grid yielded 84 possible sites. Nine of the 14 settlements had at least one usable terrain-aware link. With every site assigned one modeled cost unit, the question is how few sites can serve those nine settlements.

| Method | Sites selected | Settlements reached | Modeled cost units |
| --- | ---: | ---: | ---: |
| Greedy | 5 | 9 of 14 | 5 |
| Exact | 5 | 9 of 14 | 5 |

Greedy and the exact solver shared three sites and chose different locations for the other two. Both selections reach the same nine settlements. The exact solver returned a lower bound of five cost units and a zero optimality gap, so four towers cannot reach all nine on this matrix. An independent enumeration of reachable coverage patterns also found a minimum of five. [SciPy mixed-integer solver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

Full coverage is infeasible with the evaluated links. No candidate reaches Laza, Adur, Qrızdəhnə, Aladaş or Kuzun. Sites have equal assumed cost in this run. The result is a minimum for the simulated link matrix and cost assumptions.

## Reproduce

From the project root in PowerShell, install the optimization extra and generate the [height and spacing cases](mast-height-and-spacing.md) if they are missing, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[geodata,optimization]'
.\.venv\Scripts\coverage-optimizer.exe select-sites --matrix outputs/quba-height-spacing/mast-40m-grid-3000m/matrix.json
```

Open `outputs/quba-selection/selection.json` for the selected site IDs, the settlements each can reach, the full-cover status and the input matrix checksum. Greedy breaks ties by site ID. The exact solver can return another equally good selection when several are optimal.
