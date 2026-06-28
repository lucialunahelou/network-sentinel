import platform
import re
import subprocess
import time
import json

# Graceful fallback so you can run this file directly to test it
try:
    from config import Config
except ImportError:
    class Config:
        GATEWAY_IP = "192.168.1.1"
        EXTERNAL_DNS = "1.1.1.1"

class NetworkChecker:
    def __init__(self):
        self.last_speedtest_time = 0
        self.cached_speedtest = {"download_mbps": 0.0, "upload_mbps": 0.0, "ping_ms": 0.0}
        self.speedtest_interval = 3600  # Run heavy speedtest only once per hour (3600s)

    def _ping(self, host: str, count: int = 4) -> dict:
        """Runs OS-level ping and calculates reachability, latency, and jitter."""
        current_os = platform.system().lower()
        
        if current_os == "windows":
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), host]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = result.stdout
        except subprocess.TimeoutExpired:
            return {"reachable": False, "loss_percent": 100.0, "avg_ms": 999.0, "jitter_ms": 0.0}
        except Exception:
            return {"reachable": False, "loss_percent": 100.0, "avg_ms": 999.0, "jitter_ms": 0.0}

        # Parse Packet Loss
        loss = 100.0
        loss_match = re.search(r"(\d+(?:\.\d+)?)%\s*packet loss|Lost = \d+ \((\d+(?:\.\d+)?)%", output, re.IGNORECASE)
        if loss_match:
            loss = float(loss_match.group(1) or loss_match.group(2))

        reachable = loss < 100.0

        # Parse Latency & Jitter
        avg_ms = 0.0
        jitter_ms = 0.0

        if current_os == "windows":
            # Windows format: Minimum = 1ms, Maximum = 4ms, Average = 2ms
            win_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output)
            if win_match:
                min_ms, max_ms, avg_ms = float(win_match.group(1)), float(win_match.group(2)), float(win_match.group(3))
                jitter_ms = round(max_ms - min_ms, 2)
        else:
            # Linux format: rtt min/avg/max/mdev = 1.1/2.4/3.8/0.5 ms
            lin_match = re.search(r"=\s*([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)", output)
            if lin_match:
                avg_ms = float(lin_match.group(2))
                jitter_ms = float(lin_match.group(4))  # mdev is standard deviation (jitter)

        return {
            "reachable": reachable,
            "loss_percent": loss,
            "avg_ms": round(avg_ms, 2),
            "jitter_ms": round(jitter_ms, 2)
        }

    def _run_speedtest(self) -> dict:
        """Executes speedtest-cli. Cached to prevent network flooding."""
        now = time.time()
        if (now - self.last_speedtest_time) < self.speedtest_interval and self.cached_speedtest["download_mbps"] > 0:
            return self.cached_speedtest

        try:
            # Requires speedtest-cli installed in the Python environment
            cmd = ["speedtest-cli", "--json", "--secure"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            data = json.loads(result.stdout)
            
            self.cached_speedtest = {
                "download_mbps": round(data["download"] / 1_000_000, 2),
                "upload_mbps": round(data["upload"] / 1_000_000, 2),
                "ping_ms": round(data["ping"], 2)
            }
            self.last_speedtest_time = now
        except Exception:
            # Fallback if speedtest fails or CLI is missing
            pass

        return self.cached_speedtest

    def run_diagnostics(self) -> dict:
        """Main entrypoint: Gathers gateway health, WAN health, and bandwidth speeds."""
        gateway_stats = self._ping(Config.GATEWAY_IP, count=3)
        external_stats = self._ping(Config.EXTERNAL_DNS, count=3)
        speed_stats = self._run_speedtest()

        return {
            "timestamp": int(time.time()),
            "gateway": gateway_stats,
            "external": external_stats,
            "bandwidth": speed_stats
        }

# Standalone test execution block
if __name__ == "__main__":
    print("Testing Wi-Fi & Gateway Module (Pinging local gateway and 1.1.1.1)...")
    checker = NetworkChecker()
    stats = checker.run_diagnostics()
    print(json.dumps(stats, indent=2))