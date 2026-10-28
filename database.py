import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime
import cv2


class SafetyDatabase:
    def __init__(self, db_path=None, evidence_dir=None):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = db_path or os.path.join(project_dir, "sentineledge.db")
        self.evidence_dir = evidence_dir or os.path.join(project_dir, "evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        violation_type TEXT,
                        zone TEXT,
                        confidence REAL,
                        image_path TEXT
                    )
                """)

    def log_incident(self, frame, violation_type, zone, confidence):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S_%f")
        safe_violation_type = re.sub(r"[^A-Za-z0-9._-]+", "_", violation_type).strip("._")
        filename = f"{timestamp}_{safe_violation_type or 'incident'}.jpg"
        image_path = os.path.join(self.evidence_dir, filename)
        if frame is not None:
            if not cv2.imwrite(image_path, frame):
                raise OSError(f"Could not write incident evidence image: {image_path}")
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                conn.execute("""
                    INSERT INTO incidents (timestamp, violation_type, zone, confidence, image_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    now.strftime("%Y-%m-%d %H:%M:%S"),
                    violation_type,
                    zone,
                    confidence,
                    image_path,
                ))
        return image_path

    def get_all_incidents(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT timestamp, violation_type, zone, confidence, image_path "
                "FROM incidents ORDER BY id DESC"
            )
            return cursor.fetchall()

    def delete_all_incidents(self) -> int:
        """Delete every incident record and return the number of rows removed."""
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                cursor = conn.execute("DELETE FROM incidents")
                return cursor.rowcount
