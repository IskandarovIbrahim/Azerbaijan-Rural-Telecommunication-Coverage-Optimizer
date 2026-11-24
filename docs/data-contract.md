# Pilot data contract

## Pilot configuration

[config/quba-pilot.json](../config/quba-pilot.json) is UTF-8 JSON. Version 1 defines a circular study area with a configurable radius and a single fixed-wireless downlink scenario. A `null` field is unresolved. The [pilot input guide](pilot-inputs.md) records the selected study extent and terrain buffer. Propagation must require a complete set of documented radio assumptions before it produces links. The scaffold's `check-config` command checks the basic file structure and permits these unresolved values.

Set `center_lon_lat` to `[longitude, latitude]` in WGS84 decimal degrees using a verified settlement point. Store the study radius and terrain buffer in kilometers, frequency in MHz, transmit power and receiver threshold in dBm, antenna gain in dBi, losses and fade margin in dB, and antenna height above the sampled surface in meters.

## Prepared inputs

| Input | Required fields and conventions |
| --- | --- |
| Study area | Stable study area ID, AOI geometry and documented terrain buffer. Export WGS84 GeoJSON in longitude, latitude order. Record the prepared metric CRS. |
| Settlements | Unique `settlement_id`, source feature identifier, local name, one receiver point and demand weight. Preserve the OSM element type and ID as a source key, such as `osm:node:<id>`, and record any deduplication. Keep weights finite and nonnegative. The base case gives each settlement a weight of 1. |
| Candidate sites | Unique `site_id`, point, surface elevation in meters and a positive cost in modeled cost units. Derive IDs from the pinned grid definition and cell index so filtering or sorting does not change them. Record slope in degrees, mapped road distance in meters and exclusion reasons when applicable. |
| Terrain | Elevation raster with CRS, grid resolution, vertical datum and NoData policy retained in metadata. Use a suitable local metric CRS for analysis and keep NoData distinct from zero. |

Record for every acquired input the source ID, publisher, dataset name, exact URL or tile ID, release or snapshot, UTC retrieval date, SHA-256, license and credit, input CRS and resolution where applicable, vertical datum for elevations, and preparation steps. Keep local paths and authentication details out of committed source metadata. Label synthetic inputs explicitly.

A manifest can include one verified WGS84 GeoJSON input with role "boundary". When supplied, preparation keeps only settlement points within or on the boundary, marks outside candidate points ineligible, and reports the number of excluded settlements. The study circle and terrain buffer retain their original extents.

## Modeled links

Each run records one row per eligible candidate–settlement pair per model variant with `scenario_id`, model variant, `site_id`, `settlement_id`, distance in meters, FSPL in dB, received power in dBm, margin in dB, LOS state, minimum clearance in meters, decision and reason. CSV represents unavailable numeric values as empty fields. Keep FSPL-only LOS flagged as unevaluated. Margin is measured after reserving the configured fade margin. The binary matrix uses site rows and settlement columns with matching ID arrays for both variants.

- **Usable** means the link meets the applicable visibility and link-budget constraints. It contributes 1 to the binary coverage matrix.
- **Unusable** means a known constraint rules it out, such as a blocked path or insufficient received power. It contributes 0.
- **Unknown** means an applicable test was inconclusive, such as an otherwise eligible path with missing terrain. It contributes 0 to optimization and is counted separately in diagnostics.

Keep all included settlement IDs in coverage denominators, including settlements with no usable links. Label reachable-only summaries explicitly. Report simulation assumptions with each output.
