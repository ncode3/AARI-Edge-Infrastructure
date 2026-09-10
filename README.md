# AARI Edge Infrastructure
### Secure edge operations for AI, robotics, and data-center education

![Status](https://img.shields.io/badge/Status-Active_Development-green) ![Security](https://img.shields.io/badge/Security-Review_in_Progress-blue)

## Mission

The Atlanta AI & Robotics Initiative (AARI) builds hands-on infrastructure from the physical layer upward: power and cooling, networking, Linux and systems, containers, cloud, and AI.

This repository contains public-safe code and documentation for AARI edge nodes. Production addresses, credentials, tokens, infrastructure state, and private network diagrams are intentionally excluded.

## Active modules

### AARI RackSentinel v0

`jetson/racksentinel/` turns an NVIDIA Jetson into a private edge operations node. It:

- collects compute, GPU, thermal, memory, storage, and uptime telemetry;
- evaluates local warning and critical thresholds;
- retains JSONL evidence when upstream systems are unavailable;
- provides a private dashboard through an SSH tunnel; and
- optionally forwards structured events to Splunk HEC over HTTPS.

The first target is an AARI data-center lab. Future inputs include rack inlet and outlet temperature, humidity, airflow, UPS and rack power, and approved RS-485/Modbus sensors.

### Raspberry Pi gateway prototype

The original prototype uses a Raspberry Pi 4 to teach:

- WAN/LAN and IoT segmentation;
- key-based SSH and least privilege;
- stateful firewalling; and
- traffic inspection concepts.

It remains a learning reference while the Jetson becomes the accelerated inference and telemetry platform.

## Security posture

- Key-based SSH only for managed nodes.
- No direct public exposure of device dashboards.
- Secrets stay in device-local environment files or an approved secrets manager.
- Production access passes through the approved firewall and jump-box path.
- Security testing is limited to systems AARI owns or has written permission to assess.

See [SECURITY.md](SECURITY.md) before contributing.

## Getting started

Start with [Jetson RackSentinel](jetson/racksentinel/README.md).

## Contributing

Issues and pull requests are welcome for documentation, tests, sensor adapters, telemetry parsers, and deployment hardening.

---

Architected by Nolan S. Code for the Atlanta AI & Robotics Initiative.
