# Lahıc rural coverage pilot

The study circle extends 17.5 km from Lahıc in İsmayıllı District. It includes 68 named village and hamlet points from the same OpenStreetMap snapshot as the first pilot. A 2 km elevation buffer covers link profiles near the edge. The study circle falls inside the exterior national boundary at the 90 m raster resolution. [geoBoundaries Azerbaijan metadata](https://www.geoboundaries.org/api/current/gbOpen/AZE/ADM0/)

## Results

| Mast height | Candidate spacing | Candidates | Reachable with terrain | Minimum towers | Minimum base estimate |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 m | 6 km | 24 | 33 of 68 | 12 | 1,756,900 AZN |
| 40 m | 6 km | 24 | 37 of 68 | 13 | 2,334,100 AZN |
| 20 m | 3 km | 96 | 59 of 68 | 21 | 2,935,900 AZN |
| 40 m | 3 km | 96 | 64 of 68 | 21 | 3,611,400 AZN |

The signal-only model reached all 68 settlements in every scenario. On the denser grid, taller masts added five modeled connections at the same minimum tower count. The 20 m, 3 km scenario had the lowest base cost per reachable settlement, about 49,800 AZN. The 40 m, 3 km scenario served the most settlements. Səkkizatlı, Hacıman, Səfalı and Pirəbülqasım lacked a passing link in that scenario.

Greedy and exact selection agreed on the minimum tower count in all four scenarios. Under the base cost assumptions for 40 m masts on the 3 km grid, pricing the original minimum-count layout gave about 3,729,500 AZN, cost-aware greedy gave about 3,637,700 AZN, and exact cost-aware selection gave about 3,611,400 AZN. All three layouts reached the same 64 settlements.

The cost model uses the same assumptions for site setup, mast and foundation, and access as the first pilot. Values use the [23 November 2026 exchange rate](https://www.cbar.az/currency/rates?date=23%2F11%2F2026&language=en) and are rounded to the nearest 100 manat. Actual construction budgets would need site surveys and local quotes.

## Reproduce the run

Run from the project root in PowerShell. The [source manifest](../config/lahic-sources.json) pins the elevation and village data. Add `--fetch` to the first command to fetch missing cached files.

```powershell
.\.venv\Scripts\python.exe scripts/compare_mast_height_and_spacing.py --area lahic
.\.venv\Scripts\python.exe scripts/compare_tower_selections.py --area lahic
.\.venv\Scripts\python.exe scripts/compare_infrastructure_costs.py --area lahic
```

Results are under `outputs/lahic-height-spacing`, `outputs/lahic-selection`, and `outputs/lahic-costs`.
