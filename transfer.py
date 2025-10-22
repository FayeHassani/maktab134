from db_connect import PostgresConnection

class BusManager:
    def __init__(self, db):
        self.db = db

    def add_bus(self, bus_name, bus_number, total_seats, ticket_price, departure_time, arrival_time, route):
        try:
            if self.db.fetch_one("SELECT bus_id FROM buses WHERE bus_number = %s", (bus_number,)):
                print("Bus number already exists!")
                return False

            if not self.db.execute_query(
                "INSERT INTO buses (bus_name, bus_number, total_seats, ticket_price, departure_time, arrival_time, route) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (bus_name, bus_number, total_seats, ticket_price, departure_time, arrival_time, route)
            ):
                print("Failed to add bus!")
                return False

            self.db.commit()
            bus_id = self.db.fetch_one("SELECT bus_id FROM buses WHERE bus_number = %s", (bus_number,))[0]

            for seat_num in range(1, total_seats + 1):
                self.db.execute_query("INSERT INTO seats (bus_id, seat_number) VALUES (%s,%s)", (bus_id, seat_num))
            self.db.commit()
            print(f"Bus {bus_name} added with {total_seats} seats!")
            return True

        except Exception as e:
            self.db.con.rollback()
            print(f"Error adding bus: {e}")
            return False

    def get_all_buses(self):
        try:
            results = self.db.fetch_all("SELECT bus_id, bus_name, bus_number, total_seats, ticket_price, departure_time, arrival_time, route FROM buses")
            buses = []
            for row in results:
                bus_id, bus_name, bus_number, total_seats, ticket_price, departure_time, arrival_time, route = row
                available_seats = self.db.fetch_one("SELECT COUNT(*) FROM seats WHERE bus_id=%s AND is_booked=FALSE", (bus_id,))[0]
                buses.append({
                    "bus_id": bus_id,
                    "bus_name": bus_name,
                    "bus_number": bus_number,
                    "total_seats": total_seats,
                    "available_seats": available_seats,
                    "price_per_seat": float(ticket_price),
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "route": route
                })
            return buses
        except Exception as e:
            print(f"Error getting buses: {e}")
            return []

    def get_bus_by_id(self, bus_id):
        try:
            row = self.db.fetch_one("SELECT bus_id, bus_name, bus_number, total_seats, ticket_price, departure_time, arrival_time, route FROM buses WHERE bus_id=%s", (bus_id,))
            if not row:
                print("Bus not found!")
                return None
            bus_id, bus_name, bus_number, total_seats, ticket_price, departure_time, arrival_time, route = row
            return {
                "bus_id": bus_id,
                "bus_name": bus_name,
                "bus_number": bus_number,
                "total_seats": total_seats,
                "price_per_seat": float(ticket_price),
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "route": route
            }
        except Exception as e:
            print(f"Error getting bus: {e}")
            return None

    def delete_bus(self, bus_id):
        try:
            if self.db.execute_query("DELETE FROM buses WHERE bus_id = %s", (bus_id,)):
                self.db.commit()
                print("Bus deleted successfully!")
                return True
            return False
        except Exception as e:
            self.db.con.rollback()
            print(f"Error deleting bus: {e}")
            return False

    def update_bus(self, bus_id, bus_name, ticket_price, departure_time, arrival_time, route):
        try:
            if self.db.execute_query(
                "UPDATE buses SET bus_name=%s, ticket_price=%s, departure_time=%s, arrival_time=%s, route=%s WHERE bus_id=%s",
                (bus_name, ticket_price, departure_time, arrival_time, route, bus_id)
            ):
                self.db.commit()
                print("Bus updated successfully!")
                return True
            return False
        except Exception as e:
            self.db.con.rollback()
            print(f"Error updating bus: {e}")
            return False

    def get_available_seats(self, bus_id):
        try:
            results = self.db.fetch_all("SELECT seat_id, seat_number FROM seats WHERE bus_id=%s AND is_booked=FALSE ORDER BY seat_number", (bus_id,))
            seats = [{"seat_id": r[0], "seat_number": r[1]} for r in results]
            return seats
        except Exception as e:
            print(f"Error getting seats: {e}")
            return []

    def book_seat(self, seat_id):
        try:
            seat = self.db.fetch_one("SELECT is_booked FROM seats WHERE seat_id=%s", (seat_id,))
            if not seat:
                print("Seat not found!")
                return False
            if seat[0]:
                print("Seat already booked!")
                return False
            if self.db.execute_query("UPDATE seats SET is_booked=TRUE WHERE seat_id=%s", (seat_id,)):
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.con.rollback()
            print(f"Error booking seat: {e}")
            return False
