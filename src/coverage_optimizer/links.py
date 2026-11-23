"""Compare free-space and terrain-aware links on the same pilot inputs."""

from collections import Counter
import csv
import json
from math import hypot, isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from pyproj import Transformer
import rasterio

from .inputs import sha256
from .radio import RadioScenario, terrain_clearance_m

VARIANTS = ("fspl_only", "terrain_los")


def read_points(path: Path, id_key: str, *, eligible_only: bool = False) -> list[dict]:
    features = json.loads(path.read_text(encoding="utf-8"))["features"]
    points = [
        {**feature["properties"], "point": feature["geometry"]["coordinates"]}
        for feature in features
        if not eligible_only or feature["properties"]["eligible"] is True
    ]
    ids = {point[id_key] for point in points}
    if not points or len(ids) != len(points):
        raise ValueError(f"{path.name} requires a nonempty set of unique {id_key} values")
    for point in points:
        lon, lat = point["point"]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"{path.name} has invalid longitude/latitude coordinates")
    return points


def link_records(site: dict, settlement: dict, surface: np.ndarray, scenario: RadioScenario,
                 scenario_id: str) -> tuple[dict, dict]:
    distance_m = hypot(site["x"] - settlement["x"], site["y"] - settlement["y"])
    common = {
        "scenario_id": scenario_id,
        "site_id": site["site_id"],
        "settlement_id": settlement["settlement_id"],
        "settlement_name": settlement["name"],
        "distance_m": distance_m,
        "fspl_db": None,
        "received_power_dbm": None,
        "margin_db": None,
        "min_clearance_m": None,
    }
    if distance_m == 0:
        common.update(decision="unknown", reason="coincident_endpoints")
        return (
            dict(common, model_variant="fspl_only", los_state="unevaluated"),
            dict(common, model_variant="terrain_los", los_state="unknown"),
        )

    loss_db, power_dbm, margin_db = scenario.budget(distance_m)
    common.update(fspl_db=loss_db, received_power_dbm=power_dbm, margin_db=margin_db)
    budget_pass = margin_db >= 0
    free_space = dict(common, model_variant="fspl_only", los_state="unevaluated",
                      decision="usable" if budget_pass else "unusable",
                      reason="meets_constraints" if budget_pass else "insufficient_margin")

    clearance = terrain_clearance_m(surface, site["pixel"], settlement["pixel"], distance_m, scenario)
    if clearance is None:
        los_state = "unknown"
    else:
        los_state = "clear" if clearance > 0 else "blocked"

    # A known low margin rules out the link even if terrain data is incomplete.
    if not budget_pass:
        decision, reason = "unusable", "insufficient_margin"
    elif los_state == "unknown":
        decision, reason = "unknown", "incomplete_terrain"
    elif los_state == "blocked":
        decision, reason = "unusable", "terrain_obstruction"
    else:
        decision, reason = "usable", "meets_constraints"
    terrain = dict(common, model_variant="terrain_los", los_state=los_state,
                   min_clearance_m=clearance, decision=decision, reason=reason)
    return free_space, terrain


def write_outputs(output: Path, records: list[dict], matrix: dict, summary: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp)
        with (stage / "links.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        for name, data in (("matrix.json", matrix), ("summary.json", summary)):
            (stage / name).write_text(
                json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
            )
        output.mkdir(exist_ok=True)
        for name in ("links.csv", "matrix.json", "summary.json"):
            (stage / name).replace(output / name)


def model_links(config: dict, prepared: Path, output: Path) -> dict:
    scenario_config = config["scenario"]
    scenario = RadioScenario.from_config(scenario_config)
    preparation = config["preparation"]
    prepared_summary = json.loads((prepared / "summary.json").read_text(encoding="utf-8"))
    expected = {"study_area": config["study_area"], "preparation": preparation}
    if prepared_summary["prepared_config"] != expected:
        raise ValueError("prepared inputs use different study or grid settings. Rerun prepare-pilot.")

    sites = read_points(prepared / "candidate-sites.geojson", "site_id", eligible_only=True)
    settlements = read_points(prepared / "settlements.geojson", "settlement_id")
    with rasterio.open(prepared / "terrain.tif") as raster:
        if (raster.crs is None or raster.crs.to_string() != preparation["metric_crs"]
                or not raster.crs.is_projected or raster.crs.linear_units_factor[1] != 1):
            raise ValueError("prepared terrain must use the configured projected CRS in meters")
        surface = raster.read(1, masked=True).astype(np.float64).filled(np.nan)
        to_metric = Transformer.from_crs(4326, raster.crs, always_xy=True)
        inverse_transform = ~raster.transform
        for point in sites + settlements:
            point["x"], point["y"] = to_metric.transform(*point["point"])
            if not (isfinite(point["x"]) and isfinite(point["y"])):
                raise ValueError("point could not be projected to the terrain CRS")
            point["pixel"] = inverse_transform * (point["x"], point["y"])

    records = [
        record
        for site in sites
        for settlement in settlements
        for record in link_records(site, settlement, surface, scenario, scenario_config["id"])
    ]
    matrices = {
        variant: np.asarray([row["decision"] == "usable" for row in records
                             if row["model_variant"] == variant], dtype=int)
        .reshape(len(sites), len(settlements))
        for variant in VARIANTS
    }
    matrix = {
        "scenario_id": scenario_config["id"],
        "site_ids": [site["site_id"] for site in sites],
        "site_cost_units": [site["cost_units"] for site in sites],
        "settlement_ids": [settlement["settlement_id"] for settlement in settlements],
        "settlement_weights": [settlement["demand_weight"] for settlement in settlements],
        "variants": {variant: values.tolist() for variant, values in matrices.items()},
    }
    summary = {
        "study_area_id": config["study_area"]["id"],
        "scenario": scenario_config,
        "site_count": len(sites),
        "settlement_count": len(settlements),
        "pairs_per_variant": len(sites) * len(settlements),
        "prepared_sha256": {name: sha256(prepared / name) for name in (
            "summary.json", "candidate-sites.geojson", "settlements.geojson", "terrain.tif"
        )},
        "variants": {},
    }
    for variant, values in matrices.items():
        variant_records = [row for row in records if row["model_variant"] == variant]
        reasons = Counter(row["reason"] for row in variant_records)
        los_states = Counter(row["los_state"] for row in variant_records)
        reachable = values.any(axis=0)
        summary["variants"][variant] = {
            "usable_links": int(values.sum()),
            "reachable_settlements": int(reachable.sum()),
            "unreachable_settlements": [
                {"settlement_id": row["settlement_id"], "name": row["name"]}
                for row, covered in zip(settlements, reachable) if not covered
            ],
            "reasons": dict(sorted(reasons.items())),
            "los_states": dict(sorted(los_states.items())),
        }
    write_outputs(output, records, matrix, summary)
    return summary
