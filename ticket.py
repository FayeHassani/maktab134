from db_connect import PostgresConnection
import datetime
from db_connect import db_logger
from bus import BusManager
from wallet import WalletManager

class TicketManager:
    def __init__(self, db: PostgresConnection):
        self.db = db

    def buy_ticket(self, user_id, bus_id, seat_id, price):
        try:
            # lock wallet
            wallet_result = self.db.fetch_one(
                "SELECT wallet FROM users WHERE user_id=%s FOR UPDATE",
                (user_id,)
            )
            if not wallet_result:
                db_logger.info("User not found!")
                self.db.rollback()
                return False

            wallet = float(wallet_result[0])
            if wallet < price:
                db_logger.error("Insufficient balance!")
                self.db.rollback()
                return False

            #check if seat is available
            seat_result = self.db.fetch_one(
                "SELECT is_booked FROM seats WHERE seat_id=%s FOR UPDATE",
                (seat_id,)
            )
            if not seat_result:
                db_logger.info("Seat not found!")
                self.db.rollback()
                return False

            if seat_result[0]:
                db_logger.info("Seat already booked!")
                self.db.rollback()
                return False

            #reserve seat
            bus_manager = BusManager(self.db)
            bus_manager.reserve_seat(seat_id)
            
            # wallet deduction
            wallet_manager = WalletManager(self.db)
            wallet_manager.deduct_balance(user_id, price, type= "Ticket purchase")

            # log ticket
            self.db.execute_query(
                "INSERT INTO tickets (user_id,bus_id,seat_id,price,status) VALUES (%s,%s,%s,%s,'PAID')",
                (user_id, bus_id, seat_id, price)
            )

            self.db.commit()
            db_logger.info(f"Ticket purchased successfully! Remaining balance: ${wallet - price:.2f}")
            return True
        except Exception:
            db_logger.exception(f"Error buying ticket")
            self.db.rollback()
            return False

    # Cancel ticket
    def cancel_ticket(self, user_id, ticket_id, refund_percent=80):
        try:
            ticket = self.db.fetch_one(
                "SELECT status, price, seat_id FROM tickets WHERE ticket_id=%s AND user_id=%s",
                (ticket_id, user_id)
            )
            if not ticket:
                db_logger.info("Ticket not found")
                return False

            status, price, seat_id = ticket
            if status != "PAID":
                db_logger.error("Ticket cannot be cancelled!")
                return False

            refund_amount = float(price) * refund_percent / 100

            # Update ticket
            self.db.execute_query(
                "UPDATE tickets SET status='CANCELLED' WHERE ticket_id=%s",
                (ticket_id,)
            )
            # Update seat
            self.db.execute_query(
                "UPDATE seats SET is_booked=FALSE WHERE seat_id=%s",
                (seat_id,)
            )

            # Refund amount
            wallet_manager = WalletManager(self.db)
            wallet_manager.refund_balance(user_id, refund_amount, type="Ticket refund")
           
            self.db.commit()
            db_logger.info(f"Ticket cancelled. Refund: ${refund_amount:.2f}")
            return True
        except Exception:
            db_logger.exception("Error cancelling ticket")
            self.db.rollback()
            return False

    def get_user_tickets(self, user_id):
        try:
            query = """
                SELECT t.ticket_id, b.bus_name, b.bus_number, s.seat_number, 
                       t.price, t.purchase_date, t.status, b.departure_time, b.arrival_time, b.route
                FROM tickets t
                JOIN buses b ON t.bus_id=b.bus_id
                JOIN seats s ON t.seat_id=s.seat_id
                WHERE t.user_id=%s
                ORDER BY t.purchase_date DESC
            """
            results = self.db.fetch_all(query, (user_id,))
            tickets = []
            for row in results:
                ticket_id, bus_name, bus_number, seat_number, price, purchase_date, status, departure_time, arrival_time, route = row
                tickets.append({
                    "ticket_id": ticket_id,
                    "bus_name": bus_name,
                    "bus_number": bus_number,
                    "seat_number": seat_number,
                    "price": float(price),
                    "status": status,
                    "purchase_date": purchase_date,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "route": route
                })
            return tickets
        except Exception:
            db_logger.exception("Error fetching tickets")
            return []
