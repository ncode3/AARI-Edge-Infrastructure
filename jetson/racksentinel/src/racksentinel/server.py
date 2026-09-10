from __future__ import annotations

import html
import json
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .splunk import SplunkError, send_if_configured
from .telemetry import Settings, append_jsonl, collect


class State:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event: dict[str, Any] | None = None
        self._splunk_status = "not-configured"

    def update(self, event: dict[str, Any], splunk_status: str) -> None:
        with self._lock:
            self._event = event
            self._splunk_status = splunk_status

    def snapshot(self) -> tuple[dict[str, Any] | None, str]:
        with self._lock:
            return self._event, self._splunk_status


def _dashboard(event: dict[str, Any] | None, splunk_status: str) -> bytes:
    if event is None:
        status = "starting"
        max_temp = "waiting"
        gpu = "waiting"
        memory = "waiting"
        node = "AARI edge node"
        timestamp = "waiting for first sample"
    else:
        status = str(event["health"]["status"])
        max_temp = event["health"].get("max_temperature_c")
        max_temp = "unavailable" if max_temp is None else f"{max_temp:.1f} C"
        gpu_value = event["compute"].get("gpu_load_percent")
        gpu = "unavailable" if gpu_value is None else f"{gpu_value:.1f}%"
        memory_value = event["memory"].get("used_percent")
        memory = "unavailable" if memory_value is None else f"{memory_value:.1f}%"
        node = str(event["node"])
        timestamp = str(event["timestamp"])
    safe = {k: html.escape(str(v)) for k, v in {
        "status": status,
        "max_temp": max_temp,
        "gpu": gpu,
        "memory": memory,
        "node": node,
        "timestamp": timestamp,
        "splunk": splunk_status,
    }.items()}
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="refresh" content="10">
  <title>AARI RackSentinel</title>
  <style>
    :root {{ color-scheme: dark; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; background: #07120d; color: #edf8f1; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 48px 24px; }}
    h1 {{ color: #76e59a; margin-bottom: 4px; }}
    .sub {{ color: #a7b8ad; margin-top: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap: 16px; margin-top: 32px; }}
    .card {{ background: #102419; border: 1px solid #254f35; border-radius: 14px; padding: 20px; }}
    .label {{ color: #9cb7a5; font-size: .85rem; text-transform: uppercase; letter-spacing: .08em; }}
    .value {{ font-size: 1.65rem; font-weight: 700; margin-top: 8px; }}
    footer {{ color: #779184; margin-top: 32px; font-size: .85rem; }}
  </style>
</head>
<body><main>
  <h1>AARI RackSentinel</h1>
  <p class="sub">{safe['node']} | infrastructure-up edge operations</p>
  <section class="grid">
    <div class="card"><div class="label">Health</div><div class="value">{safe['status']}</div></div>
    <div class="card"><div class="label">Maximum temperature</div><div class="value">{safe['max_temp']}</div></div>
    <div class="card"><div class="label">GPU load</div><div class="value">{safe['gpu']}</div></div>
    <div class="card"><div class="label">Memory used</div><div class="value">{safe['memory']}</div></div>
    <div class="card"><div class="label">Splunk forwarding</div><div class="value">{safe['splunk']}</div></div>
  </section>
  <footer>Last sample: {safe['timestamp']} | JSON: /api/v1/telemetry | Health: /healthz</footer>
</main></body></html>"""
    return page.encode("utf-8")


def handler_for(state: State) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "AARI-RackSentinel/0.1"

        def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            event, splunk_status = state.snapshot()
            if self.path == "/":
                self._send(HTTPStatus.OK, "text/html; charset=utf-8", _dashboard(event, splunk_status))
                return
            if self.path == "/api/v1/telemetry":
                body = json.dumps(event or {"status": "starting"}).encode("utf-8")
                self._send(HTTPStatus.OK, "application/json", body)
                return
            if self.path == "/healthz":
                health = "starting" if event is None else event["health"]["status"]
                status = HTTPStatus.SERVICE_UNAVAILABLE if health == "critical" else HTTPStatus.OK
                self._send(status, "application/json", json.dumps({"status": health}).encode("utf-8"))
                return
            self._send(HTTPStatus.NOT_FOUND, "application/json", b'{"error":"not found"}')

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def collector_loop(state: State, settings: Settings, interval: float, stop: threading.Event) -> None:
    while not stop.is_set():
        event = collect(settings)
        append_jsonl(event, settings.data_path)
        splunk_status = "not-configured"
        try:
            if send_if_configured(event):
                splunk_status = "connected"
        except SplunkError as exc:
            splunk_status = f"error: {exc}"
        state.update(event, splunk_status)
        stop.wait(interval)


def serve(bind: str, port: int, interval: float, settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    state = State()
    stop = threading.Event()
    collector = threading.Thread(
        target=collector_loop,
        args=(state, settings, interval, stop),
        name="telemetry-collector",
        daemon=True,
    )
    collector.start()
    server = ThreadingHTTPServer((bind, port), handler_for(state))
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.shutdown()
        collector.join(timeout=max(interval, 1.0) + 1.0)

