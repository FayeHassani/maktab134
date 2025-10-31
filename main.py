import argparse
from db_connect import PostgresConnection
from users import UserManager
from bus import BusManager
from ticket import TicketManager
from wallet import WalletManager
from audit_log import AuditLogger
from reports import ReportManager
from db_connect import db_logger


class BusReservationSystem:
    def __init__(self, db):
        self.db = db
        self.user_manager = UserManager(self.db)
        self.bus_manager = BusManager(self.db)
        self.ticket_manager = TicketManager(self.db)
        self.wallet_manager = WalletManager(self.db)
        self.audit = AuditLogger(self.db)
        self.report_manager = ReportManager(self.db)

    def register(self, name, email, password):
        self.user_manager.register_user(name, email, password)

    def login(self, email, password):
        return self.user_manager.login_user(email, password)

    def add_bus(self, admin_id, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route):
        success = self.bus_manager.add_bus(admin_id, bus_name, bus_number, total_seats, price_per_seat, departure_time, arrival_time, route)
        if success:
            self.audit.log(admin_id, f"Bus added: {bus_name} ({bus_number})")
            db_logger.info(f"Bus '{bus_name}' added successfully.")
        else:
            db_logger.info(f"Failed to add bus: {bus_name} ({bus_number})")

    def book_ticket(self, user_id, bus_id, seat_number):
        buses = self.bus_manager.get_all_buses()
        bus = next((b for b in buses if b["bus_id"] == bus_id), None)
        if not bus:
            db_logger.info("Bus not found.")
            return

        price = bus["price_per_seat"]
        seats = self.bus_manager.get_available_seats(bus_id)
        seat = next((s for s in seats if s["seat_number"] == seat_number), None)
        if not seat:
            db_logger.info("Seat not available.")
            return

        success = self.ticket_manager.buy_ticket(user_id, bus_id, seat["seat_id"], price)
        if success:
            self.audit.log(user_id, f"Booked seat {seat_number} on bus {bus_id}")
        else:
            db_logger.info(f"Failed to book seat {seat_number} on bus {bus_id}")

    def cancel_ticket(self, user_id, ticket_id):
        success = self.ticket_manager.cancel_ticket(user_id, ticket_id)
        if success:
            self.audit.log(user_id, f"Cancelled ticket {ticket_id}")
        else:
            db_logger.info(f"Failed to cancel ticket {ticket_id}")

    def add_money(self, user_id, amount):
        success = self.wallet_manager.add_balance(user_id, amount, "Wallet deposit")
        if success:
            self.audit.log(user_id, f"Wallet topped up by ${amount:.2f}")
        else:
            db_logger.info(f"Failed to add ${amount:.2f} to wallet for user {user_id}")

    def show_balance(self, user_id):
        balance = self.wallet_manager.get_balance(user_id)
        print(f"Wallet Balance: ${balance:.2f}")

    def show_transactions(self, user_id):
        self.wallet_manager.show_transactions(user_id)

    def show_buses(self):
        buses = self.bus_manager.get_all_buses()
        if not buses:
            db_logger.info("No buses found")
            return
        print("Available Buses:")
        for b in buses:
            print(f"ID {b['bus_id']} - {b['bus_name']} | Route: {b['route']} | "
                  f"Seats: {b['available_seats']}/{b['total_seats']} | Price: ${b['price_per_seat']:.2f}")

    def show_income_report(self, admin_id, bus_id=None):
        if bus_id:
            total = self.report_manager.get_revenue_by_bus(admin_id, bus_id)
            print(f"Total income for bus {bus_id}: ${total:.2f}")
        else:
            total = self.report_manager.get_total_revenue(admin_id)
            print(f"Total terminal income: ${total:.2f}")

    def show_stats(self, admin_id):
        stats = self.report_manager.get_trip_statistics(admin_id)
        print(f"Total Trips: {stats['trips']}, Tickets Sold: {stats['tickets']}, Income: ${stats['income']:.2f}")

    def show_audit_log(self, limit=10):
        self.audit.show_logs(limit)


def main():
    parser = argparse.ArgumentParser(description="Bus Reservation System CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # Register
    reg = sub.add_parser("register", help="Register a new user")
    reg.add_argument("name")
    reg.add_argument("email")
    reg.add_argument("password")

    # Login
    login = sub.add_parser("login", help="Login user")
    login.add_argument("email")
    login.add_argument("password")

    # Add bus
    addbus = sub.add_parser("addbus", help="Add a new bus (admin only)")
    addbus.add_argument("admin_id", type=int)
    addbus.add_argument("name")
    addbus.add_argument("number")
    addbus.add_argument("seats", type=int)
    addbus.add_argument("price", type=float)
    addbus.add_argument("departure")
    addbus.add_argument("arrival")
    addbus.add_argument("route")

    # Book ticket
    book = sub.add_parser("book", help="Book a ticket")
    book.add_argument("user_id", type=int)
    book.add_argument("bus_id", type=int)
    book.add_argument("seat_number", type=int)

    # Cancel ticket
    cancel = sub.add_parser("cancel", help="Cancel a ticket")
    cancel.add_argument("user_id", type=int)
    cancel.add_argument("ticket_id", type=int)

    # Add money
    addmoney = sub.add_parser("addmoney", help="Add money to wallet")
    addmoney.add_argument("user_id", type=int)
    addmoney.add_argument("amount", type=float)

    # Balance
    balance = sub.add_parser("balance", help="Show wallet balance")
    balance.add_argument("user_id", type=int)

    # Transactions
    trans = sub.add_parser("transactions", help="Show wallet transactions")
    trans.add_argument("user_id", type=int)

    # Show buses
    buses = sub.add_parser("buses", help="Show all buses")

    # Reports
    rep = sub.add_parser("report", help="Show income reports")
    rep.add_argument("admin_id", type=int)
    rep.add_argument("--bus", type=int, help="Bus ID to report income for")

    # Stats
    stat = sub.add_parser("stats", help="Show system stats")
    stat.add_argument("admin_id", type=int)

    # Audit log
    audit = sub.add_parser("audit", help="Show audit log")
    audit.add_argument("--limit", type=int, default=30)

    args = parser.parse_args()

    # --- Use context manager for DB connection ---
    with PostgresConnection() as db:
        system = BusReservationSystem(db)

        if args.command == "register":
            system.register(args.name, args.email, args.password)

        elif args.command == "login":
            system.login(args.email, args.password)

        elif args.command == "addbus":
            system.add_bus(args.admin_id, args.name, args.number, args.seats, args.price, args.departure, args.arrival, args.route)

        elif args.command == "book":
            system.book_ticket(args.user_id, args.bus_id, args.seat_number)

        elif args.command == "cancel":
            system.cancel_ticket(args.user_id, args.ticket_id)

        elif args.command == "addmoney":
            system.add_money(args.user_id, args.amount)

        elif args.command == "balance":
            system.show_balance(args.user_id)

        elif args.command == "transactions":
            system.show_transactions(args.user_id)

        elif args.command == "buses":
            system.show_buses()

        elif args.command == "report":
            system.show_income_report(args.admin_id, args.bus)

        elif args.command == "stats":
            system.show_stats(args.admin_id)

        elif args.command == "audit":
            system.show_audit_log(args.limit)


if __name__ == "__main__":
    main()
