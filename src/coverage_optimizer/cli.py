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

    prepare = commands.add_parser("prepare-pilot", help="Prepare terrain, settlements and sites.")
    prepare.add_argument("--config", dest="path", type=Path, default=Path("config/quba-pilot.json"))
    prepare.add_argument("--manifest", type=Path, default=Path("config/quba-sources.json"))
    prepare.add_argument("--cache", type=Path, default=Path("data/raw"))
    prepare.add_argument("--output", type=Path, default=Path("data/processed/quba-pilot"))
    prepare.add_argument("--offline", action="store_true", help="Use only locally cached source files.")

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

    if args.command == "prepare-pilot":
        try:
            from .prepare import prepare_pilot
        except ModuleNotFoundError as exc:
            parser.error(f"{exc}. Install the project with the geodata extra: pip install -e .[geodata]")

        try:
            summary = prepare_pilot(config, args.manifest, args.cache, args.output, args.offline)
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
            parser.error(f"could not prepare pilot: {exc}")
        print(f"Prepared {summary['settlements']} settlements and "
              f"{summary['candidate_sites']} eligible candidate sites in {args.output}")
        return 0

    print(f"Config loaded: {name} ({radius_km:g} km radius)")
    print(f"Scenario: {scenario_id}")
    if study.get("center_lon_lat") is None:
        print("Study area center is unverified.")
    if scenario.get("status") == "unverified":
        print("Radio assumptions are unverified.")
    return 0
