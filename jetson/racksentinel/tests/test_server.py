import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from racksentinel.server import State, handler_for


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.state = State()
        self.state.update(
            {
                "node": "aari-edge-01",
                "timestamp": "2026-09-10T00:00:00+00:00",
                "health": {"status": "ok", "max_temperature_c": 43.5},
                "compute": {"gpu_load_percent": 12.0},
                "memory": {"used_percent": 25.0},
            },
            "not-configured",
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.state))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_health_endpoint(self):
        with urllib.request.urlopen(f"{self.base_url}/healthz", timeout=2) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.load(response), {"status": "ok"})

    def test_dashboard(self):
        with urllib.request.urlopen(f"{self.base_url}/", timeout=2) as response:
            page = response.read().decode("utf-8")
            self.assertIn("AARI RackSentinel", page)
            self.assertIn("aari-edge-01", page)
            self.assertIn("43.5 C", page)


if __name__ == "__main__":
    unittest.main()
