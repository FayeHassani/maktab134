from datetime import datetime
from audit_log import AuditLogger

class BusManager:
    def __init__(self, db):
        self.db = db
        self.audit = AuditLogger(db)
        self.create_tables()

    def create_tables(self):
        """ایجاد جدول‌های موردنیاز در صورت نبودن"""
        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS buses (
            bus_id SERIAL PRIMARY KEY,
            bus_name VARCHAR(100),
            bus_number VARCHAR(50) UNIQUE,
            total_seats INTEGER,
            price_per_seat NUMERIC(10,2),
            departure_time TIMESTAMP,
            arrival_time TIMESTAMP,
            route TEXT
        );
        """)
        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_id SERIAL PRIMARY KEY,
            bus_id INTEGER REFERENCES buses(bus_id) ON DELETE CASCADE,
            seat_number INTEGER,
            is_booked BOOLEAN DEFAULT FALSE,
            UNIQUE (bus_id, seat_number)
        );
        """)
        self.db.commit()

    # -----------------------------
    # افزودن سفر جدید
    # -----------------------------
    def add_bus(self, admin_id, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route):
        try:
            result = self.db.fetch_one("SELECT bus_id FROM buses WHERE bus_number=%s", (bus_number,))
            if result:
                print("❌ Bus number already exists!")
                return False

            query = """INSERT INTO buses (bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING bus_id"""
            result = self.db.fetch_one(query, (bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route))
            bus_id = result[0]

            # ایجاد صندلی‌ها
            for seat_num in range(1, total_seats + 1):
                self.db.execute_query("INSERT INTO seats (bus_id, seat_number) VALUES (%s, %s)", (bus_id, seat_num))
            self.db.commit()

            self.audit.log(admin_id, f"Added new bus {bus_name} ({bus_number}) with {total_seats} seats")
            print(f"✅ Bus '{bus_name}' added successfully with {total_seats} seats.")
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error adding bus: {e}")
            return False

    # -----------------------------
    # لیست همه سفرها
    # -----------------------------
    def get_all_buses(self):
        try:
            query = """SELECT bus_id, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route
                       FROM buses ORDER BY departure_time"""
            results = self.db.fetch_all(query)
            if not results:
                print("No buses found.")
                return []

            buses = []
            for row in results:
                bus_id, bus_name, bus_number, total_seats, price, dep, arr, route = row
                available = self.db.fetch_one("SELECT COUNT(*) FROM seats WHERE bus_id=%s AND is_booked=FALSE", (bus_id,))
                available_seats = available[0] if available else 0
                buses.append({
                    "bus_id": bus_id,
                    "bus_name": bus_name,
                    "bus_number": bus_number,
                    "route": route,
                    "departure_time": dep,
                    "arrival_time": arr,
                    "price_per_seat": float(price),
                    "total_seats": total_seats,
                    "available_seats": available_seats
                })
            return buses
        except Exception as e:
            print(f"Error getting buses: {e}")
            return []

    # -----------------------------
    # دریافت اطلاعات یک سفر
    # -----------------------------
    def get_bus_by_id(self, bus_id):
        try:
            result = self.db.fetch_one("SELECT * FROM buses WHERE bus_id=%s", (bus_id,))
            if not result:
                print("Bus not found!")
                return None

            bus_id, name, number, total, price, dep, arr, route = result
            available = self.db.fetch_one("SELECT COUNT(*) FROM seats WHERE bus_id=%s AND is_booked=FALSE", (bus_id,))
            available_seats = available[0] if available else 0
            return {
                "bus_id": bus_id,
                "bus_name": name,
                "bus_number": number,
                "total_seats": total,
                "price_per_seat": float(price),
                "departure_time": dep,
                "arrival_time": arr,
                "route": route,
                "available_seats": available_seats
            }
        except Exception as e:
            print(f"Error getting bus: {e}")
            return None

    # -----------------------------
    # حذف سفر (و صندلی‌ها)
    # -----------------------------
    def delete_bus(self, admin_id, bus_id):
        try:
            bus = self.db.fetch_one("SELECT bus_name FROM buses WHERE bus_id=%s", (bus_id,))
            if not bus:
                print("Bus not found.")
                return False

            self.db.execute_query("DELETE FROM buses WHERE bus_id=%s", (bus_id,))
            self.db.commit()

            self.audit.log(admin_id, f"Deleted bus {bus[0]} (ID {bus_id})")
            print(f"🗑️ Bus {bus[0]} deleted successfully.")
            return True
        except Exception as e:
            print(f"Error deleting bus: {e}")
            self.db.rollback()
            return False

    # -----------------------------
    # به‌روزرسانی اطلاعات سفر
    # -----------------------------
    def update_bus(self, admin_id, bus_id, bus_name, price_per_seat, departure_time, arrival_time, route):
        try:
            query = """UPDATE buses SET bus_name=%s, price_per_seat=%s, departure_time=%s, arrival_time=%s, route=%s WHERE bus_id=%s"""
            self.db.execute_query(query, (bus_name, price_per_seat, departure_time, arrival_time, route, bus_id))
            self.db.commit()

            self.audit.log(admin_id, f"Updated bus {bus_name} (ID {bus_id})")
            print("✅ Bus updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating bus: {e}")
            self.db.rollback()
            return False

    # -----------------------------
    # مدیریت صندلی‌ها
    # -----------------------------
    def get_available_seats(self, bus_id):
        try:
            query = "SELECT seat_id, seat_number FROM seats WHERE bus_id=%s AND is_booked=FALSE ORDER BY seat_number"
            results = self.db.fetch_all(query)
            return [{"seat_id": s_id, "seat_number": num} for s_id, num in results]
        except Exception as e:
            print(f"Error fetching seats: {e}")
            return []

    def reserve_seat(self, seat_id):
        """رزرو صندلی با کنترل همزمانی"""
        try:
            self.db.cur.execute("BEGIN;")
            result = self.db.fetch_one("SELECT is_booked FROM seats WHERE seat_id=%s FOR UPDATE;", (seat_id,))
            if not result:
                print("Seat not found.")
                self.db.rollback()
                return False

            if result[0]:
                print("Seat already booked.")
                self.db.rollback()
                return False

            self.db.execute_query("UPDATE seats SET is_booked=TRUE WHERE seat_id=%s;", (seat_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error reserving seat: {e}")
            self.db.rollback()
            return False
