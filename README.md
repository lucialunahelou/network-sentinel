# 🏰 Network Sentinel

*An active, zero-bloat network observability and health-scoring dashboard designed for self-hosted Docker environments.*

Instead of just pinging an external IP, **Network Sentinel** acts as an active diagnostic agent for your specific home infrastructure chain: 
`Local Wi-Fi Gateway` ➔ `Pi-hole DNS` ➔ `Tailscale Mesh`

It continuously audits these three pillars, logs historical trends to an embedded SQLite database, calculates a weighted live System Health Score out of **100**, and pushes plain-English recovery instructions to the UI the second anything degrades.

---

## ✨ Core Features

* **Active Wi-Fi Auditing:** Tracks local gateway reachability, packet loss, and latency jitter, paired with decoupled scheduled `speedtest-cli` bandwidth checks.
* **Pi-hole v6 Ready:** Features a native REST API session engine with smart `sid` badge auto-renewal (with full legacy support for Pi-hole v5 PHP instances).
* **UNIX Socket Tunneling:** Reads live Tailscale mesh status directly from the host daemon socket (`/var/run/tailscale/tailscaled.sock`) via `curl`, keeping the Docker image featherlight.
* **The Brain:** An automated grading engine that translates complex network drag into a clean 0–100 score.
* **Actionable Advice:** Dynamically generates targeted remediation text (e.g., *"Gateway latency high: 45ms. Check 2.4GHz channel congestion"*).
* **Zero Frontend Bloat:** Styled natively with **Water.css** for automatic, gorgeous dark-mode rendering without heavy JS frameworks.

---

## 📐 The Scoring Engine

The master score is calculated via a configurable weighted average:

`Total Score = (WiFi Score × 0.45) + (Pi-hole Score × 0.35) + (Tailscale Score × 0.20)`

* **Wi-Fi Deductions:** `-20 pts` per 1% packet loss | `-10 pts` for gateway ping >15ms | `-10 pts` for high jitter.
* **Pi-hole Deductions:** `-100 pts` if API is down | `-25 pts` for expired session auth | `-15 pts` for DNS resolution >50ms.
* **Tailscale Deductions:** `-100 pts` if daemon is unreachable | `-50 pts` if backend state drops from `Running`.

---

## 🚀 Portainer / Docker Compose Deployment

Because Sentinel needs to inspect your hardware's actual routing table and communicate with host daemons, it runs strictly in **`network_mode: "host"`**. 

### 1. The Stack Blueprint

```yaml
services:
  network-sentinel:
    container_name: network-sentinel
    build: .
    network_mode: "host"
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - /var/run/tailscale/tailscaled.sock:/var/run/tailscale/tailscaled.sock:ro
    environment:
      - SENTINEL_PORT=5050
      - SENTINEL_GATEWAY_IP=192.168.1.1
      - SENTINEL_EXTERNAL_DNS=1.1.1.1
      - SENTINEL_INTERVAL_SEC=60
      - PIHOLE_URL=[http://192.168.1.100](http://192.168.1.100)
      - PIHOLE_API_TOKEN=${SECRET_PIHOLE_PW}
      - PIHOLE_VERSION=6
      - WEIGHT_WIFI=0.45
      - WEIGHT_PIHOLE=0.35
      - WEIGHT_TAILSCALE=0.20