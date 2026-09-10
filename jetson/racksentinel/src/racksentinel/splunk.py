from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class SplunkError(RuntimeError):
    pass


def send_event(event: dict[str, Any], url: str, token: str, timeout: float = 5.0) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SplunkError("SPLUNK_HEC_URL must be a complete HTTPS URL")
    body = json.dumps(
        {
            "event": event,
            "host": event.get("node"),
            "source": "aari-racksentinel",
            "sourcetype": "aari:racksentinel:telemetry",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Splunk {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            if response.status < 200 or response.status >= 300:
                raise SplunkError(f"Splunk HEC returned HTTP {response.status}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SplunkError(str(exc)) from exc


def send_if_configured(event: dict[str, Any]) -> bool:
    url = os.getenv("SPLUNK_HEC_URL", "").strip()
    token = os.getenv("SPLUNK_HEC_TOKEN", "").strip()
    if not url or not token:
        return False
    send_event(event, url, token)
    return True

