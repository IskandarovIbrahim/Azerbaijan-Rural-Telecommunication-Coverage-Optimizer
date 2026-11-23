---
name: prepare-azerbaijan-geodata
description: Prepare elevation, settlements, roads and population inputs for the Azerbaijan rural wireless pilot. Use for study-area selection, dataset acquisition, spatial transforms, candidate screening and provenance checks.
---

1. Read [data source decisions](../../../docs/data-sources.md) before acquisition. Check exact products and terms, then pin object IDs or dated downloads and checksums. Store credentials and raw downloads locally outside tracked inputs.
2. Verify the Xınalıq pilot against settlement count, terrain coverage and manageable extent. Buffer elevation for complete link profiles. Keep stable settlement IDs and Azerbaijani names, reconcile duplicate point and polygon features, and report exclusions. Check coordinate order on WGS84 export and perform distances and slope calculations with appropriate metric units.
3. Generate candidate sites deterministically. Keep screening decisions, slope, road distance and surface elevation as explicit fields. Preserve elevation NoData and vertical datum throughout the workflow.
4. When population is used, allocate each populated grid cell at most once and record the reference year, unassigned count and allocation rule. Keep population estimates separate from settlement counts.
5. Produce a source manifest and sanity checks for CRS, geometry validity, bounds, duplicate IDs, raster gaps, full-profile availability and unit conversions.
