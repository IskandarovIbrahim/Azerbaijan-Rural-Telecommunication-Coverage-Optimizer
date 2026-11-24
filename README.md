# Azerbaijan Rural Telecommunication Coverage Optimizer

A terrain-aware planning study that estimates which rural settlements can be reached by hypothetical wireless towers and which tower locations provide that reach at the lowest modeled cost. All five study areas use the same terrain resolution, radio assumptions, mast heights, and candidate grid spacings.

## Results

The highest-reach scenario used **40 m masts and a 3 km candidate grid** in each modeled area.

| Study area | Settlements reached | Minimum towers | Minimum base cost estimate |
| --- | ---: | ---: | ---: |
| Quba (Xınalıq) | 9 of 14 | 5 | 885,500 AZN |
| İsmayıllı (Lahıc) | 64 of 68 | 21 | 3,611,400 AZN |
| Gədəbəy (Slavyanka) | 67 of 92 | 30 | 5,060,600 AZN |
| Lerik (Piran) | 111 of 138 | 25 | 4,321,500 AZN |
| Ordubad (Bist) | 16 of 24 | 9 | 1,723,900 AZN |

In Slavyanka, the exact method reached the same 67 settlements as greedy with one fewer tower. When the two methods used site-specific costs, the exact selection saved about **167,100 AZN** under the base assumptions. The estimates are for upfront infrastructure and use illustrative inputs. [Study areas](docs/study-areas.md) · [Slavyanka results](docs/slavyanka-study.md)

## How it works

1. Use named OpenStreetMap village and hamlet points, a 90 m Copernicus elevation surface, and a grid of candidate sites screened for terrain and water.
2. Model signal loss and terrain clearance for every tower-to-settlement pair at 20 m and 40 m mast heights and 3 km and 6 km site spacing.
3. Compare greedy selection with exact mixed-integer optimization on the same terrain-aware links. Run both methods with equal site costs to compare tower count, then with estimated site costs to compare infrastructure budgets.

The simulation uses one outdoor receiver point per settlement, assumes power and backhaul at each candidate, and checks direct line of sight. Field measurements, site surveys, and local quotes would be needed for deployment. [Data sources](docs/data-sources.md) · [Radio model](docs/radio-model.md) · [Tower selection](docs/site-selection.md)

## Interactive map

Open [Signal Atlas](site/dist/index.html) in a browser from your local checkout to explore Quba, İsmayıllı, Gədəbəy, Lerik and Ordubad. Choose a district and scenario to compare all candidates, the greedy layout, and the exact layout. Zoom or drag the map, turn on **Elevation** to inspect a 90 m cell, and select a settlement to see a usable link or an example terrain obstruction when available. The cost table compares lower, base, and higher assumptions in AZN.

## Reproduce on Windows

From the repository root with Python 3.11 and curl installed:

```powershell
py -3.11 -m venv .venv
$python = '.\.venv\Scripts\python.exe'
& $python -m pip install -e '.[geodata,optimization]'
& $python -m unittest discover -s tests -v

foreach ($area in 'quba', 'lahic', 'slavyanka', 'piran', 'bist') {
    & $python scripts/compare_mast_height_and_spacing.py --area $area --fetch
    if ($LASTEXITCODE -ne 0) { throw "Link modeling failed for $area" }
    & $python scripts/compare_tower_selections.py --area $area
    if ($LASTEXITCODE -ne 0) { throw "Tower selection failed for $area" }
    & $python scripts/compare_infrastructure_costs.py --area $area
    if ($LASTEXITCODE -ne 0) { throw "Cost estimation failed for $area" }
}
& $python site/generate_assets.py
```

The source manifests pin file URLs and checksums. Keep the dated Geofabrik extract in the local cache for exact reproduction if the original URL expires. With the input files already cached, omit `--fetch` for an offline run. Outputs are written under `outputs/`, and the site generator exports the precomputed results to `site/dist/`. [Data contract](docs/data-contract.md) · [Lahıc results](docs/lahic-pilot.md) · [Piran results](docs/piran-study.md) · [Bist results](docs/bist-study.md)

## Author

Created by **Ibrahim Iskandarov**. [LinkedIn](https://www.linkedin.com/in/ibrahimiskandarov/) · [GitHub](https://github.com/IskandarovIbrahim) · [Contact](mailto:ibrahim.iskandarov@rwth-aachen.de)
