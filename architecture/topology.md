# Network Topology: AARI Edge Node v1

```mermaid
graph TD
    %% Nodes
    ISP[ISP Modem]
    RPI[<b>AARI Edge Router</b><br/>(Raspberry Pi 4)]
    Admin[Admin Laptop]
    IoT[IoT VLAN<br/>(Sensors/Cameras)]
    Guest[Guest VLAN]

    %% Styles
    style RPI fill:#f9f,stroke:#333,stroke-width:4px
    style ISP fill:#eee,stroke:#333
    style IoT fill:#d4edda,stroke:#333
    style Admin fill:#cce5ff,stroke:#333

    %% Connections
    ISP == WAN (eth0) ==> RPI
    RPI -- SSH (Key Auth) --> Admin
    RPI -. VLAN 10 .- IoT
    RPI -. VLAN 20 .- Guest

    %% Subgraph for Internal Logic
    subgraph "Edge Node Logic"
        FW[iptables Firewall]
        DNS[DNS/DHCP]
        IDS[Suricata IDS]
    end

    %% Logic Connections
    RPI --- FW
    FW --> DNS
    FW --> IDS
```
