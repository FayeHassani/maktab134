from datetime import datetime
from audit_log import AuditLogger
from db_connect import db_logger

class BusManager:
    def __init__(self, db):
        self.db = db
        self.audit = AuditLogger(db)

    # --- Add bus ---
    def add_bus(self, admin_id, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route):
        try:
            # Check duplicate bus number
            if self.db.fetch_one("SELECT bus_id FROM buses WHERE bus_number=%s", (bus_number,)):
                db_logger.error("Bus number already exists")
                return False

            # Insert bus
            query = """INSERT INTO buses (bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING bus_id"""
            result = self.db.fetch_one(query, (bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route))
            if not result:
                db_logger.error("Failed to insert bus")
                return False
            bus_id = result[0]

            # Insert seats in batch
            seat_values = [(bus_id, i) for i in range(1, total_seats+1)]
            self.db.cur.executemany("INSERT INTO seats (bus_id, seat_number) VALUES (%s, %s);", seat_values)

            self.db.commit()
            db_logger.info(f"Bus '{bus_name}' added successfully with {total_seats} seats.")
            return True
        except Exception:
            self.db.rollback()
            db_logger.exception(f"Error adding bus: {bus_name}", exc_info=True)
            return False

    # --- Get all buses ---
    def get_all_buses(self):
        try:
            query = """
                SELECT b.bus_id, b.bus_name, b.bus_number, b.total_seats, b.price_per_seat,
                       b.departure_time, b.arrival_time, b.route,
                       COUNT(s.seat_id) FILTER (WHERE s.is_booked=FALSE) AS available_seats
                FROM buses b
                LEFT JOIN seats s ON b.bus_id = s.bus_id
                GROUP BY b.bus_id
                ORDER BY b.departure_time
            """
            results = self.db.fetch_all(query)
            buses = []
            for row in results:
                bus_id, bus_name, bus_number, total_seats, price, departure_time, arrival_time, route, available_seats = row
                buses.append({
                    "bus_id": bus_id,
                    "bus_name": bus_name,
                    "bus_number": bus_number,
                    "route": route,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "price_per_seat": float(price),
                    "total_seats": total_seats,
                    "available_seats": available_seats
                })
            return buses
        except Exception:
            db_logger.exception("Error getting buses", exc_info=True)
            return []

    # --- Get bus by ID ---
    def get_bus_by_id(self, bus_id):
        try:
            query = """
                SELECT b.bus_id, b.bus_name, b.bus_number, b.total_seats, b.price_per_seat,
                       b.departure_time, b.arrival_time, b.route,
                       COUNT(s.seat_id) FILTER (WHERE s.is_booked=FALSE) AS available_seats
                FROM buses b
                LEFT JOIN seats s ON b.bus_id = s.bus_id
                WHERE b.bus_id=%s
                GROUP BY b.bus_id
            """
            result = self.db.fetch_one(query, (bus_id,))
            if not result:
                db_logger.info("Bus not found")
                return None

            bus_id, bus_name, bus_number, total_seats, price, departure_time, arrival_time, route, available_seats = result
            return {
                "bus_id": bus_id,
                "bus_name": bus_name,
                "bus_number": bus_number,
                "total_seats": total_seats,
                "price_per_seat": float(price),
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "route": route,
                "available_seats": available_seats
            }
        except Exception:
            db_logger.exception(f"Error getting bus: {bus_id}", exc_info=True)
            return None

    # --- Delete bus ---
    def delete_bus(self, admin_id, bus_id):
        try:
            bus = self.db.fetch_one("SELECT bus_name FROM buses WHERE bus_id=%s", (bus_id,))
            if not bus:
                db_logger.info("Bus not found")
                return False

            self.db.execute_query("DELETE FROM buses WHERE bus_id=%s", (bus_id,))
            self.db.commit()
            self.audit.log(admin_id, f"Deleted bus {bus[0]} (ID {bus_id})")
            db_logger.info(f"Bus {bus[0]} deleted successfully")
            return True
        except Exception:
            self.db.rollback()
            db_logger.exception(f"Error deleting bus: {bus_id}", exc_info=True)
            return False

    # --- Update bus ---
    def update_bus(self, admin_id, bus_id, bus_name, price_per_seat, departure_time, arrival_time, route):
        try:
            query = """UPDATE buses SET bus_name=%s, price_per_seat=%s, departure_time=%s, arrival_time=%s, route=%s WHERE bus_id=%s"""
            self.db.execute_query(query, (bus_name, price_per_seat, departure_time, arrival_time, route, bus_id))
            self.db.commit()
            self.audit.log(admin_id, f"Updated bus {bus_name} (ID {bus_id})")
            db_logger.info("Bus updated successfully.")
            return True
        except Exception:
            self.db.rollback()
            db_logger.exception(f"Error updating bus: {bus_id}", exc_info=True)
            return False

    # --- Get available seats ---
    def get_available_seats(self, bus_id):
        try:
            query = "SELECT seat_id, seat_number FROM seats WHERE bus_id=%s AND is_booked=FALSE ORDER BY seat_number"
            results = self.db.fetch_all(query, (bus_id,))
            return [{"seat_id": s_id, "seat_number": num} for s_id, num in results]
        except Exception:
            db_logger.exception("Error fetching seats", exc_info=True)
            return []

    # --- Reserve seat ---
    def reserve_seat(self, seat_id):
        try:
            result = self.db.fetch_one("SELECT is_booked FROM seats WHERE seat_id=%s FOR UPDATE;", (seat_id,))
            if not result:
                db_logger.info("Seat not found.")
                return False

            if result[0]:
                db_logger.info("Seat already booked.")
                return False

            self.db.execute_query("UPDATE seats SET is_booked=TRUE WHERE seat_id=%s;", (seat_id,))
            return True
        except Exception:
            db_logger.exception(f"Error reserving seat: {seat_id}", exc_info=True)
            return False
