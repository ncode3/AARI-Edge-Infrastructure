import tempfile
import unittest
from pathlib import Path

from racksentinel.splunk import SplunkError, send_event
from racksentinel.telemetry import (
    _temperature_c,
    append_jsonl,
    collect_memory,
    evaluate_health,
)


class TemperatureTests(unittest.TestCase):
    def test_millidegrees(self):
        self.assertEqual(_temperature_c("42500"), 42.5)

    def test_degrees(self):
        self.assertEqual(_temperature_c("42.5"), 42.5)

    def test_invalid(self):
        self.assertIsNone(_temperature_c("not-a-temperature"))


class HealthTests(unittest.TestCase):
    def test_critical(self):
        health = evaluate_health(
            [{"name": "cpu", "temperature_c": 92.0}],
            warning_temp_c=80,
            critical_temp_c=90,
        )
        self.assertEqual(health["status"], "critical")

    def test_unknown_without_sensors(self):
        self.assertEqual(evaluate_health([], 80, 90)["status"], "unknown")


class StorageTests(unittest.TestCase):
    def test_memory_parser_and_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            meminfo = Path(tmp) / "meminfo"
            meminfo.write_text("MemTotal: 1000 kB\nMemAvailable: 250 kB\n", encoding="utf-8")
            self.assertEqual(collect_memory(meminfo)["used_percent"], 75.0)
            output = Path(tmp) / "nested" / "telemetry.jsonl"
            append_jsonl({"status": "ok"}, output)
            self.assertEqual(output.read_text(encoding="utf-8"), '{"status":"ok"}\n')


class SplunkTests(unittest.TestCase):
    def test_rejects_non_https_url(self):
        with self.assertRaises(SplunkError):
            send_event({"node": "test"}, "http://example.test/hec", "token")


if __name__ == "__main__":
    unittest.main()

