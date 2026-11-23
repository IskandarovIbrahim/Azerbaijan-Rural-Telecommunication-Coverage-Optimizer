# Azerbaijan Rural Telecommunication Coverage Optimizer

A terrain-aware wireless planning study for 14 settlements within 17.5 km of Xınalıq, Azerbaijan. The pipeline prepares mapped settlements and elevation, screens hypothetical mast locations, and estimates which site-to-settlement links pass the signal and line-of-sight checks. The next stage will use these results to compare site-selection algorithms.

The free-space model found a passing link to all 14 settlements with the baseline setup. Adding terrain reduced that result to five. Doubling the mast height from 20 m to 40 m and reducing candidate spacing from 6 km to 3 km increased modeled reachability to nine. These are simulated links to outdoor receiver points under stated assumptions.

- [Pilot area and data preparation](docs/pilot-inputs.md)
- [Data sources](docs/data-sources.md)
- [Radio model and baseline results](docs/radio-model.md)
- [Mast height and site spacing experiment](docs/mast-height-and-spacing.md)
- [Interactive explainer source](site/dist/index.html)

## Set up the project in Windows PowerShell

From the project root, with Python 3.11 or newer:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[geodata]'
.\.venv\Scripts\coverage-optimizer.exe --help
.\.venv\Scripts\coverage-optimizer.exe check-config config/quba-pilot.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use your installed Python version in the first command if it differs. The config check and tests run offline after installation. The [pilot config](config/quba-pilot.json) and [data contract](docs/data-contract.md) define the study settings and file formats.

## Prepare the Quba pilot data

Follow the [pilot input guide](docs/pilot-inputs.md) to fetch the pinned files, rerun preparation from your local cache, or inspect the results in VS Code.

## Model radio links

Once pilot data is prepared, run `.\.venv\Scripts\coverage-optimizer.exe model-links`. The [radio model guide](docs/radio-model.md) explains the link-budget assumptions and generated files.

## Interactive pilot explainer

Open [the website](site/dist/index.html) to explore the four simulation cases. The page works from local files and needs no account or API keys for its controls. Select a mast height, candidate spacing and signal model, then choose a settlement to inspect its passing links.

To refresh the website data after regenerating the pilot inputs and scenarios, run these commands from the project root:

```powershell
.\.venv\Scripts\python.exe scripts/compare_mast_height_and_spacing.py
.\.venv\Scripts\python.exe site/generate_assets.py
```

The generator builds a terrain preview from the pinned elevation inputs and reads the run summaries and link tables to make the browser data. The browser presents precomputed results. It shows which settlements are reachable from the candidate pool, ahead of selecting a final set of towers.
