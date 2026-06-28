import time
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify

from config import Config
from database import Database
from checkers.wifi_gateway import NetworkChecker
from checkers.pihole import PiholeChecker
from checkers.tailscale import TailscaleChecker
from engine.scoring import ScoreCalculator
from engine.suggestions import SuggestionEngine

app = Flask(__name__)
db = Database()

# In-memory cache using CSS class names instead of raw hex colors
latest_state = {
    "timestamp_str": "Initializing...",
    "scores": {"general": 0.0, "wifi": 0.0, "pihole": 0.0, "tailscale": 0.0},
    "score_class": "score-good",
    "suggestions": ["Running initial diagnostic sweep..."],
    "raw": {}
}

def diagnostic_loop():
    global latest_state
    
    wifi_checker = NetworkChecker()
    pihole_checker = PiholeChecker()
    tailscale_checker = TailscaleChecker()

    while True:
        raw_wifi = wifi_checker.run_diagnostics()
        raw_pihole = pihole_checker.run_diagnostics()
        raw_ts = tailscale_checker.run_diagnostics()

        scores = ScoreCalculator.calculate_scores(raw_wifi, raw_pihole, raw_ts)
        suggestions = SuggestionEngine.generate_suggestions(scores, raw_wifi, raw_pihole, raw_ts)
        
        # Determine CSS class cleanly in Python
        gen = scores["general"]
        score_class = "score-good" if gen >= 90 else "score-warn" if gen >= 70 else "score-bad"

        now = int(time.time())
        time_str = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
        raw_combined = {"wifi": raw_wifi, "pihole": raw_pihole, "tailscale": raw_ts}

        db.log_health(now, scores, suggestions, raw_combined)

        latest_state = {
            "timestamp_str": time_str,
            "scores": scores,
            "score_class": score_class,
            "suggestions": suggestions,
            "raw": raw_combined
        }

        time.sleep(Config.CHECK_INTERVAL)

@app.route("/")
def dashboard():
    raw_logs = db.get_recent_logs(limit=15)
    formatted_logs = []
    
    for l in raw_logs:
        formatted_logs.append({
            "time_str": datetime.fromtimestamp(l["timestamp"]).strftime("%H:%M:%S"),
            "general_score": l["general_score"],
            "wifi_score": l["wifi_score"],
            "pihole_score": l["pihole_score"],
            "tailscale_score": l["tailscale_score"],
            "suggestions": l["suggestions"]
        })

    return render_template("index.html", current=latest_state, history=formatted_logs)

@app.route("/api/status")
def api_status():
    return jsonify(latest_state)

if __name__ == "__main__":
    worker = threading.Thread(target=diagnostic_loop, daemon=True)
    worker.start()

    print(f"Network Sentinel online! Open your browser to: http://localhost:{Config.FLASK_PORT}")
    app.run(host="0.0.0.0", port=Config.FLASK_PORT, debug=Config.DEBUG_MODE)