from db_connect import PostgresConnection

class TicketManager:
    def __init__(self, db: PostgresConnection):
        self.db = db

    # ---buy ticket ---
    def buy_ticket(self, user_id, bus_id, seat_id, price):
        try:
            self.db.cur.execute("BEGIN;")
            wallet = self.db.fetch_one("SELECT wallet FROM users WHERE user_id = %s FOR UPDATE;", (user_id,))
            if not wallet:
                print("User not found!")
                self.db.rollback()
                return False

            wallet = float(wallet[0])
            if wallet < price:
                print("Insufficient balance!")
                self.db.rollback()
                return False

            seat = self.db.fetch_one("SELECT is_booked FROM seats WHERE seat_id = %s FOR UPDATE;", (seat_id,))
            if not seat or seat[0]:
                print("Seat already booked or not found!")
                self.db.rollback()
                return False

            # reserve seat
            self.db.execute_query("UPDATE seats SET is_booked = TRUE WHERE seat_id = %s;", (seat_id,))
            #update wallet
            self.db.execute_query("UPDATE users SET wallet = wallet - %s WHERE user_id = %s;", (price, user_id))
            # transition
            self.db.execute_query("INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s);",
                                  (user_id, "TICKET_PURCHASE", price))
            # tickrt
            self.db.execute_query(
                "INSERT INTO tickets (user_id, bus_id, seat_id, price, status) VALUES (%s, %s, %s, %s, 'PAID');",
                (user_id, bus_id, seat_id, price)
            )
            # log
            self.db.log_action(user_id, f"Purchased ticket for bus_id={bus_id}, seat_id={seat_id}")

            self.db.commit()
            print(f"Ticket purchased successfully! Remaining wallet: ${wallet - price:.2f}")
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error buying ticket: {e}")
            return False

    # --- cancel tichet
    def cancel_ticket(self, user_id, ticket_id, refund_percent=80):
        try:
            ticket = self.db.fetch_one("SELECT status, price, seat_id, bus_id FROM tickets WHERE ticket_id=%s AND user_id=%s;",
                                       (ticket_id, user_id))
            if not ticket:
                print("Ticket not found!")
                return False

            status, price, seat_id, bus_id = ticket
            if status != "PAID":
                print("Ticket cannot be cancelled!")
                return False

            # بروزرسانی وضعیت بلیط
            self.db.execute_query("UPDATE tickets SET status='CANCELLED' WHERE ticket_id=%s;", (ticket_id,))
            # آزاد کردن صندلی
            self.db.execute_query("UPDATE seats SET is_booked=FALSE WHERE seat_id=%s;", (seat_id,))
            # برگشت وجه با درصد مشخص
            refund_amount = price * (refund_percent / 100)
            self.db.execute_query("UPDATE users SET wallet = wallet + %s WHERE user_id=%s;", (refund_amount, user_id))
            # ثبت تراکنش برگشت وجه
            self.db.execute_query("INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s);",
                                  (user_id, "REFUND", refund_amount))
            # لاگ
            self.db.log_action(user_id, f"Cancelled ticket_id={ticket_id}, refund={refund_amount}")

            self.db.commit()
            print(f"Ticket cancelled! ${refund_amount:.2f} refunded to wallet.")
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error cancelling ticket: {e}")
            return False

    # --- گزارش ها ---
    def get_reports(self, bus_id=None):
        try:
            if bus_id:
                # درآمد و تعداد بلیط برای یک سفر
                result = self.db.fetch_one(
                    "SELECT COUNT(*), SUM(price) FROM tickets WHERE bus_id=%s AND status='PAID';", (bus_id,))
                count, revenue = result if result else (0, 0)
                return {"tickets_sold": count, "revenue": float(revenue or 0)}
            else:
                # کل درآمد و تعداد بلیط
                result = self.db.fetch_one(
                    "SELECT COUNT(*), SUM(price) FROM tickets WHERE status='PAID';")
                count, revenue = result if result else (0, 0)
                return {"tickets_sold": count, "revenue": float(revenue or 0)}
        except Exception as e:
            print(f"Error fetching reports: {e}")
            return {"tickets_sold": 0, "revenue": 0}


    def get_user_tickets(self, user_id):
        try:
            query = """
                SELECT t.ticket_id, b.bus_name, b.bus_number, s.seat_number, t.price, t.purchase_date,
                       b.departure_time, b.arrival_time, b.route
                FROM tickets t
                JOIN buses b ON t.bus_id = b.bus_id
                JOIN seats s ON t.seat_id = s.seat_id
                WHERE t.user_id = %s
                ORDER BY t.purchase_date DESC
            """
            results = self.db.fetch_all(query, (user_id,))
            tickets = []
            for row in results:
                ticket_id, bus_name, bus_number, seat_number, price, purchase_date, departure_time, arrival_time, route = row
                tickets.append({
                    "ticket_id": ticket_id,
                    "bus_name": bus_name,
                    "bus_number": bus_number,
                    "seat_number": seat_number,
                    "price": float(price),
                    "purchase_date": purchase_date,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "route": route
                })
            return tickets
        except Exception as e:
            print(f"Error fetching tickets: {e}")
            return []

    def get_all_tickets(self):
        try:
            query = """
                SELECT t.ticket_id, u.name, u.email, b.bus_name, b.bus_number, s.seat_number, t.price, t.purchase_date, b.route
                FROM tickets t
                JOIN users u ON t.user_id = u.user_id
                JOIN buses b ON t.bus_id = b.bus_id
                JOIN seats s ON t.seat_id = s.seat_id
            """
            results = self.db.fetch_all(query)
            tickets = []
            for row in results:
                ticket_id, user_name, user_email, bus_name, bus_number, seat_number, price, purchase_date, route = row
                tickets.append({
                    "ticket_id": ticket_id,
                    "user_name": user_name,
                    "user_email": user_email,
                    "bus_name": bus_name,
                    "bus_number": bus_number,
                    "seat_number": seat_number,
                    "price": float(price),
                    "purchase_date": purchase_date,
                    "route": route
                })
            return tickets
        except Exception as e:
            print(f"Error fetching all tickets: {e}")
            return []

    def cancel_ticket(self, ticket_id):
        try:
            ticket = self.db.fetch_one("SELECT seat_id FROM tickets WHERE ticket_id = %s", (ticket_id,))
            if not ticket:
                print("Ticket not found!")
                return False

            seat_id = ticket[0]

            # Delete ticket
            if not self.db.execute_query("DELETE FROM tickets WHERE ticket_id = %s", (ticket_id,)):
                print("Failed to cancel ticket!")
                return False

            # Free seat
            if not self.db.execute_query("UPDATE seats SET is_booked = FALSE WHERE seat_id = %s", (seat_id,)):
                print("Failed to free seat!")
                return False

            self.db.commit()
            print("Ticket canceled successfully!")
            return True
        except Exception as e:
            self.db.con.rollback()
            print(f"Error canceling ticket: {e}")
            return False
