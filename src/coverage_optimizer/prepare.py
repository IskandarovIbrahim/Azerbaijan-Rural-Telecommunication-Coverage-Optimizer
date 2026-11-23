"""Prepare the Quba pilot terrain, settlement points and candidate grid."""

from collections import Counter
from importlib.metadata import version
import json
from math import ceil, cos, floor, hypot, pi, sin
from pathlib import Path
import platform
from tempfile import TemporaryDirectory

import numpy as np
from pyproj import Transformer
import rasterio
from rasterio.transform import from_origin, rowcol

from .geodata import PilotOSM, distance_to_roads, project_tiles
from .inputs import load_sources, sha256


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n",
                    encoding="utf-8")


def point_collection(rows: list[dict]) -> dict:
    features = []
    for row in rows:
        properties = {key: value for key, value in row.items() if key not in {"point", "metric_point"}}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": row["point"]},
            "properties": properties,
        })
    return {"type": "FeatureCollection", "features": features}


def candidate_grid(
    study: dict, settings: dict, center, inverse, transform, terrain, water, road_segments
) -> list[dict]:
    spacing = settings["candidate_spacing_m"]
    radius = study["radius_km"] * 1000
    cx, cy = center
    resolution = transform.a
    gradient_y, gradient_x = np.gradient(terrain, resolution)
    slope = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))
    rows = []
    for gy in range(ceil((cy - radius) / spacing), floor((cy + radius) / spacing) + 1):
        for gx in range(ceil((cx - radius) / spacing), floor((cx + radius) / spacing) + 1):
            x, y = gx * spacing, gy * spacing
            if hypot(x - cx, y - cy) > radius:
                continue
            i, j = rowcol(transform, x, y)
            elevation = float(terrain[i, j])
            angle = float(slope[i, j])
            water_class = water[i, j]
            reasons = []
            if not np.isfinite(elevation) or not np.isfinite(angle):
                reasons.append("missing_elevation_or_slope")
            if not np.isfinite(water_class):
                reasons.append("unknown_water_mask")
            elif water_class != 0:
                reasons.append("mapped_water")
            if angle > settings["max_slope_degrees"]:
                reasons.append("slope_exceeds_threshold")
            road_distance = distance_to_roads((x, y), road_segments)
            rows.append({
                "site_id": f"{study['id']}-grid{spacing}m-{gx}-{gy}",
                "point": inverse.transform(x, y),
                "surface_elevation_m": round(elevation, 2) if np.isfinite(elevation) else None,
                "slope_degrees": round(angle, 2) if np.isfinite(angle) else None,
                "road_distance_m": round(road_distance, 2) if road_distance is not None else None,
                "exclusion_reasons": reasons,
                "eligible": not reasons,
                "cost_units": 1,
            })
    return rows


def prepare_pilot(config: dict, manifest: Path, cache: Path, output: Path, offline: bool) -> dict:
    study = config["study_area"]
    settings = config["preparation"]
    raster_size = settings["raster_cell_m"]
    crs = settings["metric_crs"]
    radius = study["radius_km"] * 1000
    extent = radius + study["terrain_buffer_km"] * 1000
    to_metric = Transformer.from_crs(4326, crs, always_xy=True)
    inverse = Transformer.from_crs(crs, 4326, always_xy=True)
    cx, cy = center = to_metric.transform(*study["center_lon_lat"])
    sources = load_sources(manifest, cache, offline)

    osm = PilotOSM(to_metric, center, radius)
    osm.apply_file(str(sources["osm"][0]), locations=True)
    settlements = sorted(osm.settlements, key=lambda row: row["distance_from_center_m"])
    ids = {row["settlement_id"] for row in settlements}
    if len(ids) != len(settlements) or study["center_source_id"] not in ids:
        raise ValueError("settlement IDs are duplicated or the pinned center was not found")
    center_settlement = next(row for row in settlements if row["settlement_id"] == study["center_source_id"])
    if center_settlement["distance_from_center_m"] > 1:
        raise ValueError("configured center differs from the pinned settlement position")
    center_settlement["name"] = study["center_name"]
    roads = np.asarray(osm.segments)

    left = floor((cx - extent) / raster_size) * raster_size
    top = ceil((cy + extent) / raster_size) * raster_size
    width = ceil((cx + extent - left) / raster_size)
    height = ceil((top - cy + extent) / raster_size)
    transform = from_origin(left, top, raster_size, raster_size)
    terrain = project_tiles(sources["elevation"], (height, width), transform, crs)
    water = project_tiles(sources["water_mask"], (height, width), transform, crs, mask=True)
    x = left + (np.arange(width) + 0.5) * raster_size
    y = top - (np.arange(height) + 0.5) * raster_size
    in_buffer = np.hypot(x[None, :] - cx, y[:, None] - cy) <= extent
    missing = int(np.count_nonzero(in_buffer & ~np.isfinite(terrain)))
    if missing:
        raise ValueError(f"terrain is missing from {missing} pixels within the buffered study area")

    for settlement in settlements:
        i, j = rowcol(transform, *settlement["metric_point"])
        settlement["surface_elevation_m"] = round(float(terrain[i, j]), 2)
    sites = candidate_grid(study, settings, center, inverse, transform, terrain, water, roads)
    eligible = sum(site["eligible"] for site in sites)
    if not eligible:
        raise ValueError("no candidate grid points passed initial screening")
    exclusions = Counter(reason for site in sites for reason in site["exclusion_reasons"])
    ring = [inverse.transform(cx + radius * cos(2 * pi * i / 120),
                              cy + radius * sin(2 * pi * i / 120)) for i in range(120)]
    ring.append(ring[0])
    summary = {
        "study_area_id": study["id"],
        "software": {
            "python": platform.python_version(),
            **{name: version(name) for name in ("numpy", "osmium", "pyproj", "rasterio")},
        },
        "radius_km": study["radius_km"],
        "terrain_buffer_km": study["terrain_buffer_km"],
        "metric_crs": crs,
        "raster_cell_m": raster_size,
        "vertical_datum": settings["vertical_datum"],
        "settlements": len(settlements),
        "candidate_sites": eligible,
        "grid_points": len(sites),
        "exclusion_reasons": dict(exclusions),
        "road_segments": len(roads),
        "terrain_nodata_pixels_in_buffer": missing,
        "source_manifest_sha256": sha256(manifest),
        "prepared_config": {"study_area": study, "preparation": settings},
        "attribution": json.loads(manifest.read_text(encoding="utf-8"))["attribution"],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp)
        write_json(stage / "study-area.geojson", {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {"study_area_id": study["id"], "radius_km": study["radius_km"]},
        })
        write_json(stage / "settlements.geojson", point_collection(settlements))
        write_json(stage / "candidate-sites.geojson", point_collection(sites))
        with rasterio.open(
            stage / "terrain.tif", "w", driver="GTiff", width=width, height=height, count=1,
            dtype="float32", crs=crs, transform=transform, nodata=float("nan"), compress="deflate"
        ) as dst:
            dst.write(terrain, 1)
            dst.set_band_unit(1, "m")
            dst.update_tags(vertical_datum=settings["vertical_datum"])
        write_json(stage / "summary.json", summary)
        output.mkdir(exist_ok=True)
        for file in ("study-area.geojson", "settlements.geojson", "candidate-sites.geojson",
                     "terrain.tif", "summary.json"):
            (stage / file).replace(output / file)
    return summary
