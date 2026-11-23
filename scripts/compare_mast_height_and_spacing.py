"""Run the four Quba mast-height and grid-spacing combinations offline."""

import json
from pathlib import Path

from coverage_optimizer.inputs import sha256
from coverage_optimizer.links import model_links
from coverage_optimizer.prepare import prepare_pilot, write_json


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    base_path = project / "config" / "quba-pilot.json"
    manifest = project / "config" / "quba-sources.json"
    cache = project / "data" / "raw"
    prepared_root = project / "data" / "processed" / "quba-height-spacing"
    output = project / "outputs" / "quba-height-spacing"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    results = []

    for spacing_m in (6000, 3000):
        preparation = {**base["preparation"], "candidate_spacing_m": spacing_m}
        prepared = prepared_root / f"grid-{spacing_m}m"
        grid_config = {**base, "preparation": preparation}
        prepare_pilot(grid_config, manifest, cache, prepared, offline=True)

        for height_m in (20, 40):
            case_id = f"mast-{height_m}m-grid-{spacing_m}m"
            scenario = {**base["scenario"], "id": case_id, "transmit_antenna_height_m": height_m}
            config = {**grid_config, "scenario": scenario}
            case_output = output / case_id
            result = model_links(config, prepared, case_output)
            write_json(case_output / "config.json", config)
            baseline = result["variants"]["fspl_only"]
            terrain = result["variants"]["terrain_los"]
            results.append({
                "scenario_id": case_id,
                "mast_height_m": height_m,
                "grid_spacing_m": spacing_m,
                "eligible_candidate_sites": result["site_count"],
                "settlements": result["settlement_count"],
                "pairs": result["pairs_per_variant"],
                "free_space_usable_links": baseline["usable_links"],
                "terrain_usable_links": terrain["usable_links"],
                "terrain_reachable_settlements": terrain["reachable_settlements"],
                "terrain_unreachable_settlements": terrain["unreachable_settlements"],
            })
            print(f"{case_id}: {result['site_count']} candidates, "
                  f"{terrain['reachable_settlements']}/{result['settlement_count']} settlements, "
                  f"{terrain['usable_links']}/{result['pairs_per_variant']} terrain links")

    write_json(output / "comparison.json", {
        "study_area_id": base["study_area"]["id"],
        "base_config_sha256": sha256(base_path),
        "source_manifest_sha256": sha256(manifest),
        "cases": results,
    })


if __name__ == "__main__":
    main()
