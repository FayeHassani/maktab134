from datetime import datetime
from audit_log import AuditLogger
from db_connect import db_logger

class ReportManager:
    def __init__(self, db):
        self.db = db
        self.audit = AuditLogger(db)
      
    def _save_report(self, admin_id, report_type, details):
        try:
            self.db.execute_query(
                "INSERT INTO reports (report_type, generated_by, details) VALUES (%s, %s, %s)",
                (report_type, admin_id, details)
            )
            self.audit.log(admin_id, f"Generated report: {report_type}")
        except Exception:
            db_logger.exception(f"Error saving report: {report_type}")

    # total revenue
    def get_total_revenue(self, admin_id):
        try:
            result = self.db.fetch_one("SELECT SUM(price) FROM tickets WHERE status = 'PAID'")
            total = float(result[0]) if result and result[0] else 0.0
            details = f"Total revenue from all tickets: ${total:.2f}"
            self._save_report(admin_id, "TOTAL_REVENUE", details)
            return total
        except Exception:
            db_logger.exception(f"Error fetching total revenue")
            return 0.0

    def get_revenue_by_bus(self, admin_id, bus_id):
        try:
            result = self.db.fetch_one(
                "SELECT SUM(price) FROM tickets WHERE bus_id = %s AND status = 'PAID'",
                (bus_id,)
            )
            total = float(result[0]) if result and result[0] else 0.0
            details = f"Revenue for bus {bus_id}: ${total:.2f}"
            self._save_report(admin_id, "BUS_REVENUE", details)
            return total
        except Exception:
            db_logger.exception(f"Error fetching bus revenue")
            return 0.0

    #-----Statistics-----
    def get_ticket_statistics(self, admin_id):
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
            return {"sold": sold, "cancelled": cancelled, "used": used}
        except Exception:
            db_logger.exception("Error fetching ticket stats")
            return {}

    def get_trip_statistics(self, admin_id):
        """total trips and used seats"""
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
            return {"trips": trips, "tickets": tickets, "income": income}
        except Exception:
            db_logger.exception("Error fetching trip stats")
            return {}

    def view_reports(self, admin_id):
        try:
            query = """
            SELECT report_id, report_type, generated_at, details
            FROM reports
            ORDER BY generated_at DESC
            """
            results = self.db.fetch_all(query)
            if not results:
                db_logger.info("No reports found.")
                return []

            return results
        except Exception:
            db_logger.exception("Error viewing reports")
            return []
            
