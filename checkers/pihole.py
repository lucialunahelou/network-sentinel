import json
import time
import urllib.request
import urllib.error

try:
    from config import Config
except ImportError:
    class Config:
        PIHOLE_URL = "http://192.168.1.188"
        PIHOLE_API_TOKEN = ""  # <-- Type your actual web login password here!
        PIHOLE_VERSION = 6

class PiholeChecker:
    def __init__(self):
        self.v6_sid = None

    def _v6_authenticate(self) -> str:
        """Logs into Pi-hole v6 to acquire a temporary Session ID (sid)."""
        if not Config.PIHOLE_API_TOKEN:
            return ""

        url = f"{Config.PIHOLE_URL.rstrip('/')}/api/auth"
        payload = json.dumps({"password": Config.PIHOLE_API_TOKEN}).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return data.get("session", {}).get("sid", "")
        except Exception:
            return ""

    def _fetch_v5_summary(self) -> dict:
        """Legacy fallback for Pi-hole v5 PHP instances."""
        url = f"{Config.PIHOLE_URL.rstrip('/')}/admin/api.php?summary"
        if Config.PIHOLE_API_TOKEN:
            url += f"&auth={Config.PIHOLE_API_TOKEN}"
        
        headers = {"User-Agent": "Mozilla/5.0"}
        start_time = time.time()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                latency = round((time.time() - start_time) * 1000, 2)
                data = json.loads(response.read().decode())
                return {
                    "reachable": True, "authenticated": True, "latency_ms": latency,
                    "queries_24h": data.get("dns_queries_today", 0),
                    "blocked_24h": data.get("ads_blocked_today", 0),
                    "blocked_percent": round(float(data.get("ads_percentage_today", 0.0)), 2),
                    "status": data.get("status", "unknown")
                }
        except Exception as e:
            return {"reachable": False, "authenticated": False, "latency_ms": 999.0, "error": str(e)}

    def _fetch_v6_summary(self, retry: bool = True) -> dict:
        """Queries the modern Pi-hole v6 REST API with session auto-renewal."""
        url = f"{Config.PIHOLE_URL.rstrip('/')}/api/stats/summary"
        
        # If we have a password configured but no active session ID badge, go fetch one!
        if Config.PIHOLE_API_TOKEN and not self.v6_sid:
            self.v6_sid = self._v6_authenticate()

        headers = {"Accept": "application/json", "User-Agent": "NetworkSentinel/1.0"}
        if self.v6_sid:
            headers["X-FTL-SID"] = self.v6_sid

        start_time = time.time()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                latency = round((time.time() - start_time) * 1000, 2)
                raw_data = json.loads(response.read().decode())
                
                q = raw_data.get("queries", {})
                
                return {
                    "reachable": True,
                    "authenticated": bool(self.v6_sid),
                    "latency_ms": latency,
                    "queries_24h": q.get("total", 0),
                    "blocked_24h": q.get("blocked", 0),
                    "blocked_percent": round(float(q.get("percent_blocked", q.get("percent", 0.0))), 2),
                    "status": "active"
                }
        except urllib.error.HTTPError as e:
            # If our Session ID badge expired (401), wipe it and retry logging in exactly once
            if e.code == 401 and retry and Config.PIHOLE_API_TOKEN:
                self.v6_sid = None
                return self._fetch_v6_summary(retry=False)
            return {"reachable": False, "authenticated": False, "latency_ms": 999.0, "error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            return {"reachable": False, "authenticated": False, "latency_ms": 999.0, "error": str(e)}

    def run_diagnostics(self) -> dict:
        if Config.PIHOLE_VERSION == 6:
            return self._fetch_v6_summary()
        return self._fetch_v5_summary()

if __name__ == "__main__":
    print(f"Testing Pi-hole v{Config.PIHOLE_VERSION} API at {Config.PIHOLE_URL}...")
    checker = PiholeChecker()
    print(json.dumps(checker.run_diagnostics(), indent=2))