import json
import subprocess
import time
import os

class TailscaleChecker:
    def __init__(self):
        self.socket_path = "/var/run/tailscale/tailscaled.sock"

    def run_diagnostics(self) -> dict:
        """Queries Tailscale daemon via CLI fallback or direct UNIX socket curl."""
        start_time = time.time()
        output = ""

        try:
            # Method A: Try native CLI (Works locally on Windows or hosts with CLI installed)
            cmd = ["tailscale", "status", "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout
            else:
                raise FileNotFoundError

        except (FileNotFoundError, Exception):
            # Method B: Direct UNIX Socket query via curl (Lightweight Docker approach)
            if not os.path.exists(self.socket_path):
                return {
                    "reachable": False, "running": False, "latency_ms": 0.0,
                    "error": "Tailscale socket not mounted inside container volume"
                }
            try:
                curl_cmd = [
                    "curl", "-s", "--unix-socket", self.socket_path,
                    "http://local-tailscaled.sock/localapi/v0/status"
                ]
                res = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=5)
                output = res.stdout
            except Exception as e:
                return {"reachable": False, "running": False, "latency_ms": 0.0, "error": str(e)}

        if not output:
            return {"reachable": False, "running": False, "latency_ms": 0.0, "error": "Empty response from Tailscale daemon"}

        try:
            data = json.loads(output)
            latency = round((time.time() - start_time) * 1000, 2)

            backend_state = data.get("BackendState", "Unknown")
            is_running = backend_state.lower() == "running"
            
            self_node = data.get("Self", {})
            hostname = self_node.get("HostName", "unknown")
            
            peers = data.get("Peer", {})
            active_peers = sum(1 for p in peers.values() if p.get("Online", False))

            return {
                "reachable": True,
                "running": is_running,
                "state": backend_state,
                "latency_ms": latency,
                "assigned_ips": self_node.get("TailscaleIPs", []),
                "hostname": hostname,
                "active_peers": active_peers
            }
        except Exception as e:
            return {"reachable": False, "running": False, "latency_ms": 0.0, "error": f"JSON Parse Error: {str(e)}"}

if __name__ == "__main__":
    print(json.dumps(TailscaleChecker().run_diagnostics(), indent=2))