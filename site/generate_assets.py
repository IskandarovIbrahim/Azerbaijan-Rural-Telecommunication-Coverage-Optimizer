"""Export the local pilot results and shaded elevation used by the static site."""

import base64
import csv
import gzip
import json
from pathlib import Path
import struct
import zlib

import numpy as np
from pyproj import Transformer
import rasterio
from rasterio.transform import from_origin

from coverage_optimizer.geodata import project_tiles
from coverage_optimizer.inputs import sha256


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_png(path, pixels):
    def chunk(kind, payload):
        content = kind + payload
        return struct.pack(">I", len(payload)) + content + struct.pack(">I", zlib.crc32(content))

    height, width, _ = pixels.shape
    header = struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0)
    scanlines = b"".join(b"\0" + row.tobytes() for row in pixels)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b""))


def shaded_elevation(terrain):
    valid = np.isfinite(terrain)
    height = np.where(valid, terrain, np.nanmedian(terrain))
    dy, dx = np.gradient(height, 90)
    light = (0.8 + 0.42 * dx + 0.42 * dy) / np.sqrt(1 + dx**2 + dy**2)
    anchors = [700, 1350, 2100, 2950, 4350]
    palette = np.array([[96, 144, 123], [126, 166, 141], [167, 183, 158],
                        [190, 187, 158], [226, 225, 214]])
    color = np.stack([np.interp(height, anchors, palette[:, channel]) for channel in range(3)], axis=2)
    color *= np.clip(light / 0.8, 0.48, 1.24)[..., None]
    levels = np.floor(height / 250)
    contours = np.zeros_like(valid)
    contours[1:, :] |= levels[1:, :] != levels[:-1, :]
    contours[:, 1:] |= levels[:, 1:] != levels[:, :-1]
    color[contours] *= 0.88
    color[~valid] = [169, 188, 177]
    return np.clip(color, 0, 255).astype("uint8")


ELEVATION_STOPS = [
    (0, [30, 69, 109]),
    (1000, [40, 126, 121]),
    (2000, [144, 175, 112]),
    (3000, [219, 200, 122]),
    (4000, [238, 220, 177]),
    (4500, [255, 247, 219]),
]
# Landmark locations are from the pinned OpenStreetMap snapshot.
MAP_LABELS = {
    "quba": [
        ("Bazardüzü", 47.8581573, 41.2207625),
        ("Şahdağ", 48.0097153, 41.2706726),
        ("Tufandağ", 47.9918518, 41.1624215),
        ("Qrız waterfall", 48.2189776, 41.2246736),
    ],
    "lahic": [
        ("İsmayıllı", 48.1482869, 40.7879263),
        ("Qaranohur Lake", 48.2509563, 40.8127779),
        ("Şahnəzər", 48.4397300, 40.9662430),
        ("Beyqurd Castle", 48.5538391, 40.7508693),
    ],
    "slavyanka": [
        ("Gədəbəy", 45.8103471, 40.5747098),
        ("Siemens Bridge", 45.7283135, 40.5295896),
        ("Namərdqala", 45.9011463, 40.5477528),
        ("Qalaboynu Castle", 45.8195824, 40.7281997),
    ],
    "piran": [
        ("Lerik", 48.4181550, 38.7752945),
        ("İstisu", 48.7421992, 38.7654957),
        ("Lənkəran", 48.8539286, 38.7537311),
        ("Liman", 48.8071452, 38.8783968),
    ],
}


def export_elevation(site, area, terrain):
    valid = np.isfinite(terrain)
    samples = np.where(valid, np.rint(terrain), -32768).astype("<i2")
    heights = [height for height, _ in ELEVATION_STOPS]
    palette = np.array([color for _, color in ELEVATION_STOPS])
    colors = np.stack([np.interp(samples, heights, palette[:, channel])
                       for channel in range(3)], axis=2).astype("uint8")
    colors[~valid] = [169, 188, 177]
    image = f"elevation-{area}.png"
    write_png(site / "dist" / image, colors)
    height, width = samples.shape
    return {
        "image": image,
        "width": width,
        "height": height,
        "samples": base64.b64encode(gzip.compress(samples.tobytes(), mtime=0)).decode("ascii"),
        "legend": ELEVATION_STOPS,
    }


def summarize_links(links, settlements):
    by_settlement = {item["id"]: [] for item in settlements}
    obstructions = {}
    for row in links:
        if row["decision"] == "usable":
            by_settlement[row["settlement_id"]].append(row)
        elif row["reason"] == "terrain_obstruction":
            identifier = row["settlement_id"]
            clearance = float(row["min_clearance_m"])
            previous = obstructions.get(identifier)
            if previous is None or clearance > previous["clearance"]:
                obstructions[identifier] = {"site": row["site_id"], "clearance": clearance}

    details = {}
    for identifier, passing in by_settlement.items():
        best = max(passing, key=lambda row: float(row["margin_db"]), default=None)
        details[identifier] = {"count": len(passing), "bestSite": best["site_id"] if best else None}
        if not best and identifier in obstructions:
            details[identifier]["obstruction"] = obstructions[identifier]
    return {
        "settlements": details,
        "reachable": sum(item["count"] > 0 for item in details.values()),
        "links": sum(item["count"] for item in details.values()),
    }


def export_area(site, area, label, terrain_image):
    project = site.parent
    prepared = project / f"data/processed/{area}-height-spacing"
    runs = project / f"outputs/{area}-height-spacing"
    selections_root = project / f"outputs/{area}-selection"
    coarse = prepared / "grid-6000m"
    manifest = read_json(project / f"config/{area}-sources.json")
    raster_paths = [project / "data/raw" / entry["filename"]
                    for entry in manifest["inputs"] if entry["role"] == "elevation"]
    with rasterio.open(coarse / "terrain.tif") as raster:
        rows = raster.height
        cols = round(rows * 1.52)
        resolution = raster.res[0]
        left = raster.bounds.left - ((cols - raster.width) // 2) * resolution
        grid = from_origin(left, raster.bounds.top, resolution, resolution)
        terrain = project_tiles(raster_paths, (rows, cols), grid, raster.crs)
        project_point = Transformer.from_crs(4326, raster.crs, always_xy=True)
    inverse = ~grid

    def screen_point(coordinates):
        col, row = inverse * project_point.transform(*coordinates)
        return [round(col / cols, 6), round(row / rows, 6)]

    settlements = [
        dict(zip(("x", "y"), screen_point(item["geometry"]["coordinates"])),
             id=item["properties"]["settlement_id"],
             name=item["properties"]["name"])
        for item in read_json(coarse / "settlements.geojson")["features"]
    ]
    boundary = [screen_point(point) for point in
                read_json(coarse / "study-area.geojson")["geometry"]["coordinates"][0]]
    sites = {
        str(spacing): {
            item["properties"]["site_id"]: screen_point(item["geometry"]["coordinates"])
            for item in read_json(prepared / f"grid-{spacing * 1000}m" / "candidate-sites.geojson")["features"]
            if item["properties"]["eligible"]
        }
        for spacing in (3, 6)
    }

    cases = {}
    for case in read_json(runs / "comparison.json")["cases"]:
        run = runs / case["scenario_id"]
        report = read_json(run / "summary.json")
        height = case["mast_height_m"]
        spacing = str(case["grid_spacing_m"] // 1000)
        variants = {}
        with (run / "links.csv").open(encoding="utf-8", newline="") as stream:
            links = list(csv.DictReader(stream))
        for variant, metrics in report["variants"].items():
            variants[variant] = summarize_links(
                (row for row in links if row["model_variant"] == variant), settlements
            )
            if (variants[variant]["reachable"] != metrics["reachable_settlements"]
                    or variants[variant]["links"] != metrics["usable_links"]):
                raise ValueError(f"link summary mismatch for {case['scenario_id']} / {variant}")

        selection_path = selections_root / case["scenario_id"] / "selection.json"
        selection = read_json(selection_path)
        if (selection["matrix_sha256"] != sha256(run / "matrix.json")
                or selection["scenario_id"] != case["scenario_id"]
                or selection["model_variant"] != "terrain_los"):
            raise ValueError(f"selection was generated from different link inputs: {selection_path}")
        selections = {}
        for method, result in selection["methods"].items():
            site_ids = [site["site_id"] for site in result["selected_sites"]]
            site_set = set(site_ids)
            if not site_set <= sites[spacing].keys() or len(site_set) != result["selected_site_count"]:
                raise ValueError(f"invalid selected site IDs in {selection_path}")
            view = summarize_links(
                (row for row in links if row["model_variant"] == "terrain_los"
                 and row["site_id"] in site_set), settlements
            )
            if view["reachable"] != result["covered_settlement_count"]:
                raise ValueError(f"selected network coverage mismatch in {selection_path}")
            selections[method] = {**view, "siteIds": site_ids}
        cases[f"{height}-{spacing}"] = {
            "height": height, "spacing": spacing, "candidates": case["eligible_candidate_sites"],
            "variants": variants, "selections": selections,
        }

    data = {
        "label": label, "terrainImage": terrain_image,
        "elevation": export_elevation(site, area, terrain),
        "mapLabels": [
            dict(zip(("x", "y"), screen_point((lon, lat))), name=name)
            for name, lon, lat in MAP_LABELS[area]
        ],
        "settlements": settlements, "boundary": boundary, "sites": sites, "cases": cases,
        "costs": read_json(project / f"outputs/{area}-costs/comparison.json"),
        "terrainCredit": "Produced using Copernicus WorldDEM™-90. " + manifest["attribution"]["terrain"],
    }
    write_png(site / "dist" / terrain_image, shaded_elevation(terrain))
    return data


def main():
    site = Path(__file__).resolve().parent
    areas = {
        "quba": export_area(site, "quba", "Quba", "terrain.png"),
        "lahic": export_area(site, "lahic", "Lahıc, İsmayıllı", "terrain-lahic.png"),
        "slavyanka": export_area(site, "slavyanka", "Slavyanka, Gədəbəy", "terrain-slavyanka.png"),
        "piran": export_area(site, "piran", "Piran, Lerik", "terrain-piran.png"),
    }
    (site / "dist/pilot-data.js").write_text(
        "window.PILOT_DATA = " + json.dumps({"areas": areas}, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
