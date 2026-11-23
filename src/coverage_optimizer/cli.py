"""Command-line entry point for the coverage optimizer."""

import argparse
import json
import sys
from io import TextIOWrapper
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run terrain-aware wireless planning simulations."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check-config", help="Load and check a pilot config.")
    check.add_argument("path", type=Path, help="Path to a UTF-8 JSON config.")

    args = parser.parse_args(argv)
    try:
        config = json.loads(args.path.read_text(encoding="utf-8"))
        version = config.get("schema_version") if isinstance(config, dict) else None
        if type(version) is not int or version != 1:
            raise ValueError("expected a JSON object with schema_version 1")

        study = config.get("study_area")
        scenario = config.get("scenario")
        if not isinstance(study, dict) or not isinstance(scenario, dict):
            raise ValueError("study_area and scenario must be JSON objects")

        name = study.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("study_area.name must be nonempty text")

        radius_km = study.get("radius_km")
        if type(radius_km) not in (int, float) or not 0 < radius_km < float("inf"):
            raise ValueError("study_area.radius_km must be finite and positive")

        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            raise ValueError("scenario.id must be nonempty text")
    except (OSError, ValueError) as exc:
        parser.error(f"{args.path}: {exc}")

    # Redirected Windows streams can otherwise lose Azerbaijani characters.
    if isinstance(sys.stdout, TextIOWrapper) and not sys.stdout.isatty():
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"Config loaded: {name} ({radius_km:g} km radius)")
    print(f"Scenario: {scenario_id}")
    if study.get("center_lon_lat") is None:
        print("Study area center is unverified.")
    if scenario.get("status") == "unverified":
        print("Radio assumptions are unverified.")
    return 0
