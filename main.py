from db_connect import PostgresConnection
from users import UserManager, Customer, Admin
from transfer import BusManager
from function import TicketManager

class BusReservationSystem:
    def __init__(self):
        self.db = PostgresConnection()
        self.user_manager = UserManager(self.db)
        self.bus_manager = BusManager(self.db)
        self.ticket_manager = TicketManager(self.db)
        self.current_user = None

    def start(self):
        with self.db as db:
            db.create_tables()
            self.main_menu()

    def main_menu(self):
        while True:
            print("\nMAIN MENU")
            print("1. Register\n2. Login\n3. Exit")
            choice = input("Choice: ")
            if choice == "1":
                self.register()
            elif choice == "2":
                self.login()
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid choice!")

    def register(self):
        name = input("Name: ")
        email = input("Email: ")
        password = input("Password: ")
        self.user_manager.register_user(name, email, password)

    def login(self):
        email = input("Email: ")
        password = input("Password: ")
        user = self.user_manager.login_user(email, password)
        if user:
            self.current_user = user
            if user.is_admin:
                self.admin_menu()
            else:
                self.customer_menu()
        else:
            print("Login failed!")

    # --- Customer Menu ---
    def customer_menu(self):
        while True:
            print(f"\nCUSTOMER MENU ({self.current_user.name})")
            print("1. View Buses\n2. Book Ticket\n3. My Tickets\n4. Wallet\n5. Add Money\n6. Logout")
            choice = input("Choice: ")
            if choice == "1":
                self.view_all_buses()
            elif choice == "2":
                self.book_ticket()
            elif choice == "3":
                self.view_my_tickets()
            elif choice == "4":
                print(f"Wallet: ${self.user_manager.get_wallet(self.current_user.user_id)}")
            elif choice == "5":
                amt = float(input("Add amount: "))
                self.user_manager.update_wallet(self.current_user.user_id, amt)
            elif choice == "6":
                self.current_user = None
                break

    # --- Admin Menu ---
    def admin_menu(self):
        while True:
            print(f"\nADMIN MENU ({self.current_user.name})")
            print("1. View Buses\n2. Add Bus\n3. Update Bus\n4. Delete Bus\n5. View Users\n6. Delete User\n7. View Tickets\n8. Cancel Ticket\n9. Logout")
            choice = input("Choice: ")
            if choice == "1":
                self.view_all_buses()
            elif choice == "2":
                self.add_bus()
            elif choice == "3":
                self.update_bus()
            elif choice == "4":
                self.delete_bus()
            elif choice == "5":
                self.view_all_users()
            elif choice == "6":
                self.delete_user()
            elif choice == "7":
                self.view_all_tickets()
            elif choice == "8":
                self.cancel_ticket_admin()
            elif choice == "9":
                self.current_user = None
                break

    # --- Bus/Booking Methods ---
    def view_all_buses(self):
        buses = self.bus_manager.get_all_buses()
        for bus in buses:
            print(bus)

    def book_ticket(self):
        bus_id = int(input("Bus ID: "))
        seats = self.bus_manager.get_available_seats(bus_id)
        print("Seats:", [s['seat_number'] for s in seats])
        seat_num = int(input("Seat Number: "))
        seat_id = next((s['seat_id'] for s in seats if s['seat_number']==seat_num), None)
        if seat_id:
            bus = self.bus_manager.get_bus_by_id(bus_id)
            self.ticket_manager.buy_ticket(self.current_user.user_id, bus_id, seat_id, bus['price_per_seat'])

    def view_my_tickets(self):
        tickets = self.ticket_manager.get_user_tickets(self.current_user.user_id)
        for t in tickets:
            print(t)

    def add_bus(self):
        bus_name = input("Bus name: ")
        bus_number = input("Bus number: ")
        total_seats = int(input("Total seats: "))
        price = float(input("Price per seat: "))
        departure = input("Departure time: ")
        arrival = input("Arrival time: ")
        route = input("Route: ")
        self.bus_manager.add_bus(bus_name, bus_number, total_seats, price, departure, arrival, route)

    def update_bus(self):
        bus_id = int(input("Bus ID: "))
        bus_name = input("New name: ")
        price = float(input("New price: "))
        departure = input("New departure: ")
        arrival = input("New arrival: ")
        route = input("New route: ")
        self.bus_manager.update_bus(bus_id, bus_name, price, departure, arrival, route)

    def delete_bus(self):
        bus_id = int(input("Bus ID: "))
        self.bus_manager.delete_bus(bus_id)

    def view_all_users(self):
        users = self.user_manager.get_all_users()
        for u in users:
            print(u)

    def delete_user(self):
        user_id = int(input("User ID: "))
        self.user_manager.delete_user(user_id)

    def view_all_tickets(self):
        tickets = self.ticket_manager.get_all_tickets()
        for t in tickets:
            print(t)

    def cancel_ticket_admin(self):
        ticket_id = int(input("Ticket ID: "))
        self.ticket_manager.cancel_ticket(ticket_id)


def main():
    system = BusReservationSystem()
    system.start()


if __name__ == "__main__":
    main()
