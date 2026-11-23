"""Export the local pilot results and shaded elevation used by the static site."""

import csv
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


def summarize_links(links, settlements):
    by_settlement = {item["id"]: [] for item in settlements}
    for row in links:
        if row["decision"] == "usable":
            by_settlement[row["settlement_id"]].append(row)

    details = {}
    for identifier, passing in by_settlement.items():
        best = max(passing, key=lambda row: float(row["margin_db"]), default=None)
        details[identifier] = {"count": len(passing), "bestSite": best["site_id"] if best else None}
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
        center_x = (raster.bounds.left + raster.bounds.right) / 2
        rows = raster.height
        cols = round(rows * 1.52)
        resolution = raster.res[0]
        grid = from_origin(center_x - cols * resolution / 2, raster.bounds.top, resolution, resolution)
        terrain = project_tiles(raster_paths, (rows, cols), grid, raster.crs)
        project_point = Transformer.from_crs(4326, raster.crs, always_xy=True)
    inverse = ~grid

    def screen_point(coordinates):
        col, row = inverse * project_point.transform(*coordinates)
        return [round(col / cols, 6), round(row / rows, 6)]

    study = read_json(coarse / "summary.json")["prepared_config"]["study_area"]
    center_id = study["center_source_id"]
    settlements = [
        dict(zip(("x", "y"), screen_point(item["geometry"]["coordinates"])),
             id=item["properties"]["settlement_id"],
             name=("Pilot center settlement" if area == "quba" and item["properties"]["settlement_id"] == center_id
                   else item["properties"]["name"]))
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
        "settlements": settlements, "boundary": boundary, "sites": sites, "cases": cases,
        "costs": read_json(project / f"outputs/{area}-costs/comparison.json"),
        "terrainCredit": "Produced using Copernicus WorldDEM™-90. " + manifest["attribution"]["terrain"],
    }
    write_png(site / "dist" / terrain_image, shaded_elevation(terrain))
    return data


def main():
    site = Path(__file__).resolve().parent
    areas = {
        "quba": export_area(site, "quba", "Quba pilot", "terrain.png"),
        "lahic": export_area(site, "lahic", "Lahıc, İsmayıllı", "terrain-lahic.png"),
    }
    (site / "dist/pilot-data.js").write_text(
        "window.PILOT_DATA = " + json.dumps({"areas": areas}, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
