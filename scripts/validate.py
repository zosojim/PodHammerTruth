#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from truthlib import ROOT, json_files, load_json, scan_observation


def validate_collection(
    directory: Path,
    schema_path: Path,
    *,
    scan_secrets: bool = False,
) -> list[str]:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    identifier_key = "run_id" if directory.name == "observations" else "id"

    for path in json_files(directory):
        try:
            value = load_json(path)
        except Exception as error:  # noqa: BLE001 - validation reports parse errors
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {error}")
            continue
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "$"
            errors.append(f"{path.relative_to(ROOT)}:{location}: {error.message}")
        identifier = value.get(identifier_key) if isinstance(value, dict) else None
        if identifier:
            if identifier in seen_ids:
                errors.append(
                    f"{path.relative_to(ROOT)}: duplicate {identifier_key} also in "
                    f"{seen_ids[identifier].relative_to(ROOT)}"
                )
            seen_ids[identifier] = path
        if scan_secrets:
            for label in scan_observation(value):
                errors.append(f"{path.relative_to(ROOT)}: possible {label} is not publishable")
    return errors


def main() -> int:
    errors = []
    errors.extend(validate_collection(
        ROOT / "recipes",
        ROOT / "schemas" / "recipe.schema.json",
    ))
    errors.extend(validate_collection(
        ROOT / "observations",
        ROOT / "schemas" / "observation.schema.json",
        scan_secrets=True,
    ))
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Validated {len(json_files(ROOT / 'recipes'))} recipe(s) and "
        f"{len(json_files(ROOT / 'observations'))} observation(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
