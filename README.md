# Azerbaijan Rural Telecommunication Coverage Optimizer

Where should hypothetical wireless access sites go to reach a group of mountain villages at the lowest modeled cost? This project will compare greedy and exact optimization using the same terrain-aware radio model.

The first study will focus on a small area around Xınalıq in Quba District, subject to a check of settlement counts and elevation data. Results will describe simulated links to settlement receiver points under stated assumptions.

- [Game plan and commit sequence](docs/game-plan.md)
- [Data source decisions](docs/data-sources.md)
- [First prompt and follow-up template](docs/prompts.md)
- [Project skills](.agents/skills)

## Run the scaffold in Windows PowerShell

From the project root, with Python 3.11 or newer:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\coverage-optimizer.exe --help
.\.venv\Scripts\coverage-optimizer.exe check-config config/quba-pilot.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Use your installed Python version in the first command if it differs. The config check and tests run offline after installation. The [pilot config](config/quba-pilot.json) and [data contract](docs/data-contract.md) define the inputs for the data preparation checkpoint.

## Prepare the Quba pilot data

Follow the [pilot input guide](docs/pilot-inputs.md) to fetch the pinned files, rerun preparation from your local cache, or inspect the results in VS Code.
