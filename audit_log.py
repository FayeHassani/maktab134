from datetime import datetime

class AuditLogger:
    def __init__(self, db):
        self.db = db
        self.create_table()

    def create_table(self):
        """ایجاد جدول لاگ در صورت نبودن"""
        query = """
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            actor VARCHAR(100) NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.db.execute_query(query)
        self.db.commit()

    def log(self, actor, action):
        """
        ثبت یک رویداد در جدول لاگ
        :param actor: کاربری که عملیات را انجام داده (user_id یا admin)
        :param action: توضیح عملیات انجام شده
        """
        try:
            query = "INSERT INTO audit_log (actor, action, timestamp) VALUES (%s, %s, %s)"
            self.db.execute_query(query, (str(actor), action, datetime.now()))
            self.db.commit()
        except Exception as e:
            print(f"[AuditLog Error] Failed to log action: {e}")

    def show_logs(self, limit=10):
        """نمایش آخرین لاگ‌ها"""
        try:
            query = "SELECT actor, action, timestamp FROM audit_log ORDER BY timestamp DESC LIMIT %s"
            logs = self.db.fetch_all(query, (limit,))
            if not logs:
                print("No audit logs found.")
                return

            print("\n🧾 Recent Audit Logs:")
            print("-" * 60)
            for actor, action, timestamp in logs:
                print(f"[{timestamp}] {actor}: {action}")
            print("-" * 60)

        except Exception as e:
            print(f"[AuditLog Error] Failed to fetch logs: {e}")
