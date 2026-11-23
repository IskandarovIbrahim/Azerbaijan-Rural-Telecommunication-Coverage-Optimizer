"""Estimate and compare upfront site costs for the four pilot scenarios."""

import json
from math import isfinite
from pathlib import Path

from coverage_optimizer.inputs import sha256
from coverage_optimizer.selection import compare_selection

# USD planning assumptions, with a separate access multiplier for each profile.
PROFILES = {
    "lower": {"label": "Lower assumptions", "core_usd": 40_000, "mast_usd": {20: 20_000, 40: 35_000},
              "access_usd_per_km": 6_000},
    "base": {"label": "Base assumptions", "core_usd": 50_000, "mast_usd": {20: 25_000, 40: 45_000},
             "access_usd_per_km": 12_000},
    "higher": {"label": "Higher assumptions", "core_usd": 65_000, "mast_usd": {20: 38_000, 40: 65_000},
               "access_usd_per_km": 24_000},
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def estimate_case(project, case):
    scenario = case["scenario_id"]
    height = case["mast_height_m"]
    spacing = case["grid_spacing_m"]
    matrix_path = project / "outputs/quba-height-spacing" / scenario / "matrix.json"
    matrix = read_json(matrix_path)
    baseline_path = project / "outputs/quba-selection" / scenario / "selection.json"
    baseline = read_json(baseline_path)
    variant = "terrain_los"
    matrix_hash = sha256(matrix_path)
    if (matrix["scenario_id"] != scenario or baseline["scenario_id"] != scenario
            or baseline["model_variant"] != variant or baseline["matrix_sha256"] != matrix_hash):
        raise ValueError(f"tower selection inputs do not match the link matrix for {scenario}")

    sites_path = project / "data/processed/quba-height-spacing" / f"grid-{spacing}m" / "candidate-sites.geojson"
    candidate_data = read_json(sites_path)["features"]
    distances = {item["properties"]["site_id"]: item["properties"]["road_distance_m"]
                 for item in candidate_data if item["properties"]["eligible"]}
    if set(distances) != set(matrix["site_ids"]):
        raise ValueError(f"site geometry does not match the link matrix for {scenario}")
    if any(type(distance) not in (int, float) or not isfinite(distance) or distance < 0
           for distance in distances.values()):
        raise ValueError(f"missing or invalid road distance for {scenario}")

    baseline_sites = [site["site_id"] for site in baseline["methods"]["exact"]["selected_sites"]]
    estimates = {}
    for key, profile in PROFILES.items():
        site_costs = {
            site_id: profile["core_usd"] + profile["mast_usd"][height]
            + round(profile["access_usd_per_km"] * distance_m / 1000)
            for site_id, distance_m in distances.items()
        }
        weighted = {**matrix, "site_cost_units": [site_costs[site_id] for site_id in matrix["site_ids"]]}
        selection = compare_selection(weighted, variant)
        if selection["target_settlement_count"] != baseline["target_settlement_count"]:
            raise ValueError(f"coverage targets differ for {scenario}")
        methods = {}
        for method, result in selection["methods"].items():
            methods[method] = {
                "total_usd": round(result["total_cost_units"]),
                "site_count": result["selected_site_count"],
                "site_ids": [site["site_id"] for site in result["selected_sites"]],
            }
        estimates[key] = {
            "minimum_count": {
                "total_usd": sum(site_costs[site_id] for site_id in baseline_sites),
                "site_count": len(baseline_sites),
                "site_ids": baseline_sites,
            },
            **methods,
        }
    return {
        "scenario_id": scenario,
        "mast_height_m": height,
        "grid_spacing_m": spacing,
        "settlement_count": baseline["total_settlement_count"],
        "reachable_count": baseline["target_settlement_count"],
        "matrix_sha256": matrix_hash,
        "site_geometry_sha256": sha256(sites_path),
        "estimates": estimates,
    }


def main():
    project = Path(__file__).resolve().parents[1]
    cases = read_json(project / "outputs/quba-height-spacing/comparison.json")["cases"]
    estimates = [estimate_case(project, case) for case in cases]
    result = {"currency": "USD", "profiles": PROFILES, "cases": estimates}
    output = project / "outputs/quba-costs/comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for case in estimates:
        base = case["estimates"]["base"]
        print(case["scenario_id"], {method: outcome["total_usd"] for method, outcome in base.items()})


if __name__ == "__main__":
    main()
