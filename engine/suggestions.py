class SuggestionEngine:
    @staticmethod
    def generate_suggestions(scores: dict, wifi_data: dict, pihole_data: dict, tailscale_data: dict) -> list:
        suggestions = []

        # Perfect Score Check
        if scores["general"] == 100.0:
            return ["All network subsystems operating at 100% peak efficiency."]

        # Wi-Fi Diagnostics
        if scores["wifi"] < 100.0:
            gw = wifi_data.get("gateway", {})
            if not gw.get("reachable", False):
                suggestions.append("CRITICAL: Default Gateway unreachable. Verify router power and physical host connection.")
            elif gw.get("loss_percent", 0.0) > 0:
                suggestions.append(f"Wi-Fi experiencing {gw['loss_percent']}% packet loss. Check for 2.4GHz/5GHz channel interference.")
            elif gw.get("avg_ms", 0.0) > 15.0:
                suggestions.append(f"Local router latency high ({gw['avg_ms']}ms). Access point may be congested.")

        # Pi-hole Diagnostics
        if scores["pihole"] < 100.0:
            if not pihole_data.get("reachable", False):
                suggestions.append("Pi-hole API unresponsive. Verify Pi-hole Docker container is active.")
            elif not pihole_data.get("authenticated", False):
                suggestions.append("Pi-hole session authentication failed. Check password in environment variables.")

        # Tailscale Diagnostics
        if scores["tailscale"] < 100.0:
            if not tailscale_data.get("running", False):
                suggestions.append("Tailscale daemon offline. Restart the tailscaled background service on the host.")

        if not suggestions:
            suggestions.append("Minor latency variance detected. Inspect historical trends in database logs.")

        return suggestions