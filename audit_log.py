from datetime import datetime
from db_connect import db_logger

class AuditLogger:
    def __init__(self, db):
        self.db = db
    
    def log(self, actor_id, action):
        try:
            query = "INSERT INTO audit_log (actor_id, action) VALUES (%s, %s)"
            self.db.execute_query(query, (actor_id, action))
            self.db.commit()
        except Exception:
            db_logger.exception ("Error Logging action")

    def show_logs(self, limit=10):
        """showing last logs"""
        try:
            query = "SELECT actor, action, timestamp FROM audit_log ORDER BY timestamp DESC LIMIT %s"
            logs = self.db.fetch_all(query, (limit,))
            if not logs:
                db_logger.info("No audit logs found.")
                return

            print("Recent Audit Logs:")
            print("-" * 60)
            for actor, action, timestamp in logs:
                print(f"[{timestamp}] {actor}: {action}")
            print("-" * 60)

        except Exception:
            db_logger.exception("Error fetching audit logs")