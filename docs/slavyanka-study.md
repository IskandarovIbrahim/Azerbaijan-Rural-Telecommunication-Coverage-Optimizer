# Slavyanka rural coverage study

The study circle extends 17.5 km from Slavyanka in Gədəbəy District and uses the same OpenStreetMap snapshot, 90 m elevation product, radio assumptions, and candidate screening as the Quba and Lahıc studies. It includes 92 distinct mapped village and hamlet points. Three names occur twice at separate locations 16–29 km apart. The circle and its 2 km terrain buffer fall inside the exterior Azerbaijan boundary at raster resolution. [geoBoundaries Azerbaijan metadata](https://www.geoboundaries.org/api/current/gbOpen/AZE/ADM0/)

## Results

| Mast height | Site spacing | Candidate sites | Reachable with terrain | Greedy towers | Minimum towers | Minimum base estimate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 m | 6 km | 28 | 26 of 92 | 12 | 12 | 1,589,000 AZN |
| 40 m | 6 km | 28 | 34 of 92 | 14 | 14 | 2,326,600 AZN |
| 20 m | 3 km | 109 | 56 of 92 | 28 | 27 | 3,661,300 AZN |
| 40 m | 3 km | 109 | 67 of 92 | 31 | 30 | 5,060,600 AZN |

The signal-only model reached all 92 settlement points in each scenario. Under the terrain-aware model, moving to a 3 km grid added 30 reachable settlements at 20 m and 33 at 40 m. The 40 m, 3 km case had the highest reach. No evaluated candidate provided a passing link to 25 settlements in that case, so serving all 92 is infeasible under those assumptions.

At 3 km spacing, the exact solver reached the same settlements as greedy with one fewer tower at each height. Under the base cost assumptions for the 40 m, 3 km case, pricing the existing minimum-count layout gave about 5,078,500 AZN. Cost-aware greedy gave 5,227,700 AZN, and exact cost-aware selection gave 5,060,600 AZN. All served the same 67 settlements. The minimum estimates use the [23 November 2026 exchange rate](https://www.cbar.az/currency/rates?date=23%2F11%2F2026&language=en) and the same illustrative setup, mast and access costs used in the other areas.

## Reproduce

The [source manifest](../config/slavyanka-sources.json) pins the inputs. Add `--fetch` to the first command if its source files are missing from the local cache.

```powershell
.\.venv\Scripts\python.exe scripts/compare_mast_height_and_spacing.py --area slavyanka
.\.venv\Scripts\python.exe scripts/compare_tower_selections.py --area slavyanka
.\.venv\Scripts\python.exe scripts/compare_infrastructure_costs.py --area slavyanka
```

Results are under `outputs/slavyanka-height-spacing`, `outputs/slavyanka-selection`, and `outputs/slavyanka-costs`.
