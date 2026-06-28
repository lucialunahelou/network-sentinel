import json
import subprocess
import time

class TailscaleChecker:
    def __init__(self):
        pass

    def run_diagnostics(self) -> dict:
        """Queries the local Tailscale daemon for tunnel health and peer status."""
        start_time = time.time()
        try:
            # Executes the native Tailscale CLI command
            cmd = ["tailscale", "status", "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return {
                    "reachable": False, "running": False, "latency_ms": 0.0,
                    "error": result.stderr.strip() or "Tailscale daemon returned non-zero exit code"
                }

            data = json.loads(result.stdout)
            latency = round((time.time() - start_time) * 1000, 2)

            # Parse core Tailscale node data
            backend_state = data.get("BackendState", "Unknown")
            is_running = backend_state.lower() == "running"
            
            self_node = data.get("Self", {})
            tailscale_ips = self_node.get("TailscaleIPs", [])
            hostname = self_node.get("HostName", "unknown")
            
            # Count active peer connections
            peers = data.get("Peer", {})
            active_peers = sum(1 for p in peers.values() if p.get("Online", False))

            return {
                "reachable": True,
                "running": is_running,
                "state": backend_state,
                "latency_ms": latency,
                "assigned_ips": tailscale_ips,
                "hostname": hostname,
                "active_peers": active_peers
            }

        except FileNotFoundError:
            return {
                "reachable": False, "running": False, "latency_ms": 0.0,
                "error": "Tailscale CLI command not found on this host"
            }
        except subprocess.TimeoutExpired:
            return {
                "reachable": False, "running": False, "latency_ms": 999.0,
                "error": "Tailscale daemon timed out (service may be hung)"
            }
        except Exception as e:
            return {
                "reachable": False, "running": False, "latency_ms": 0.0,
                "error": str(e)
            }

if __name__ == "__main__":
    print("Testing Tailscale Daemon Health Module...")
    checker = TailscaleChecker()
    print(json.dumps(checker.run_diagnostics(), indent=2))