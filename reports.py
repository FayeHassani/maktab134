from datetime import datetime
from audit_log import AuditLogger

class ReportManager:
    def __init__(self, db):
        self.db = db
        self.audit = AuditLogger(db)
        self.create_tables()

    def create_tables(self):
        """ایجاد جدول گزارش‌ها (در صورت نیاز)"""
        query = """
        CREATE TABLE IF NOT EXISTS reports (
            report_id SERIAL PRIMARY KEY,
            report_type VARCHAR(50),
            generated_by INTEGER REFERENCES users(user_id),
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        );
        """
        self.db.execute_query(query)
        self.db.commit()

    def _save_report(self, admin_id, report_type, details):
        """ذخیره گزارش در جدول"""
        self.db.execute_query(
            "INSERT INTO reports (report_type, generated_by, details) VALUES (%s, %s, %s)",
            (report_type, admin_id, details)
        )
        self.db.commit()
        self.audit.log(admin_id, f"Generated report: {report_type}")

    # -----------------------------
    #  گزارش درآمدها
    # -----------------------------
    def get_total_revenue(self, admin_id):
        """مجموع کل درآمد بلیط‌ها"""
        try:
            result = self.db.fetch_one("SELECT SUM(price) FROM tickets WHERE status = 'PAID'")
            total = float(result[0]) if result and result[0] else 0.0
            details = f"Total revenue from all tickets: ${total:.2f}"
            self._save_report(admin_id, "TOTAL_REVENUE", details)
            print(details)
            return total
        except Exception as e:
            print(f"Error fetching total revenue: {e}")
            return 0.0

    def get_revenue_by_bus(self, admin_id, bus_id):
        """درآمد یک سفر خاص"""
        try:
            result = self.db.fetch_one(
                "SELECT SUM(price) FROM tickets WHERE bus_id = %s AND status = 'PAID'",
                (bus_id,)
            )
            total = float(result[0]) if result and result[0] else 0.0
            details = f"Revenue for bus {bus_id}: ${total:.2f}"
            self._save_report(admin_id, "BUS_REVENUE", details)
            print(details)
            return total
        except Exception as e:
            print(f"Error fetching bus revenue: {e}")
            return 0.0

    # -----------------------------
    #  گزارش آماری سفرها و بلیط‌ها
    # -----------------------------
    def get_ticket_statistics(self, admin_id):
        """تعداد کل بلیط‌ها، لغوشده‌ها و استفاده‌شده‌ها"""
        try:
            query = """
            SELECT 
                COUNT(*) FILTER (WHERE status = 'PAID') AS sold,
                COUNT(*) FILTER (WHERE status = 'CANCELLED') AS cancelled,
                COUNT(*) FILTER (WHERE status = 'USED') AS used
            FROM tickets;
            """
            result = self.db.fetch_one(query)
            sold, cancelled, used = result if result else (0, 0, 0)
            details = f"Tickets - Sold: {sold}, Cancelled: {cancelled}, Used: {used}"
            self._save_report(admin_id, "TICKET_STATS", details)
            print(details)
            return {"sold": sold, "cancelled": cancelled, "used": used}
        except Exception as e:
            print(f"Error fetching ticket stats: {e}")
            return {}

    def get_trip_statistics(self, admin_id):
        """تعداد سفرهای انجام‌شده و ظرفیت استفاده‌شده"""
        try:
            query = """
            SELECT 
                COUNT(DISTINCT bus_id) AS total_trips,
                COUNT(ticket_id) AS total_tickets,
                SUM(price) AS total_income
            FROM tickets WHERE status = 'PAID';
            """
            result = self.db.fetch_one(query)
            trips, tickets, income = result if result else (0, 0, 0.0)
            details = f"Trips: {trips}, Tickets sold: {tickets}, Income: ${income:.2f}"
            self._save_report(admin_id, "TRIP_STATS", details)
            print(details)
            return {"trips": trips, "tickets": tickets, "income": income}
        except Exception as e:
            print(f"Error fetching trip stats: {e}")
            return {}

    # -----------------------------
    #  مشاهده گزارش‌های ذخیره‌شده
    # -----------------------------
    def view_reports(self, admin_id):
        """نمایش گزارش‌های ذخیره‌شده"""
        try:
            query = """
            SELECT report_id, report_type, generated_at, details
            FROM reports
            ORDER BY generated_at DESC
            """
            results = self.db.fetch_all(query)
            if not results:
                print("No reports found.")
                return []

            print("\n📋 Saved Reports:")
            print("-" * 70)
            for r_id, r_type, date, details in results:
                print(f"[{r_id}] {r_type} | {date}")
                print(f"    {details}")
            print("-" * 70)
            return results
        except Exception as e:
            print(f"Error viewing reports: {e}")
            return []
