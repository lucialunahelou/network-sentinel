try:
    from config import Config
except ImportError:
    class Config:
        WEIGHT_WIFI = 0.45
        WEIGHT_PIHOLE = 0.35
        WEIGHT_TAILSCALE = 0.20

class ScoreCalculator:
    @staticmethod
    def calculate_scores(wifi_data: dict, pihole_data: dict, tailscale_data: dict) -> dict:
        # 1. Wi-Fi Score Calculation
        wifi_score = 100.0
        gw = wifi_data.get("gateway", {})
        if not gw.get("reachable", False):
            wifi_score = 0.0
        else:
            loss = gw.get("loss_percent", 0.0)
            wifi_score -= (loss * 2.0)  # -20 points for every 10% packet loss
            if gw.get("avg_ms", 0.0) > 15.0:
                wifi_score -= 10.0      # -10 points if local router ping is sluggish (>15ms)
            if gw.get("jitter_ms", 0.0) > 10.0:
                wifi_score -= 10.0      # -10 points for high jitter

        wifi_score = max(0.0, min(100.0, round(wifi_score, 1)))

        # 2. Pi-hole Score Calculation
        pihole_score = 100.0
        if not pihole_data.get("reachable", False):
            pihole_score = 0.0
        else:
            if not pihole_data.get("authenticated", False):
                pihole_score -= 25.0    # Deduct if API locks us out due to expired auth
            if pihole_data.get("latency_ms", 0.0) > 50.0:
                pihole_score -= 15.0    # Deduct if DNS server response is lagging

        pihole_score = max(0.0, min(100.0, round(pihole_score, 1)))

        # 3. Tailscale Score Calculation
        ts_score = 100.0
        if not tailscale_data.get("reachable", False) or not tailscale_data.get("running", False):
            ts_score = 0.0
        else:
            if tailscale_data.get("state", "").lower() != "running":
                ts_score -= 50.0

        ts_score = max(0.0, min(100.0, round(ts_score, 1)))

        # 4. General Weighted Average
        general = (
            (wifi_score * Config.WEIGHT_WIFI) +
            (pihole_score * Config.WEIGHT_PIHOLE) +
            (ts_score * Config.WEIGHT_TAILSCALE)
        )
        general = max(0.0, min(100.0, round(general, 1)))

        return {
            "general": general,
            "wifi": wifi_score,
            "pihole": pihole_score,
            "tailscale": ts_score
        }