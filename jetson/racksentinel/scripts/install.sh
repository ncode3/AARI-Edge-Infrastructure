#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run with sudo: sudo ./scripts/install.sh" >&2
  exit 1
fi

install -d -m 0755 /opt/aari-racksentinel
python3 -m venv /opt/aari-racksentinel/venv
/opt/aari-racksentinel/venv/bin/pip install --no-deps .

if ! id -u aari-edge >/dev/null 2>&1; then
  useradd --system --home /var/lib/aari-racksentinel --shell /usr/sbin/nologin aari-edge
fi
install -d -o aari-edge -g aari-edge -m 0750 /var/lib/aari-racksentinel
install -m 0644 deploy/aari-racksentinel.service /etc/systemd/system/aari-racksentinel.service

if [[ ! -f /etc/aari-racksentinel.env ]]; then
  install -m 0600 .env.example /etc/aari-racksentinel.env
fi

systemctl daemon-reload
systemctl enable --now aari-racksentinel.service
systemctl --no-pager --full status aari-racksentinel.service || true

