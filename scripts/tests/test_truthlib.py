import unittest

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from truthlib import aggregate_observations, percentile, scan_observation


def observation(run_id: str, duration: int, status: str = "ready") -> dict:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "observed_day": "2026-08-01",
        "provenance": "client-measured",
        "provider": "runpod",
        "data_center": "EU-TEST-1",
        "recipe_id": "podhammer.test",
        "hardware": {
            "gpu_sku": "Test GPU",
            "gpu_count": 1,
            "gpu_memory_gb": 96,
        },
        "storage": {"kind": "ephemeral", "size_gb": 300},
        "cache_state": "cold",
        "timings_ms": {
            "request_to_ssh_ready": duration,
            "segments": {"provider_boot": duration - 1, "ssh_wait": 1},
        },
        "outcome": {"status": status},
    }


class TruthLibraryTests(unittest.TestCase):
    def test_percentile_uses_nearest_rank(self):
        self.assertEqual(percentile([100, 200, 300, 400], 50), 200)
        self.assertEqual(percentile([100, 200, 300, 400], 90), 400)

    def test_aggregate_reports_success_and_long_pole(self):
        result = aggregate_observations([
            observation("00000000-0000-4000-8000-000000000001", 100),
            observation("00000000-0000-4000-8000-000000000002", 300, "ssh-failed"),
        ])
        group = result["groups"][0]
        self.assertEqual(group["samples"], 2)
        self.assertEqual(group["success_rate"], 0.5)
        self.assertEqual(group["metrics"]["request_to_ssh_ready"]["median_ms"], 100)
        self.assertEqual(group["long_poles"]["winner_counts"]["provider_boot"], 2)

    def test_secret_scanner_rejects_connection_data(self):
        value = observation("00000000-0000-4000-8000-000000000003", 100)
        value["unexpected"] = "ssh root@192.0.2.4"
        findings = scan_observation(value)
        self.assertIn("IPv4 address", findings)
        self.assertIn("SSH command", findings)


if __name__ == "__main__":
    unittest.main()
