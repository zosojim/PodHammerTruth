#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from truthlib import ROOT, load_json, scan_observation


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and split a Pod Hammer truth export bundle."
    )
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    bundle = load_json(arguments.bundle)
    schema_path = ROOT / "schemas" / "export-bundle.schema.json"
    schema = load_json(schema_path)
    observation_schema = load_json(
        ROOT / "schemas" / "observation.schema.json"
    )
    registry = Registry().with_resource(
        observation_schema["$id"],
        Resource.from_contents(observation_schema),
    )
    validator = Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(bundle), key=lambda item: list(item.path))
    if errors:
        for error in errors:
            print(f"Bundle validation failed: {error.message}")
        return 1
    for observation in bundle["observations"]:
        findings = scan_observation(observation)
        if findings:
            print(f"Refusing {observation['run_id']}: possible {', '.join(findings)}")
            return 1
        year, month, _ = observation["observed_day"].split("-")
        destination = ROOT / "observations" / year / month / f"{observation['run_id']}.json"
        if destination.exists():
            print(f"Already present: {destination.relative_to(ROOT)}")
            continue
        print(f"Import: {destination.relative_to(ROOT)}")
        if not arguments.dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(observation, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
