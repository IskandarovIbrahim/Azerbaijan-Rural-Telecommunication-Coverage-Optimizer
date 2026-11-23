# Quba pilot inputs

The study area is a 17.5 km circle centered on the mapped point for Xınalıq. The original 15 km circle included eight named villages and hamlets. The larger circle includes 14 and can cross district boundaries. The terrain covers an extra 2 km around it. The pilot uses Copernicus GLO-90 because two nearby public GLO-30 tile URLs returned 404. At 90 m, narrow ridges and other small features can be missed. [Copernicus DEM catalogue](https://registry.opendata.aws/copernicus-dem/)

## Run the preparation

From the project folder in the VS Code PowerShell terminal:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[geodata]'
.\.venv\Scripts\coverage-optimizer.exe prepare-pilot
```

The command uses curl to fetch missing inputs and checks each file against the SHA-256 in the [source manifest](../config/quba-sources.json). Add `--offline` to use only cached inputs. Keep the dated extract in the cache for exact reproduction if Geofabrik rotates that URL out. A newer snapshot needs its own manifest and run. [Geofabrik Azerbaijan extracts](https://download.geofabrik.de/asia/azerbaijan.html)

## Inspect the results

Open `data/processed/quba-pilot/summary.json` in VS Code, or print it:

```powershell
Get-Content -Raw -Encoding utf8 .\data\processed\quba-pilot\summary.json
```

The verified run produced 14 settlements and 19 eligible sites from 28 grid points. All 9 exclusions were above the 30° slope threshold. No elevation pixels were missing inside the buffered circle. The summary records the config, software versions, manifest checksum and counts.

The same folder holds `study-area.geojson`, `settlements.geojson`, `candidate-sites.geojson`, and `terrain.tif`. GeoJSON uses longitude, latitude order. The GeoTIFF uses EPSG:32639, 90 m cells and EGM2008 elevations. Inputs and generated data are local and ignored by Git.

## How points were chosen

Demand uses named OpenStreetMap village and hamlet nodes, with one unit-weight receiver per node. Using nodes avoids counting an overlapping place polygon as a second receiver. The 14 included points have distinct names.

Candidate points come from a fixed 6 km metric grid. Points with missing terrain or water-mask values, mapped water, or slopes over 30° are excluded. Road distance is a straight-line distance to nearby mapped road segments, excluding segments tagged private or closed to motor vehicles. Site costs are all one unit in this baseline. The candidates are modeled options. Assessing installation feasibility would require site-specific evidence. [Copernicus DEM product handbook](https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf)
