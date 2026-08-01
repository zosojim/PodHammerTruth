#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from truthlib import ROOT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / "site", output)
    data = output / "data"
    data.mkdir(parents=True, exist_ok=True)
    aggregate_path = data / "summary.json"

    # Avoid coupling this helper to aggregate.py's CLI parser.
    from truthlib import aggregate_observations, json_files, load_json

    observations = [load_json(path) for path in json_files(ROOT / "observations")]
    aggregate_path.write_text(
        json.dumps(aggregate_observations(observations), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    recipe_values = [load_json(path) for path in json_files(ROOT / "recipes")]
    (data / "recipes.json").write_text(
        json.dumps(recipe_values, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Built site at {output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
