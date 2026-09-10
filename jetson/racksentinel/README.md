# AARI RackSentinel v0

RackSentinel turns an NVIDIA Jetson into a private edge operations node for AARI infrastructure labs. It collects local compute, thermal, memory, storage, and health telemetry, keeps an on-device evidence log, exposes a small private dashboard, and can forward structured events to Splunk HEC.

No Solar addresses, credentials, or production configuration belong in this public repository.

## First one-hour milestone

The first milestone is complete when the Jetson:

1. boots as `aari-edge-01`;
2. produces one valid telemetry event;
3. serves the dashboard through a local SSH tunnel;
4. records JSONL evidence locally; and
5. reports a warning or critical state when a test threshold is lowered.

## Quick start on the Jetson

```bash
git clone https://github.com/ncode3/AARI-Edge-Infrastructure.git
cd AARI-Edge-Infrastructure/jetson/racksentinel
python3 -m venv .venv
. .venv/bin/activate
pip install --no-deps -e .
racksentinel once
```

Run the private dashboard:

```bash
mkdir -p data
export AARI_DATA_PATH="$PWD/data/telemetry.jsonl"
racksentinel serve
```

From the Lenovo, create an SSH tunnel and open `http://127.0.0.1:9105`:

```powershell
ssh -L 9105:127.0.0.1:9105 <jetson-user>@<jetson-private-ip>
```

At Solar, the tunnel should traverse the approved jump-box path. Never expose port `9105` publicly.

## Splunk

Set the full HTTPS HEC endpoint and token only in `/etc/aari-racksentinel.env` on the Jetson:

```bash
SPLUNK_HEC_URL=https://<splunk-host>:8088/services/collector/event
SPLUNK_HEC_TOKEN=<secret-token>
```

The source type is `aari:racksentinel:telemetry`. The agent continues logging locally when Splunk is unavailable.

## Service installation

After validating the manual run:

```bash
sudo bash scripts/install.sh
```

The dashboard binds to `127.0.0.1` by default. Production network assignment and firewall policy must be approved separately.

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Next hardware inputs

- rack inlet and outlet temperature;
- humidity and airflow;
- UPS and rack power over approved RS-485/Modbus interfaces;
- optional visual or thermal inspection sensor.

These inputs will feed the same event schema without changing the secure management pattern.
