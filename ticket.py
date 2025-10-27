from db_connect import PostgresConnection
import datetime

class TicketManager:
    def __init__(self, db: PostgresConnection):
        self.db = db

    # خرید بلیط با تراکنش امن و ثبت تراکنش کیف پول
    def buy_ticket(self, user_id, bus_id, seat_id, price):
        try:
            # شروع تراکنش
            self.db.cur.execute("BEGIN;")

            # قفل کردن موجودی کاربر
            wallet_result = self.db.fetch_one(
                "SELECT wallet FROM users WHERE user_id=%s FOR UPDATE",
                (user_id,)
            )
            if not wallet_result:
                print("User not found!")
                self.db.rollback()
                return False

            wallet = float(wallet_result[0])
            if wallet < price:
                print("Insufficient balance!")
                self.db.rollback()
                return False

            # بررسی وضعیت صندلی
            seat_result = self.db.fetch_one(
                "SELECT is_booked FROM seats WHERE seat_id=%s FOR UPDATE",
                (seat_id,)
            )
            if not seat_result:
                print("Seat not found!")
                self.db.rollback()
                return False

            if seat_result[0]:
                print("Seat already booked!")
                self.db.rollback()
                return False

            # رزرو صندلی
            self.db.execute_query(
                "UPDATE seats SET is_booked=TRUE WHERE seat_id=%s",
                (seat_id,)
            )

            # کسر از کیف پول
            self.db.execute_query(
                "UPDATE users SET wallet=wallet-%s WHERE user_id=%s",
                (price, user_id)
            )

            # ثبت تراکنش
            self.db.execute_query(
                "INSERT INTO transactions (user_id,type,amount) VALUES (%s,%s,%s)",
                (user_id, "BUY_TICKET", price)
            )

            # ثبت بلیط
            self.db.execute_query(
                "INSERT INTO tickets (user_id,bus_id,seat_id,price,status) VALUES (%s,%s,%s,%s,'PAID')",
                (user_id, bus_id, seat_id, price)
            )

            self.db.commit()
            print(f"Ticket purchased successfully! Remaining balance: ${wallet - price:.2f}")
            return True
        except Exception as e:
            print(f"Error buying ticket: {e}")
            self.db.rollback()
            return False

    # لغو بلیط
    def cancel_ticket(self, user_id, ticket_id, refund_percent=80):
        try:
            ticket = self.db.fetch_one(
                "SELECT status, price, seat_id FROM tickets WHERE ticket_id=%s AND user_id=%s",
                (ticket_id, user_id)
            )
            if not ticket:
                print("Ticket not found!")
                return False

            status, price, seat_id = ticket
            if status != "PAID":
                print("Ticket cannot be cancelled!")
                return False

            refund_amount = price * refund_percent / 100

            # بروزرسانی وضعیت بلیط و صندلی
            self.db.execute_query(
                "UPDATE tickets SET status='CANCELLED' WHERE ticket_id=%s",
                (ticket_id,)
            )
            self.db.execute_query(
                "UPDATE seats SET is_booked=FALSE WHERE seat_id=%s",
                (seat_id,)
            )

            # بازگرداندن مبلغ به کیف پول
            self.db.execute_query(
                "UPDATE users SET wallet=wallet+%s WHERE user_id=%s",
                (refund_amount, user_id)
            )
            # ثبت تراکنش
            self.db.execute_query(
                "INSERT INTO transactions (user_id,type,amount) VALUES (%s,%s,%s)",
                (user_id, "REFUND", refund_amount)
            )

            self.db.commit()
            print(f"Ticket cancelled. Refund: ${refund_amount:.2f}")
            return True
        except Exception as e:
            print(f"Error cancelling ticket: {e}")
            self.db.rollback()
            return False

    # مشاهده بلیط‌های کاربر
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
        except Exception as e:
            print(f"Error fetching tickets: {e}")
            return []
