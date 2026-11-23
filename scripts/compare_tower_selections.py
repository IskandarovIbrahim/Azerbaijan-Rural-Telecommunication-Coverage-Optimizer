"""Compare terrain-aware tower selection across the four Quba scenarios."""

import json
from pathlib import Path

from coverage_optimizer.selection import select_sites


def main():
    project = Path(__file__).resolve().parents[1]
    runs = project / "outputs/quba-height-spacing"
    output = project / "outputs/quba-selection"
    experiments = json.loads((runs / "comparison.json").read_text(encoding="utf-8"))
    results = []
    for case in experiments["cases"]:
        scenario = case["scenario_id"]
        selection = select_sites(
            runs / scenario / "matrix.json", "terrain_los", output / scenario / "selection.json"
        )
        methods = selection["methods"]
        results.append({
            "scenario_id": scenario,
            "mast_height_m": case["mast_height_m"],
            "grid_spacing_m": case["grid_spacing_m"],
            "candidate_site_count": selection["candidate_site_count"],
            "settlements_reached": selection["target_settlement_count"],
            "settlements_total": selection["total_settlement_count"],
            "full_cover_status": selection["full_cover_status"],
            "greedy_site_count": methods["greedy"]["selected_site_count"],
            "minimum_site_count": methods["exact"]["selected_site_count"],
            "greedy_relative_cost_gap": selection["greedy_relative_cost_gap"],
        })
    (output / "comparison.json").write_text(
        json.dumps({"model_variant": "terrain_los", "cases": results}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
