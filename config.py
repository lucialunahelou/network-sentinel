import os

class Config:
    # Flask configuration
    FLASK_PORT = int(os.environ.get("SENTINEL_PORT", 5000))
    DEBUG_MODE = os.environ.get("SENTINEL_DEBUG", "False").lower() in ("true", "1", "t")

    # Network Targets
    GATEWAY_IP = os.environ.get("SENTINEL_GATEWAY_IP", "192.168.1.1")
    EXTERNAL_DNS = os.environ.get("SENTINEL_EXTERNAL_DNS", "1.1.1.1")
    CHECK_INTERVAL = int(os.environ.get("SENTINEL_INTERVAL_SEC", 60))

    # Pi-hole Configuration
    PIHOLE_URL = os.environ.get("PIHOLE_URL", "http://192.168.1.2")
    PIHOLE_API_TOKEN = os.environ.get("PIHOLE_API_TOKEN", "")
    PIHOLE_VERSION = int(os.environ.get("PIHOLE_VERSION", 5))  # Support 5 or 6

    # Scoring Weights (Must add up to 1.0)
    WEIGHT_WIFI = float(os.environ.get("WEIGHT_WIFI", 0.45))
    WEIGHT_PIHOLE = float(os.environ.get("WEIGHT_PIHOLE", 0.35))
    WEIGHT_TAILSCALE = float(os.environ.get("WEIGHT_TAILSCALE", 0.20))