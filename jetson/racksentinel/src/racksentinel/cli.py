from __future__ import annotations

import argparse
import json
import os

from .server import serve
from .splunk import SplunkError, send_if_configured
from .telemetry import Settings, append_jsonl, collect


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="racksentinel")
    commands = root.add_subparsers(dest="command", required=True)

    once = commands.add_parser("once", help="collect and print one telemetry event")
    once.add_argument("--store", action="store_true", help="append the event to the configured JSONL file")
    once.add_argument("--send", action="store_true", help="send the event to configured Splunk HEC")

    server = commands.add_parser("serve", help="run the collector and private dashboard")
    server.add_argument("--bind", default=os.getenv("AARI_BIND_HOST", "127.0.0.1"))
    server.add_argument("--port", type=int, default=int(os.getenv("AARI_BIND_PORT", "9105")))
    server.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("AARI_SAMPLE_INTERVAL_SECONDS", "10")),
    )
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = Settings.from_env()
    if settings.warning_temp_c >= settings.critical_temp_c:
        raise SystemExit("AARI_WARNING_TEMP_C must be lower than AARI_CRITICAL_TEMP_C")
    if args.command == "once":
        event = collect(settings)
        if args.store:
            append_jsonl(event, settings.data_path)
        if args.send:
            try:
                send_if_configured(event)
            except SplunkError as exc:
                raise SystemExit(f"Splunk send failed: {exc}") from exc
        print(json.dumps(event, indent=2))
        return 0
    if args.command == "serve":
        if args.port < 1 or args.port > 65535:
            raise SystemExit("port must be between 1 and 65535")
        if args.interval < 1:
            raise SystemExit("interval must be at least 1 second")
        serve(args.bind, args.port, args.interval, settings)
        return 0
    return 2

