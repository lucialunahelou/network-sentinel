import json
import time
import urllib.request
import urllib.error

try:
    from config import Config
except ImportError:
    class Config:
        PIHOLE_URL = "http://192.168.1.2"  # Fallback target for local testing
        PIHOLE_API_TOKEN = ""
        PIHOLE_VERSION = 5

class PiholeChecker:
    def __init__(self):
        pass

    def _fetch_v5_summary(self) -> dict:
        """Queries the classic Pi-hole v5 PHP API."""
        url = f"{Config.PIHOLE_URL.rstrip('/')}/admin/api.php?summary"
        if Config.PIHOLE_API_TOKEN:
            url += f"&auth={Config.PIHOLE_API_TOKEN}"
        
        start_time = time.time()
        try:
            # 5-second timeout to prevent the app from hanging if Pi-hole is dead
            with urllib.request.urlopen(url, timeout=5) as response:
                latency = round((time.time() - start_time) * 1000, 2)
                data = json.loads(response.read().decode())
                
                # If token is missing/wrong, Pi-hole v5 returns an empty list [] instead of stats
                if isinstance(data, list) or not data:
                    return {"reachable": True, "authenticated": False, "latency_ms": latency, "error": "Invalid or missing token"}
                
                return {
                    "reachable": True,
                    "authenticated": True,
                    "latency_ms": latency,
                    "queries_24h": data.get("dns_queries_today", 0),
                    "blocked_24h": data.get("ads_blocked_today", 0),
                    "blocked_percent": round(data.get("ads_percentage_today", 0.0), 2),
                    "status": data.get("status", "unknown")
                }
        except urllib.error.URLError as e:
            return {"reachable": False, "authenticated": False, "latency_ms": 999.0, "error": str(e.reason)}
        except Exception as e:
            return {"reachable": False, "authenticated": False, "latency_ms": 999.0, "error": str(e)}

    def _fetch_v6_summary(self) -> dict:
        """Queries the modern Pi-hole v6 REST API."""
        # Pi-hole v6 handles unauthenticated queries to /api/info/summary
        url = f"{Config.PIHOLE_URL.rstrip('/')}/api/info/summary"
        
        headers = {}
        if Config.PIHOLE_API_TOKEN:
            headers = {"X-FTL-SID": Config.PIHOLE_API_TOKEN}
            
        start_time = time.time()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                latency = round((time.time() - start_time) * 1000, 2)
                data = json.loads(response.read().decode())
                
                return {
                    "reachable": True,
                    "authenticated": True if Config.PIHOLE_API_TOKEN else False,
                    "latency_ms": latency,
                    "queries_24h": data.get("queries", {}).get("total", 0),
                    "blocked_24h": data.get("queries", {}).get("blocked", 0),
                    "blocked_percent": round(data.get("queries", {}).get("percent", 0.0), 2),
                    "status": data.get("status", "unknown")
                }
        except urllib.error.URLError as e:
            return {"reachable": False, "authenticated": False, "latency_ms": 999.0, "error": str(e.reason)}
        except Exception as e:
            return {"reachable": False, "authenticated": False, "latency_ms": 999.0, "error": str(e)}

    def run_diagnostics(self) -> dict:
        """Main entrypoint: Routes request based on Pi-hole target version."""
        if Config.PIHOLE_VERSION == 6:
            return self._fetch_v6_summary()
        return self._fetch_v5_summary()

if __name__ == "__main__":
    print(f"Testing Pi-hole Module targeting version {Config.PIHOLE_VERSION} at {Config.PIHOLE_URL}...")
    checker = PiholeChecker()
    stats = checker.run_diagnostics()
    print(json.dumps(stats, indent=2))