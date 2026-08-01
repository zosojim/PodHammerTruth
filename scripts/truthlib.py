from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = {
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "RunPod API key": re.compile(r"\brpa_[A-Za-z0-9]{20,}\b"),
    "private key": re.compile(r"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----"),
    "bearer credential": re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE),
    "IPv4 address": re.compile(r"(?<![A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9])"),
    "SSH command": re.compile(r"\bssh\s+[^\n]*@", re.IGNORECASE),
}


def json_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob("*.json") if path.is_file())


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def scan_observation(value: Any) -> list[str]:
    text = canonical_json(value)
    return [label for label, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def percentile(values: Iterable[int], percent: int) -> int | None:
    ordered = sorted(values)
    if not ordered:
        return None
    rank = max(1, math.ceil((percent / 100) * len(ordered)))
    return ordered[rank - 1]


def metric_summary(values: Iterable[int]) -> dict[str, int | float] | None:
    ordered = sorted(values)
    if not ordered:
        return None
    return {
        "samples": len(ordered),
        "mean_ms": round(sum(ordered) / len(ordered), 1),
        "median_ms": percentile(ordered, 50),
        "p75_ms": percentile(ordered, 75),
        "p90_ms": percentile(ordered, 90),
        "minimum_ms": ordered[0],
        "maximum_ms": ordered[-1],
    }


def observation_group_key(value: dict[str, Any]) -> tuple[str, ...]:
    hardware = value["hardware"]
    storage = value["storage"]
    return (
        value["provider"],
        value["data_center"],
        hardware["gpu_sku"],
        str(hardware["gpu_count"]),
        value.get("recipe_id", "unclassified"),
        value["cache_state"],
        storage["kind"],
    )


def aggregate_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for observation in observations:
        grouped.setdefault(observation_group_key(observation), []).append(observation)

    groups: list[dict[str, Any]] = []
    metric_names = (
        "request_to_provider_running",
        "request_to_ssh_ready",
        "ssh_ready_to_stack_ready",
        "request_to_stack_ready",
        "first_completion",
    )
    for key in sorted(grouped):
        rows = grouped[key]
        metrics: dict[str, Any] = {}
        for metric in metric_names:
            summary = metric_summary(
                row["timings_ms"][metric]
                for row in rows
                if metric in row["timings_ms"]
            )
            if summary is not None:
                metrics[metric] = summary

        outcomes = Counter(row["outcome"]["status"] for row in rows)
        ready = outcomes.get("ready", 0)
        segment_winners: Counter[str] = Counter()
        segment_values: dict[str, list[int]] = {}
        for row in rows:
            segments = row["timings_ms"].get("segments", {})
            if not segments:
                continue
            winner = max(sorted(segments), key=lambda name: segments[name])
            segment_winners[winner] += 1
            for name, duration in segments.items():
                segment_values.setdefault(name, []).append(duration)

        groups.append({
            "provider": key[0],
            "data_center": key[1],
            "gpu_sku": key[2],
            "gpu_count": int(key[3]),
            "recipe_id": key[4],
            "cache_state": key[5],
            "storage_kind": key[6],
            "samples": len(rows),
            "ready_samples": ready,
            "success_rate": round(ready / len(rows), 4),
            "outcomes": dict(sorted(outcomes.items())),
            "metrics": metrics,
            "long_poles": {
                "winner_counts": dict(sorted(segment_winners.items())),
                "segment_metrics": {
                    name: metric_summary(values)
                    for name, values in sorted(segment_values.items())
                },
            },
            "first_observed_day": min(row["observed_day"] for row in rows),
            "last_observed_day": max(row["observed_day"] for row in rows),
        })

    latest_day = max((row["observed_day"] for row in observations), default=None)
    return {
        "schema_version": 1,
        "through_observed_day": latest_day,
        "observation_count": len(observations),
        "group_count": len(groups),
        "dataset_sha256": content_digest(observations),
        "groups": groups,
    }
