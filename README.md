# AARI Edge Infrastructure: Prototype v1
### Bare-Metal Edge Gateway for AI & Robotics Education

![Status](https://img.shields.io/badge/Status-Active_Development-green) ![Security](https://img.shields.io/badge/Security-Hardened-blue)

## 📡 Mission Overview
The **Atlanta AI & Robotics Initiative (AARI)** is building a decentralized, hands-on curriculum to teach the next generation of engineers. This repository documents the construction of the **Edge Node Prototype**—a secure, localized data center designed to handle:

* **Secure Traffic Analysis** (IDS/IPS)
* **Low-Latency AI Streams** (Computer Vision/Inference)
* **Network Segmentation** (IoT vs. User Data)

## 🏗 Architecture
This is not a standard consumer router setup. It is an enterprise-grade gateway built on ARM architecture (Raspberry Pi 4), mimicking edge deployments found in industrial IoT and modern cloud-edge scenarios.

### Hardware Bill of Materials (BOM)
| Component | Spec | Role |
|-----------|------|------|
| **Compute** | Raspberry Pi 4 (4GB) | Packet Processing & Logic |
| **Storage** | 32GB Class 10 SD | OS & Logs |
| **Network** | Gigabit Ethernet + USB 3.0 NIC | WAN/LAN Segmentation |
| **Power** | 5V 3A USB-C | Stable Voltage for Peripherals |

## 🛡 Security Posture (Security+ Implementation)
As part of the validation process, this infrastructure implements core CompTIA Security+ concepts:
* **Identity Management:** Key-based SSH authentication (No passwords).
* **Perimeter Defense:** Custom `iptables` stateful firewall.
* **Traffic Inspection:** (Upcoming) Suricata IDS integration.
* **Least Privilege:** User role separation (`moneymaker` vs root).

## 🚀 Getting Started
*See `/docs/ops/` for detailed runbooks.*

1.  **Flash OS:** Debian-based (Raspberry Pi OS Lite)
2.  **Network Config:** See `src/network/interfaces`
3.  **Access:** `ssh -i <your-key> user@gateway-ip`

## 🤝 Contributing
This project is open-source to support students and educators.
* **Issues:** Please log bugs or security concerns via GitHub Issues.
* **Pull Requests:** Welcome for documentation or script optimization.

---
*Architected by Nolan S. Code for the Atlanta AI & Robotics Initiative.*
