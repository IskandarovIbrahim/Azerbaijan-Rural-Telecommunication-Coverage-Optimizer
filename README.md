# Azerbaijan Rural Telecommunication Coverage Optimizer

Where should hypothetical wireless access sites go to reach a group of mountain villages at the lowest modeled cost? This project will compare greedy and exact optimization using the same terrain-aware radio model.

The first study will focus on a small area around Xınalıq in Quba District, subject to a check of settlement counts and elevation data. Results will describe simulated links to settlement receiver points under stated assumptions.

- [Game plan and commit sequence](docs/game-plan.md)
- [Data source decisions](docs/data-sources.md)
- [First prompt and follow-up template](docs/prompts.md)
- [Project skills](.agents/skills)

## Set up the project in Windows PowerShell

From the project root, with Python 3.11 or newer:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[geodata]'
.\.venv\Scripts\coverage-optimizer.exe --help
.\.venv\Scripts\coverage-optimizer.exe check-config config/quba-pilot.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use your installed Python version in the first command if it differs. The config check and tests run offline after installation. The [pilot config](config/quba-pilot.json) and [data contract](docs/data-contract.md) define the inputs for the data preparation checkpoint.

## Prepare the Quba pilot data

Follow the [pilot input guide](docs/pilot-inputs.md) to fetch the pinned files, rerun preparation from your local cache, or inspect the results in VS Code.

## Model radio links

Once pilot data is prepared, run `.\.venv\Scripts\coverage-optimizer.exe model-links`. The [radio model guide](docs/radio-model.md) explains the assumptions, results and files used by the next checkpoint.

## Interactive pilot explainer

Open [the website](site/dist/index.html) to explore the four measured simulation cases. The page works from local files and needs no account or API keys for its controls. Select a mast height, candidate spacing and signal model, then choose a settlement to inspect its passing links.

To refresh the website data after regenerating the pilot inputs and scenarios, run these commands from the project root:

```powershell
.\.venv\Scripts\python.exe scripts/compare_mast_height_and_spacing.py
.\.venv\Scripts\python.exe site/generate_assets.py
```

The generator builds a terrain preview from the pinned elevation inputs and reads the run summaries and link tables to make the browser data. The browser presents precomputed results. It shows which settlements are reachable from the candidate pool, ahead of selecting a final set of towers.
