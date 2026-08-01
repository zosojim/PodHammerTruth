#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from truthlib import ROOT, aggregate_observations, json_files, load_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "aggregates" / "summary.json",
    )
    arguments = parser.parse_args()
    observations = [load_json(path) for path in json_files(ROOT / "observations")]
    result = aggregate_observations(observations)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Aggregated {len(observations)} observation(s) into {arguments.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
