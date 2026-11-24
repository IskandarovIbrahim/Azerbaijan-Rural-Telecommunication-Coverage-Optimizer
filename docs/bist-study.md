# Bist rural coverage study

The fifth study area extends 17.5 km from Bist in Ordubad District, Nakhchivan. All 24 named OpenStreetMap village and hamlet points inside the circle also fell inside Azerbaijan. The boundary check excluded two points on the 6 km tower grid and nine on the 3 km grid. The 90 m elevation data had no missing cells in the 2 km terrain buffer. [Ordubad district listing](https://ordubad-ih.gov.az/inzibati-erazi) · [geoBoundaries Azerbaijan metadata](https://www.geoboundaries.org/api/current/gbOpen/AZE/ADM0/)

## Results

| Mast height | Candidate spacing | Eligible sites | Settlements reached | Greedy towers | Minimum towers | Minimum base cost |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 m | 6 km | 22 | 5 of 24 | 2 | 2 | 329,600 AZN |
| 40 m | 6 km | 22 | 6 of 24 | 3 | 3 | 596,700 AZN |
| 20 m | 3 km | 89 | 14 of 24 | 9 | 9 | 1,404,200 AZN |
| 40 m | 3 km | 89 | 16 of 24 | 9 | 9 | 1,723,900 AZN |

The signal-only model found links to all 24 settlement points in each scenario. With terrain included, the denser grid added nine reachable points at 20 m and ten at 40 m. Bist itself was reachable with both mast heights on the 3 km grid. In the highest-reach scenario, eight points still had no usable modeled link.

Greedy and exact selection agreed on tower count and minimum cost in every scenario. In the 40 m, 3 km scenario, cost-aware selection saved about 34,200 AZN compared with pricing the original tower-count solution. The base estimate is about 107,700 AZN per reachable settlement point. Varying site setup, mast, and road-access assumptions gives a modeled range of 1.28–2.53 million AZN for this scenario. Two unused candidates had their nearest mapped road point across the national boundary. Both had zero usable terrain-aware links and contributed zero to the totals. The estimates cover upfront modeled site costs and use the same assumptions and exchange rate as the other studies. [Piran cost assumptions](piran-study.md)

## Reproduce

The [source manifest](../config/bist-sources.json) pins the inputs. Add `--fetch` to the first command if the inputs are missing from the local cache.

```powershell
.\.venv\Scripts\python.exe scripts/compare_mast_height_and_spacing.py --area bist
.\.venv\Scripts\python.exe scripts/compare_tower_selections.py --area bist
.\.venv\Scripts\python.exe scripts/compare_infrastructure_costs.py --area bist
```

Results are written to `outputs/bist-height-spacing`, `outputs/bist-selection`, and `outputs/bist-costs`.
