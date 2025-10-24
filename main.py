import argparse
from db_connect import PostgresConnection
from users import UserManager, Customer, Admin
from transfer import BusManager
from function import TicketManager

def main():
    parser = argparse.ArgumentParser(description="Bus Reservation System CLI")
    parser.add_argument("--register", nargs=3, metavar=("NAME","EMAIL","PASS"), help="Register a new user")
    parser.add_argument("--login", nargs=2, metavar=("EMAIL","PASS"), help="Login a user")
    parser.add_argument("--view_buses", action="store_true", help="View all buses")
    parser.add_argument("--buy_ticket", nargs=3, metavar=("USER_ID","BUS_ID","SEAT_ID"), help="Buy a ticket")
    parser.add_argument("--cancel_ticket", nargs=2, metavar=("USER_ID","TICKET_ID"), help="Cancel ticket")
    parser.add_argument("--report", nargs="?", const=True, metavar="BUS_ID", help="Get report (optional bus_id)")

    args = parser.parse_args()

    with PostgresConnection() as db:
        db.create_tables()
        user_mgr = UserManager(db)
        bus_mgr = BusManager(db)
        ticket_mgr = TicketManager(db)

        if args.register:
            name, email, password = args.register
            user_mgr.register_user(name, email, password)

        elif args.login:
            email, password = args.login
            user = user_mgr.login_user(email, password)
            if user:
                print(f"Logged in as {user.name} ({'Admin' if isinstance(user, Admin) else 'Customer'})")
            else:
                print("Login failed")

        elif args.view_buses:
            buses = bus_mgr.get_all_buses()
            for b in buses:
                print(f"{b['bus_id']}: {b['bus_name']} | Route: {b['route']} | Seats: {b['available_seats']}/{b['total_seats']} | ${b['price_per_seat']}")

        elif args.buy_ticket:
            user_id, bus_id, seat_id = map(int, args.buy_ticket)
            bus = bus_mgr.get_bus_by_id(bus_id)
            if not bus:
                print("Bus not found!")
                return
            price = bus['price_per_seat']
            ticket_mgr.buy_ticket(user_id, bus_id, seat_id, price)

        elif args.cancel_ticket:
            user_id, ticket_id = map(int, args.cancel_ticket)
            ticket_mgr.cancel_ticket(user_id, ticket_id)

        elif args.report:
            bus_id = int(args.report) if args.report != True else None
            report = ticket_mgr.get_reports(bus_id)
            print(f"Tickets sold: {report['tickets_sold']}, Revenue: ${report['revenue']}")

if __name__ == "__main__":
    main()
