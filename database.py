import sqlite3
import json
import os

class Database:
    def __init__(self, db_path="data/sentinel.db"):
        self.db_path = db_path
        # Automatically create the /data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Creates the historical logs table if running for the first time."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    general_score REAL NOT NULL,
                    wifi_score REAL NOT NULL,
                    pihole_score REAL NOT NULL,
                    tailscale_score REAL NOT NULL,
                    suggestions TEXT,
                    raw_data TEXT
                )
            """)
            conn.commit()

    def log_health(self, timestamp: int, scores: dict, suggestions: list, raw_data: dict):
        """Appends a new diagnostic snapshot to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO health_logs 
                (timestamp, general_score, wifi_score, pihole_score, tailscale_score, suggestions, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                scores["general"],
                scores["wifi"],
                scores["pihole"],
                scores["tailscale"],
                json.dumps(suggestions),
                json.dumps(raw_data)
            ))
            conn.commit()

    def get_recent_logs(self, limit: int = 20) -> list:
        """Retrieves the latest logs for the frontend dashboard."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM health_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            
            results = []
            for r in rows:
                results.append({
                    "timestamp": r["timestamp"],
                    "general_score": r["general_score"],
                    "wifi_score": r["wifi_score"],
                    "pihole_score": r["pihole_score"],
                    "tailscale_score": r["tailscale_score"],
                    "suggestions": json.loads(r["suggestions"] or "[]"),
                    "raw_data": json.loads(r["raw_data"] or "{}")
                })
            return results