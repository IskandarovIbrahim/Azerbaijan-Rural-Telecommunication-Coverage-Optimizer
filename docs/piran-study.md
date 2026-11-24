# Piran rural coverage study

The study extends 17.5 km from Piran in Lerik District. It contains 138 named village and hamlet points from the same OpenStreetMap snapshot used for the other study areas. Two points named Qışlaq are 12.1 km apart and were retained. A small part of the circular footprint extends past the reference boundary. Every modeled settlement and eligible tower location in both grids falls within the exterior Azerbaijan boundary. The 2 km terrain buffer has no missing elevation cells. [geoBoundaries Azerbaijan metadata](https://www.geoboundaries.org/api/current/gbOpen/AZE/ADM0/)

## Results

| Mast height | Site spacing | Eligible sites | Reachable with terrain | Greedy towers | Minimum towers | Minimum base cost estimate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 m | 6 km | 24 | 67 of 138 | 9 | 8 | 1,084,400 AZN |
| 40 m | 6 km | 24 | 76 of 138 | 13 | 12 | 2,048,100 AZN |
| 20 m | 3 km | 101 | 102 of 138 | 24 | 22 | 3,022,300 AZN |
| 40 m | 3 km | 101 | 111 of 138 | 26 | 25 | 4,321,500 AZN |

The signal-only model found passing links to all 138 points in every scenario. The denser grid added 35 terrain-reachable settlements at either height. Taller masts added nine at either grid spacing. The 40 m mast and 3 km grid left 27 settlements without a usable modeled link.

The exact method used fewer towers than greedy in every equal-cost comparison. With site-specific base costs in the 40 m, 3 km case, cost-aware greedy and exact selection both found a 25-tower layout costing about 4,321,500 AZN. Pricing the original count-minimizing layout gave about 4,345,700 AZN for the same coverage. Cost figures use the same illustrative setup, mast and access assumptions as the other areas, with the [23 November 2026 exchange rate](https://www.cbar.az/currency/rates?date=23%2F11%2F2026&language=en). Values are rounded to the nearest 100 manat.

## Reproduce

The [source manifest](../config/piran-sources.json) pins the inputs. Add `--fetch` to the first command if its source files are missing from the local cache.

```powershell
.\.venv\Scripts\python.exe scripts/compare_mast_height_and_spacing.py --area piran
.\.venv\Scripts\python.exe scripts/compare_tower_selections.py --area piran
.\.venv\Scripts\python.exe scripts/compare_infrastructure_costs.py --area piran
```

Results are under `outputs/piran-height-spacing`, `outputs/piran-selection`, and `outputs/piran-costs`.
