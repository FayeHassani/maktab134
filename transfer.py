from db_connect import PostgresConnection

class BusManager:
    def __init__(self, db: PostgresConnection):
        self.db = db

    def add_bus(self, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route, actor_id=None):
        result = self.db.fetch_one("SELECT * FROM buses WHERE bus_number=%s;", (bus_number,))
        if result:
            print("Bus number already exists!")
            return False

        self.db.execute_query(
            "INSERT INTO buses (bus_name,bus_number,total_seats,price_per_seat,departure_time,arrival_time,route) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s);",
            (bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route)
        )

        bus_id = self.db.fetch_one("SELECT bus_id FROM buses WHERE bus_number=%s;", (bus_number,))[0]
        for seat_num in range(1, total_seats + 1):
            self.db.execute_query("INSERT INTO seats (bus_id,seat_number,is_booked) VALUES (%s,%s,FALSE);", (bus_id, seat_num))

        if actor_id:
            self.db.log_action(actor_id, f"Added bus {bus_name} with bus_number {bus_number} and {total_seats} seats")

        self.db.commit()
        print(f"Bus {bus_name} added successfully with {total_seats} seats!")
        return True

    def get_all_buses(self):
        buses = self.db.fetch_all("SELECT bus_id,bus_name,bus_number,total_seats,price_per_seat,departure_time,arrival_time,route FROM buses;")
        bus_list = []
        for bus in buses:
            bus_id, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route = bus
            available_seats = self.db.fetch_one(
                "SELECT COUNT(*) FROM seats WHERE bus_id=%s AND is_booked=FALSE;", (bus_id,)
            )[0]
            bus_list.append({
                "bus_id": bus_id,
                "bus_name": bus_name,
                "bus_number": bus_number,
                "total_seats": total_seats,
                "available_seats": available_seats,
                "price_per_seat": float(price_per_seat),
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "route": route
            })
        return bus_list

    def get_bus_by_id(self, bus_id):
        bus = self.db.fetch_one(
            "SELECT bus_id,bus_name,bus_number,total_seats,price_per_seat,departure_time,arrival_time,route FROM buses WHERE bus_id=%s;",
            (bus_id,)
        )
        if not bus:
            return None
        bus_id, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route = bus
        return {
            "bus_id": bus_id,
            "bus_name": bus_name,
            "bus_number": bus_number,
            "total_seats": total_seats,
            "price_per_seat": float(price_per_seat),
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "route": route
        }

    def delete_bus(self, bus_id, actor_id=None):
        self.db.execute_query("DELETE FROM buses WHERE bus_id=%s;", (bus_id,))
        if actor_id:
            self.db.log_action(actor_id, f"Deleted bus_id={bus_id}")
        self.db.commit()
        print("Bus deleted successfully!")
        return True

    def update_bus(self, bus_id, bus_name, price_per_seat, departure_time, arrival_time, route, actor_id=None):
        self.db.execute_query(
            "UPDATE buses SET bus_name=%s, price_per_seat=%s, departure_time=%s, arrival_time=%s, route=%s WHERE bus_id=%s;",
            (bus_name, price_per_seat, departure_time, arrival_time, route, bus_id)
        )
        if actor_id:
            self.db.log_action(actor_id, f"Updated bus_id={bus_id} with new details")
        self.db.commit()
        print("Bus updated successfully!")
        return True

    def get_available_seats(self, bus_id):
        seats = self.db.fetch_all("SELECT seat_id,seat_number FROM seats WHERE bus_id=%s AND is_booked=FALSE ORDER BY seat_number;", (bus_id,))
        return [{"seat_id": s[0], "seat_number": s[1]} for s in seats]

    def book_seat(self, seat_id):
        seat = self.db.fetch_one("SELECT is_booked FROM seats WHERE seat_id=%s FOR UPDATE;", (seat_id,))
        if not seat or seat[0]:
            return False
        self.db.execute_query("UPDATE seats SET is_booked=TRUE WHERE seat_id=%s;", (seat_id,))
        self.db.commit()
        return True
